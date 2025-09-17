# 🏛️ Project Architecture Overview

This document provides a detailed technical overview of the Smart File Classifier v3.0 project. It is intended for developers, contributors, and anyone interested in the software's internal design, advanced concurrency patterns, and data flow.

---

### **Table of Contents**
1.  [**✨ Architectural Philosophy**](#-1-architectural-philosophy)
2.  [**🗺️ High-Level Component Diagram**](#-2-high-level-component-diagram)
3.  [**📂 Directory & File Responsibilities**](#-3-directory--file-responsibilities)
4.  [**⚙️ Component Deep Dive: The Core Engine (`core/`)**](#-4-component-deep-dive-the-core-engine-core)
    *   [🚦 State Management: The Control System](#-state-management-the-control-system)
    *   [🚀 The Producer-Consumer Pattern: High-Speed, Controllable Execution](#-the-producer-consumer-pattern-high-speed-controllable-execution)
5.  [**🎨 Component Deep Dive: The GUI (`gui/`)**](#-5-component-deep-dive-the-gui-gui)
    *   [👷 The "Supervisor" Worker Pattern: A Truly Non-Blocking UI](#-the-supervisor-worker-pattern-a-truly-non-blocking-ui)
    *   [📡 Signal & Slot Mechanism: Decoupled & Thread-Safe Communication](#-signal--slot-mechanism-decoupled--thread-safe-communication)
    *   [🧠 The UI State Machine: Proactive & Reliable Control](#-the-ui-state-machine-proactive--reliable-control)
6.  [**➡️ Data Flow of a Typical GUI Operation**](#-6-data-flow-of-a-typical-gui-operation)

---

## ✨ 1. Architectural Philosophy

The architecture was built upon three foundational principles to ensure a robust, maintainable, and scalable application:

*   **🧩 Separation of Concerns**: Each component of the application has a single, well-defined responsibility. The user interface is completely separate from the business logic, and file operations are isolated from the main classification engine. This makes the codebase easier to understand, test, and extend.
*   **🔌 UI-Agnostic Core Engine**: The entire business logic—scanning, planning, executing, and undoing file operations—is contained within a `core` package that has no knowledge of any user interface. This is a critical design choice that allows the same powerful, tested engine to be used by the GUI, the CLI, or any future integration (e.g., a web API) without changing a single line of engine code.
*   **💨 State-Driven and Truly Non-Blocking UI**: The Graphical User Interface (GUI) offloads **all** long-running tasks (including scanning and planning) to a background "Supervisor" worker thread (`QThread`). The UI's state is updated safely and reliably through Qt's signal and slot mechanism, guaranteeing a smooth, truthful, and non-blocking user experience at all times.

## 🗺️ 2. High-Level Component Diagram

The following diagram illustrates the decoupled nature of the application's main components and their primary classes.

+-------------------------------------------------+
| 🎬 User Interaction Layer |
|-------------------------------------------------|
| / \ |
| [🎨 GUI (PySide6)] [🖥️ CLI (Click)] |
| - MainWindow - main.py |
| - Worker/UndoWorker |
| \ / |
| \ / |
| [main.py - Unified Entry Point] |
+-------------------------------------------------+
| (Safe, Decoupled Calls)
V
+-------------------------------------------------+
| 🧠 Core Engine (Business Logic) |
| [ClassificationEngine] |
|-------------------------------------------------|
| / | \ |
| [🤲 FileOperations] [💾 UndoManager] [🛠️ Utils] |
| - safe_move - log_move - (Helpers) |
+-------------------------------------------------+


## 📂 3. Directory & File Responsibilities

*   `smart_classifier/` - The main Python source code package.
    *   `core/` - The UI-agnostic business logic.
        *   `classification_engine.py`: The "brain" 🧠 of the application. Orchestrates all operations using advanced concurrency patterns.
        *   `file_operations.py`: The "hands" 🤲. Contains the low-level, safe, and atomic functions for moving files.
        *   `undo_manager.py`: The "memory" 💾. Manages the thread-safe transaction log for the undo feature.
    *   `cli/` - Code for the Command-Line Interface, built with `click`.
    *   `gui/` - Code for the Graphical User Interface, built with `PySide6`.
        *   `main_window.py`: The main application window. Its primary role is to manage widgets and orchestrate the creation of worker threads.
        *   `resources.py`: A professional helper module for loading, validating, and caching assets (icons, styles).
        *   `widgets.py`: Contains reusable, self-contained UI components (`DirectorySelector`, `StatusWidget`) to promote clean code.
    *   `utils/` - Shared utility modules.
        *   `logger.py`: Configures the application-wide logging system 📜.
        *   `thread_manager.py`: Helper for determining the optimal number of worker threads ⚙️.
    *   `main.py` - The single, unified entry point for launching the application in either CLI or GUI mode.

## ⚙️ 4. Component Deep Dive: The Core Engine (`core/`)

### 🚦 State Management: The Control System

The `ClassificationEngine` is stateful, designed for fine-grained control during multi-threaded operations.
*   `_pause_event = threading.Event()`: We use a `threading.Event` as a thread-safe "gate." Calling `.clear()` pauses workers, while `.set()` resumes them. Its `.wait()` method is highly efficient, consuming **zero CPU** while a thread is paused, as it relies on the operating system's schedulers. This is vastly superior to a "busy-wait" loop (`while is_paused: time.sleep()`).
*   `_is_cancelled = False`: A simple boolean flag. This is the most efficient and direct way to signal a termination request across threads.

### 🚀 The Producer-Consumer Pattern: High-Speed, Controllable Execution

The `execute_plan()` method is the heart of the engine's performance. It is a high-speed, multi-threaded implementation based on the classic **Producer-Consumer Pattern**. This provides the best of both worlds: the instant responsiveness of a sequential loop and the raw throughput of a parallel system.

*   **👨‍🍳 The Producer**: The main `for` loop inside `execute_plan` acts as the "Producer." Its only job is to iterate through the plan and `put()` file-moving tasks onto a shared `queue.Queue`.
    *   **Controllability**: Because this producer loop is sequential, the `_pause_event.wait()` and `if self._is_cancelled:` checkpoints inside it are hit instantly, giving the UI immediate control over the flow of new tasks.
*   **📦 The `queue.Queue`**: This is the thread-safe "shared buffer" or "conveyor belt" between the Producer and the Consumers. We set a `maxsize` on it to act as a backpressure mechanism, preventing it from consuming too much memory if the consumers are slower than the producer.
*   **👷 The Consumers**: These are worker functions running inside a `ThreadPoolExecutor`. Their only job is to `get()` a task from the queue and execute it (by calling `safe_move`). This allows multiple file operations (which are I/O-bound) to happen in parallel, maximizing disk throughput.
*   **🛡️ Graceful Shutdown**: The cancellation logic is architecturally robust. When a cancel is requested, the Producer stops and a "poison pill" (`None`) is put on the queue for each consumer thread. This wakes up any idle consumers and signals them to exit their loops cleanly. The `executor.shutdown(wait=True)` call then ensures all in-flight tasks are completed before the method returns, guaranteeing a clean, deadlock-free exit.

## 🎨 5. Component Deep Dive: The GUI (`gui/`)

### 👷 The "Supervisor" Worker Pattern: A Truly Non-Blocking UI

This is the key to the GUI's responsiveness. The `MainWindow` itself performs **no blocking operations**. When the user clicks "Start," it follows this pattern:
1.  It creates a `Worker` object and a new `QThread`.
2.  It uses `worker.moveToThread(thread)` to assign the worker to the new thread.
3.  It starts the thread.

The `Worker`'s `run()` method is a true "supervisor." It is responsible for the *entire sequence* of backend tasks: first calling `scan_directory()`, then `generate_plan()`, and finally `execute_plan()`. Because this entire long-running chain happens in the background, the main UI thread is always free, guaranteeing a perfectly responsive, non-blocking user experience with truthful, real-time progress updates.

### 📡 Signal & Slot Mechanism: Decoupled & Thread-Safe Communication

Communication between the background `Worker` thread and the main `MainWindow` thread is handled exclusively through Qt's thread-safe signals and slots.
*   The `Worker` emits signals like `progress_updated(percentage, filename, status)` without knowing or caring who is listening.
*   The `MainWindow` connects its slots (like `update_progress`) to these signals during setup.
*   When a signal is emitted from the background thread, Qt safely marshals it to the main thread and invokes the connected slot. This is the professionally recommended way to perform thread-safe UI updates and keeps the components fully decoupled.

### 🧠 The UI State Machine: Proactive & Reliable Control

The `_update_button_states(state: str, operation_type: str)` method acts as a formal state machine for the UI. It takes the application's current state (e.g., `"IDLE"`, `"RUNNING"`, `"PAUSED"`) and the type of operation (`"CLASSIFY"`, `"UNDO"`) and reliably configures the entire UI.

Crucially, it also performs a **proactive validity check** on the user's inputs. This allows it to disable the "Start" and "Dry Run" buttons *before* the user can make a mistake, guiding them towards a successful operation and creating a more intelligent and satisfying user experience.

## ➡️ 6. Data Flow of a Typical GUI Operation

This sequence ties all the architectural concepts together:

1.  **👤 User Action**: The user clicks the **"Start"** button in the `MainWindow`.
2.  **🎬 UI Prepares**: The `start_classification` slot is triggered on the main UI thread. It is a non-blocking method. The UI is immediately set to the "RUNNING" state (buttons are disabled/enabled).
3.  **👷 Worker Created**: A `Worker` object is instantiated and moved to a new `QThread`.
4.  **🚀 Thread Starts**: The `QThread` is started, which calls the `Worker`'s `run` method in the background.
5.  **⚙️ Worker Executes**: Inside the `Worker`, the sequence begins:
    *   It first calls `engine.scan_directory()`.
    *   Then, it calls `engine.generate_plan()`.
    *   Finally, it calls the powerful `engine.execute_plan()` Producer-Consumer loop.
6.  **📊 Real-Time Feedback**: As the `execute_plan` method runs, its producer and consumer threads emit progress information via the `progress_callback`.
7.  **📡 Signal Emitted**: The `progress_callback` is connected to the `Worker`'s `progress_updated` signal, which is emitted in the background.
8.  **🎨 UI Updates**: The `MainWindow`'s `update_progress` slot receives this signal on the main UI thread and safely updates the `QProgressBar` and `QListView`.
9.  **⏸️ User Interruption**: If the user clicks **"Pause"**, the `handle_pause` slot calls `self.engine.pause()`, which clears the `threading.Event`, causing both the producer and consumer loops to block instantly.
10. **🏁 Operation Finishes**: When the `execute_plan` loop finishes (or is cancelled), the `Worker`'s `run` method completes, and the `finished` signal is emitted.
11. **🧹 Cleanup**: The `MainWindow`'s `on_operation_finished` slot receives this signal, performs a robust and non-blocking cleanup, and resets the UI to the "IDLE" state, ready for the next operation.