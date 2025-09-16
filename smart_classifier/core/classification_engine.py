# smart_classifier/core/classification_engine.py

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our robust file operations module and the duplicate strategy Enum
from .file_operations import DuplicateStrategy, safe_move
from .undo_manager import UndoManager
from smart_classifier.utils.thread_manager import get_optimal_thread_count
import threading

# Configure logger for this module
logger = logging.getLogger(__name__)

# Define the supported version for our configuration file.
# This is a critical safety check as mandated.
SUPPORTED_CONFIG_VERSION = "2.0"
DEFAULT_UNKNOWN_CATEGORY = "Others"


class ClassificationEngine:
    """
    The main engine for scanning, classifying, and organizing files.

    This class is designed to be UI-agnostic. It can be used by the CLI,
    the GUI, or any other interface. It handles the core logic of the
    application in a structured, testable, and modular way.
    """


    def __init__(self, config_path: Path):
        """
        Initializes the engine and loads the classification rules from the config file.

        Args:
            config_path: The path to the file_types.json configuration file.
        """
        """Initializes the engine and its state-management objects."""
        self.config_path = config_path
        self.classification_rules: Dict[str, str] = {}

        # --- NEW: State Management for Threading ---
        self._is_cancelled = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Initially, the event is "set" (meaning: not paused)

        self._load_classification_rules()

    def _load_classification_rules(self):
        """
        Loads and parses the file_types.json configuration.

        It performs a crucial version check and builds an efficient reverse
        mapping for quick lookups during classification. This is where we
        enforce the compatibility rules.
        """
        logger.info(f"Loading classification rules from: {self.config_path}")
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # --- Version Check ---
            metadata = data.get("_metadata", {})
            version = metadata.get("version")
            if version != SUPPORTED_CONFIG_VERSION:
                error_msg = f"Unsupported configuration version: '{version}'. This application requires version '{SUPPORTED_CONFIG_VERSION}'."
                logger.critical(error_msg)
                # In a real app, this would raise a custom exception for the UI to catch.
                raise ValueError(error_msg)

            # --- Rule Parsing ---
            # We create a reverse map for fast lookups: {extension: category_name}
            # This is far more efficient than searching the structure for every file.
            for category, extensions in data.items():
                if category == "_metadata":
                    continue
                if isinstance(extensions, dict):
                    for ext in extensions.keys():
                        if ext in self.classification_rules:
                            logger.warning(
                                f"Duplicate extension '{ext}' found. Using first entry in category '{self.classification_rules[ext]}'.")
                        else:
                            self.classification_rules[ext.lower()] = category

            logger.info(f"Successfully loaded {len(self.classification_rules)} classification rules.")

        except FileNotFoundError:
            logger.critical(f"Configuration file not found at: {self.config_path}")
            raise
        except (json.JSONDecodeError, ValueError) as e:
            logger.critical(f"Error parsing configuration file: {e}")
            raise

    def scan_directory(self, source_dir: Path) -> List[Path]:
        """
        Scans the source directory recursively and returns a list of all files.

        Args:
            source_dir: The directory to scan.

        Returns:
            A list of Path objects, each representing a file.
        """
        logger.info(f"Scanning directory: {source_dir}")
        if not source_dir.is_dir():
            logger.error(f"Source path is not a valid directory: {source_dir}")
            return []

        # Using rglob('*') is a powerful and efficient way to find all files
        # in all subdirectories. We then filter to ensure we only have files.
        files = [item for item in source_dir.rglob('*') if item.is_file()]
        logger.info(f"Scan complete. Found {len(files)} files.")
        return files

    def generate_plan(self, files: List[Path], dest_dir: Path) -> List[Tuple[Path, Path]]:
        """
                Generates a 'move plan' without touching any files (Dry Run).

                This plan details the source and intended destination for every file,
                allowing the user to review before execution.

                Args:
                    files: A list of file paths to classify.
                    dest_dir: The root destination directory.

                Returns:
                    A list of tuples, where each tuple is (source_path, destination_directory).
                """
        """
        Generates a 'move plan' with the new sub-directory structure.
        """
        logger.info("Generating classification plan (Dry Run)...")
        plan = []
        for file_path in files:
            category = self.classification_rules.get(file_path.name.lower())

            if not category:
                category = self.classification_rules.get(file_path.suffix.lower(), DEFAULT_UNKNOWN_CATEGORY)

            # --- MODIFIED BLOCK ---
            # This is the updated logic to include the extension-based sub-directory.
            destination_category_dir = dest_dir.joinpath(category)

            # Use the file's extension as the sub-directory name.
            # We strip the leading dot ('.') from the suffix for a clean folder name.
            # For files with no extension, they are placed in the root of the category.
            extension = file_path.suffix[1:].lower() if file_path.suffix else "no_extension"

            # This line constructs the final, deeper path.
            # e.g., .../Destination/Images & Graphics/jpg
            final_destination_dir = destination_category_dir.joinpath(extension)

            plan.append((file_path, final_destination_dir))
            # --- END MODIFIED BLOCK ---

        logger.info(f"Generated plan for {len(plan)} file operations.")
        return plan

    def execute_plan(
            self,
            plan: List[Tuple[Path, Path]],
            duplicate_strategy: DuplicateStrategy,
            progress_callback: Callable[[int, str, str], None] | None = None
    ):
        """
        Executes the move plan sequentially, with robust support for Pause, Resume, and Cancel.
        This single-threaded orchestration guarantees control and UI responsiveness.
        """
        total_files = len(plan)
        if total_files == 0:
            logger.info("Plan is empty. Nothing to execute.")
            return

        # (PRESERVED) Step 1: Ensure all state flags are reset for a clean run.
        self.reset_state()

        logger.info(f"Executing plan for {total_files} files with strategy: {duplicate_strategy.name}")

        # (PRESERVED) Step 2: Prepare the transaction log for a potential undo operation.
        UndoManager.clear_log()

        files_processed = 0

        # (PRESERVED) Step 3: Iterate through every file in the plan.
        for source_path, dest_dir in plan:
            # --- NEW CONTROL LOGIC ---
            # This is the "checkpoint" that gives us full control.
            self._pause_event.wait()
            if self._is_cancelled:
                logger.warning("Operation cancelled by user. Halting processing.")
                break
            # --- END NEW LOGIC ---

            try:
                # (PRESERVED) Step 4: Call the robust safe_move function for each file.
                status, final_dest_path = safe_move(source_path, dest_dir, duplicate_strategy)

                # (PRESERVED) Step 5: Log the transaction for the Undo feature on success.
                if status == "MOVED":
                    UndoManager.log_move(source_path, final_dest_path)

            # (PRESERVED) Step 6: Handle exceptions gracefully for a single file.
            except Exception as e:
                status = "ERROR"
                logger.error(f"Error processing {source_path}: {e}", exc_info=True)

            # (PRESERVED) Step 7: Send real-time progress updates back to the UI.
            files_processed += 1
            if progress_callback:
                progress_percentage = int((files_processed / total_files) * 100)
                progress_callback(progress_percentage, source_path.name, status)

        logger.info("Execution of plan complete.")

    def pause(self):
        """Signals the running operation to pause."""
        self._pause_event.clear() # Clearing the event causes the worker to wait.
        logger.info("Pause signal sent to classification engine.")

    def resume(self):
        """Signals the paused operation to resume."""
        self._pause_event.set() # Setting the event allows the worker to continue.
        logger.info("Resume signal sent to classification engine.")

    # We also add a reset_state method for good measure
    def reset_state(self):
        """Resets the state flags for a new operation."""
        self._is_cancelled = False
        self._pause_event.set()

    def cancel(self):
        """Signals the running operation to cancel."""
        self._is_cancelled = True
        self._pause_event.set()  # Also un-pause if cancelling, so the loop can exit
        logger.info("Cancel signal sent to classification engine.")
