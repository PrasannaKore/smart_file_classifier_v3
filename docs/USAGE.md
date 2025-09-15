# Smart File Classifier: User Guide

This guide provides detailed, step-by-step instructions for using both the Graphical User Interface (GUI) and the Command-Line Interface (CLI) versions of the Smart File Classifier.

---

### **Table of Contents**

1.  [GUI Usage](#-graphical-user-interface-gui-usage)
    *   [Launching the GUI](#launching-the-gui)
    *   [A Typical Workflow: Step-by-Step](#a-typical-workflow-step-by-step)
2.  [CLI Usage](#-command-line-interface-cli-usage)
    *   [Main Command Structure](#main-command-structure)
    *   [Detailed Command Breakdown](#detailed-command-breakdown)
3.  [Advanced Topics](#-advanced-topics)
    *   [Customizing Classification Rules](#customizing-classification-rules)

---

## 🎨 Graphical User Interface (GUI) Usage

The GUI provides a rich, interactive, and user-friendly experience, making it the recommended mode for most users.

### Launching the GUI

Ensure you have installed the project and activated your virtual environment as described in the main [README.md](../README.md). To launch the application, run the following command from the project's root directory:

```bash
python -m smart_classifier.main gui
```

---

## A Typical Workflow: Step-by-Step

Here is a guide to using the GUI for a standard file organization task.

---

### Step 1: Select Your Directories

**Source Directory:**  
Click the "Browse..." button next to this field to select the messy folder you want to organize.

**Destination Directory:**  
Click the "Browse..." button next to this field to choose the parent folder where the new, sorted sub-folders will be created.

---

### Step 2: Choose Your Options

**Duplicate Files:** Use the dropdown menu to select your preferred strategy for handling files that already exist at the destination.

- **Append Number (Default & Safest):**  
  If `report.pdf` already exists, the new file will be renamed to `report_1.pdf`.

- **Skip:**  
  If `report.pdf` already exists, the source file will be left in its original location and will not be moved.

- **Replace:**  
  Overwrites the existing file at the destination with the new file from the source.  
  ⚠️ Use this option with caution as it can lead to data loss.

---

### Step 3: Perform a Dry Run (Highly Recommended)

Before moving any files, it is always a good idea to see what the application plans to do.

- Click the **"Dry Run"** button.
- The application will scan the source directory and populate the Operation Log with a detailed plan of every file it intends to move and its new destination.
- No files will be moved at this stage. This is a safe preview.

---

### Step 4: Start the Classification

Once you have reviewed the plan and are satisfied, you can begin the real operation.

- Click the **"Start"** button.
- The process will begin, and you can monitor its progress in real-time:
  - The **Status Bar** will show the current action (e.g., `"Classifying 10,000 files..."`).
  - The **Progress Bar** will fill up, turning **GREEN** to indicate it's running.
  - The **Operation Log** will show a live feed of each file being moved.

---

### Step 5: Control the Operation (Pause, Resume, Cancel)

For large operations, you have full control:

- **Pause:**  
  Click this button to temporarily halt the process.  
  The progress bar will turn **YELLOW**, and the Status Bar will indicate that the operation is paused.

- **Resume:**  
  Once paused, click this button to continue the operation from where it left off.  
  The progress bar will turn **GREEN** again.

- **Cancel:**  
  Click this button and confirm in the dialog to abort the operation completely.  
  The progress bar will turn **RED** and then reset, and the UI will return to its idle state.

---

### Step 6: Undo the Operation (If Needed)

If you are not happy with the results of the classification, you can easily revert it.

- Click the **"Undo"** button.
- The application will read its transaction log from the last operation and move every single file back to its original location.

---

## 🖥️ Command-Line Interface (CLI) Usage

The CLI is a powerful tool for power users, scripting, and automating organization tasks.

---

### Main Command Structure

All CLI interactions start with the same base command from the project root:

```bash
python -m smart_classifier.main [COMMAND] [OPTIONS]
```

---

## 🔍Detailed Command Breakdown

### 1. `classify`

This is the main command for running a classification task.

**Usage:**

```bash
python -m smart_classifier.main classify [OPTIONS]
```

> 🔁 **Note:** In earlier versions, this command was invoked using `cli`, which is still supported as an alias for backward compatibility.

---

## 🧰 CLI Options Summary
| Option          | Shorthand | Description                                                                                          | Required |
|-----------------|-----------|------------------------------------------------------------------------------------------------------|----------|
| `--source`      | `-s`      | The path to the source directory to scan.                                                           | ✅ Yes   |
| `--destination` | `-d`      | The root destination directory for sorted files.                                                    | ✅ Yes   |
| `--duplicates`  |           | Sets the duplicate handling strategy: `skip`, `replace`, or `append_number`. Defaults to append.    | ❌ No    |
| `--dry-run`     |           | Performs a simulation without moving files.                                                         | ❌ No    |
| `--config`      |           | Path to a custom `file_types.json`. Defaults to the one in the project.                             | ❌ No    |
| `--help`        |           | Shows all CLI options and exits.                                                                    | ❌ No    |

---

## 🧪 CLI Examples

```bash
# A safe first run to preview the changes in the "Downloads" folder
python -m smart_classifier.main classify -s "./Downloads" -d "./Sorted_Files" --dry-run

# A real run, skipping duplicate files at the destination
python -m smart_classifier.main classify -s "./Downloads" -d "./Sorted_Files" --duplicates skip

# A real run, replacing any existing files at the destination
python -m smart_classifier.main classify -s "./Downloads" -d "./Sorted_Files" --duplicates replace
```

---

## 🔁 2. `undo`

This command **reverts the most recent classify operation**.  
It takes **no arguments**.

**Example:**

```bash
python -m smart_classifier.main undo
```

---

## 🖼️ 3. `gui`

This command **launches the Graphical User Interface (GUI)**.  
It takes **no arguments**.

**Example:**

```bash
python -m smart_classifier.main gui
```

---

## 🚀 Advanced Topics

### 🧠Customizing Classification Rules

The “intelligence” of the classifier comes from the `config/file_types.json` file.  
You can edit this file to:

- ✅ Change existing categories  
- ✅ Add new file types  
- ✅ Create new folders automatically based on extensions

---

**Example:**  
To add a new category for 3D model files, add the following to your JSON config:

```json
{
  "3D Models": {
    ".obj": "Wavefront 3D Object File",
    ".fbx": "Autodesk FBX File",
    ".blend": "Blender 3D File"
  }
}
```

> 💡 The next time you run the classifier, it will automatically recognize these extensions and create a `3D Models` folder.

---
