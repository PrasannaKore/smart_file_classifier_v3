# smart_classifier/gui/widgets.py

"""
This module is intended for custom, reusable GUI widgets.

To keep the main_window.py file clean, complex or repeated UI components
can be built here as self-contained classes. For example, a widget that
combines a QLabel, QLineEdit, and QPushButton for directory selection could
be created here and then instantiated twice in the main window.

This promotes code reuse and separation of concerns.
"""

# smart_classifier/gui/widgets.py

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QFrame
)
from PySide6.QtCore import Slot


class DirectorySelector(QWidget):
    """
    A compound widget for selecting a directory.
    Combines a label, a line edit to display the path, and a browse button.
    """

    def __init__(self, label_text: str, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label_text)
        self.path_edit = QLineEdit()
        self.browse_button = QPushButton("Browse...")

        # FIX: Changed from setFixedWidth to setMinimumWidth to prevent label clipping.
        self.label.setMinimumWidth(120)

        layout.addWidget(self.label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)

        self.browse_button.clicked.connect(self._select_directory)

    @Slot()
    def _select_directory(self):
        """Opens a QFileDialog to choose a directory."""
        dir_path = QFileDialog.getExistingDirectory(self, f"Select {self.label.text()}")
        if dir_path:
            self.path_edit.setText(dir_path)

    def path(self) -> str:
        """Returns the currently selected path as a string."""
        return self.path_edit.text()

    def setPath(self, path: str):
        """Sets the text of the path edit."""
        self.path_edit.setText(path)


class StatusWidget(QFrame):
    """
    A dedicated widget to display the current operation status.
    Provides a clear, at-a-glance status message.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("Status:")
        self.status_message = QLabel("Idle. Ready to start.")

        self.status_label.setStyleSheet("font-weight: bold;")

        layout.addWidget(self.status_label)
        layout.addWidget(self.status_message)
        layout.addStretch()

    def set_status(self, message: str, is_error: bool = False):
        """Updates the status message and its color."""
        self.status_message.setText(message)
        if is_error:
            self.status_message.setStyleSheet("color: #BF616A;")  # Red for errors
        else:
            self.status_message.setStyleSheet("color: #ECEFF4;")  # Default text color