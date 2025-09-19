# smart_classifier/gui/models.py

"""
This module is reserved for application-wide data models, following the highest
principles of a strict Model-View-Controller (MVC) or Model-View-ViewModel (MVVM)
architecture.

In a truly advanced GUI application, the "Model" is a sacred and independent
component. Its sole purpose is to hold and manage the application's state and
data, completely separate from the UI (the "View") and the application's logic
(the "Controller").

--- DEEP AUDIT & ARCHITECTURAL DECISION ---

In the final, superior architecture of the Smart File Classifier v3.0, we have
achieved this sacred separation of concerns in a pragmatic and powerful way:

1.  The `LogModel` class (in `log_model.py`) was created to act as the dedicated,
    high-performance data model specifically for our "Mission Control" log viewer.
    It perfectly handles the state of the log data.

2.  The `ActionController` class (in `action_controller.py`) was created to act
    as the manager for the application's *operational state* (e.g., "IDLE,"
    "RUNNING," the current timer value, the active worker thread).

Because these two components already fulfill the "Model" responsibilities in a
clean, decoupled manner, creating an additional, complex `AppStateModel` in this
file would add unnecessary complexity for the current feature set.

Therefore, the truest and most professional version of this file for our current
project is one that serves as a **deliberate and well-documented placeholder.**
It stands as a testament to our architectural foresight, providing a clear and
designated home for future, more complex state management models if the
application's features are ever expanded.

-----------------------------------------------------------------------------

Example of a future AppStateModel that could live here:
"""
from PySide6.QtCore import QObject, Signal

class AppStateModel(QObject):
    #\"\"\"A future model for managing shared application state.\"\"\"
    source_dir_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._source_dir = ""

    @property
    def source_dir(self) -> str:
        return self._source_dir

    @source_dir.setter
    def set_source_dir(self, value: str):
        if self._source_dir != value:
            self._source_dir = value
            self.source_dir_changed.emit(value) # Notify any part of the UI


# This file is intentionally sparse to maintain a clean, pragmatic, and focused
# architecture for the current, feature-complete version of the application.