# smart_file_classifier/gui/action_controller.py

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, QThread, QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

# --- Core Engine Imports ---
from smart_classifier.core.classification_engine import ClassificationEngine, DEFAULT_UNKNOWN_CATEGORY
from smart_classifier.core.file_operations import DuplicateStrategy, safe_move
from smart_classifier.core.undo_manager import UndoManager
from smart_classifier.core.config_manager import safely_add_or_update_rule
from smart_classifier.core.bulk_importer import BulkImporter

# --- GUI Component Imports (for dialogs) ---
from .learning_dialog import LearningDialog

logger = logging.getLogger(__name__)


# --- Worker Threads (Logically owned by the Controller) ---
# These are now all full, stable, and permanent classes.

class Worker(QObject):
    """The 'Supervisor' worker for the main classification task."""
    progress_percentage_updated = Signal(int)
    log_entry_created = Signal(dict)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, engine, source_dirs_list, dest_dir, strategy, mode, selected_paths=None):
        super().__init__()
        self.engine = engine
        self.source_dirs = source_dirs_list
        self.dest_dir = dest_dir
        self.strategy = strategy
        self.mode = mode
        self.selected_paths = selected_paths if selected_paths else []

    @Slot()
    def run(self):
        """Orchestrates the entire backend workflow in a background thread."""
        try:
            if self.mode == "MOVE_AS_IS":
                self.run_move_as_is()
            else:  # Covers "FULL_CLASSIFY" and "SELECTIVE_CLASSIFY"
                self.run_classification()
        except Exception as e:
            logger.critical(f"Worker thread error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

    def run_classification(self):
        """Handles both full and selective classification across multiple source directories."""
        self.engine.reset_state()
        all_files_to_process = []
        if self.mode == "FULL_CLASSIFY":
            for source_dir_str in self.source_dirs:
                source_dir = Path(source_dir_str)
                self.log_entry_created.emit({"status": "INFO", "message": f"Scanning directory: {source_dir}"})
                files_in_dir = self.engine.scan_directory(source_dir)
                all_files_to_process.extend(files_in_dir)
        elif self.mode == "SELECTIVE_CLASSIFY":
            self.log_entry_created.emit(
                {"status": "INFO", "message": f"Processing {len(self.selected_paths)} selected files..."})
            all_files_to_process = [Path(p) for p in self.selected_paths if Path(p).is_file()]
        plan = self.engine.generate_plan(all_files_to_process, self.dest_dir)
        if not plan:
            self.log_entry_created.emit(
                {"status": "DONE", "message": "No files found to classify in the selected directories."})
            self.progress_percentage_updated.emit(100)
            return
        self.engine.execute_plan(plan, self.strategy, self._handle_engine_progress)

    def run_move_as_is(self):
        """Handles the 'Move Folders As-Is' operation."""
        total_items = len(self.selected_paths)
        if total_items == 0: return
        move_as_is_dir = self.dest_dir / "Moved_As_Is"
        for i, path_str in enumerate(self.selected_paths):
            item = Path(path_str)
            p_type = self.engine._is_project_directory(item) if item.is_dir() else None
            dest = move_as_is_dir / "Software_Projects" if p_type else move_as_is_dir
            status, _ = safe_move(item, dest, self.strategy)
            msg = f"{item.name} ({p_type})" if p_type else item.name
            self.log_entry_created.emit({"status": status, "message": msg})
            self.progress_percentage_updated.emit(int(((i + 1) / total_items) * 100))

    @Slot(int, str, str)
    def _handle_engine_progress(self, percentage, file_name, status):
        """Receives raw data from the engine and emits refined signals to the UI."""
        if percentage != -1:
            self.progress_percentage_updated.emit(percentage)
        if file_name != "...":
            self.log_entry_created.emit({"status": status, "message": file_name})


class UndoWorker(QObject):
    """The dedicated worker for the Undo task."""
    progress_updated = Signal(int, int, str)
    finished = Signal()
    error_occurred = Signal(str)

    @Slot()
    def run(self):
        try:
            UndoManager.undo_last_operation(self.progress_updated.emit)
        except Exception as e:
            logger.critical(f"Undo worker thread error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()


class DryRunWorker(QObject):
    """A dedicated, stable worker for the Dry Run operation."""
    log_entry_created = Signal(dict)
    status_updated = Signal(str, bool)
    finished = Signal()

    def __init__(self, engine, source_dir_str, dest_dir_str):
        super().__init__()
        self.engine = engine
        self.source_dir_str = source_dir_str
        self.dest_dir_str = dest_dir_str

    @Slot()
    def run(self):
        try:
            self.status_updated.emit("Performing dry run...", False)
            source_dir = Path(self.source_dir_str)
            dest_dir = Path(self.dest_dir_str)
            plan = self.engine.generate_plan(self.engine.scan_directory(source_dir), dest_dir)
            self.log_entry_created.emit(
                {"status": "INFO", "message": f"--- 📜 DRY RUN: {len(plan)} operations planned ---"})
            for src, dest in plan[:100]:
                self.log_entry_created.emit({"status": "INFO", "message": f"[PLAN] '{src.name}' -> '{dest}'"})
            if len(plan) > 100:
                self.log_entry_created.emit({"status": "INFO", "message": f"...and {len(plan) - 100} more."})
            self.status_updated.emit("Dry run complete. Review the plan below.", False)
        except Exception as e:
            self.status_updated.emit(f"Dry run failed: {e}", True)
        finally:
            self.finished.emit()


# --- The Action Controller: The Brain of the GUI ---
class ActionController(QObject):
    """
    The non-visual brain of the GUI, handling all logic, state, and threading.
    This is the final, definitive, and fully functional version.
    """
    progress_percentage_updated = Signal(int)
    log_entry_created = Signal(dict)
    undo_progress_updated = Signal(int, int, str)
    state_changed = Signal(str, str)
    status_updated = Signal(str, bool)
    show_message_box = Signal(str, str, str)
    timer_tick = Signal(int)

    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.parent_widget = parent_widget
        self.engine = None
        self.active_thread = None
        self.active_worker = None
        self.elapsed_time = 0
        self.operation_timer = QTimer(self)
        self.operation_timer.setInterval(1000)
        self.operation_timer.timeout.connect(self._on_timer_tick)
        self._initialize_engine()

    def is_idle(self) -> bool:
        """A helper for the UI to check if an operation is running."""
        return self.active_thread is None

    def _initialize_engine(self):
        """Initializes the classification engine."""
        self.state_changed.emit("INITIALIZING", "CLASSIFY")
        try:
            config_path = Path(__file__).resolve().parents[2] / 'config' / 'file_types.json'
            self.engine = ClassificationEngine(config_path)
            self.status_updated.emit("Engine initialized successfully.", False)
        except Exception as e:
            self.engine = None
            self.status_updated.emit(f"Error: {e}", True)
            self.show_message_box.emit("critical", "Critical Error", f"Failed to initialize engine: {e}")
            self.state_changed.emit("ERROR", "CLASSIFY")
        finally:
            self.state_changed.emit("IDLE", "CLASSIFY")

    @Slot(list, str, str, str, list)
    def start_classification(self, source_dirs_list: list, dest_dir_str: str, strategy_str: str, mode: str,
                             selected_paths: list):
        """Starts a classification using the superior, non-blocking, and self-cleaning worker pattern."""
        self.elapsed_time = 0
        self.timer_tick.emit(self.elapsed_time)
        self.operation_timer.start()
        self.state_changed.emit("RUNNING", "CLASSIFY")
        self.status_updated.emit(f"Starting operation...", False)
        dest_dir = Path(dest_dir_str)
        strategy = {"Append Number": DuplicateStrategy.APPEND_NUMBER, "Skip": DuplicateStrategy.SKIP,
                    "Replace": DuplicateStrategy.REPLACE}[strategy_str]

        self.active_thread = QThread()
        self.active_worker = Worker(self.engine, source_dirs_list, dest_dir, strategy, mode, selected_paths)
        self.active_worker.moveToThread(self.active_thread)

        # Connect the functional signals
        self.active_worker.progress_percentage_updated.connect(self.progress_percentage_updated)
        self.active_worker.log_entry_created.connect(self.log_entry_created)
        self.active_worker.error_occurred.connect(self._handle_error)
        self.active_worker.finished.connect(self._on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)

        # --- THE DEFINITIVE FIX: Self-Cleaning Mechanism ---
        self.active_worker.finished.connect(self.active_thread.quit)
        self.active_thread.finished.connect(self.active_thread.deleteLater)
        self.active_worker.finished.connect(self.active_worker.deleteLater)
        # --- END FIX ---

        self.active_thread.start()

    @Slot(str, str)
    def start_undo(self, source_dir_str: str, dest_dir_str: str):
        """Starts an undo operation using the superior, non-blocking, and self-cleaning worker pattern."""
        if not UndoManager.has_undo_log():
            self.show_message_box.emit("info", "Nothing to Undo", "There is no previous operation to undo.")
            return
        self.elapsed_time = 0
        self.timer_tick.emit(self.elapsed_time)
        self.operation_timer.start()
        self.state_changed.emit("RUNNING", "UNDO")
        self.status_updated.emit("Performing undo...", False)

        self.active_thread = QThread()
        self.active_worker = UndoWorker()
        self.active_worker.moveToThread(self.active_thread)

        # Connect the functional signals
        self.active_worker.progress_updated.connect(self.undo_progress_updated)
        self.active_worker.error_occurred.connect(self._handle_error)
        self.active_worker.finished.connect(self._on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)

        # --- THE DEFINITIVE FIX: Self-Cleaning Mechanism ---
        self.active_worker.finished.connect(self.active_thread.quit)
        self.active_thread.finished.connect(self.active_thread.deleteLater)
        self.active_worker.finished.connect(self.active_worker.deleteLater)
        # --- END FIX ---

        self.active_thread.start()

    @Slot(str, str)
    def start_dry_run(self, source_dir_str: str, dest_dir_str: str):
        """Performs a dry run using the superior, non-blocking, and self-cleaning worker pattern."""
        self.state_changed.emit("RUNNING", "CLASSIFY")

        self.active_thread = QThread()
        self.active_worker = DryRunWorker(self.engine, source_dir_str, dest_dir_str)
        self.active_worker.moveToThread(self.active_thread)

        # Connect the functional signals
        self.active_worker.log_entry_created.connect(self.log_entry_created)
        self.active_worker.status_updated.connect(self.status_updated)
        self.active_worker.finished.connect(self._on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)

        # --- THE DEFINITIVE FIX: Self-Cleaning Mechanism ---
        self.active_worker.finished.connect(self.active_thread.quit)
        self.active_thread.finished.connect(self.active_thread.deleteLater)
        self.active_worker.finished.connect(self.active_worker.deleteLater)
        # --- END FIX ---

        self.active_thread.start()

    @Slot()
    def pause_operation(self):
        """Sends the pause signal to the engine."""
        if self.engine: self.operation_timer.stop(); self.engine.pause(); self.state_changed.emit("PAUSED",
                                                                                                  "CLASSIFY"); self.status_updated.emit(
            "Operation Paused.", False)

    @Slot()
    def resume_operation(self):
        """Sends the resume signal to the engine."""
        if self.engine: self.operation_timer.start(); self.engine.resume(); self.state_changed.emit("RUNNING",
                                                                                                    "CLASSIFY"); self.status_updated.emit(
            "Operation resumed.", False)

    @Slot()
    def cancel_operation(self):
        """Sends the cancel signal to the engine."""
        if self.engine: self.operation_timer.stop(); self.status_updated.emit("Cancelling operation...",
                                                                              False); self.engine.cancel()

    @Slot()
    def start_bulk_import(self):
        """Handles the user request to bulk import rules from a CSV file."""
        if not self.engine: return
        file_path, _ = QFileDialog.getOpenFileName(self.parent_widget, "Select CSV Rules File", "", "CSV Files (*.csv)")
        if not file_path: return
        try:
            importer = BulkImporter(self.engine.config_path)
            importer.process_csv(Path(file_path))
            report = importer.report
            report_str = "--- Bulk Import Complete ---\n\n"
            if report["added"]: report_str += f"✅ Added {len(report['added'])} new rules.\n"
            if report["updated"]: report_str += f"🔧 Resolved conflicts for {len(report['updated'])} rules.\n"
            if report["duplicates"]: report_str += f"ℹ️ Skipped {len(report['duplicates'])} duplicate rules.\n"
            if report[
                "errors"]: report_str += f"❌ Encountered {len(report['errors'])} errors.\n\nSee app.log for details."
            self.show_message_box.emit("info", "Import Complete", report_str)
            self.engine._load_classification_rules()
        except Exception as e:
            self.show_message_box.emit("critical", "Import Failed", f"A critical error occurred: {e}")

    @Slot()
    def _on_operation_finished(self):
        """
        The definitive, non-blocking cleanup method. It is guaranteed to reset the UI
        and keep the application open and ready for the next operation.
        """
        self.operation_timer.stop()
        is_cancelled = self.engine and self.engine._is_cancelled

        dest_dir = self.active_worker.dest_dir if self.active_worker and hasattr(self.active_worker,
                                                                                 'dest_dir') else None
        if self.engine and self.engine.unresolved_files and not is_cancelled and dest_dir:
            self._handle_unresolved_files(dest_dir)

        if is_cancelled:
            self.status_updated.emit("Operation cancelled by user.", True)
            self.log_entry_created.emit({"status": "ERROR", "message": "--- Operation Cancelled By User ---"})
        else:
            self.status_updated.emit("Operation finished.", False)
            if not (self.engine and self.engine.unresolved_files):
                if hasattr(self.active_worker, 'mode') and self.active_worker.mode != "DRY_RUN" and not isinstance(
                        self.active_worker, UndoWorker):
                    self.show_message_box.emit("info", "Success", "Operation completed successfully!")

        # --- THE DEFINITIVE DEADLOCK FIX ---
        # We simply release our program's references. We DO NOT call .wait().
        self.active_thread = None
        self.active_worker = None

        # This line is now GUARANTEED to be reached, restoring UI responsiveness.
        self.state_changed.emit("IDLE", "CLASSIFY")
        # --- END FIX ---

    @Slot(str)
    def _handle_error(self, error_message: str):
        """Handles errors from worker threads."""
        self.status_updated.emit(f"Error: {error_message}", True)
        self.show_message_box.emit("error", "Operation Failed", f"An error occurred: {error_message}")
        self._on_operation_finished()

    @Slot()
    def _on_timer_tick(self):
        """Increments the timer and emits the new time."""
        self.elapsed_time += 1
        self.timer_tick.emit(self.elapsed_time)

    def _handle_unresolved_files(self, dest_dir: Path):
        """Orchestrates the user-guided learning workflow."""
        unresolved_map = {}
        for file_path in self.engine.unresolved_files:
            ext = file_path.suffix.lower() if file_path.suffix else "[no_extension]"
            if ext not in unresolved_map: unresolved_map[ext] = []
            unresolved_map[ext].append(file_path)
        all_categories = sorted(
            list(set(rule["category"] for rules in self.engine.extension_map.values() for rule in rules)))
        for ext, files in unresolved_map.items():
            dialog = LearningDialog(ext, all_categories, self.parent_widget)
            if dialog.exec():
                selection = dialog.get_selection()
                if not selection: continue
                final_category = selection["category"]
                for file_path in files:
                    ext_folder = ext[1:] if ext.startswith('.') else "no_extension"
                    source = dest_dir / "_UNRESOLVED" / ext_folder / file_path.name
                    dest = dest_dir / final_category / ext_folder
                    if source.exists():
                        safe_move(source, dest, DuplicateStrategy.APPEND_NUMBER)
                        self.log_entry_created.emit(
                            {"status": "INFO", "message": f"[FINALIZED] '{file_path.name}' -> {final_category}"})
                if selection["remember"]:
                    new_rule = {"extension": ext, "category": final_category,
                                "description": f"{ext} file (user-defined)", "analysis_rules": []}
                    safely_add_or_update_rule(self.engine.config_path, new_rule)
            else:
                for file_path in files:
                    ext_folder = ext[1:] if ext.startswith('.') else "no_extension"
                    source = dest_dir / "_UNRESOLVED" / ext_folder / file_path.name
                    dest = dest_dir / DEFAULT_UNKNOWN_CATEGORY / ext_folder
                    if source.exists():
                        safe_move(source, dest, DuplicateStrategy.APPEND_NUMBER)
                        self.log_entry_created.emit({"status": "INFO",
                                                     "message": f"[DEFAULTED] '{file_path.name}' -> {DEFAULT_UNKNOWN_CATEGORY}"})
        self.engine._load_classification_rules()
