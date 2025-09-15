# Smart File Classifier v3.0

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)

A professional, dual-mode (CLI + GUI) file organization tool built with Python and PySide6. Designed for performance, safety, and scalability, it intelligently organizes messy directories into a clean, structured format based on a powerful, user-customizable configuration.

---

## ✨ Project Overview

The Smart File Classifier is a robust utility designed to tackle the common problem of digital clutter. It scans a source directory filled with miscellaneous files and intelligently moves them into a structured destination, creating categories and sub-folders based on file types. Its dual-mode nature makes it perfect for both interactive, visual organization (GUI) and powerful, automated scripting workflows (CLI).

The core philosophy of this project is **Security, Safety, and Robustness**. Every file operation is designed to be safe, with features like a "Dry Run" mode to preview changes and a crucial "Undo" function to revert the last operation, ensuring peace of mind when organizing critical data.

## 🚀 Key Features

*   **Dual Mode Operation**: A beautiful, intuitive **Graphical User Interface (GUI)** for interactive use and a powerful **Command-Line Interface (CLI)** for scripting and automation.
*   **Intelligent Classification**: Sorts files into `Category/extension` sub-folders (e.g., `Documents & Text/pdf/`) based on a comprehensive and easily editable `file_types.json` configuration.
*   **Full Operation Control**:
    *   **Dry Run**: Preview exactly what changes will be made without moving a single file.
    *   **Undo**: Instantly revert the last classification operation with a single command.
    *   **Pause, Resume & Cancel**: Full control over long-running operations directly from the GUI.
*   **Advanced Duplicate Handling**: Choose how to handle files that already exist in the destination: `skip`, `replace`, or `append_number` (default).
*   **High Performance**: Leverages a multi-threaded architecture (`ThreadPoolExecutor`) to dramatically speed up file operations by utilizing multiple CPU cores, making it ideal for large datasets.
*   **Responsive & Stable GUI**: The classification engine runs in a separate background thread, ensuring the user interface remains smooth and responsive at all times, even when processing hundreds of thousands of files.
*   **Professional Logging**: Captures detailed, persistent logs in `app.log` for auditing, debugging, and history tracking.

## 🛠️ Full Installation Guide

Follow these steps to set up the project on your local machine.

**1. Prerequisites:**
*   Python 3.9 or newer.
*   `git` for cloning the repository.

**2. Clone the Repository:**
Open your terminal or command prompt and run the following command to clone the project:
```bash
git clone https://github.com/PrasannaKore/smart_file_classifier_v3.git
cd smart_file_classifier_v3
```

**3. Create a Virtual Environment:**
It is highly recommended to use a virtual environment to manage dependencies and avoid conflicts.
code
Bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

**4. Install Dependencies:**
**The project's dependencies are listed in requirements.txt. Install them using pip:**
```Bash
pip install -r requirements.txt
```

**For developers who wish to run tests, install the development dependencies:**
```Bash
pip install -r requirements-dev.txt
```

**5. Verify Installation:**
You are now ready to run the application. Test the launch of the GUI:

```Bash
python -m smart_classifier.main gui
```

The application window should appear, indicating a successful installation.

## ⚙️ Modes of the Project
The application can be used in two distinct modes, sharing the same powerful core engine.

## 🎨 Graphical User Interface (GUI)
The GUI provides a rich, interactive, and user-friendly experience. It is the recommended mode for most users.
To Launch:
```Bash
python -m smart_classifier.main gui
```
**GUI Features Explained:**
* **Source & Destination Selectors**: Use the "Browse..." buttons to easily select the messy folder you want to organize and the destination where the sorted folders will be created.
*   **Duplicate Files Dropdown**: Choose your strategy for handling filename conflicts:
*   **Append Number**: (Default & Safest) Renames duplicates (e.g., report.pdf becomes report_1.pdf).
*   **Skip**: If a file already exists at the destination, the original file is left untouched.
*   **Replace**: Overwrites the file at the destination. Use with caution.
**Action Buttons:**
*   **Start**: Begins the main classification process.
*   **Pause**: Temporarily halts the operation. The progress bar turns yellow.
*   **Resume**: Continues a paused operation. The progress bar turns green again.
*   **Cancel**: Aborts the current operation. The progress bar turns red and resets.
*   **Dry Run**: Scans and generates a plan, showing what will happen in the Operation Log without moving any files.
*   **Undo**: Reverts the last completed classification operation.
*   **Status Bar**: Provides real-time, at-a-glance feedback on the application's current state (e.g., "Idle," "Classifying 5,000 files...," "Operation Paused").
*   **Progress Bar**: Shows the overall progress of the current operation with color-coded states: Green (Running/Success), Yellow (Paused), Red (Cancelled/Error).
Operation Log: A scalable, memory-efficient log that displays a real-time list of every file operation as it happens.

## 🖥️ Command-Line Interface (CLI)
The CLI is a powerful tool for power users, scripting, and automation. It exposes all core features of the application through a clean and well-documented command structure.
To Launch & Get Help:
```Bash
python -m smart_classifier.main cli --help
```
**CLI Commands & Features Explained:**
**1. classify**
This is the main command for running a classification task.
Usage:
```Bash
python -m smart_classifier.main cli [OPTIONS]
```
**Options:**
*   **-s, --source PATH**: (Required) The path to the source directory containing the files to classify.
*   **-d, --destination PATH**: (Required) The path to the destination directory where sorted folders will be created.
*   **--duplicates [skip|replace|append_number]**: Sets the strategy for handling duplicates. Defaults to append_number.
*   **--dry-run**: A flag to perform a simulation. It will print the planned operations without moving any files.
*   **--config PATH**: Optionally provide a path to a custom file_types.json configuration file.
*   **Examples**:

```Bash
# Perform a safe dry run to preview the changes
python -m smart_classifier.main cli -s "./Downloads" -d "./Sorted Documents" --dry-run
```

# Run the classification, skipping any existing files
```
python -m smart_classifier.main cli -s "./Downloads" -d "./Sorted Documents" --duplicates skip
```

**2. undo**
This command reverts the last completed classification operation. It takes no arguments.
Usage:

```Bash
python -m smart_classifier.main undo
```
The command will read the transaction log from the last operation and move all files back to their original locations, showing a progress bar as it works.

## 🤝 Contribution Guide
Contributions are welcome! Please follow these steps to contribute:
Fork the repository.
Create a new branch for your feature or bug fix (git checkout -b feature/my-new-feature).
Commit your changes (git commit -m 'Add some amazing feature').
Push to the branch (git push origin feature/my-new-feature).
Open a Pull Request.
Please open an issue first to discuss any major changes you would like to make.

## 📜 License
This project is licensed under the [LICENSE](./LICENSE). See the LICENSE file for full details.