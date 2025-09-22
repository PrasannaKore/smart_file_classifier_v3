# smart_classifier/gui/tabs/classifier_tab.py

from pathlib import Path

from PySide6.QtCore import Slot, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar,
    QComboBox, QMessageBox, QGridLayout, QSpacerItem, QSizePolicy,
    QFileDialog, QGroupBox, QRadioButton
)

# We import the brain and the building blocks.
from ..action_controller import ActionController
from ..widgets import DirectorySelector, StatusWidget
from ..log_viewer import LogViewer
from ..resources import get_icon, ICON_SIZE


class ClassifierTab(QWidget):

    """
    The UI for the main classification feature. This widget is a "dumb" view.
    It holds all the visual components and delegates all actions to the ActionController.
    It contains no complex application logic itself.
    """

    def __init__(self, controller: ActionController, parent=None):
        super().__init__(parent)
        self.controller = controller

        # --- Build the entire UI for this tab ---
        self._init_ui()

        # --- Connect this UI's signals to the controller ---
        # The typo is corrected here.
        self.connect_signals()

        # --- Connect the controller's signals to this UI's slots ---
        self._connect_controller_signals()

        # --- PRESERVED AND RESTORED: All Crucial State Variables ---

        # This variable holds the state for the main operation timer display.
        self.elapsed_time = 0

        # This timer is the heart of our "form validation" feature. It is used to
        # display a temporary warning message in the status bar for a few seconds
        # if the user tries to perform an action with invalid inputs.
        self.status_flash_timer = QTimer(self)
        self.status_flash_timer.setSingleShot(True)  # It should only fire once per message.
        self.status_flash_timer.timeout.connect(self._clear_flash_status)

    def _init_ui(self):
        """
        REPLACED: This is the definitive, final version. It creates and arranges
        all widgets and implements the crucial "Fail-Safe" principle for ALL
        operational buttons, ensuring a perfectly safe and predictable initial state.
        """
        main_layout = QVBoxLayout(self)
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
        mode_group.setObjectName("Advanced Operation Modes (Optional)")
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

        # --- THE FINAL, COMPLETE FAIL-SAFE FIX ---
        # All buttons that control an operation are now "born" in a safe,
        # disabled state. They can only be enabled by our intelligent state machine
        # when it is logically correct to do so.
        self.start_button.setEnabled(False)
        self.dry_run_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        # The Undo button is the only exception, as it can be used when idle.
        # --- END FIX ---

        self.start_button.setIcon(get_icon("start"))
        self.pause_button.setIcon(get_icon("pause"))
        self.resume_button.setIcon(get_icon("resume"))
        self.cancel_button.setIcon(get_icon("cancel"))
        self.dry_run_button.setIcon(get_icon("preview"))
        self.undo_button.setIcon(get_icon("undo"))

        all_buttons = [self.start_button, self.pause_button, self.resume_button,
                       self.cancel_button, self.dry_run_button, self.undo_button]
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
        """Connects ALL signals, including the proactive input checks."""
        # Main operations
        self.start_button.clicked.connect(self._on_start_clicked)
        self.dry_run_button.clicked.connect(self._on_dry_run_clicked)
        self.undo_button.clicked.connect(self._on_undo_clicked)

        # In-flight operation controls
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.resume_button.clicked.connect(self._on_resume_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)

        # --- THE RESTORED PROACTIVE UI CONNECTIONS ---
        # This is the "wiring" that makes the UI intelligent. Every time the
        # user types a character, _check_input_validity will be called.
        self.source_selector.path_edit.textChanged.connect(self._check_input_validity)
        self.dest_selector.path_edit.textChanged.connect(self._check_input_validity)

    def _connect_controller_signals(self):
        """Connects signals FROM the ActionController TO this tab's slots for UI updates."""
        self.controller.progress_percentage_updated.connect(self.progress_bar.setValue)
        self.controller.log_entry_created.connect(self._handle_log_entry)
        self.controller.undo_progress_updated.connect(self.update_undo_progress)
        self.controller.state_changed.connect(self._update_button_states)
        self.controller.status_updated.connect(self.status_widget.set_status)
        self.controller.show_message_box.connect(self._show_message_box)
        self.controller.timer_tick.connect(self._update_timer_display)

    def _flash_status_message(self, message: str):
        """Displays a temporary warning message in the status bar."""
        self.status_widget.set_status(message, is_error=True)
        # The message will disappear after 3.5 seconds.
        self.status_flash_timer.start(3500)

    @Slot()
    def _clear_flash_status(self):
        """Resets the status bar to idle after a temporary message."""
        # We only reset the message if the application is still idle.
        if self.controller.is_idle():
            self.status_widget.set_status("Idle. Ready to start.", is_error=False)

    # --- Slots that trigger the controller, now with robust validation ---

    @Slot()
    def _on_start_clicked(self):
        """Gathers data and tells the controller to start, ONLY if inputs are valid."""
        source_dir_str = self.source_selector.path().strip()
        dest_dir_str = self.dest_selector.path().strip()

        # --- The New, Intelligent Form Validation ---
        if not source_dir_str and not dest_dir_str:
            self._flash_status_message("⚠️ Source and Destination directories must be selected.")
            return
        if not source_dir_str:
            self._flash_status_message("⚠️ Source directory must be selected.")
            return
        if not dest_dir_str:
            self._flash_status_message("⚠️ Destination directory must be selected.")
            return

        mode_group = self.findChild(QGroupBox, "Advanced Operation Modes (Optional)")
        use_advanced_mode = mode_group.isChecked()
        operation_mode, selected_paths = "FULL_CLASSIFY", []
        if use_advanced_mode:
            dialog_dir = source_dir_str if Path(source_dir_str).is_dir() else str(Path.home())
            if self.mode_move_as_is.isChecked():
                operation_mode = "MOVE_AS_IS"
                dialog = QFileDialog(self, "Select Folders/Files to Move As-Is", dialog_dir)
                dialog.setFileMode(QFileDialog.ExistingFiles)
                if dialog.exec():
                    selected_paths = dialog.selectedFiles()
                else:
                    return
            elif self.mode_selective_classify.isChecked():
                operation_mode = "SELECTIVE_CLASSIFY"
                dialog = QFileDialog(self, "Select Files to Classify", dialog_dir)
                dialog.setFileMode(QFileDialog.ExistingFiles)
                if dialog.exec():
                    selected_paths = dialog.selectedFiles()
                else:
                    return
        self.log_view.clear_logs()
        self.controller.start_classification(source_dir_str, dest_dir_str, self.duplicates_combo.currentText(),
                                             operation_mode, selected_paths)

    @Slot()
    def _on_undo_clicked(self):
        """Calls the controller to start an undo, now with validation."""
        # Undo doesn't strictly need the paths, but it's good practice to check.
        source_dir_str = self.source_selector.path().strip()
        dest_dir_str = self.dest_selector.path().strip()

        if QMessageBox.question(self, 'Confirm Undo', "This will reverse the last operation. Are you sure?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.log_view.clear_logs()
            self.controller.start_undo(source_dir_str, dest_dir_str)

    @Slot()
    def _on_dry_run_clicked(self):
        """Calls the controller to start a dry run, ONLY if inputs are valid."""
        source_dir_str = self.source_selector.path().strip()
        dest_dir_str = self.dest_selector.path().strip()

        # --- The New, Intelligent Form Validation ---
        if not source_dir_str or not dest_dir_str:
            self._flash_status_message("⚠️ Source and Destination directories are required for a Dry Run.")
            return

        self.log_view.clear_logs()
        self.controller.start_dry_run(source_dir_str, dest_dir_str)

    @Slot()
    def _on_pause_clicked(self):
        """
        This is the "King's Command". This method's only job is to tell
        the controller (the "General") that the user wants to pause.
        All the complex logic is handled by the controller.
        """
        self.controller.pause_operation()

    @Slot()
    def _on_resume_clicked(self):
        """
        The King gives the command to resume.
        """
        self.controller.resume_operation()

    @Slot()
    def _on_cancel_clicked(self):
        """
        The King asks for confirmation, then gives the command to cancel.
        """
        if QMessageBox.question(self, 'Confirm Cancel', "Are you sure you want to cancel?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.controller.cancel_operation()

    @Slot(dict)
    def _handle_log_entry(self, entry: dict):
        self.log_view.add_log_entry(entry["status"], entry["message"])

    @Slot(int, int, str)
    def update_undo_progress(self, processed, total, message):
        if total > 0: self.progress_bar.setValue(int((processed / total) * 100))
        self.log_view.add_log_entry("INFO", message)

    @Slot(str, str)
    def _update_button_states(self, state: str, operation_type: str):
        """The definitive, proactive state machine for this tab's buttons."""
        is_idle = state == "IDLE"
        is_running = state == "RUNNING"
        is_paused = state == "PAUSED"

        # --- The Proactive Logic ---
        inputs_are_valid = bool(self.source_selector.path().strip() and self.dest_selector.path().strip())
        can_start_operation = is_idle and inputs_are_valid

        # Rule 1: At start, Start/Dry Run are disabled until paths are valid.
        self.start_button.setEnabled(can_start_operation)
        self.dry_run_button.setEnabled(can_start_operation)

        # The Undo button only depends on the idle state.
        self.undo_button.setEnabled(is_idle)

        # Input fields are only enabled when the app is idle.
        self.source_selector.setEnabled(is_idle)
        self.dest_selector.setEnabled(is_idle)
        self.duplicates_combo.setEnabled(is_idle)
        self.findChild(QGroupBox, "Advanced Operation Modes (Optional)").setEnabled(is_idle)

        # Rules for in-flight operations.
        can_pause = is_running and operation_type == "CLASSIFY"
        can_resume = is_paused and operation_type == "CLASSIFY"
        self.pause_button.setEnabled(can_pause)
        self.resume_button.setEnabled(can_resume)

        self.cancel_button.setEnabled(is_running or is_paused)

        if state in ["ERROR", "INITIALIZING"]:
            for btn in [self.start_button, self.dry_run_button, self.undo_button, self.pause_button, self.resume_button,
                        self.cancel_button]:
                btn.setEnabled(False)

    @Slot(str, str, str)
    def _show_message_box(self, msg_type, title, message):
        if msg_type == "critical":
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)

    @Slot()
    def _check_input_validity(self):
        """
        This is the heart of the proactive UI. It is called every time the
        user types in a path field. It tells the main state machine to re-evaluate
        whether the Start and Dry Run buttons should be enabled or disabled.
        """
        # We only re-evaluate the state if no operation is currently running.
        if self.controller.is_idle():
            self._update_button_states("IDLE", "CLASSIFY")

    @Slot(int)
    def _update_timer_display(self, elapsed_time: int):
        minutes, seconds = divmod(elapsed_time, 60)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")