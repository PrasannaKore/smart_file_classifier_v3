# smart_classifier/gui/tabs/knowledge_tab.py

from PySide6.QtCore import Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QSpacerItem, QSizePolicy
)

from ..action_controller import ActionController
from ..resources import get_icon, ICON_SIZE


class KnowledgeTab(QWidget):
    """
    The UI for managing the application's knowledge base.
    This is a "dumb" view that delegates all logic to the ActionController.
    """

    def __init__(self, controller: ActionController, parent=None):
        super().__init__(parent)
        self.controller = controller

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        import_group = QGroupBox("Teach the Application")
        import_layout = QVBoxLayout()

        import_label = QLabel(
            "You can teach the application about many new file types at once by creating a simple CSV file.\n"
            "This is the most powerful way to customize the classifier to your specific needs."
        )
        import_label.setWordWrap(True)

        self.import_button = QPushButton("  Bulk Import Rules from CSV...")
        self.import_button.setIcon(get_icon("import"))
        self.import_button.setIconSize(ICON_SIZE)

        self.help_button = QPushButton("  How to Create the CSV File (Help)")
        self.help_button.setIcon(get_icon("info"))
        self.help_button.setIconSize(ICON_SIZE)

        import_layout.addWidget(import_label)
        import_layout.addWidget(self.import_button)
        import_layout.addWidget(self.help_button)
        import_group.setLayout(import_layout)

        editor_group = QGroupBox("Future: Rule Editor")
        editor_layout = QVBoxLayout()
        editor_label = QLabel(
            "A future update will include a full, interactive editor here to add, edit, and delete individual rules.")
        editor_label.setWordWrap(True)
        editor_label.setEnabled(False)
        editor_layout.addWidget(editor_label)
        editor_group.setLayout(editor_layout)

        main_layout.addWidget(import_group)
        main_layout.addWidget(editor_group)
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.import_button.clicked.connect(self._on_import_clicked)
        self.help_button.clicked.connect(self._open_help_link)

    @Slot()
    def _on_import_clicked(self):
        # This UI component's job is simple: tell the controller to start the import process.
        self.controller.start_bulk_import()

    @Slot()
    def _open_help_link(self):
        """Opens the link to the bulk import guide in the user's default web browser."""
        help_url = "https://github.com/PrasannaKore/smart_file_classifier_v3/blob/main/docs/BULK_IMPORT_GUIDE.md"
        QDesktopServices.openUrl(QUrl(help_url))