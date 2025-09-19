# smart_classifier/gui/learning_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QCheckBox
)


class LearningDialog(QDialog):
    """
    A dedicated dialog that appears when the application finds an unknown file type.
    It provides a safe and user-friendly way for the user to "teach" the application.
    """

    def __init__(self, extension: str, categories: list, parent=None):
        """
        Initializes the dialog.

        Args:
            extension: The new, unknown extension that was found (e.g., ".xyz").
            categories: A list of all known categories to populate the dropdown.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Teach Me: New File Type Found")

        # --- UI Components ---
        self.layout = QVBoxLayout(self)
        self.label = QLabel(
            f"The application found a new file type: <b>{extension}</b><br>Please choose a category for it, or type a new one.")

        self.category_combo = QComboBox()
        self.category_combo.addItems(categories)
        self.category_combo.setEditable(True)  # Allows the user to type a new category
        self.category_combo.setPlaceholderText("Select or type a new category name...")

        self.remember_checkbox = QCheckBox("Remember this choice for the future?")
        self.remember_checkbox.setChecked(True)  # Default to learning

        # Standard OK and Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # --- Layout Assembly ---
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.category_combo)
        self.layout.addWidget(self.remember_checkbox)
        self.layout.addWidget(self.buttons)

        # --- Signal Connections ---
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def get_selection(self) -> dict | None:
        """
        Returns the user's choices in a structured dictionary if they clicked OK.
        Returns None if they clicked Cancel.
        """
        # We must validate that the user actually entered or selected a category.
        category = self.category_combo.currentText().strip()
        if not category:
            return None  # Return None if the category is empty

        return {
            "category": category,
            "remember": self.remember_checkbox.isChecked()
        }