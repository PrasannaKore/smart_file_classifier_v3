# smart_classifier/core/undo_manager.py

import json
import logging
from pathlib import Path
from tqdm import tqdm
from typing import Callable

from .file_operations import safe_move, DuplicateStrategy

logger = logging.getLogger(__name__)

# The dedicated path for our transaction log.
TRANSACTION_LOG_PATH = Path(__file__).resolve().parents[2] / 'last_operation.json'


class UndoManager:
    """
    Manages the transaction log for undoing the last classification operation.
    """

    @staticmethod
    def clear_log():
        """Creates a new, empty transaction log before an operation starts."""
        try:
            with open(TRANSACTION_LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump([], f)
            logger.info("Transaction log cleared and ready for new operation.")
        except IOError as e:
            logger.error(f"Failed to clear transaction log: {e}")

    @staticmethod
    def log_move(source_path: Path, dest_path: Path):
        """Appends a successful move operation to the transaction log."""
        log_entry = {
            'source': str(source_path.resolve()),
            'destination': str(dest_path.resolve())
        }
        try:
            # Read-modify-write is a safe way to handle JSON lists.
            with open(TRANSACTION_LOG_PATH, 'r+', encoding='utf-8') as f:
                log_data = json.load(f)
                log_data.append(log_entry)
                f.seek(0)
                json.dump(log_data, f, indent=2)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to write to transaction log: {e}")

    @staticmethod
    def undo_last_operation(
            progress_callback: Callable[[int, int, str], None] | None = None
    ):
        """
        Reads the transaction log and moves files back, providing progress updates.

        Args:
            progress_callback: An optional function that receives updates.
                               It is called with (items_processed, total_items, message).
        """
        if not TRANSACTION_LOG_PATH.exists():
            logger.warning("No transaction log found. Cannot perform undo.")
            if progress_callback:
                progress_callback(0, 0, "No previous operation found to undo.")
            return False

        try:
            with open(TRANSACTION_LOG_PATH, 'r', encoding='utf-8') as f:
                moves_to_undo = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Could not read or parse transaction log: {e}")
            if progress_callback:
                progress_callback(0, 0, "Error: Could not read the undo log.")
            return False

        if not moves_to_undo:
            if progress_callback:
                progress_callback(0, 0, "Last operation was empty. Nothing to undo.")
            return True

        total_moves = len(moves_to_undo)
        moves_processed = 0

        if progress_callback:
            progress_callback(moves_processed, total_moves, f"Starting undo for {total_moves} files...")

        for move in reversed(moves_to_undo):
            source_file = Path(move['destination'])
            original_parent_dir = Path(move['source']).parent
            message: str

            if source_file.exists():
                safe_move(
                    source_path=source_file,
                    destination_dir=original_parent_dir,
                    duplicate_strategy=DuplicateStrategy.APPEND_NUMBER
                )
                message = f"Reverted: {source_file.name}"
            else:
                logger.warning(f"File '{source_file}' not found at destination. Cannot undo this move.")
                message = f"[SKIPPED] Original file not found: {source_file.name}"

            moves_processed += 1
            if progress_callback:
                progress_callback(moves_processed, total_moves, message)

        TRANSACTION_LOG_PATH.unlink()
        logger.info("Undo operation complete. Transaction log has been cleared.")
        if progress_callback:
            progress_callback(total_moves, total_moves, "✅ Undo operation complete.")

        return True
