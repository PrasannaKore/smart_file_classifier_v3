# 🚀 Execution Guide: Creating a Standalone Application

This guide provides step-by-step instructions on how to build the Smart File Classifier into a single, standalone executable file (`.exe` on Windows). This allows you to distribute and run the application on other machines **without requiring users to install Python or any dependencies**.

We will use **PyInstaller**, a powerful and popular tool for this purpose.

---

## 1. 🧱 Prerequisites

Before you begin, ensure you have the following:

- A working project setup as described in the main `README.md`.
- All dependencies installed from `requirements.txt`.
- **PyInstaller**: If you don't have it, install it into your virtual environment:

```bash
pip install pyinstaller
```

---

## 2. 📦 The Challenge: Bundling Data Files

A standard PyInstaller build only packages your `.py` source code. It will **not** automatically include your project's essential data files:

- The `config/` directory (containing `file_types.json`)
- The `assets/` directory (containing `styles/` and `icons/`)

If these are not included, the executable will fail at runtime because it won’t be able to find its configuration or icons. We solve this using the `--add-data` flag.

---

## 3. 🛠️ How to Create the Executable

Open your terminal, activate your virtual environment, and navigate to the **root directory** of the project (`smart_file_classifier_v3/`).

### ✅ Command for the GUI Application

This command builds the GUI into a single `.exe` and correctly bundles all necessary data files.

```bash
# For Windows (use ; as the path separator in --add-data)
pyinstaller --onefile --windowed --noconfirm --name "SmartFileClassifier" --add-data "config;config" --add-data "assets;assets" smart_classifier/main.py

# For macOS/Linux (use : as the path separator in --add-data)
pyinstaller --onefile --windowed --noconfirm --name "SmartFileClassifier" --add-data "config:config" --add-data "assets:assets" smart_classifier/main.py
```

---

## 🧩 Command Breakdown

To package the Smart File Classifier as a standalone executable, you typically use **PyInstaller** with the following flags:

- `--onefile`:  
  Packages everything into a single `.exe` file for easy distribution.

- `--windowed`:  
  Prevents a console window from appearing when the GUI is run.

- `--noconfirm`:  
  Automatically overwrites previous builds without prompting.

- `--name "SmartFileClassifier"`:  
  Sets the name of the output executable.

- `--add-data "source;destination"` (Windows) or `"source:destination"` (macOS/Linux):  
  Copies the `config` and `assets` folders into the final package so they are available at runtime.

- `smart_classifier/main.py`:  
  The main entry point of the application.

---

## 📤 Output

After the command finishes, PyInstaller will create a new `dist/` directory. Inside it, you’ll find your standalone application:

```bash
dist/
└── SmartFileClassifier.exe   # On Windows
```

You can now share this `.exe` file with others—even if they don’t have Python installed.

---

## 🔁 How to Reflect Updates in the Code

If you make **any changes** to the source code, `config/file_types.json`, or assets:

1. Save all your changes.
2. *(Optional but recommended)* Delete the old `dist/` and `build/` directories to ensure a clean build.
3. Run the exact same PyInstaller command from Step 3 again.

This will regenerate the executable with the latest code and assets.

---

## ▶️ How to Run the Executable

### On Windows:

1. Navigate to the `dist/` folder.
2. Double-click `SmartFileClassifier.exe` to launch the GUI.

### On macOS/Linux:

1. Navigate to the `dist/` folder.
2. You may need to make the app executable:

```bash
chmod +x SmartFileClassifier
```

**3. Run it from the terminal**:

```bash
./SmartFileClassifier
```

The application will launch and function just like it does when running from the source code.

---

## 🧰 Troubleshooting & Tips

### ❌ Problem: The executable starts, but icons/configs are missing

**Symptom:**  
App launches but assets or `file_types.json` are not found.

**Fix:**  
- Check that `--add-data` paths are correct.
- Ensure you're running PyInstaller from the **project root directory**.
- Verify you're using the correct path separator (`;` for Windows, `:` for macOS/Linux).

---

### ❌ Problem: The app flashes and disappears

**Symptom:**  
The executable opens and closes immediately.

**Fix:**  
- Run the executable from a terminal (e.g., PowerShell or `cmd.exe`) to see error messages.
- Alternatively, remove `--windowed` when building to expose errors in a console window.

---

### 💡 Tip: Use a `.spec` file for advanced control

PyInstaller generates a `.spec` file (e.g., `SmartFileClassifier.spec`) after the first build. You can:

- Edit it for fine-grained control (e.g., include more data or modify settings).
- Rebuild using the spec file:

```bash
pyinstaller SmartFileClassifier.spec
```

---

## 📜 Example PyInstaller Command (Final)

```bash
pyinstaller --onefile --windowed --noconfirm --name "SmartFileClassifier" \
--add-data "config;config" --add-data "assets;assets" smart_classifier/main.py
```

> ✅ Make sure you're in the **project root directory** when running this command.
