# smart_classifier/core/classification_engine.py

import json
import logging
import os
import queue
from pathlib import Path
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor

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
        Scans the source directory recursively, now intelligently ignoring common
        system-generated hidden files like Thumbs.db and .DS_Store.
        """
        logger.info(f"Scanning directory: {source_dir}")
        if not source_dir.is_dir():
            logger.error(f"Source path is not a valid directory: {source_dir}")
            return []

        # List of system files/patterns to ignore completely
        ignore_list = ['thumbs.db', '.ds_store']

        found_files = []
        try:
            for root, _, filenames in os.walk(source_dir):
                for filename in filenames:
                    # --- NEW: The intelligent filter ---
                    if filename.lower() not in ignore_list:
                        file_path = Path(root) / filename
                        found_files.append(file_path)
                    else:
                        logger.debug(f"Ignoring system file: {filename}")
        except Exception as e:
            logger.error(f"An error occurred during directory scan: {e}", exc_info=True)
            return []

        logger.info(f"Scan complete. Found {len(found_files)} user files.")
        return found_files

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
        Executes the plan using a high-performance Producer-Consumer pattern with
        a fully robust, graceful shutdown protocol for cancellation.
        """
        total_files = len(plan)
        if total_files == 0: return

        self.reset_state()
        logger.info(f"Executing hybrid plan for {total_files} files...")
        UndoManager.clear_log()

        task_queue = queue.Queue(maxsize=get_optimal_thread_count() * 2)
        files_processed = 0

        def consumer():
            """The worker function that runs in the thread pool."""
            while not self._is_cancelled:
                try:
                    self._pause_event.wait(timeout=0.1)
                    if self._is_cancelled: break

                    # Get a task from the queue.
                    task = task_queue.get(timeout=0.1)

                    # --- THE DEFINITIVE FIX ---
                    # First, check if the task is a "poison pill" (None).
                    # If it is, the consumer's job is done, and it should exit.
                    if task is None:
                        break
                    # --- END FIX ---

                    # If it's a real task, unpack it and proceed.
                    source_path, dest_dir = task

                    status, final_dest_path = safe_move(source_path, dest_dir, duplicate_strategy)
                    if status == "MOVED":
                        UndoManager.log_move(source_path, final_dest_path)

                    if progress_callback:
                        progress_callback(-1, source_path.name, status)

                    task_queue.task_done()
                except queue.Empty:
                    if self._producer_done:
                        break
                except Exception as e:
                    logger.error(f"Error in consumer thread: {e}", exc_info=True)
                    task_queue.task_done()

        # --- The Producer ---
        self._producer_done = False
        with ThreadPoolExecutor(max_workers=get_optimal_thread_count()) as executor:
            consumers = [executor.submit(consumer) for _ in range(get_optimal_thread_count())]

            try:
                for source_path, dest_dir in plan:
                    self._pause_event.wait()
                    if self._is_cancelled:
                        logger.warning("Cancellation detected in producer.")
                        break

                    task_queue.put((source_path, dest_dir))
                    files_processed += 1
                    if progress_callback:
                        percentage = int((files_processed / total_files) * 100)
                        progress_callback(percentage, "...", "...")
            finally:
                # --- Graceful Shutdown Protocol ---
                self._producer_done = True

                # Wake up any sleeping consumers with poison pills so they can exit.
                for _ in consumers:
                    try:
                        task_queue.put(None, timeout=0.1)
                    except queue.Full:
                        pass  # If queue is full, consumers are busy and will see flags later.

                # Wait for all consumer threads to finish their work and exit.
                executor.shutdown(wait=True)
                logger.info("All consumer threads have shut down.")

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
