# smart_classifier/gui/main_window.py

import sys

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PySide6.QtGui import QAction, QActionGroup

# --- Our Application's Own, Final Modules ---
# We import the final, modular components of our new architecture.
from .tabs.classifier_tab import ClassifierTab
from .tabs.knowledge_tab import KnowledgeTab
from .action_controller import ActionController
from .resources import load_stylesheet, get_icon, validate_assets, get_current_theme, set_current_theme
from smart_classifier.utils.logger import setup_logging


class MainWindow(QMainWindow):
    """
    The main application window, now refactored into a simple, stable container
    for our modular tabbed interface. This is the definitive "shell".
    Its only job is to assemble the components and show itself.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(" Smart File Classifier v3.0")
        self.setWindowIcon(get_icon("app_icon"))
        self.setGeometry(100, 100, 900, 750)

        # The core application logic is now in a dedicated, decoupled controller.
        self.action_controller = ActionController(self)

        # --- Create the menu bar for advanced features like theme switching ---
        self._create_menus()

        # --- Create and Assemble the Tabs ---
        self.tab_widget = QTabWidget()
        self.classifier_tab = ClassifierTab(self.action_controller)
        self.knowledge_tab = KnowledgeTab(self.action_controller)

        self.tab_widget.addTab(self.classifier_tab, "Classifier")
        self.tab_widget.addTab(self.knowledge_tab, "Knowledge Base Manager")

        self.setCentralWidget(self.tab_widget)

        # --- Final Signal Connection ---
        # The main window's only job is to show messages from the controller.
        self.action_controller.show_message_box.connect(self._show_message_box)

    def _create_menus(self):
        """Creates the main menu bar for the application."""
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("&Settings")
        settings_menu.setIcon(get_icon("settings"))
        theme_menu = settings_menu.addMenu("Theme")
        theme_group = QActionGroup(self)
        dark_action = QAction("Dark Theme", self, checkable=True)
        light_action = QAction("Light Theme", self, checkable=True)
        dark_action.triggered.connect(lambda: self._handle_theme_change("dark_theme.qss"))
        light_action.triggered.connect(lambda: self._handle_theme_change("light_theme.qss"))
        theme_menu.addAction(dark_action)
        theme_menu.addAction(light_action)
        theme_group.addAction(dark_action)
        theme_group.addAction(light_action)
        if get_current_theme() == "light_theme.qss":
            light_action.setChecked(True)
        else:
            dark_action.setChecked(True)

    @Slot(str)
    def _handle_theme_change(self, theme_file: str):
        """Applies the selected theme and saves the choice."""
        if set_current_theme(theme_file):
            QApplication.instance().setStyleSheet(load_stylesheet())
            QMessageBox.information(self, "Theme Changed", "Theme changed successfully.")
        else:
            self.show_error_message("Could not save theme setting.")

    @Slot(str, str, str)
    def _show_message_box(self, msg_type, title, message):
        """A dedicated slot to show message boxes requested by the controller."""
        if msg_type == "critical":
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)

    def show_error_message(self, message: str):
        """A simple helper for displaying errors."""
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        """Ensures the application closes gracefully."""
        # The controller now owns the thread, so we ask it if it's idle.
        if not self.action_controller.is_idle():
            reply = QMessageBox.question(self, 'Operation in Progress',
                                         "A task is running. Are you sure you want to quit?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # We ask the controller to gracefully cancel before accepting.
                self.action_controller.cancel_operation()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def run_gui():
    """
    The entry point for the GUI application. This is the final, correct version
    that assembles our superior, modular architecture.
    """
    # Step 1: Configure the application-wide logging system.
    setup_logging()

    # Step 2: Validate that all required assets (icons, styles) are present.
    validate_assets()

    # Step 3: Create the core Qt application instance.
    app = QApplication(sys.argv)

    # Step 4: Load and apply our professional, theme-aware stylesheet.
    app.setStyleSheet(load_stylesheet())

    # Step 5: Create our new, simple "shell" main window.
    window = MainWindow()

    # Step 6: Make the window visible to the user.
    window.show()

    # Step 7: Start the application's main event loop and ensure a clean exit.
    sys.exit(app.exec())