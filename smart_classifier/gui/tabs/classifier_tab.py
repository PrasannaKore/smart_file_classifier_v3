# smart_classifier/gui/tabs/classifier_tab.py

from pathlib import Path
import os

from PySide6.QtCore import Slot, QSize, QTimer, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QComboBox, QLabel, QMessageBox,
    QProgressBar, QSpacerItem, QSizePolicy, QListWidget, QListWidgetItem, QMenu, QGroupBox,
    QListView, QTreeView, QAbstractItemView
)

from ..action_controller import ActionController
from ..widgets import DirectorySelector, StatusWidget, MultiDirectorySelector
from ..log_viewer import LogViewer
from ..resources import get_icon, ICON_SIZE


class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if local_path and Path(local_path).exists():
                    paths.append(Path(local_path))
            try:
                self.parent().handle_dropped_items(paths)
            except Exception as e:
                QMessageBox.critical(self, "Drop Error", f"An error occurred while processing dropped items:\n{e}")
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        remove_action = menu.addAction("Remove Selected")
        clear_action = menu.addAction("Clear All")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == remove_action:
            self.parent().remove_selected_items()
        elif action == clear_action:
            self.parent().clear_all_selected_items()


class ClassifierTab(QWidget):
    """
    The UI for the main classification feature. This widget is a "dumb" view.
    It holds all the visual components and delegates all actions to the ActionController.
    """

    def __init__(self, controller: ActionController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.selected_items = []
        self.advanced_mode = "full_classification"  # default
        self._init_ui()
        self.connect_signals()
        self._connect_controller_signals()
        self.status_flash_timer = QTimer(self)
        self.status_flash_timer.setSingleShot(True)
        self.status_flash_timer.timeout.connect(self._clear_flash_status)
        self.last_selection_dir = str(Path.home())

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

        # --- Advanced Operation Section ---
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout as QVBoxLayout2
        self.advanced_group = QGroupBox("Advanced Operation Modes")
        advanced_layout = QVBoxLayout2()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Full Classification",
            "Move Selected As-Is",
            "Classify Selected Only"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.select_button = QPushButton("Select Files/Folders…")
        self.select_button.clicked.connect(self._select_files_folders)
        self.selected_list = DraggableListWidget(self)
        # Inline controls for managing the selection list
        selection_controls_layout = QHBoxLayout()
        self.remove_selected_btn = QPushButton("Remove selected directory from list")
        self.remove_selected_btn.setIcon(get_icon("cancel"))
        self.remove_selected_btn.clicked.connect(self.remove_selected_items)
        selection_controls_layout.addWidget(self.remove_selected_btn)
        selection_controls_layout.addStretch()
        self.selection_help_label = QLabel("Select files and/or folders to include in this operation.")
        self.selection_summary_label = QLabel("")
        advanced_layout.addWidget(self.mode_combo)
        advanced_layout.addWidget(self.select_button)
        advanced_layout.addWidget(self.selected_list)
        advanced_layout.addLayout(selection_controls_layout)
        advanced_layout.addWidget(self.selection_help_label)
        advanced_layout.addWidget(self.selection_summary_label)
        self.advanced_group.setLayout(advanced_layout)
        self.advanced_group.setFlat(False)
        # Hide advanced widgets initially if in full_classification
        self.select_button.hide()
        self.selected_list.hide()
        self.selection_help_label.hide()
        self.selection_summary_label.hide()

        # --- Layout Order: Place advanced group above log ---
        main_layout.addLayout(self.source_layout)
        main_layout.addWidget(self.dest_selector)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(action_button_layout)
        main_layout.addWidget(self.status_widget)
        main_layout.addLayout(progress_layout)
        main_layout.addWidget(self.advanced_group)  # <--- Move advanced group here
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
        """
        REPLACED: This is the definitive, superior version. It correctly enables
        multi-selection and implements the intelligent, "intent-driven" workflow.
        """
        source_dir_str = self.source_selector_single.path().strip()
        dest_dir_str = self.dest_selector.path().strip()

        if not source_dir_str or not dest_dir_str:
            self._flash_status_message("⚠️ Source and Destination directories must be selected.")
            return

        # Intelligent fallback: if an advanced mode is chosen but nothing is selected,
        # proceed with full classification instead of blocking the user.
        using_advanced = self.advanced_mode in ("move_as_is", "classify_selected_only")
        if using_advanced and not self.selected_items:
            effective_mode = "full_classification"
            selected_paths = []
        else:
            effective_mode = self.advanced_mode
            selected_paths = list(self.selected_items) if using_advanced else []

        # Check if all selected paths exist and are accessible
        for path in selected_paths:
            if not Path(path).exists():
                QMessageBox.critical(self, "File Not Found", f"Selected item does not exist:\n{path}\nPlease remove this item from your selection and try again.")
                return
            if not os.access(path, os.R_OK):
                QMessageBox.critical(self, "Permission Denied", f"Cannot access:\n{path}\nYou do not have permission to read this file or folder. Please adjust your selection or permissions and try again.")
                return

        operation_mode = {
            "full_classification": "FULL_CLASSIFY",
            "move_as_is": "MOVE_AS_IS",
            "classify_selected_only": "SELECTIVE_CLASSIFY"
        }[effective_mode]

        self.log_view.clear_logs()
        self.controller.start_classification(
            [source_dir_str],
            dest_dir_str,
            self.duplicates_combo.currentText(),
            operation_mode,
            [str(p) for p in selected_paths]
        )

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
        # self.findChild(QGroupBox, "Advanced Operation Modes (Optional)").setEnabled(is_idle)

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

    @Slot()
    def _on_mode_changed(self, idx):
        modes = [
            "full_classification",
            "move_as_is",
            "classify_selected_only"
        ]
        self.advanced_mode = modes[idx]
        # Always show the mode_combo
        if self.advanced_mode == "full_classification":
            self.selected_items = []
            self.selected_list.clear()
            self.select_button.hide()
            self.selected_list.hide()
            self.selection_help_label.hide()
            self.selection_summary_label.hide()
        else:
            self.select_button.show()
            self.selected_list.show()
            self.selection_help_label.show()
            self.selection_summary_label.show()
        self._update_selected_list()
        # Show the remove button only if at least one directory is selected
        has_dir_selected = any(p.is_dir() for p in self.selected_items)
        self.remove_selected_btn.setVisible(has_dir_selected)

    @Slot()
    def _select_files_folders(self):
        """
        Opens a single non-native dialog that supports multi-selection of files and directories,
        restricted to the source directory. Disallows any selection outside the source.
        If nothing valid is selected, provides a fallback to add directories one at a time.
        All previous logic is preserved.
        """
        source_dir = self.source_selector_single.path().strip()
        if not source_dir or not Path(source_dir).is_dir():
            QMessageBox.warning(self, "Invalid Source Directory", "Please select a valid source directory first.")
            return
        # Single non-native dialog for selecting files and folders within source_dir
        dialog = QFileDialog(self, "Select Files and Folders", source_dir)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.ShowDirsOnly, False)
        dialog.setDirectory(source_dir)
        # Enable multi-select properly by configuring the internal views
        list_views = dialog.findChildren(QListView)
        tree_views = dialog.findChildren(QTreeView)
        for view in list_views + tree_views:
            try:
                view.setSelectionMode(QAbstractItemView.ExtendedSelection)
            except Exception:
                pass
        if dialog.exec():
            selected = dialog.selectedFiles()
        else:
            selected = []

        # Add all valid paths (keep prior validation/behavior intact)
        valid_items = []
        invalid_items = []
        for item in selected:
            try:
                p = Path(item).resolve()
                # Strict restriction: allow only items that are the source dir or inside it
                if Path(source_dir).resolve() in p.parents or p == Path(source_dir).resolve():
                    if p not in self.selected_items:
                        valid_items.append(p)
                else:
                    invalid_items.append(str(p))
            except Exception:
                invalid_items.append(str(item))
        # Remove fallback loop to avoid a second dialog; rely on multi-select dialog only
        if invalid_items:
            QMessageBox.warning(self, "Invalid Selection", f"The following items are not in the source directory and were not added:\n" + '\n'.join(invalid_items))
        self.selected_items.extend(valid_items)
        if valid_items:
            self.last_selection_dir = str(valid_items[-1].parent if valid_items else Path(source_dir))
        self._update_selected_list()

    def remove_selected_items(self):
        """
        Allows user to remove selected files/directories from the list via context menu.
        """
        selected = self.selected_list.selectedItems()
        indices = sorted([self.selected_list.row(item) for item in selected], reverse=True)
        for idx in indices:
            try:
                del self.selected_items[idx]
                self.selected_list.takeItem(idx)
            except Exception as e:
                import logging; logging.warning(f"Failed to remove item at index {idx}: {e}")
        self._update_selected_list()

    def clear_all_selected_items(self):
        self.selected_items = []
        self.selected_list.clear()
        self._update_selected_list()

    def _update_selected_list(self):
        self.selected_list.clear()
        for item in self.selected_items:
            lw_item = QListWidgetItem(str(item))
            if not item.exists():
                lw_item.setForeground(Qt.red)
                lw_item.setToolTip("This item does not exist.")
            elif not os.access(str(item), os.R_OK):
                lw_item.setForeground(Qt.darkYellow)
                lw_item.setToolTip("No read permission for this item.")
            self.selected_list.addItem(lw_item)
        self._update_selection_summary()
        # Toggle visibility of the remove button based on whether any directories exist in selection
        has_dir_selected = any(p.is_dir() for p in self.selected_items)
        self.remove_selected_btn.setVisible(has_dir_selected)

    def _update_selection_summary(self):
        files = sum(1 for p in self.selected_items if p.is_file())
        dirs = sum(1 for p in self.selected_items if p.is_dir())
        self.selection_summary_label.setText(f"Selected: {files} files, {dirs} folders")


