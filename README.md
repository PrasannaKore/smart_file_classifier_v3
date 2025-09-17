# Smart File Classifier v3.0

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/status-stable%20%26%20feature--complete-brightgreen.svg?style=for-the-badge)

A professional, dual-mode (CLI + GUI) file organization tool built with Python and PySide6. Designed for performance, safety, and scalability, it intelligently organizes digital clutter into a clean, structured, and user-defined format.

---

<p align="center">
  <em>(It is highly recommended to add a GIF or screenshot of the application in action here)</em>
  <br>
  <!-- Example: <img src="docs/demo.gif" alt="Smart File Classifier in Action"> -->
</p>

---

### **Table of Contents**

1.  [**✨ Project Philosophy**](#-1-project-philosophy)
2.  [**🚀 Key Features**](#-2-key-features)
3.  [**🛠️ Technology Stack**](#-3-technology-stack)
4.  [**⚙️ Installation Guide**](#-4-installation-guide)
5.  [**🕹️ Usage Guide**](#-5-usage-guide)
    *   [🎨 Graphical User Interface (GUI)](#-graphical-user-interface-gui)
    *   [🖥️ Command-Line Interface (CLI)](#-command-line-interface-cli)
6.  [**🔧 Configuration**](#-6-configuration)
7.  [**🏛️ Architecture Deep Dive**](#-7-architecture-deep-dive)
8.  [**📚 Additional Documentation**](#-8-additional-documentation)
9.  [**🤝 Contribution Guide**](#-9-contribution-guide)
10. [**📜 License**](#-10-license)
11. [**🙏 Acknowledgments**](#-11-acknowledgments)

---

## ✨ 1. Project Philosophy

The Smart File Classifier was built upon three foundational principles, ensuring every feature is implemented with the user's peace of mind as the highest priority:

*   **🛡️ Security & Safety**: The application will never perform a destructive action without confirmation. Features like the "Dry Run" mode and a robust "Undo" capability are central to its design. The GUI is proactive, preventing users from starting operations with invalid inputs.
*   **⚙️ Robustness & Reliability**: Through a meticulous development process, the application has been architected to be stable and truthful. The UI provides accurate, real-time feedback, and the backend engine is designed with comprehensive error handling.
*   **🚀 Performance & Scalability**: The application is not just for a few files. Its core engine utilizes an advanced multi-threading pattern to deliver high-speed performance, capable of processing hundreds of thousands of files without compromising control or responsiveness.

## 🚀 2. Key Features

*   **Dual Mode Operation**: A beautiful, intuitive **Graphical User Interface (GUI)** for interactive use and a powerful **Command-Line Interface (CLI)** for scripting and automation. Both modes are powered by the same core engine.
*   **Intelligent & Proactive GUI**: The UI is designed for a mistake-free experience. Action buttons like "Start" and "Dry Run" remain disabled until valid source and destination paths are provided, guiding the user towards a successful operation.
*   **High-Performance Engine**: Utilizes an advanced **Producer-Consumer multi-threading pattern** to deliver maximum file processing speed while remaining fully controllable.
*   **Full Operation Control**:
    *   **Dry Run**: Preview all planned file movements in the Operation Log without making any changes to your filesystem.
    *   **Undo**: Instantly revert the last completed classification operation. The Pause/Resume buttons are disabled during this critical recovery task to ensure data integrity.
    *   **Pause, Resume & Cancel**: Full, real-time control over long-running classification operations. The UI provides instant, truthful feedback.
*   **Advanced Duplicate Handling**: Choose your strategy for handling filename conflicts: `skip`, `replace`, or `append_number` (default).
*   **Responsive & Stable**: The GUI's logic runs in a background "Supervisor" thread, guaranteeing the interface **never freezes** and always provides accurate, real-time progress.
*   **Professional Logging**: Captures detailed, persistent logs in `app.log` for auditing and debugging, in addition to the live log in the GUI.

## 🛠️ 3. Technology Stack

*   **Language**: Python 3.9+
*   **GUI Framework**: PySide6 (The official Qt for Python project)
*   **CLI Framework**: Click
*   **Concurrency**: Python's built-in `threading` and `concurrent.futures` modules.
*   **Styling**: Qt Style Sheets (QSS)

## ⚙️ 4. Installation Guide

Follow these steps to set up and run the project on your local machine.

**1. Prerequisites:**
*   Python 3.9 or newer.
*   `git` for cloning the repository.

**2. Clone the Repository:**
Open your terminal or command prompt and run the following command:
```bash
git clone https://github.com/PrasannaKore/smart_file_classifier_v3.git
cd smart_file_classifier_v3
```

### 3️⃣ Create and Activate a Virtual Environment:
This is a critical step to manage dependencies and avoid conflicts.

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

---

### 4️⃣ Install All Dependencies:
The project requires several packages, including the PySide6 SVG plugin for icons. Install them all with these two commands:

```bash
pip install -r requirements.txt
pip install PySide6-Addons
```

For developers who wish to run tests, also install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

---

### 5️⃣ Verify Installation:
You are now ready to run the application. Test the launch of the GUI:

```bash
python -m smart_classifier.main gui
```

The application window should appear with all icons and styles, indicating a successful installation.

---

## 🕹️ 5. Usage Guide

### 🎨 Graphical User Interface (GUI)

The GUI provides a rich, interactive, and user-friendly experience. It is the recommended mode for most users.

**To Launch:**
```bash
python -m smart_classifier.main gui
```

#### A Typical Workflow:

- **Select Directories:** Use the "Browse..." buttons to select your **Source (messy)** and **Destination** folders. The "Start" and "Dry Run" buttons will become enabled only after both paths are provided.
- **Choose Options:** Use the **Duplicate Files dropdown** to select your preferred strategy (**Append Number**, **Skip**, or **Replace**).
- **Perform a Dry Run:** Click the **"Dry Run"** button. The **Operation Log** will populate with a detailed, safe preview of all planned file movements. *No files will be moved*.
- **Start the Classification:** Click the **"Start"** button. The process will begin, and you can monitor its truthful, real-time progress in the **Status Bar**, **Progress Bar**, and **Operation Log**.
- **Control the Operation:** For large tasks, you can click **Pause** to halt the process, **Resume** to continue, or **Cancel** to abort. The UI will respond instantly.
- **Undo (If Needed):** If you are not satisfied with the results, click the **"Undo"** button to safely move all files back to their original locations.

---

### 🖥️ Command-Line Interface (CLI)

The CLI is a powerful tool for scripting and automation.

**To Get Help:**
```bash
python -m smart_classifier.main cli --help
```

#### Commands:

| Command   | Description                                       |
|-----------|---------------------------------------------------|
| `gui`     | Launches the graphical user interface.            |
| `classify`| The main command for running a classification task. |
| `undo`    | Reverts the last completed classification operation. |

---

#### The `classify` Command in Detail:

| Option        | Shorthand | Description                                                  | Required |
|---------------|-----------|--------------------------------------------------------------|----------|
| `--source`    | `-s`      | The path to the source directory to scan.                    | ✅ Yes   |
| `--destination`| `-d`     | The root destination directory for sorted files.             | ✅ Yes   |
| `--duplicates`|           | Sets the duplicate handling strategy: `skip`, `replace`, or `append_number`. | ❌ No |
| `--dry-run`   |           | A flag to perform a simulation without moving files.         | ❌ No    |
| `--config`    |           | Path to a custom `file_types.json`.                          | ❌ No    |

---

## 🔧 6. Configuration

The "intelligence" of the classifier is driven by the `config/file_types.json` file. You can easily edit this human-readable file to change categories or add new file types without touching a single line of code.

**Example:** To add a new category for 3D model files, you could add the following section to the JSON file:

```json
"3D Models": {
  ".obj": "Wavefront 3D Object File",
  ".fbx": "Autodesk FBX File",
  ".blend": "Blender 3D File"
}
```

The application will automatically recognize these extensions on the next run.

---

## 🏛️ 7. Architecture Deep Dive

This project is built on an advanced, decoupled architecture to ensure performance and stability.

- **Core Engine:**  
  The engine uses a high-speed, multi-threaded **Producer-Consumer Pattern**. A main "producer" loop prepares file-moving tasks and listens for user commands (Pause, Cancel), providing instant control. A pool of "consumer" threads execute these tasks in parallel, providing maximum speed.

- **GUI:**  
  The GUI uses a **"Supervisor" Worker Pattern**. All long-running tasks (scanning, planning, and executing) are offloaded to a background thread. This guarantees the main UI thread is always free, ensuring a perfectly responsive, non-blocking user experience with **truthful, real-time progress updates**.

For a more detailed explanation, please see the **[Architecture Overview](.\docs\ARCHITECTURE.md)**.

---

## 📚 8. Additional Documentation

- **[Execution Guide](.\docs\EXECUTION_GUIDE.md):** Learn how to build the application into a standalone executable (`.exe`).
- **[Integration Guide](.\docs\INTEGRATION_GUIDE.md):** Learn how to integrate the classifier into your own scripts and applications.
- **[Use Cases Guide](.\docs\USE_CASES.md):** Discover real-world applications and workflows for this tool.

---

## 🤝 9. Contribution Guide

Contributions are welcome! We encourage you to open an issue to discuss any major changes you would like to make before submitting a pull request.

---

## 📜 10. License

This project is licensed under the MIT License.  
📄 You can view the full license in the [`LICENSE`](./LICENSE) file.

---

## 🙏 11. Acknowledgments

This project stands on the shoulders of giants. Our deepest thanks to the open-source community and the creators of the incredible tools used in this project, including:

- The Python Software Foundation  
- The Qt Project (for the Qt framework)  
- The PySide6 Team  
- The Click Team
