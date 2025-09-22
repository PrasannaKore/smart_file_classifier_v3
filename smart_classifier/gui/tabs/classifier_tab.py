# smart_classifier/gui/tabs/classifier_tab.py

from pathlib import Path

from PySide6.QtCore import Slot, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar,
    QComboBox, QMessageBox, QGridLayout, QSpacerItem, QSizePolicy,
    QFileDialog, QGroupBox, QRadioButton
)

from ..action_controller import ActionController
from ..widgets import DirectorySelector, StatusWidget, MultiDirectorySelector
from ..log_viewer import LogViewer
from ..resources import get_icon, ICON_SIZE


class ClassifierTab(QWidget):
    """
    The UI for the main classification feature. This widget is a "dumb" view.
    It holds all the visual components and delegates all actions to the ActionController.
    """

    def __init__(self, controller: ActionController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._init_ui()
        self.connect_signals()
        self._connect_controller_signals()
        self.status_flash_timer = QTimer(self)
        self.status_flash_timer.setSingleShot(True)
        self.status_flash_timer.timeout.connect(self._clear_flash_status)

    def _init_ui(self):
        """Creates and arranges all widgets using a dynamic, context-aware layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        self.source_selector_single = DirectorySelector("Source Directory:")
        self.source_selector_multi = MultiDirectorySelector("Source Directories:")
        self.dest_selector = DirectorySelector("Destination Directory:")
        self.source_selector_multi.setVisible(False)

        self.source_layout = QVBoxLayout()
        self.source_layout.setSpacing(0)
        self.source_layout.addWidget(self.source_selector_single)
        self.source_layout.addWidget(self.source_selector_multi)

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

        self.start_button.setEnabled(False)
        self.dry_run_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

        self.start_button.setIcon(get_icon("start"))
        self.pause_button.setIcon(get_icon("pause"))
        self.resume_button.setIcon(get_icon("resume"))
        self.cancel_button.setIcon(get_icon("cancel"))
        self.dry_run_button.setIcon(get_icon("preview"))
        self.undo_button.setIcon(get_icon("undo"))

        all_buttons = [self.start_button, self.pause_button, self.resume_button, self.cancel_button,
                       self.dry_run_button, self.undo_button]
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

        main_layout.addLayout(self.source_layout)
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
        self.start_button.clicked.connect(self._on_start_clicked)
        self.dry_run_button.clicked.connect(self._on_dry_run_clicked)
        self.undo_button.clicked.connect(self._on_undo_clicked)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.resume_button.clicked.connect(self._on_resume_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)

        mode_group = self.findChild(QGroupBox, "Advanced Operation Modes (Optional)")
        mode_group.toggled.connect(self._toggle_advanced_mode)

        self.source_selector_single.path_edit.textChanged.connect(self._check_input_validity)
        self.source_selector_multi.pathsChanged.connect(self._check_input_validity)
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

    @Slot(bool)
    def _toggle_advanced_mode(self, checked: bool):
        """Shows or hides the correct source selector based on the user's choice."""
        self.source_selector_single.setVisible(not checked)
        self.source_selector_multi.setVisible(checked)
        self._check_input_validity()

    def _flash_status_message(self, message: str):
        """Displays a temporary warning message in the status bar."""
        self.status_widget.set_status(message, is_error=True)
        self.status_flash_timer.start(3500)

    @Slot()
    def _clear_flash_status(self):
        """Resets the status bar to idle after a temporary message."""
        if self.controller.is_idle():
            self.status_widget.set_status("Idle. Ready to start.", is_error=False)

    @Slot()
    def _on_start_clicked(self):
        """Gathers data from the UI and tells the controller to start a classification."""
        dest_dir_str = self.dest_selector.path().strip()
        mode_group = self.findChild(QGroupBox, "Advanced Operation Modes (Optional)")
        use_advanced_mode = mode_group.isChecked()

        source_paths = []
        if use_advanced_mode:
            source_paths = self.source_selector_multi.paths()
        else:
            source_path_str = self.source_selector_single.path().strip()
            if source_path_str:
                source_paths = [source_path_str]

        if not source_paths or not dest_dir_str:
            self._flash_status_message("⚠️ Source and Destination directories must be selected.")
            return

        operation_mode = "FULL_CLASSIFY"
        selected_paths_for_op = source_paths

        if use_advanced_mode:
            dialog_start_dir = source_paths[0]
            if self.mode_move_as_is.isChecked():
                operation_mode = "MOVE_AS_IS"
                dialog = QFileDialog(self, "Select Folders/Files to Move As-Is", dialog_start_dir)
                dialog.setFileMode(QFileDialog.ExistingFiles)
                if dialog.exec():
                    selected_paths_for_op = dialog.selectedFiles()
                else:
                    return
            elif self.mode_selective_classify.isChecked():
                operation_mode = "SELECTIVE_CLASSIFY"
                dialog = QFileDialog(self, "Select Files to Classify", dialog_start_dir)
                dialog.setFileMode(QFileDialog.ExistingFiles)
                if dialog.exec():
                    selected_paths_for_op = dialog.selectedFiles()
                else:
                    return

            if not selected_paths_for_op:
                self.status_widget.set_status("No items were selected for the advanced operation.", is_error=True)
                return

        self.log_view.clear_logs()
        self.controller.start_classification(source_paths, dest_dir_str, self.duplicates_combo.currentText(),
                                             operation_mode, selected_paths_for_op)

    @Slot()
    def _on_dry_run_clicked(self):
        """Calls the controller to start a dry run."""
        source_dir_str = self.source_selector_single.path().strip()
        dest_dir_str = self.dest_selector.path().strip()
        if not source_dir_str or not dest_dir_str:
            self._flash_status_message("⚠️ Source and Destination are required for a Dry Run.")
            return
        self.log_view.clear_logs()
        self.controller.start_dry_run(source_dir_str, dest_dir_str)

    @Slot()
    def _on_undo_clicked(self):
        """Calls the controller to start an undo."""
        if QMessageBox.question(self, 'Confirm Undo', "This will reverse the last operation. Are you sure?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.log_view.clear_logs()
            self.controller.start_undo("", "")

    @Slot()
    def _on_pause_clicked(self):
        self.controller.pause_operation()

    @Slot()
    def _on_resume_clicked(self):
        self.controller.resume_operation()

    @Slot()
    def _on_cancel_clicked(self):
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
        is_idle, is_running, is_paused = state == "IDLE", state == "RUNNING", state == "PAUSED"

        source_paths = self.source_selector_multi.paths() if self.source_selector_multi.isVisible() else [
            self.source_selector_single.path().strip()]
        inputs_are_valid = bool(any(p.strip() for p in source_paths) and self.dest_selector.path().strip())

        can_start_operation = is_idle and inputs_are_valid
        self.start_button.setEnabled(can_start_operation)
        self.dry_run_button.setEnabled(can_start_operation)
        self.undo_button.setEnabled(is_idle)

        self.source_selector_single.setEnabled(is_idle)
        self.source_selector_multi.setEnabled(is_idle)
        self.dest_selector.setEnabled(is_idle)
        self.duplicates_combo.setEnabled(is_idle)
        self.findChild(QGroupBox, "Advanced Operation Modes (Optional)").setEnabled(is_idle)

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
        """The heart of the proactive UI. It calls the state machine."""
        if self.controller.is_idle():
            self._update_button_states("IDLE", "CLASSIFY")

    @Slot(int)
    def _update_timer_display(self, elapsed_time: int):
        minutes, seconds = divmod(elapsed_time, 60)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
