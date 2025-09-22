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
# By placing the Worker classes here, we fully encapsulate the GUI's background
# processing logic within the controller, keeping the visual tabs clean.

class Worker(QObject):
    """
    The 'Supervisor' worker for the main classification task. This is the final,
    superior version that embodies the logic of the old `run` and `continue_with_plan` methods.
    """
    progress_percentage_updated = Signal(int)
    log_entry_created = Signal(dict)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, engine, source_dir, dest_dir, strategy, mode, selected_paths=None):
        super().__init__()
        self.engine = engine
        self.source_dir = source_dir
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
        """Handles both full and selective classification."""
        self.engine.reset_state()

        files_to_process = []
        if self.mode == "FULL_CLASSIFY":
            self.log_entry_created.emit({"status": "INFO", "message": f"Scanning directory: {self.source_dir}"})
            files_to_process = self.engine.scan_directory(self.source_dir)
        elif self.mode == "SELECTIVE_CLASSIFY":
            self.log_entry_created.emit(
                {"status": "INFO", "message": f"Processing {len(self.selected_paths)} selected files..."})
            files_to_process = [Path(p) for p in self.selected_paths if Path(p).is_file()]

        plan = self.engine.generate_plan(files_to_process, self.dest_dir)
        if not plan:
            self.log_entry_created.emit({"status": "DONE", "message": "No files found to classify."})
            self.progress_percentage_updated.emit(100)
            return

        # The final, atomic execution step.
        self.engine.execute_plan(plan, self.strategy, self._handle_engine_progress)

    def run_move_as_is(self):
        """Handles the 'Move Folders As-Is' operation."""
        total_items = len(self.selected_paths)
        if total_items == 0: return

        move_as_is_dir = self.dest_dir / "Moved_As_Is"

        for i, path_str in enumerate(self.selected_paths):
            item_path = Path(path_str)
            project_type = self.engine._is_project_directory(item_path) if item_path.is_dir() else None
            dest = move_as_is_dir / "Software_Projects" if project_type else move_as_is_dir
            status, _ = safe_move(item_path, dest, self.strategy)
            msg = f"{item_path.name} ({project_type})" if project_type else item_path.name
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


