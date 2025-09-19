# smart_classifier/gui/widgets.py
"""
This module is intended for custom, reusable GUI widgets.

To keep the main_window.py file clean, complex or repeated UI components
can be built here as self-contained classes. For example, a widget that
combines a QLabel, QLineEdit, and QPushButton for directory selection could
be created here and then instantiated twice in the main window.

This promotes code reuse and separation of concerns.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QSizePolicy
)
from PySide6.QtCore import Slot


# --- Custom Widget 1: The Directory Selector ---
class DirectorySelector(QWidget):
    """
    A professional, reusable compound widget for selecting a directory.
    It encapsulates a label, a line edit to display the path, and a browse button.
    This promotes code reuse and keeps the main UI code clean.
    """

    def __init__(self, label_text: str, parent=None):
        """
        Initializes the widget.

        Args:
            label_text: The text to display on the label (e.g., "Source Directory:").
            parent: The parent widget, if any.
        """
        super().__init__(parent)

        # We use a horizontal layout to arrange the components side-by-side.
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # No external margins for a tight fit.

        self.label = QLabel(label_text)
        self.path_edit = QLineEdit()
        self.browse_button = QPushButton("Browse...")

        # We set a minimum width on the label. This is a crucial UX refinement.
        # It ensures that when we stack two of these widgets vertically (for source
        # and destination), their text boxes and buttons will be perfectly aligned.
        self.label.setMinimumWidth(120)

        layout.addWidget(self.label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)

        # Connect the button's click signal to our internal slot.
        self.browse_button.clicked.connect(self._select_directory)

    @Slot()
    def _select_directory(self):
        """A private slot that opens a QFileDialog to choose a directory."""
        # This opens a native OS dialog for selecting folders.
        dir_path = QFileDialog.getExistingDirectory(self, f"Select {self.label.text()}")
        if dir_path:
            self.path_edit.setText(dir_path)

    def path(self) -> str:
        """A public method to get the currently selected path as a string."""
        return self.path_edit.text()

    def setPath(self, path: str):
        """A public method to programmatically set the path."""
        self.path_edit.setText(path)


# --- Custom Widget 2: The Status Widget ---
class StatusWidget(QWidget):
    """
    A dedicated and self-resizing widget for displaying the current operation status.
    It provides a clear, at-a-glance status message that can grow as needed.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("Status:")
        # We give the label an object name so we can style it separately in our QSS file.
        self.status_label.setObjectName("StatusLabel")
        self.status_message = QLabel("Idle. Ready to start.")

        # --- The Automatic Resizing Fix ---
        # This is the key to preventing long messages from being clipped.
        # It tells the label that it is allowed to wrap its text onto new lines.
        self.status_message.setWordWrap(True)

        # This tells the entire StatusWidget that its preferred height is not fixed
        # and it should be allowed to grow vertically to accommodate its content.
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout.addWidget(self.status_label)
        layout.addWidget(self.status_message)
        layout.addStretch()

    def set_status(self, message: str, is_error: bool = False):
        """Updates the status message and its color."""
        self.status_message.setText(message)
        # We can apply inline styles for dynamic color changes.
        if is_error:
            self.status_message.setStyleSheet("color: #BF616A;")  # A theme-appropriate red
        else:
            self.status_message.setStyleSheet("color: #ECEFF4;")  # The default theme text color