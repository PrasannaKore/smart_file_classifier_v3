# smart_classifier/gui/main_window.py

import logging
import sys
from pathlib import Path

# --- PySide6 Imports ---
from PySide6.QtCore import QObject, QThread, Signal, Slot, QSize, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QComboBox, QMessageBox,
    QGridLayout, QSpacerItem, QSizePolicy, QFileDialog, QGroupBox,
    QRadioButton
)

# --- Our Application's Own Modules ---
# This is the power of our modular design. We are now assembling our
# application from a suite of professional, specialized components.

# Core Engine Components
from smart_classifier.core.classification_engine import ClassificationEngine, DEFAULT_UNKNOWN_CATEGORY
from smart_classifier.core.file_operations import DuplicateStrategy, safe_move
from smart_classifier.core.undo_manager import UndoManager
from smart_classifier.core.bulk_importer import BulkImporter
from smart_classifier.core.config_manager import safely_add_or_update_rule

# GUI Components
from .resources import load_stylesheet, get_icon, ICON_SIZE, validate_assets
from .widgets import DirectorySelector, StatusWidget
from .log_viewer import LogViewer  # Our new, superior log viewer
# (We don't import LogModel here because it's an internal part of LogViewer)

# Utility Components
from smart_classifier.utils.logger import setup_logging

logger = logging.getLogger(__name__)


# --- Worker Threads ---
# These classes are the bridge between the UI and the non-blocking backend.

