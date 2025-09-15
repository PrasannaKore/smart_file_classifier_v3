# Execution Guide: Creating a Standalone Application

This guide provides step-by-step instructions on how to build the Smart File Classifier into a single, standalone executable file (`.exe` on Windows). This allows you to distribute and run the application on other machines without requiring users to install Python or any dependencies.

We will use **PyInstaller**, a powerful and popular tool for this purpose.

---

### 1. Prerequisites

Before you begin, ensure you have the following:

*   A working project setup as described in `README.md`.
*   All dependencies installed from `requirements.txt`.
*   **PyInstaller**: If you don't have it, install it into your virtual environment:
    ```bash
    pip install pyinstaller
    ```

### 2. The Challenge: Bundling Data Files

A standard PyInstaller build only packages your `.py` source code. It will **not** automatically include our project's essential data files:
*   The `config/` directory (containing `file_types.json`)
*   The `assets/` directory (containing `styles/` and `icons/`)

If these are not included, the executable will fail at runtime because it won't be able to find its configuration or icons. We solve this using the `--add-data` flag.

### 3. How to Create the Executable

Open your terminal or command prompt, activate your virtual environment, and navigate to the **root directory** of the project (`smart_file_classifier_v3/`).

#### Command for the GUI Application (`.exe`)

This is the main command to build the windowed GUI application. It creates a single executable file and correctly bundles all necessary data files.

```bash
# For Windows (use ; as the path separator in --add-data)
pyinstaller --onefile --windowed --name "SmartFileClassifier" --add-data "config;config" --add-data "assets;assets" smart_classifier/main.py
```
# For macOS/Linux (use : as the path separator in --add-data)
**pyinstaller --onefile --windowed --name "SmartFileClassifier" --add-data "config:config" --add-data "assets:assets" smart_classifier/main.py**
**Command Breakdown:**
* **--onefile**: Packages everything into a single .exe file for easy distribution.
* **--windowed**: Prevents a console window from appearing in the background when the GUI is run.
* **--name "SmartFileClassifier"**: Sets the name of the output executable.
* **--add-data "source;destination"**: This is the most critical part. It tells PyInstaller to copy the config and assets folders from the source into the final package, placing them in folders with the same names at the root level.
* **smart_classifier/main.py**: This is the entry point script for our application.
Output
After the command finishes, you will find a new dist folder in your project root. Inside dist, you will find your standalone application: SmartFileClassifier.exe (on Windows).

### 4. How to Reflect Updates in the Code
* If you make any changes to the Python source code, the config/file_types.json, or any of the assets, you must rebuild the executable.
* The process is simple:
* Save all your changes in the source code.
* Delete the old dist and build folders to ensure a clean build.
* Run the exact same pyinstaller command from Step 3 again.
* This will create a new .exe in the dist folder that contains all of your latest updates.

### 5. How to Run the Executable
**On Windows**:
Navigate to the dist folder.
Simply double-click SmartFileClassifier.exe to launch the GUI.
**On macOS/Linux**:
Navigate to the dist folder.
**You may need to make the application executable first**: chmod +x SmartFileClassifier.
**Run it from the terminal**: ./SmartFileClassifier.
The application will launch and function exactly as it does when run from the source code.

### 6. Troubleshooting & Tips
* **Problem**: The executable starts, but my icons are missing or it says "config file not found."
* **Solution**: This almost always means the --add-data paths were incorrect. Double-check that you are running the pyinstaller command from the project root directory and that the source;destination paths are correct for your OS.
* **Problem**: The executable flashes on the screen and then disappears immediately.
* **Solution**: This indicates a crash at startup. To see the error message, run the executable from a terminal (cmd.exe or PowerShell on Windows). The traceback will be printed to the console, revealing the cause of the crash.
* **Tip**: Using a .spec file: For complex projects, PyInstaller generates a .spec file (e.g., SmartFileClassifier.spec). You can edit this file to have more control over the build process. Once you have a working command, you can simply run pyinstaller SmartFileClassifier.spec in the future to rebuild with the same settings.