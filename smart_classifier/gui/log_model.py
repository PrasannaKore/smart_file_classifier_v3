# smart_file_classifier/gui/log_model.py

import datetime
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QIcon

# We import our own reliable resource manager to get the status icons.
# This is a perfect example of our modular design in action.
from .resources import get_icon


# --- The Log Model: The "Brain" of our Log Viewer ---
class LogModel(QAbstractTableModel):
    """
    A professional, table-based model for managing and providing structured log entries.
    This class follows the Model-View-Controller (MVC) pattern, separating the
    log data from its visual representation. This is a cornerstone of advanced
    GUI architecture.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # _log_data is a private list that will hold our structured log entries.
        # Each entry will be a dictionary, e.g., {"status": "MOVED", "message": "file.txt", ...}
        self._log_data = []

        # The headers for our "Mission Control" table view. The empty string is for
        # the icon column, which does not need a visible title.
        self._headers = ["", "Message", "Time"]

        # We pre-load the icons once when the model is created. This is a high-performance
        # pattern that avoids repeatedly accessing the disk or our resource manager.
        self._status_icons = {
            "MOVED": get_icon("success"),
            "SKIPPED": get_icon("skip"),
            "ERROR": get_icon("error"),
            "DONE": get_icon("success"),
            "INFO": get_icon("info")
        }

    # --- Required Methods for QAbstractTableModel ---

    def rowCount(self, parent=QModelIndex()):
        """Returns the total number of rows (log entries) in our data."""
        return len(self._log_data)

    def columnCount(self, parent=QModelIndex()):
        """Returns the total number of columns in our table."""
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """
        This is the most important method. The "View" (our QTableView) calls this
        function repeatedly to get the data for every single cell it needs to display.
        It is the bridge between the raw data and the visual presentation.
        """
        # First, a crucial safety check. If the index is invalid, we do nothing.
        if not index.isValid():
            return None

        row_data = self._log_data[index.row()]
        col = index.column()

        # The 'role' determines what kind of data the View is asking for.
        if role == Qt.DisplayRole:
            # For the 'DisplayRole', the View wants the text to be displayed.
            if col == 1:  # This is the "Message" column.
                return row_data["message"]
            if col == 2:  # This is the "Time" column.
                return row_data["time"]

        if role == Qt.DecorationRole:
            # For the 'DecorationRole', the View wants an icon or image to display.
            if col == 0:  # This is our "Status" icon column.
                # We return the pre-loaded QIcon object based on the status string.
                # The .get() method gracefully falls back to the "info" icon if
                # the status is unknown, preventing crashes.
                return self._status_icons.get(row_data["status"], self._status_icons["INFO"])

        if role == Qt.ToolTipRole:
            # For the 'ToolTipRole', the View wants text for a hover tooltip.
            # This is a great UX feature for providing extra context to the user.
            return f"Status: {row_data['status']}"

        # If the role is not one we are handling, we return None.
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """Provides the text for the table headers."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None

    # --- Custom Public Methods ---

    def add_entry(self, status: str, message: str):
        """
        Adds a new structured log entry to the model.
        This is the main public method our application will call to add new logs.
        """
        # This is a critical performance signal. It tells the View that we are
        # about to insert rows at the end, so it can prepare efficiently.
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())

        entry = {
            "status": status.upper(),  # We standardize the status to uppercase for reliable icon lookup.
            "message": message,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        self._log_data.append(entry)

        # This second signal tells the View that we are done inserting, and it
        # can now update itself. This two-step process is what makes the
        # updates so efficient for large numbers of logs.
        self.endInsertRows()

    def clear(self):
        """Clears all log data from the model."""
        # This signal tells the View that the entire model is about to be wiped.
        self.beginResetModel()
        self._log_data = []
        # This signal tells the View that the reset is complete.
        self.endResetModel()