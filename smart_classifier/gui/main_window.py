# smart_classifier/gui/main_window.py

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot, QStringListModel
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QComboBox, QMessageBox,
    QTextEdit, QGridLayout, QSpacerItem, QSizePolicy, QListView
)

# --- Local Imports ---
from smart_classifier.core.classification_engine import ClassificationEngine
from smart_classifier.core.file_operations import DuplicateStrategy
from smart_classifier.core.undo_manager import UndoManager
from smart_classifier.utils.logger import setup_logging

from .resources import load_stylesheet, get_icon, ICON_SIZE, validate_assets
from .widgets import DirectorySelector, StatusWidget
from . import resources_rc # Import the compiled resources


# --- Worker Threads (Unchanged but included for completeness) ---
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
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()


# --- Main Application Window ---
class MainWindow(QMainWindow):
    """The main GUI window, refactored for professionalism and maintainability."""

    def __init__(self):
        """The constructor for the main window."""
        super().__init__()
        self.setWindowTitle(" Smart File Classifier v3.0")

        # Set the main window icon. This is the only icon set in the constructor.
        self.setWindowIcon(get_icon("app_icon"))
        self.setGeometry(100, 100, 900, 700)

        # Initialize state variables
        self.engine = None
        self.active_thread = None
        self.active_worker = None

        # --- The Correct Order of Operations ---
        # 1. Build the UI components
        self.init_ui()
        # 2. Connect signals from UI components to methods
        self.connect_signals()
        # 3. Initialize the backend engine
        self.initialize_engine()
        # 4. Set the final, initial state of the UI buttons
        self._update_button_states("IDLE")

    def init_ui(self):
        """Creates and arranges all widgets and sets their icons."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Directory selectors now use our custom widget
        self.source_selector = DirectorySelector("Source Directory:")
        self.dest_selector = DirectorySelector("Destination Directory:")

        # Set icons for the browse buttons within the custom widgets
        self.source_selector.browse_button.setIcon(get_icon("folder-open"))
        self.dest_selector.browse_button.setIcon(get_icon("folder-open"))

        # Options and Actions layout
        grid_layout = QGridLayout()
        self.duplicates_label = QLabel("Duplicate Files:")
        self.duplicates_combo = QComboBox()
        self.duplicates_combo.addItems(["Append Number", "Skip", "Replace"])

        # Create all action buttons
        self.dry_run_button = QPushButton(" Dry Run")
        self.start_button = QPushButton(" Start")
        self.pause_button = QPushButton(" Pause")
        self.resume_button = QPushButton(" Resume")
        self.cancel_button = QPushButton(" Cancel")
        self.undo_button = QPushButton(" Undo")

        # Set icons for all action buttons
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

        # Status and Logging components
        self.status_widget = StatusWidget()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        # The new, scalable log viewer
        self.log_view = QListView()
        self.log_model = QStringListModel()
        self.log_view.setModel(self.log_model)

        # Assemble the final layout
        main_layout.addWidget(self.source_selector)
        main_layout.addWidget(self.dest_selector)
        main_layout.addLayout(grid_layout)
        main_layout.addLayout(action_button_layout)
        main_layout.addWidget(self.status_widget)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("Operation Log:"))
        main_layout.addWidget(self.log_view)

    def connect_signals(self):
        """Connects widget signals to their handler methods."""
        self.start_button.clicked.connect(self.start_classification)
        self.dry_run_button.clicked.connect(self.handle_dry_run)
        self.undo_button.clicked.connect(self.handle_undo)
        # TODO: Connect Pause, Resume, Cancel buttons when logic is implemented

    def initialize_engine(self):
        """Initializes the classification engine and handles potential errors."""
        self._update_button_states("INITIALIZING")
        try:
            config_path = Path(__file__).resolve().parents[2] / 'config' / 'file_types.json'
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found at: {config_path}")
            self.engine = ClassificationEngine(config_path)
            self.status_widget.set_status("Engine initialized successfully.")
        except Exception as e:
            self.engine = None
            self.show_error_message(f"Critical error during initialization: {e}")
            self.status_widget.set_status(f"Error: {e}", is_error=True)
            self._update_button_states("ERROR")

    def _prepare_for_operation(self):
        """Validates inputs and prepares the UI for an operation."""
        source_dir = Path(self.source_selector.path())
        dest_dir = Path(self.dest_selector.path())

        if not (source_dir.is_dir() and dest_dir.is_dir()):
            self.show_error_message("Please select valid source and destination directories.")
            return None

        self.log_model.setStringList([])  # Clear the log view
        self.progress_bar.setValue(0)
        return source_dir, dest_dir

    @Slot()
    def start_classification(self):
        """Starts the classification process in a background thread."""
        prep_result = self._prepare_for_operation()
        if not prep_result: return
        source_dir, dest_dir = prep_result

        strategy_map = {"Append Number": DuplicateStrategy.APPEND_NUMBER, "Skip": DuplicateStrategy.SKIP,
                        "Replace": DuplicateStrategy.REPLACE}
        duplicate_strategy = strategy_map[self.duplicates_combo.currentText()]

        plan = self.engine.generate_plan(self.engine.scan_directory(source_dir), dest_dir)
        if not plan:
            self.status_widget.set_status("No files found to classify.")
            self._update_button_states(is_running=False)
            return

        self.status_widget.set_status(f"Classifying {len(plan)} files...")
        self.active_thread = QThread()
        self.active_worker = Worker(self.engine, plan, duplicate_strategy)
        self.active_worker.moveToThread(self.active_thread)

        self.active_thread.started.connect(self.active_worker.run)
        self.active_worker.finished.connect(self.on_operation_finished)
        self.active_worker.progress_updated.connect(self.update_progress)
        self.active_worker.error_occurred.connect(self.handle_error)
        self.active_thread.start()
        self._update_button_states("RUNNING")

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
        reply = QMessageBox.question(self, 'Confirm Undo', "Reverse the last operation?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        self._update_button_states(is_running=True)
        self.status_widget.set_status("Performing undo...")

        self.active_thread = QThread()
        self.active_worker = UndoWorker()
        self.active_worker.moveToThread(self.active_thread)

        self.active_thread.started.connect(self.active_worker.run)
        self.active_worker.finished.connect(self.on_operation_finished)
        self.active_worker.progress_updated.connect(self.update_undo_progress)
        self.active_worker.error_occurred.connect(self.handle_error)
        self.active_thread.start()
        self._update_button_states("RUNNING")

    def _add_log_message(self, message: str):
        """Appends a message to the scalable log view."""
        # This is the new, memory-efficient way to add logs.
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
        if total > 0: self.progress_bar.setValue(int((processed / total) * 100))
        self._add_log_message(message)

    @Slot()
    def on_operation_finished(self):
        """Cleans up after any operation completes."""
        if self.progress_bar.value() == 100:
            self.status_widget.set_status("Operation completed successfully.")

        if self.active_thread:
            self.active_thread.quit()
            self.active_thread.wait()
            self.active_thread = None
        self._update_button_states("IDLE")

    @Slot(str)
    def handle_error(self, error_message):
        """Handles errors from worker threads."""
        self.status_widget.set_status(f"Error: {error_message}", is_error=True)
        self.on_operation_finished()
        self.show_error_message(f"An operation failed: {error_message}")
        self._update_button_states("ERROR")

    def _update_button_states(self, state: str):
        """Centralized method to manage the enabled/disabled state of all action buttons."""
        """Manages the enabled/disabled state of all action buttons based on application state."""
        # state can be "IDLE", "RUNNING", "PAUSED", "INITIALIZING", "ERROR"
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
    setup_logging() # Ensure logging is configured
    validate_assets() # Validate assets at startup
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
