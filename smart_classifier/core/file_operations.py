# smart_classifier/core/file_operations.py

import logging
import shutil
from enum import Enum, auto
from pathlib import Path

# Set up a logger for this module. The main application will configure its handlers.
# This allows us to see detailed logs of file operations without cluttering the console.
logger = logging.getLogger(__name__)


class DuplicateStrategy(Enum):
    """
    Enumeration for handling duplicate file scenarios in a type-safe way.
    Using an Enum prevents errors that could arise from using simple strings.
    """
    SKIP = auto()
    REPLACE = auto()
    APPEND_NUMBER = auto()


def _get_unique_path(destination_path: Path) -> Path:
    """
    Generates a unique path if the destination already exists by appending a number.

    This is a helper function that ensures no files are ever overwritten when
    the APPEND_NUMBER strategy is chosen.

    Example:
        If 'image.jpg' exists, it will return 'image_1.jpg'.
        If 'image_1.jpg' also exists, it will return 'image_2.jpg'.

    Args:
        destination_path: The original intended destination path.

    Returns:
        A unique path object that does not currently exist on the filesystem.
    """
    if not destination_path.exists():
        return destination_path

    parent = destination_path.parent
    stem = destination_path.stem  # Filename without the extension
    suffix = destination_path.suffix  # The file extension (e.g., '.txt')
    counter = 1

    while True:
        # Create a new filename like 'filename_1.ext', 'filename_2.ext', etc.
        new_path = parent.joinpath(f"{stem}_{counter}{suffix}")
        if not new_path.exists():
            logger.debug(f"Found unique path for '{destination_path}': '{new_path}'")
            return new_path
        counter += 1


def safe_move(
        source_path: Path,
        destination_dir: Path,
        duplicate_strategy: DuplicateStrategy = DuplicateStrategy.APPEND_NUMBER,
) -> tuple[str, Path | None]:
    """
    Safely moves a file to a destination directory with robust error handling
    and strategies for resolving duplicate filenames.

    This is the core function for all file movements, built with the principle
    of "Security + Safety + Robustness".

    Args:
        source_path: The path to the file to be moved.
        destination_dir: The directory where the file should be moved.
        duplicate_strategy: The strategy for handling existing files (default: APPEND_NUMBER).

    Returns:
        A tuple containing the operation status ('MOVED', 'SKIPPED', 'ERROR')
        and the final path of the file (or None if an error occurred).
    """
    # Pre-flight check: Ensure the source is a valid file before doing anything.
    if not source_path.is_file():
        logger.error(f"Source path is not a valid file: {source_path}")
        return "ERROR", None

    # This line constructs the full destination path in an OS-agnostic way.
    destination_path = destination_dir.joinpath(source_path.name)

    try:
        # Step 1: Ensure the destination directory exists. This is a critical
        # safety step to prevent 'FileNotFoundError' when classifying into new categories.
        destination_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: Handle potential duplicates before the move operation.
        if destination_path.exists():
            if duplicate_strategy == DuplicateStrategy.SKIP:
                logger.info(f"Skipping '{source_path.name}' as it already exists in destination.")
                return "SKIPPED", destination_path

            elif duplicate_strategy == DuplicateStrategy.REPLACE:
                logger.warning(f"Replacing existing file at '{destination_path}'.")
                # The destination_path remains the same; shutil.move will handle the overwrite.

            elif duplicate_strategy == DuplicateStrategy.APPEND_NUMBER:
                # If we need to append, we call our helper to get a new, safe path.
                destination_path = _get_unique_path(destination_path)

        # Step 3: Perform the core move operation.
        # shutil.move is highly optimized. On the same drive, it's a near-instant
        # atomic rename. If moving across drives (e.g., C: to D: on Windows),
        # it automatically performs a safe copy-then-delete operation.
        logger.info(f"Moving '{source_path}' to '{destination_path}'")
        shutil.move(str(source_path), str(destination_path))

        return "MOVED", destination_path

    except PermissionError:
        logger.error(f"Permission denied for '{source_path}'. Check file/folder permissions.")
        return "ERROR", None
    except Exception as e:
        # This is a master exception handler to catch any other unforeseen issues
        # (e.g., disk full, file in use by another program), preventing the
        # entire application from crashing.
        logger.critical(f"An unexpected error occurred while moving '{source_path}': {e}", exc_info=True)
        return "ERROR", None