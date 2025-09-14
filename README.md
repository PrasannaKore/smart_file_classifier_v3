# Smart File Classifier v3.0

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-complete-brightgreen.svg)

A professional, dual-mode (CLI + GUI) file classification tool built with Python. Designed for performance, safety, and scalability, it intelligently organizes messy directories into a clean, structured format.

---

## ✨ Core Vision

This project was built on the principles of **Security, Safety, and Robustness**. It features a modular architecture with a shared core engine, ensuring that both the command-line and graphical interfaces are powerful and reliable. Inspired by modern file systems, it is designed to handle everything from a few files to millions with grace and speed.

## 🚀 Key Features

*   **Dual Mode Operation**: Use the fast and scriptable **CLI** for automation or the user-friendly **GUI** for interactive sessions.
*   **Intelligent Classification**: Organizes files based on a comprehensive and customizable JSON configuration.
*   **Advanced Duplicate Handling**: Choose to **skip**, **replace**, or **append a number** to duplicate files.
*   **Safety First**: Includes a **Dry Run** mode to preview changes and a crucial **Undo** feature to revert the last operation.
*   **High Performance**: Leverages **multithreading** to automatically use available CPU cores for blazing-fast I/O operations.
*   **Robust & Responsive**: The GUI is built on a separate worker thread, ensuring the interface never freezes, even with large datasets.
*   **Professional Logging**: Captures detailed logs in `app.log` for auditing and debugging.

## ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/smart_file_classifier_v3.git
    cd smart_file_classifier_v3
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

This tool can be run in two modes from the main entry point.

### 🎨 Graphical User Interface (GUI)

For an interactive experience, launch the GUI.

```bash
python -m smart_classifier.main gui
```
### 🖥️ Command-Line Interface (CLI)
For scripting and automation, use the powerful CLI.
code
Bash
# Get help and see all options
python -m smart_classifier.main cli --help

# Example: Perform a dry run to see what would happen
python -m smart_classifier.main cli -s "C:\Users\User\Downloads" -d "D:\Sorted" --dry-run

# Example: Execute the classification
python -m smart_classifier.main cli -s "C:\Users\User\Downloads" -d "D:\Sorted" --duplicates skip

# Example: Undo the last operation
python -m smart_classifier.main undo```

For more detailed usage instructions, please see the [USAGE.md](./docs/USAGE.md) file.

## 🏛️ Project Structure

The project is organized into a clean, modular structure:
smart_file_classifier_v3/
├── assets/ # Icons and stylesheets
├── config/ # The file type mapping JSON
├── docs/ # Project documentation
├── smart_classifier/ # Main source code package
│ ├── core/ # Shared business logic (the "engine")
│ ├── cli/ # Command-line interface code
│ ├── gui/ # Graphical interface code
│ └── utils/ # Helper modules (logging, threading)
├── tests/ # Unit tests for the core logic
├── README.md # This file
└── LICENSE # MIT License
code
Code
For a more detailed explanation, see the [ARCHITECTURE.md](./docs/ARCHITECTURE.md) file.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.