# smart_classifier/gui/log_viewer.py

from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView

# We import the "brain" of our viewer, the LogModel.
from .log_model import LogModel


# --- The Log Viewer: The "Face" of our Logging System ---
class LogViewer(QTableView):
    """
    A professional, table-based view for displaying real-time, structured log data.
    This "View" component is designed for clarity, performance, and smooth,
    automatic resizing. It gets all of its data from the "Model" (LogModel).
    """

    def __init__(self, parent=None):
        """
        Initializes the table view and configures its appearance and behavior.
        """
        super().__init__(parent)

        # This is the crucial link in the MVC pattern. The View now has a reference
        # to its data Model.
        self._model = LogModel(self)
        self.setModel(self._model)

        # --- Professional Appearance & Behavior Configuration ---

        # When a user clicks, highlight the entire row, not just a single cell.
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Make the log read-only.
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # For performance and clarity, don't wrap long lines.
        self.setWordWrap(False)
        # A subtle visual touch to make the table look cleaner.
        self.setShowGrid(False)

        # --- Intelligent Column Sizing for a Resilient Layout ---
        header = self.horizontalHeader()

        # The Status icon column (index 0) should be just wide enough for the icon.
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        # The Message column (index 1) is the most important. It will automatically
        # stretch to fill any available space when the window is resized. This is
        # the key to a smooth, responsive layout.
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        # The Time column (index 2) should be just wide enough for the timestamp.
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # Hiding the vertical header (row numbers) gives a cleaner, more modern look.
        self.verticalHeader().hide()

    # --- Custom Public Methods ---

    def add_log_entry(self, status: str, message: str):
        """
        A convenient public method that passes a new log entry to the model.
        It also ensures the view automatically scrolls to the newest entry.
        """
        self._model.add_entry(status, message)
        self.scrollToBottom()

    def clear_logs(self):
        """A public method to clear all log entries by resetting the model."""
        self._model.clear()