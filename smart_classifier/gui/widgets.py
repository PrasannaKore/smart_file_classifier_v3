# smart_classifier/gui/widgets.py

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QSizePolicy
)
from PySide6.QtCore import Slot

# We import our resource manager to make our widgets self-sufficient and
# ensure they use the same, consistent icons and sizes as the rest of the application.
from .resources import get_icon, ICON_SIZE


# --- Custom Widget 1: The Directory Selector ---
class DirectorySelector(QWidget):
    """
    A professional, reusable compound widget for selecting a directory.
    It encapsulates a label, a line edit, and an icon-enabled browse button.
    This component promotes code reuse and keeps the main UI code clean and simple.
    """

    def __init__(self, label_text: str, parent=None):
        """
        Initializes the widget.

        Args:
            label_text: The text to display on the label (e.g., "Source Directory:").
            parent: The parent widget, if any.
        """
        super().__init__(parent)

        # We use a horizontal layout to arrange the components neatly side-by-side.
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # No external margins for a tight, integrated fit.

        self.label = QLabel(label_text)
        self.path_edit = QLineEdit()
        self.browse_button = QPushButton(" Browse...")  # A leading space provides nice padding next to the icon.

        # --- Final Refinement: Self-Contained Icon Integration ---
        # The widget is now responsible for setting its own icon, making it a true
        # "drop-in" component.
        self.browse_button.setIcon(get_icon("folder-open"))
        self.browse_button.setIconSize(ICON_SIZE)

        # This is a crucial UX refinement. It ensures that when we stack two of
        # these widgets vertically (for source and destination), their text boxes
        # and buttons will be perfectly and beautifully aligned.
        self.label.setMinimumWidth(120)

        layout.addWidget(self.label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)

        # Connect the button's click signal to our internal, private slot.
        self.browse_button.clicked.connect(self._select_directory)

    @Slot()
    def _select_directory(self):
        """A private slot that opens a native OS QFileDialog to choose a directory."""
        # This provides a familiar, native experience for the user.
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
    A dedicated and self-resizing widget for displaying the application's current status.
    It is designed to be clear, informative, and to handle messages of any length.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("Status:")
        # We give the label an object name. This is a best practice that allows our
        # QSS stylesheet to target and style it specifically for a professional look.
        self.status_label.setObjectName("StatusLabel")
        self.status_message = QLabel("Idle. Ready to start.")

        # --- The Automatic Resizing Fix ---
        # This is the key to preventing long status messages from being clipped.
        # It tells the label that it is allowed to wrap its text onto new lines.
        self.status_message.setWordWrap(True)

        # This tells the entire StatusWidget that its preferred height is not fixed
        # and it should be allowed to grow vertically to accommodate its content.
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout.addWidget(self.status_label)
        layout.addWidget(self.status_message)
        layout.addStretch()

    def set_status(self, message: str, is_error: bool = False):
        """Updates the status message and dynamically changes its color for errors."""
        self.status_message.setText(message)
        # We apply an inline style for dynamic color changes based on the state.
        # This is a simple and effective way to provide instant visual feedback.
        if is_error:
            self.status_message.setStyleSheet("color: #BF616A;")  # Nord Red
        else:
            self.status_message.setStyleSheet("color: #ECEFF4;")  # Default Nord Light Text