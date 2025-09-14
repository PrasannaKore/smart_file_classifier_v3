# smart_classifier/gui/models.py

"""
This module is intended for application data models.

In a complex GUI application, you would separate the data and business logic
from the view (the widgets). For instance, an AppStateModel could hold the
current source/destination paths, the progress percentage, and the status log.

This allows for easier testing and maintenance, as the UI simply "observes"
the model for changes. For v3.0, the state is managed within the MainWindow,
but this file is kept for architectural integrity and future expansion.
"""

class AppStateModel:
    """A placeholder for a future application state model."""
    def __init__(self):
        self.source_directory = ""
        self.destination_directory = ""
        self.last_operation_log = []

    def set_paths(self, source: str, destination: str):
        self.source_directory = source
        self.destination_directory = destination

    def clear_log(self):
        self.last_operation_log = []