def test_mode_combo_updates_advanced_mode(qtbot, classifier_tab):
    classifier_tab.mode_combo.setCurrentIndex(1)
    assert classifier_tab.advanced_mode == "move_as_is"
    classifier_tab.mode_combo.setCurrentIndex(2)
    assert classifier_tab.advanced_mode == "classify_selected_only"

def test_start_operation_full_classification(qtbot, classifier_tab, mock_controller):
    classifier_tab.mode_combo.setCurrentIndex(0)
    classifier_tab.selected_items = []
    classifier_tab._on_start_clicked()
    # Assert mock_controller.start_classification called with operation_mode="FULL_CLASSIFY"

def test_start_operation_move_as_is(qtbot, classifier_tab, mock_controller):
    classifier_tab.mode_combo.setCurrentIndex(1)
    classifier_tab.selected_items = [Path("file1.txt")]
    classifier_tab._on_start_clicked()
    # Assert mock_controller.start_classification called with operation_mode="MOVE_AS_IS" and correct selected_paths

def test_start_operation_classify_selected_only(qtbot, classifier_tab, mock_controller):
    classifier_tab.mode_combo.setCurrentIndex(2)
    classifier_tab.selected_items = [Path("file2.txt")]
    classifier_tab._on_start_clicked()
    # Assert mock_controller.start_classification called with operation_mode="SELECTIVE_CLASSIFY" and correct selected_paths
