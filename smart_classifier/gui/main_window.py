# smart_classifier/gui/main_window.py

import logging
import sys
from pathlib import Path

# --- CORRECTED IMPORT BLOCK ---
from PySide6.QtCore import QObject, QThread, Signal, Slot, QStringListModel, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QComboBox, QMessageBox,
    QGridLayout, QSpacerItem, QListView, QSizePolicy
)
# --- END CORRECTION ---

# --- Local Imports ---
from smart_classifier.core.classification_engine import ClassificationEngine
from smart_classifier.core.file_operations import DuplicateStrategy
from smart_classifier.core.undo_manager import UndoManager
from smart_classifier.utils.logger import setup_logging
from .resources import load_stylesheet, get_icon, ICON_SIZE, validate_assets
from .widgets import DirectorySelector, StatusWidget

logger = logging.getLogger(__name__)


# --- Worker Threads (Correct and Unchanged) ---
class Worker(QObject):
    progress_updated = Signal(int, str, str)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, engine, plan, strategy):
        super().__init__()
        self.engine, self.plan, self.strategy = engine, plan, strategy

    @Slot()
    def run(self):
        try:
            self.engine.execute_plan(self.plan, self.strategy, self.progress_updated.emit)
        except Exception as e:
            logger.critical(f"An error occurred in the worker thread: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()


class UndoWorker(QObject):
    progress_updated = Signal(int, int, str)
    finished = Signal()
    error_occurred = Signal(str)

    @Slot()
    def run(self):
        try:
            UndoManager.undo_last_operation(self.progress_updated.emit)
        except Exception as e:
            logger.critical(f"An error occurred in the undo worker thread: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()


# --- Main Application Window (Final Corrected Version) ---
class MainWindow(QMainWindow):
    """The main GUI window, fully refactored for professionalism, scalability, and maintainability."""

    def __init__(self):
        """The constructor for the main window."""
        super().__init__()
        self.setWindowTitle(" Smart File Classifier v3.0")
        self.setWindowIcon(get_icon("app_icon"))
        self.setGeometry(100, 100, 900, 700)

        self.engine = None
        self.active_thread = None
        self.active_worker = None

        self.init_ui()
        self.connect_signals()
        self.initialize_engine()

    def init_ui(self):
        """Creates and arranges all widgets and sets their icons."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.source_selector = DirectorySelector("Source Directory:")
        self.dest_selector = DirectorySelector("Destination Directory:")
        self.source_selector.browse_button.setIcon(get_icon("folder-open"))
        self.dest_selector.browse_button.setIcon(get_icon("folder-open"))

        grid_layout = QGridLayout()
        self.duplicates_label = QLabel("Duplicate Files:")
        self.duplicates_combo = QComboBox()
        self.duplicates_combo.addItems(["Append Number", "Skip", "Replace"])

        self.dry_run_button = QPushButton(" Dry Run")
        self.start_button = QPushButton(" Start")
        self.pause_button = QPushButton(" Pause")
        self.resume_button = QPushButton(" Resume")
        self.cancel_button = QPushButton(" Cancel")
        self.undo_button = QPushButton(" Undo")

        self.dry_run_button.setIcon(get_icon("preview"))
        self.start_button.setIcon(get_icon("start"))
        self.pause_button.setIcon(get_icon("pause"))
        self.resume_button.setIcon(get_icon("resume"))
        self.cancel_button.setIcon(get_icon("cancel"))
        self.undo_button.setIcon(get_icon("undo"))

        all_buttons = [
            self.dry_run_button, self.start_button, self.pause_button, self.resume_button,
            self.cancel_button, self.undo_button, self.source_selector.browse_button,
            self.dest_selector.browse_button
        ]
        for btn in all_buttons:
            btn.setIconSize(ICON_SIZE)

        action_button_layout = QHBoxLayout()
        action_button_layout.addWidget(self.start_button)
        action_button_layout.addWidget(self.pause_button)
        action_button_layout.addWidget(self.resume_button)
        action_button_layout.addWidget(self.cancel_button)
        action_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        action_button_layout.addWidget(self.dry_run_button)
        action_button_layout.addWidget(self.undo_button)

        grid_layout.addWidget(self.duplicates_label, 0, 0)
        grid_layout.addWidget(self.duplicates_combo, 0, 1)

        self.status_widget = StatusWidget()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.log_view = QListView()
        self.log_model = QStringListModel()
        self.log_view.setModel(self.log_model)

        main_layout.addWidget(self.source_selector)
        main_layout.addWidget(self.dest_selector)
        main_layout.addLayout(grid_layout)
        main_layout.addLayout(action_button_layout)
        main_layout.addWidget(self.status_widget)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("Operation Log:"))
        main_layout.addWidget(self.log_view)

    def connect_signals(self):
        """
        Connects ALL widget signals to their handler methods, ensuring that every
        button, including Pause, Resume, and Cancel, is fully functional.
        """
        # --- Main operations ---
        self.start_button.clicked.connect(self.start_classification)
        self.dry_run_button.clicked.connect(self.handle_dry_run)
        self.undo_button.clicked.connect(self.handle_undo)

        # --- In-flight operation controls ---
        # These lines activate the Pause, Resume, and Cancel buttons.
        self.pause_button.clicked.connect(self.handle_pause)
        self.resume_button.clicked.connect(self.handle_resume)
        self.cancel_button.clicked.connect(self.handle_cancel)

    def initialize_engine(self):
        """Initializes the classification engine and handles potential errors."""
        self._update_button_states("INITIALIZING")
        try:
            config_path = Path(__file__).resolve().parents[2] / 'config' / 'file_types.json'
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found at: {config_path}")
            self.engine = ClassificationEngine(config_path)
            self.status_widget.set_status("Engine initialized successfully.")
            self._update_button_states("IDLE")
        except Exception as e:
            self.engine = None
            self.show_error_message(f"Critical error during initialization: {e}")
            self.status_widget.set_status(f"Error: {e}", is_error=True)
            self._update_button_states("ERROR")

    def _prepare_for_operation(self):
        """Validates inputs and prepares the UI for an operation, resetting the progress bar."""
        source_dir = Path(self.source_selector.path())
        dest_dir = Path(self.dest_selector.path())

        if not (source_dir.is_dir() and dest_dir.is_dir()):
            self.show_error_message("Please select valid source and destination directories.")
            return None

        self.log_model.setStringList([])
        self.progress_bar.setValue(0)
        self._set_progress_bar_color('success')
        return source_dir, dest_dir

    @Slot()
    def start_classification(self):
        """Starts the classification process using the robust worker pattern."""
        prep_result = self._prepare_for_operation()
        if not prep_result: return
        source_dir, dest_dir = prep_result
        self._update_button_states("RUNNING")
        strategy_map = {"Append Number": DuplicateStrategy.APPEND_NUMBER, "Skip": DuplicateStrategy.SKIP,
                        "Replace": DuplicateStrategy.REPLACE}
        duplicate_strategy = strategy_map[self.duplicates_combo.currentText()]
        plan = self.engine.generate_plan(self.engine.scan_directory(source_dir), dest_dir)
        if not plan:
            self.status_widget.set_status("No files found to classify.")
            self._update_button_states("IDLE")
            return
        self.status_widget.set_status(f"Classifying {len(plan)} files...")
        self.active_thread = QThread()
        self.active_worker = Worker(self.engine, plan, duplicate_strategy)
        self.active_worker.moveToThread(self.active_thread)
        self.active_worker.progress_updated.connect(self.update_progress)
        self.active_worker.error_occurred.connect(self.handle_error)
        self.active_worker.finished.connect(self.on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)
        self.active_thread.finished.connect(self.active_thread.deleteLater)
        self.active_worker.finished.connect(self.active_worker.deleteLater)
        self.active_thread.start()

    @Slot()
    def handle_dry_run(self):
        """Performs a dry run and displays the plan."""
        prep_result = self._prepare_for_operation()
        if not prep_result: return
        source_dir, dest_dir = prep_result
        self.status_widget.set_status("Performing dry run...")
        plan = self.engine.generate_plan(self.engine.scan_directory(source_dir), dest_dir)
        log_lines = [f"--- 📜 DRY RUN: {len(plan)} operations planned ---"]
        for src, dest in plan[:100]:
            log_lines.append(f"[PLAN] '{src.name}' -> '{dest}'")
        if len(plan) > 100:
            log_lines.append(f"...and {len(plan) - 100} more.")
        self.log_model.setStringList(log_lines)
        self.status_widget.set_status("Dry run complete. Review the plan below.")
        self._update_button_states("IDLE")

    @Slot()
    def handle_undo(self):
        """Initiates the undo operation using the robust worker pattern."""
        reply = QMessageBox.question(self, 'Confirm Undo',
                                     "This will attempt to reverse the last classification operation. Are you sure?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        prep_result = self._prepare_for_operation()
        if not prep_result: return
        self._update_button_states("RUNNING")
        self.status_widget.set_status("Performing undo...")
        self.active_thread = QThread()
        self.active_worker = UndoWorker()
        self.active_worker.moveToThread(self.active_thread)
        self.active_worker.progress_updated.connect(self.update_undo_progress)
        self.active_worker.error_occurred.connect(self.handle_error)
        self.active_worker.finished.connect(self.on_operation_finished)
        self.active_thread.started.connect(self.active_worker.run)
        self.active_thread.finished.connect(self.active_thread.deleteLater)
        self.active_worker.finished.connect(self.active_worker.deleteLater)
        self.active_thread.start()

    @Slot()
    def handle_pause(self):
        """Handles the Pause button click."""
        if self.engine:
            self.engine.pause()
            self._update_button_states("PAUSED")
            self.status_widget.set_status("Operation paused.")
            self._set_progress_bar_color('paused')

    @Slot()
    def handle_resume(self):
        """Handles the Resume button click."""
        if self.engine:
            self.engine.resume()
            self._update_button_states("RUNNING")
            self.status_widget.set_status("Operation resumed.")
            self._set_progress_bar_color('success')

    @Slot()
    def handle_cancel(self):
        """Handles the Cancel button click after user confirmation."""
        reply = QMessageBox.question(self, 'Confirm Cancel',
                                     "Are you sure you want to cancel the current operation?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes and self.engine:
            self.status_widget.set_status("Cancelling operation...")
            self.engine.cancel()

    def _add_log_message(self, message: str):
        """Appends a message to the scalable log view."""
        row = self.log_model.rowCount()
        self.log_model.insertRow(row)
        index = self.log_model.index(row)
        self.log_model.setData(index, message)
        self.log_view.scrollToBottom()

    @Slot(int, str, str)
    def update_progress(self, percentage, file_name, status):
        """Updates UI during classification."""
        self.progress_bar.setValue(percentage)
        self._add_log_message(f"[{status}] {file_name}")

    @Slot(int, int, str)
    def update_undo_progress(self, processed, total, message):
        """Updates UI during undo operation."""
        if total > 0:
            self.progress_bar.setValue(int((processed / total) * 100))
        self._add_log_message(message)

    @Slot()
    def on_operation_finished(self):
        """
        Cleans up after any operation completes. This version uses a robust, non-blocking
        cleanup sequence to guarantee the UI never freezes and the application
        remains open and ready for the next operation.
        """
        # Step 1: Set the final status message and progress bar state based on the outcome.
        if self.engine and self.engine._is_cancelled:
            self.status_widget.set_status("Operation cancelled by user.", is_error=True)
            self._add_log_message("\n❌ --- Operation Cancelled By User --- ❌")
            self._set_progress_bar_color('failed')
        elif self.progress_bar.value() == 100:
            self.status_widget.set_status("Operation completed successfully.")
            self._add_log_message("\n✅ --- Classification Successfully Completed --- ✅")
            QMessageBox.information(self, "Success", "All files have been successfully classified!")
        else:
            self.status_widget.set_status("Operation finished.")

        # Step 2: Reset the progress bar for the next run.
        self.progress_bar.setValue(0)
        if self.progress_bar.property('state') != 'failed':
            self._set_progress_bar_color('success')

        # Step 3: Perform a safe, non-blocking cleanup of the thread and worker.
        if self.active_thread:
            # We signal the thread to quit gracefully.
            self.active_thread.quit()

            # We then release our references to the objects, allowing Python's
            # garbage collector to handle their eventual deletion.
            # Most importantly, we DO NOT call .wait(), which prevents any blocking.
            self.active_thread = None
            self.active_worker = None

        # Step 4: Reliably reset the UI buttons to the idle state, making the app
        # ready for the next operation.
        self._update_button_states("IDLE")

    @Slot(str)
    def handle_error(self, error_message):
        """Handles errors from worker threads."""
        self.status_widget.set_status(f"Error: {error_message}", is_error=True)
        self._set_progress_bar_color('failed')
        self.on_operation_finished()
        self.show_error_message(f"An operation failed: {error_message}")

    def _set_progress_bar_color(self, state: str):
        """Sets the color of the progress bar based on the state ('success', 'paused', or 'failed')."""
        if state == 'paused':
            self.progress_bar.setProperty('state', 'paused')
        elif state == 'failed':
            self.progress_bar.setProperty('state', 'failed')
        else:
            self.progress_bar.setProperty('state', 'success')
        self.progress_bar.style().polish(self.progress_bar)

    def _update_button_states(self, state: str):
        """Manages the enabled/disabled state of all action buttons based on application state."""
        is_idle = state == "IDLE"
        is_running = state == "RUNNING"
        is_paused = state == "PAUSED"
        self.start_button.setEnabled(is_idle)
        self.dry_run_button.setEnabled(is_idle)
        self.undo_button.setEnabled(is_idle)
        self.source_selector.setEnabled(is_idle)
        self.dest_selector.setEnabled(is_idle)
        self.duplicates_combo.setEnabled(is_idle)
        self.pause_button.setEnabled(is_running)
        self.resume_button.setEnabled(is_paused)
        self.cancel_button.setEnabled(is_running or is_paused)
        if state == "ERROR" or state == "INITIALIZING":
            for btn in [self.start_button, self.dry_run_button, self.undo_button, self.pause_button, self.resume_button,
                        self.cancel_button]:
                btn.setEnabled(False)

    def show_error_message(self, message: str):
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        """Prevents closing the app while an operation is in progress."""
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

    # Step 1: Configure the application-wide logging system.
    setup_logging()

    # Step 2: Validate that all required assets (icons, styles) are present.
    validate_assets()

    # Step 3: Create the core Qt application instance.
    app = QApplication(sys.argv)

    # Step 4: Load and apply our professional dark theme stylesheet.
    app.setStyleSheet(load_stylesheet())

    # Step 5: Create our main window. This calls the __init__ method we perfected.
    window = MainWindow()

    # Step 6: Make the window visible to the user.
    window.show()

    # Step 7: Start the application's main event loop and ensure a clean exit.
    sys.exit(app.exec())