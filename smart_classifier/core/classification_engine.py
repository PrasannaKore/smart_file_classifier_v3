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
        self.config_path = config_path
        # This dictionary will hold our parsed rules, mapping extension -> category
        # e.g., {".pdf": "Documents & Text", ".jpg": "Images & Graphics"}
        self.classification_rules: Dict[str, str] = {}
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
                        Executes the generated move plan.

                        This is the method that performs the actual file operations using our
                        safe_move function. It is designed to be run in a separate thread.

                        Args:
                            plan: The move plan generated by generate_plan().
                            duplicate_strategy: The strategy to use for duplicate files.
                            progress_callback: An optional function to call for progress updates.
                                               It receives (progress_percentage, current_file_name, status).
                        """
        """
        Executes the move plan in parallel using a pool of worker threads
        for maximum performance and logs transactions for undo.
        """
        total_files = len(plan)
        if total_files == 0:
            logger.info("Plan is empty. Nothing to execute.")
            return

        logger.info(f"Executing plan for {total_files} files with strategy: {duplicate_strategy.name}")

        UndoManager.clear_log()

        # Determine the number of threads to use.
        max_workers = get_optimal_thread_count()
        files_processed = 0

        # The ThreadPoolExecutor manages the lifecycle of the threads for us.
        # It's a safe and efficient way to perform parallel operations.
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # We submit each file move operation to the thread pool.
            # executor.submit() returns a 'future' object, which represents
            # the pending result of the operation.
            future_to_source = {
                executor.submit(safe_move, source_path, dest_dir, duplicate_strategy): source_path
                for source_path, dest_dir in plan
            }

            # as_completed() gives us the results of the futures as they finish,
            # not in the order they were submitted. This is perfect for progress updates.
            for future in as_completed(future_to_source):
                source_path = future_to_source[future]
                try:
                    # Get the result from the completed future.
                    status, final_dest_path = future.result()

                    if status == "MOVED":
                        # This part remains thread-safe because our UndoManager
                        # uses a read-modify-write pattern on the JSON file,
                        # though for extreme performance, a queue-based logger would be better.
                        # For this project, file-based locking is sufficient.
                        UndoManager.log_move(source_path, final_dest_path)

                except Exception as e:
                    # If the safe_move function raised an unexpected exception.
                    status = "ERROR"
                    logger.error(f"Error processing {source_path} in thread: {e}")

                files_processed += 1
                if progress_callback:
                    progress_percentage = int((files_processed / total_files) * 100)
                    progress_callback(progress_percentage, source_path.name, status)

        logger.info("Execution of plan complete.")