class Worker(QObject):
    """
    The "Supervisor" worker for the main classification task. It is a self-contained
    unit that handles the entire backend workflow, ensuring the UI never freezes.
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

        # Connect the engine's callback to our internal aggregator
        self.engine.execute_plan(plan, self.strategy, self._handle_engine_progress)

    def run_move_as_is(self):
        """Handles the 'Move Folders As-Is' operation."""
        total_items = len(self.selected_paths)
        if total_items == 0:
            self.log_entry_created.emit({"status": "DONE", "message": "No items were selected to move."})
            self.progress_percentage_updated.emit(100)
            return

        # Create a dedicated sub-folder in the destination for these items.
        move_as_is_dir = self.dest_dir / "Moved_As_Is"

        for i, path_str in enumerate(self.selected_paths):
            item_path = Path(path_str)

            project_type = self.engine._is_project_directory(item_path) if item_path.is_dir() else None
            if project_type:
                project_dest_dir = move_as_is_dir / "Software_Projects"
                status, _ = safe_move(item_path, project_dest_dir, self.strategy)
                msg = f"{item_path.name} ({project_type})"
                self.log_entry_created.emit({"status": status, "message": msg})
            else:
                status, _ = safe_move(item_path, move_as_is_dir, self.strategy)
                self.log_entry_created.emit({"status": status, "message": item_path.name})

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


# --- Main Application Window ---
# --- Main Application Window (Final Corrected Version) ---
class MainWindow(QMainWindow):
    """
    The main application window, fully refactored for professionalism, scalability, and maintainability.
    This is the definitive, feature-complete version.
    """

    def __init__(self):
        """The constructor for the main window."""
        super().__init__()
        self.setWindowTitle(" Smart File Classifier v3.0")
        self.setWindowIcon(get_icon("app_icon"))
        self.setGeometry(100, 100, 900, 750)

        self.engine = None
        self.active_thread = None
        self.active_worker = None

        self.elapsed_time = 0
        self.operation_timer = QTimer(self)
        self.operation_timer.setInterval(1000)

        self.init_ui()
        self.connect_signals()
        self.initialize_engine()

    def init_ui(self):
        """Creates and arranges all widgets using our reusable components and a resilient layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        self.source_selector = DirectorySelector("Source Directory:")
        self.dest_selector = DirectorySelector("Destination Directory:")

        options_layout = QHBoxLayout()
        self.duplicates_label = QLabel("Duplicate Files:")
        self.duplicates_combo = QComboBox()
        self.duplicates_combo.addItems(["Append Number", "Skip", "Replace"])
        options_layout.addWidget(self.duplicates_label)
        options_layout.addWidget(self.duplicates_combo)
        options_layout.addStretch()

        mode_group = QGroupBox("Advanced Operation Modes (Optional)")
        mode_group.setCheckable(True)
        mode_group.setChecked(False)
        mode_layout = QVBoxLayout()
        self.mode_full_classify = QRadioButton("Full Directory Classification (Default)")
        self.mode_move_as_is = QRadioButton("Move Selected Folders/Files As-Is")
        self.mode_selective_classify = QRadioButton("Classify Selected Files Only")
        self.mode_full_classify.setChecked(True)
        mode_layout.addWidget(self.mode_full_classify)
        mode_layout.addWidget(self.mode_move_as_is)
        mode_layout.addWidget(self.mode_selective_classify)
        mode_group.setLayout(mode_layout)

        action_button_layout = QHBoxLayout()
        self.start_button = QPushButton(" Start")
        self.pause_button = QPushButton(" Pause")
        self.resume_button = QPushButton(" Resume")
        self.cancel_button = QPushButton(" Cancel")
        self.dry_run_button = QPushButton(" Dry Run")
        self.undo_button = QPushButton(" Undo")

        self.start_button.setIcon(get_icon("start"))
        self.pause_button.setIcon(get_icon("pause"))
        self.resume_button.setIcon(get_icon("resume"))
        self.cancel_button.setIcon(get_icon("cancel"))
        self.dry_run_button.setIcon(get_icon("preview"))
        self.undo_button.setIcon(get_icon("undo"))
        self.source_selector.browse_button.setIcon(get_icon("folder-open"))
        self.dest_selector.browse_button.setIcon(get_icon("folder-open"))

        all_buttons = [self.start_button, self.pause_button, self.resume_button,
                       self.cancel_button, self.dry_run_button, self.undo_button,
                       self.source_selector.browse_button, self.dest_selector.browse_button]
        for btn in all_buttons:
            btn.setIconSize(ICON_SIZE)

        action_button_layout.addWidget(self.start_button)
        action_button_layout.addWidget(self.pause_button)
        action_button_layout.addWidget(self.resume_button)
        action_button_layout.addWidget(self.cancel_button)
        action_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        action_button_layout.addWidget(self.dry_run_button)
        action_button_layout.addWidget(self.undo_button)

        self.status_widget = StatusWidget()
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("TimerLabel")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.timer_label)

        self.log_view = LogViewer()

        main_layout.addWidget(self.source_selector)
        main_layout.addWidget(self.dest_selector)
        main_layout.addLayout(options_layout)
        main_layout.addWidget(mode_group)
        main_layout.addLayout(action_button_layout)
        main_layout.addWidget(self.status_widget)
        main_layout.addLayout(progress_layout)
        main_layout.addWidget(QLabel("Operation Log:"))
        main_layout.addWidget(self.log_view)

    def connect_signals(self):
        """Connects all UI signals to their respective handler slots."""
        self.start_button.clicked.connect(self.start_classification)
        self.pause_button.clicked.connect(self.handle_pause)
        self.resume_button.clicked.connect(self.handle_resume)
        self.cancel_button.clicked.connect(self.handle_cancel)
        self.dry_run_button.clicked.connect(self.handle_dry_run)
        self.undo_button.clicked.connect(self.handle_undo)
        self.operation_timer.timeout.connect(self._update_timer_display)
        self.source_selector.path_edit.textChanged.connect(self._check_input_validity)
        self.dest_selector.path_edit.textChanged.connect(self._check_input_validity)

    def initialize_engine(self):
        """Initializes the classification engine and handles potential errors."""
        self._update_button_states("INITIALIZING")
        try:
            config_path = Path(__file__).resolve().parents[2] / 'config' / 'file_types.json'
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            self.engine = ClassificationEngine(config_path)
            self.status_widget.set_status("Engine initialized successfully.")
            self._update_button_states("IDLE")
        except Exception as e:
            self.engine = None
            self.show_error_message(f"Critical error during initialization: {e}")
            self.status_widget.set_status(f"Error: {e}", is_error=True)
            self._update_button_states("ERROR")

    def _prepare_for_operation(self):
        """Validates inputs and resets the UI for a new operation."""
        source_path_text = self.source_selector.path().strip()
        dest_path_text = self.dest_selector.path().strip()
        if not source_path_text or not dest_path_text:
            self.show_error_message("Source and Destination directories must be selected.")
            return None

        source_dir = Path(source_path_text)
        dest_dir = Path(dest_path_text)
        if not source_dir.is_dir():
            self.show_error_message(f"Source is not a valid directory:\n{source_dir}")
            return None
        if not dest_dir.is_dir():
            self.show_error_message(f"Destination is not a valid directory:\n{dest_dir}")
            return None

        self.elapsed_time = 0
        self.timer_label.setText("00:00")
        self.operation_timer.start(1000)
        self.log_view.clear_logs()
        self.progress_bar.setValue(0)
        self._set_progress_bar_color('running')
        return source_dir, dest_dir

    @Slot()
    def start_classification(self):
        """Orchestrates the start of an operation based on the selected mode."""
        prep_result = self._prepare_for_operation()
        if not prep_result: return
        source_dir, dest_dir = prep_result

        mode_group = self.findChild(QGroupBox, "Advanced Operation Modes (Optional)")
        use_advanced_mode = mode_group.isChecked()

        operation_mode = "FULL_CLASSIFY"
        selected_paths = []

        if use_advanced_mode:
            if self.mode_move_as_is.isChecked():
                operation_mode = "MOVE_AS_IS"
                dialog = QFileDialog(self, "Select Folders/Files to Move As-Is", str(source_dir))
                dialog.setFileMode(QFileDialog.ExistingFiles)
                if dialog.exec():
                    selected_paths = dialog.selectedFiles()
                else:
                    self.operation_timer.stop(); return
            elif self.mode_selective_classify.isChecked():
                operation_mode = "SELECTIVE_CLASSIFY"
                dialog = QFileDialog(self, "Select Files to Classify", str(source_dir))
                dialog.setFileMode(QFileDialog.ExistingFiles)
                if dialog.exec():
                    selected_paths = dialog.selectedFiles()
                else:
                    self.operation_timer.stop(); return

        self._update_button_states("RUNNING")
        strategy_map = {"Append Number": DuplicateStrategy.APPEND_NUMBER, "Skip": DuplicateStrategy.SKIP,
                        "Replace": DuplicateStrategy.REPLACE}
        duplicate_strategy = strategy_map[self.duplicates_combo.currentText()]
        self.status_widget.set_status("Starting operation...")
        self.active_thread = QThread()
        self.active_worker = Worker(self.engine, source_dir, dest_dir, duplicate_strategy, operation_mode,
                                    selected_paths)
        self.active_worker.moveToThread(self.active_thread)
        self.active_worker.progress_percentage_updated.connect(self.progress_bar.setValue)
        self.active_worker.log_entry_created.connect(self._handle_log_entry)
        self.active_worker.error_occurred.connect(self.handle_error)
        self.active_worker.finished.connect(self.on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)
        self.active_thread.start()

    @Slot()
    def handle_dry_run(self):
        """Performs a dry run and displays the plan."""
        # This logic is self-contained and correct.
        prep_result = self._prepare_for_operation()
        if not prep_result: return
        source_dir, dest_dir = prep_result
        self.operation_timer.stop()  # Dry run is fast, no timer needed.

        self.status_widget.set_status("Performing dry run...")
        plan = self.engine.generate_plan(self.engine.scan_directory(source_dir), dest_dir)

        self.log_view.add_log_entry("INFO", f"--- 📜 DRY RUN: {len(plan)} operations planned ---")
        for src, dest in plan[:100]:
            self.log_view.add_log_entry("INFO", f"[PLAN] '{src.name}' -> '{dest}'")
        if len(plan) > 100:
            self.log_view.add_log_entry("INFO", f"...and {len(plan) - 100} more.")

        self.status_widget.set_status("Dry run complete. Review the plan below.")
        self._update_button_states("IDLE")

    @Slot()
    def handle_undo(self):
        """Initiates the undo operation."""
        # This logic is self-contained and correct.
        reply = QMessageBox.question(self, 'Confirm Undo', "This will reverse the last operation. Are you sure?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return

        prep_result = self._prepare_for_operation()
        if not prep_result: return

        self._update_button_states("RUNNING", operation_type="UNDO")
        self.status_widget.set_status("Performing undo...")

        self.active_thread = QThread()
        self.active_worker = UndoWorker()
        self.active_worker.moveToThread(self.active_thread)
        self.active_worker.progress_updated.connect(self.update_undo_progress)
        self.active_worker.error_occurred.connect(self.handle_error)
        self.active_worker.finished.connect(self.on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)
        self.active_thread.start()

    @Slot()
    def handle_pause(self):
        """Handles the Pause button click with instant feedback and timer control."""
        if self.engine:
            self.operation_timer.stop()
            self.status_widget.set_status("Pausing... waiting for active tasks to clear.")
            self.engine.pause()
            self._update_button_states("PAUSED")
            self.status_widget.set_status("Operation Paused. Click Resume to continue.")
            self._set_progress_bar_color('paused')

    @Slot()
    def handle_resume(self):
        """Handles the Resume button click with instant feedback and timer control."""
        if self.engine:
            self.operation_timer.start(1000)
            self.engine.resume()
            self._update_button_states("RUNNING")
            self.status_widget.set_status("Operation resumed.")
            self._set_progress_bar_color('running')

    @Slot()
    def handle_cancel(self):
        """Handles the Cancel button click after user confirmation."""
        if self.engine:
            reply = QMessageBox.question(self, 'Confirm Cancel', "Are you sure you want to cancel?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.operation_timer.stop()
                self.status_widget.set_status("Cancelling operation...")
                self.engine.cancel()

    @Slot(dict)
    def _handle_log_entry(self, entry: dict):
        self.log_view.add_log_entry(entry["status"], entry["message"])

    @Slot(int, int, str)
    def update_undo_progress(self, processed, total, message):
        if total > 0: self.progress_bar.setValue(int((processed / total) * 100))
        self.log_view.add_log_entry("INFO", message)

    @Slot()
    def on_operation_finished(self):
        """Cleans up after any operation completes with a robust, explicit sequence."""
        self.operation_timer.stop()
        final_state = 'success'
        if self.engine and self.engine._is_cancelled:
            self.status_widget.set_status("Operation cancelled by user.", is_error=True)
            self.log_view.add_log_entry("ERROR", "--- Operation Cancelled By User ---")
            final_state = 'failed'
        elif self.progress_bar.value() == 100:
            self.status_widget.set_status("Operation completed successfully.")
            self.log_view.add_log_entry("DONE", "--- Classification Successfully Completed ---")
            QMessageBox.information(self, "Success", "All files have been successfully classified!")
        else:
            self.status_widget.set_status("Operation finished.")

        self._set_progress_bar_color(final_state)

        if self.active_thread:
            self.active_thread.quit()
            self.active_thread.wait()

        self.active_thread = None
        self.active_worker = None
        self._update_button_states("IDLE")

        self.progress_bar.setValue(0)
        if final_state != 'failed':
            self._set_progress_bar_color('running')

    @Slot()
    def _update_timer_display(self):
        self.elapsed_time += 1
        minutes, seconds = divmod(self.elapsed_time, 60)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    @Slot(str)
    def handle_error(self, error_message):
        self.operation_timer.stop()
        self.status_widget.set_status(f"Error: {error_message}", is_error=True)
        self._set_progress_bar_color('failed')
        # We call on_operation_finished here to ensure consistent cleanup.
        self.on_operation_finished()
        self.show_error_message(f"An operation failed: {error_message}")

    def _set_progress_bar_color(self, state: str):
        self.progress_bar.setProperty('state', state)
        self.progress_bar.style().polish(self.progress_bar)

    def _check_input_validity(self):
        source_path = self.source_selector.path().strip()
        dest_path = self.dest_selector.path().strip()
        if self.active_thread is None:
            self._update_button_states("IDLE")

    def _update_button_states(self, state: str, operation_type: str = "CLASSIFY"):
        is_idle = state == "IDLE"
        is_running = state == "RUNNING"
        is_paused = state == "PAUSED"

        source_path = self.source_selector.path().strip()
        dest_path = self.dest_selector.path().strip()
        inputs_are_valid = bool(source_path and dest_path)

        can_start_operation = is_idle and inputs_are_valid
        self.start_button.setEnabled(can_start_operation)
        self.dry_run_button.setEnabled(can_start_operation)
        self.undo_button.setEnabled(is_idle)

        self.source_selector.setEnabled(is_idle)
        self.dest_selector.setEnabled(is_idle)
        self.duplicates_combo.setEnabled(is_idle)

        can_pause = is_running and operation_type == "CLASSIFY"
        can_resume = is_paused and operation_type == "CLASSIFY"
        self.pause_button.setEnabled(can_pause)
        self.resume_button.setEnabled(can_resume)

        self.cancel_button.setEnabled(is_running or is_paused)
        if state == "ERROR" or state == "INITIALIZING":
            for btn in [self.start_button, self.dry_run_button, self.undo_button, self.pause_button, self.resume_button,
                        self.cancel_button]:
                btn.setEnabled(False)

    def show_error_message(self, message: str):
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        if self.active_thread and self.active_thread.isRunning():
            reply = QMessageBox.question(self, 'Operation in Progress',
                                         "A task is running. Are you sure you want to quit?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def run_gui():
    """The entry point for the GUI application."""
    setup_logging()
    validate_assets()
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())