# --- The Action Controller: The Brain of the GUI ---
class ActionController(QObject):
    """
    This non-visual class is the new brain of the GUI. It handles all backend
    interactions, thread management, and state changes, completely decoupling
    the UI from the application's logic.
    """
    # --- Signals that the UI tabs will listen to ---
    progress_percentage_updated = Signal(int)
    log_entry_created = Signal(dict)
    undo_progress_updated = Signal(int, int, str)
    state_changed = Signal(str, str)  # Emits state (e.g., "IDLE") and operation_type
    status_updated = Signal(str, bool)  # Emits message and is_error flag
    show_message_box = Signal(str, str, str)  # type, title, message
    timer_tick = Signal(int)  # Emits the current elapsed time in seconds

    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.parent_widget = parent_widget  # Store a reference to the main window for dialogs
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

    @Slot(str, str, str, str, list)
    def start_classification(self, source_dir_str, dest_dir_str, strategy_str, mode, selected_paths):
        """Starts a classification operation by creating and running a Worker thread."""
        self.elapsed_time = 0
        self.timer_tick.emit(self.elapsed_time)
        self.operation_timer.start()
        self.state_changed.emit("RUNNING", "CLASSIFY")
        self.status_updated.emit(f"Starting operation...", False)
        source_dir, dest_dir = Path(source_dir_str), Path(dest_dir_str)
        strategy = {"Append Number": DuplicateStrategy.APPEND_NUMBER, "Skip": DuplicateStrategy.SKIP,
                    "Replace": DuplicateStrategy.REPLACE}[strategy_str]

        self.active_thread = QThread()
        self.active_worker = Worker(self.engine, source_dir, dest_dir, strategy, mode, selected_paths)
        self.active_worker.moveToThread(self.active_thread)

        self.active_worker.progress_percentage_updated.connect(self.progress_percentage_updated)
        self.active_worker.log_entry_created.connect(self.log_entry_created)
        self.active_worker.error_occurred.connect(self._handle_error)
        self.active_worker.finished.connect(self._on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)

        self.active_thread.start()

    @Slot(str, str)
    def start_undo(self, source_dir_str, dest_dir_str):
        """Starts an undo operation."""
        self.elapsed_time = 0
        self.timer_tick.emit(self.elapsed_time)
        self.operation_timer.start()
        self.state_changed.emit("RUNNING", "UNDO")
        self.status_updated.emit("Performing undo...", False)

        self.active_thread = QThread()
        self.active_worker = UndoWorker()
        self.active_worker.moveToThread(self.active_thread)

        self.active_worker.progress_updated.connect(self.undo_progress_updated)
        self.active_worker.error_occurred.connect(self._handle_error)
        self.active_worker.finished.connect(self._on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)

        self.active_thread.start()

    @Slot(str, str)
    def start_dry_run(self, source_dir_str: str, dest_dir_str: str):
        """Performs a dry run in a simple background thread to keep the UI responsive."""
        self.state_changed.emit("RUNNING", "CLASSIFY")
        self.status_updated.emit("Performing dry run...", False)

        class DryRunWorker(QObject):
            finished = Signal()

            def run(self_worker):
                try:
                    engine = self.engine
                    source_dir, dest_dir = Path(source_dir_str), Path(dest_dir_str)
                    plan = engine.generate_plan(engine.scan_directory(source_dir), dest_dir)
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

        self.active_thread = QThread()
        self.active_worker = DryRunWorker()
        self.active_worker.moveToThread(self.active_thread)
        self.active_worker.finished.connect(self._on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)
        self.active_thread.start()

    @Slot()
    def pause_operation(self):
        """Sends the pause signal to the engine."""
        if self.engine: self.operation_timer.stop(); self.engine.pause(); self.state_changed.emit("PAUSED",
                                                                                                  "CLASSIFY"); self.status_updated.emit(
            "Operation Paused. Click Resume to continue.", False)

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
        Handles the completion of any background task. This is the crucial trigger
        for our "Ask and Learn" workflow.
        """
        self.operation_timer.stop()
        is_cancelled = self.engine and self.engine._is_cancelled

        # This is the "magic". After the main work is done, we check if the engine
        # has any questions for the user.
        dest_dir = self.active_worker.dest_dir if self.active_worker and hasattr(self.active_worker,
                                                                                 'dest_dir') else None
        if self.engine and self.engine.unresolved_files and not is_cancelled and dest_dir:
            # If there are questions, we begin the sacred "Human-in-the-Loop" phase.
            self._handle_unresolved_files(dest_dir)

        # The final status update is now more intelligent.
        if is_cancelled:
            self.status_updated.emit("Operation cancelled by user.", True)
            self.log_entry_created.emit({"status": "ERROR", "message": "--- Operation Cancelled By User ---"})
        else:
            # We don't show the "Success" popup if the learning dialog was just shown,
            # as that would be confusing for the user.
            if not (self.engine and self.engine.unresolved_files):
                self.status_updated.emit("Operation finished.", False)
                self.show_message_box.emit("info", "Success", "Operation completed successfully!")
            else:
                # The user has just finished teaching the app, so we give a different message.
                self.status_updated.emit("Finalization complete.", False)

        # The final, robust cleanup.
        if self.active_thread:
            self.active_thread.quit()
            self.active_thread.wait()

        self.active_thread, self.active_worker = None, None
        self.state_changed.emit("IDLE", "CLASSIFY")

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
        """
        REPLACED: This superior version now meticulously logs every user-guided
        file move to the UndoManager, ensuring a complete and truly reversible transaction.
        """
        unresolved_map = {}
        for file_path in self.engine.unresolved_files:
            # We use a placeholder for files with no extension to create a valid folder name.
            ext = file_path.suffix.lower() if file_path.suffix else "[no_extension]"
            if ext not in unresolved_map:
                unresolved_map[ext] = []
            unresolved_map[ext].append(file_path)

        # Get a unique list of all known categories to populate the dialog's dropdown.
        all_categories = sorted(
            list(set(rule["category"] for rules in self.engine.extension_map.values() for rule in rules)))

        # Now we ask the user about each unique new extension.
        for ext, files in unresolved_map.items():
            dialog = LearningDialog(ext, all_categories, self.parent_widget)
            if dialog.exec():
                # User clicked "OK"
                selection = dialog.get_selection()
                if not selection: continue  # Skip if user entered an empty category

                final_category = selection["category"]

                # --- Finalization Loop for "OK" ---
                for file_path in files:
                    ext_folder_name = ext[1:] if ext.startswith('.') else "no_extension"
                    # Define the source (where the file is now, in our temp folder)
                    source_file = dest_dir / "_UNRESOLVED" / ext_folder_name / file_path.name
                    # Define the final, user-chosen destination
                    destination_dir = dest_dir / final_category / ext_folder_name

                    if source_file.exists():
                        # --- THE DEFINITIVE FIX ---
                        # We perform the final move from the temporary folder.
                        status, final_dest_path = safe_move(source_file, destination_dir,
                                                            DuplicateStrategy.APPEND_NUMBER)

                        # If that final move was successful, we LOG IT to the same transaction.
                        if status == "MOVED":
                            # CRUCIAL: We log the move from the ORIGINAL source path,
                            # not the temporary one, to create a perfect return ticket.
                            UndoManager.log_move(file_path, final_dest_path)
                        # --- END FIX ---

                        self.log_entry_created.emit(
                            {"status": "INFO", "message": f"[FINALIZED] '{file_path.name}' -> {final_category}"})

                if selection["remember"]:
                    # Teach the application for the future.
                    new_rule = {"extension": ext, "category": final_category,
                                "description": f"{ext} file (user-defined)", "analysis_rules": []}
                    safely_add_or_update_rule(self.engine.config_path, new_rule)
            else:
                # User clicked "Cancel" on the dialog. We move the files to the default "Others" category.
                for file_path in files:
                    ext_folder_name = ext[1:] if ext.startswith('.') else "no_extension"
                    source_file = dest_dir / "_UNRESOLVED" / ext_folder_name / file_path.name
                    destination_dir = dest_dir / DEFAULT_UNKNOWN_CATEGORY / ext_folder_name
                    if source_file.exists():
                        # We must also log this fallback move to the transaction log.
                        status, final_dest_path = safe_move(source_file, destination_dir,
                                                            DuplicateStrategy.APPEND_NUMBER)
                        if status == "MOVED":
                            UndoManager.log_move(file_path, final_dest_path)
                        self.log_entry_created.emit({"status": "INFO",
                                                     "message": f"[DEFAULTED] '{file_path.name}' -> {DEFAULT_UNKNOWN_CATEGORY}"})

        # After all user decisions are handled, we can now safely clean up the temporary folder.
        try:
            unresolved_root = dest_dir / "_UNRESOLVED"
            if unresolved_root.exists():
                import shutil
                shutil.rmtree(unresolved_root)
        except Exception as e:
            logger.error(f"Could not clean up _UNRESOLVED folder: {e}")

        # Finally, we reload the engine's rules to include any newly learned knowledge.
        self.engine._load_classification_rules()
