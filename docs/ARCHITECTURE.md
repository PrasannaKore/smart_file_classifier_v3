# Project Architecture Overview

This document provides a detailed technical overview of the Smart File Classifier v3.0 project. It is intended for developers, contributors, and anyone interested in the software's internal design and data flow.

---

### 1. Core Principles

The architecture was built upon three foundational principles to ensure a robust, maintainable, and scalable application:

*   **Separation of Concerns**: Each component of the application has a single, well-defined responsibility. The user interface is completely separate from the business logic, and file operations are isolated from the main classification engine.
*   **UI-Agnostic Core Engine**: The entire business logic—scanning, planning, executing, and undoing file operations—is contained within a `core` package that has no knowledge of any user interface. This allows the same powerful, tested engine to be used by the GUI, the CLI, or any future integration.
*   **State-Driven and Thread-Safe UI**: The Graphical User Interface (GUI) offloads all long-running tasks to a background worker thread (`QThread`). The UI's state (e.g., enabled/disabled buttons, progress bar color) is updated safely and reliably through Qt's signal and slot mechanism, ensuring a smooth, non-blocking user experience.

### 2. High-Level Diagram

The following diagram illustrates the decoupled nature of the application's main components:
+---------------------------------+
| User Interaction Layer |
|---------------------------------|
| / \ |
| [GUI (PySide6)] [CLI (Click)] |
| \ / |
| \ / |
| [main.py - Entry Point] |
+---------------------------------+
| (Imports & Calls)
V
+---------------------------------+
| Core Engine (Business Logic) |
| [ClassificationEngine] |
|---------------------------------|
| / | \ |
| [File Ops] [Undo Manager] [Utils]|
+---------------------------------+


### 3. Directory Structure Breakdown

The project is organized into a clean, modular structure where each directory and file has a specific purpose.

*   `smart_file_classifier_v3/` - The root directory of the project.
    *   `assets/` - Contains all non-code assets for the GUI.
        *   `icons/` - Holds all `.svg` icons for buttons and the window.
        *   `styles/` - Contains the `.qss` stylesheet for theming the application.
    *   `config/` - External configuration files.
        *   `file_types.json` - The customizable, metadata-driven mapping of file extensions to categories.
    *   `docs/` - All project documentation.
        *   `README.md` - The main, comprehensive documentation portal.
        *   `ARCHITECTURE.md` - **This file.**
        *   `EXECUTION_GUIDE.md` - Guide for creating a standalone executable.
        *   `INTEGRATION_GUIDE.md` - Guide for integrating the project as a library or subprocess.
        *   `USE_CASES.md` - Real-world applications of the tool.
    *   `smart_classifier/` - The main Python source code package.
        *   `core/` - The UI-agnostic business logic.
            *   `classification_engine.py`: The "brain" of the application. Orchestrates all operations.
            *   `file_operations.py`: The "hands." Contains the low-level, safe functions for moving files.
            *   `undo_manager.py`: The "memory." Manages the transaction log for the undo feature.
        *   `cli/` - Code for the Command-Line Interface, built with `click`.
        *   `gui/` - Code for the Graphical User Interface, built with `PySide6`.
            *   `main_window.py`: The main application window and its event-handling logic.
            *   `resources.py`: A helper module for loading and validating assets (icons, styles).
            *   `widgets.py`: Contains reusable, custom UI components like `DirectorySelector`.
        *   `utils/` - Shared utility modules.
            *   `logger.py`: Configures the application-wide logging system.
            *   `thread_manager.py`: Helper for determining the optimal number of worker threads.
        *   `main.py` - The single, unified entry point for launching the application in either CLI or GUI mode.
    *   `tests/` - Contains all unit and integration tests.
    *   `README.md` - The concise, top-level README that points to the main documentation in `docs/`.

### 4. Component Deep Dive

#### Core Engine (`core/`)
*   **`ClassificationEngine`**: This is the central class. It is initialized with the path to the configuration file.
    *   It contains the state-management objects for multi-threading: a `threading.Event` for pausing/resuming and a boolean `_is_cancelled` flag for stopping.
    *   `scan_directory()`: Uses the robust `os.walk` to recursively find all files in a given path.
    *   `generate_plan()`: Creates a "dry run" plan of all file move operations without touching any files.
    *   `execute_plan()`: The workhorse method. It uses a `concurrent.futures.ThreadPoolExecutor` to dispatch `safe_move` operations to multiple worker threads for high performance. The main loop within this method checks the pause event and cancellation flag before processing each file, allowing for full operational control.

#### GUI (`gui/`)
*   **`MainWindow`**: This class orchestrates the entire GUI.
    *   **Worker Threads**: It creates a `Worker` or `UndoWorker` object (derived from `QObject`) and moves it to a separate `QThread` for any long-running operation. This keeps the UI from freezing.
    *   **Signal & Slot Mechanism**: Communication between the background worker thread and the main UI thread is handled exclusively through Qt's thread-safe signals and slots. The worker emits signals like `progress_updated` or `finished`, and the `MainWindow` has slots like `update_progress` or `on_operation_finished` that receive these signals and safely update UI elements.
    *   **State Machine**: The `_update_button_states(state: str)` method acts as a simple state machine, enabling and disabling the appropriate buttons (`Start`, `Pause`, `Resume`, `Cancel`) based on the application's current state ("IDLE", "RUNNING", "PAUSED", "ERROR").

### 5. Data Flow of a Typical GUI Operation

1.  A user clicks the **"Start"** button in the `MainWindow`.
2.  The `start_classification` slot is triggered on the main UI thread.
3.  The UI is set to the "RUNNING" state (buttons are disabled/enabled accordingly).
4.  A `Worker` object is instantiated and moved to a new `QThread`.
5.  The `QThread` is started, which calls the `Worker`'s `run` method in the background.
6.  The `Worker` calls `self.engine.execute_plan()`.
7.  The `execute_plan` method starts processing files in a `ThreadPoolExecutor`. For each file processed, it calls the `progress_callback`.
8.  The `progress_callback` is connected to the `Worker`'s `progress_updated` signal, which is emitted.
9.  The `MainWindow`'s `update_progress` slot receives this signal on the main UI thread and safely updates the `QProgressBar` and `QListView`.
10. If the user clicks **"Pause"**, the `handle_pause` slot calls `self.engine.pause()`, which clears the `threading.Event`, causing the `execute_plan` loop to block.
11. When the `execute_plan` loop finishes (or is cancelled), the `Worker`'s `run` method completes, and the `finished` signal is emitted.
12. The `MainWindow`'s `on_operation_finished` slot receives this signal, cleans up the thread, and resets the UI to the "IDLE" state.