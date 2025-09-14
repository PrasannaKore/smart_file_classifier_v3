# Architecture Overview

This document outlines the high-level architecture of the Smart File Classifier project. The design emphasizes modularity, separation of concerns, and reusability.

## Core Principles

*   **Shared Core Engine:** All business logic is contained in a UI-agnostic `core` package. This allows both the CLI and GUI to use the same reliable, tested code.
*   **Separation of Concerns:** Each part of the application has a distinct responsibility. The `gui` package knows how to draw windows; the `cli` package knows how to parse command-line arguments; the `core` package knows how to classify files. They do not mix.
*   **Configuration-Driven:** The classification rules are not hard-coded. They are stored in an external `config/file_types.json` file, making the application flexible and easy to update.

## Directory Structure Breakdown

*   **`smart_classifier/`**: The main Python package.
    *   **`core/`**: The heart of the application.
        *   `classification_engine.py`: Orchestrates the scanning, planning, and execution.
        *   `file_operations.py`: Contains the low-level, safe functions for moving files.
        *   `undo_manager.py`: Manages the transaction log for the undo feature.
    *   **`cli/`**: Contains all code related to the Command-Line Interface, built with `click`.
    *   **`gui/`**: Contains all code for the Graphical User Interface, built with `PySide6`.
        *   `main_window.py`: The main application window and its logic.
        *   `models.py`: (Future) For handling application state.
        *   `widgets.py`: (Future) For custom, reusable UI components.
    *   **`utils/`**: Utility modules used across the application.
        *   `logger.py`: Configures the application-wide logging system.
        *   `thread_manager.py`: Helper for determining optimal thread counts.
    *   **`main.py`**: The single, unified entry point for the application.

*   **`assets/`**: Non-code files like stylesheets (`.qss`) and icons (`.svg`).

*   **`tests/`**: Unit tests, primarily for the `core` package, to ensure logic is correct.