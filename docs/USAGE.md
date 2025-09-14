# Usage Guide

This guide provides detailed instructions for using both the GUI and CLI versions of the Smart File Classifier.

## GUI Usage

1.  **Launch the application:**
    ```bash
    python -m smart_classifier.main gui
    ```
2.  **Select Directories:**
    *   Click **"Browse..."** next to "Source Directory" to choose the messy folder you want to organize.
    *   Click **"Browse..."** next to "Destination Directory" to choose where the new, sorted folders will be created.

3.  **Set Options:**
    *   Use the **"Duplicate Files"** dropdown to select your preferred strategy:
        *   `Append Number` (Default & Safest): Renames duplicates (e.g., `file_1.txt`).
        *   `Skip`: Ignores any file that already exists in the destination.
        *   `Replace`: Overwrites the existing file in the destination. **Use with caution.**

4.  **Perform Actions:**
    *   **Dry Run (Preview):** Click this button first. It will scan the source directory and show a plan in the console log of what files will be moved where, without actually moving anything. This is highly recommended.
    *   **Start Classification:** After reviewing the dry run, click this to begin the real operation. The UI will remain responsive, and you can monitor the progress via the progress bar and console.
    *   **Undo Last Operation:** If you are not satisfied with the result of the last classification, click this button to automatically move every file back to its original location.

## CLI Usage

The CLI is perfect for automation, scripting, and power users.

### Main Command Structure
```bash
python -m smart_classifier.main [COMMAND] [OPTIONS]
```
## Commands

### `cli`
The main classification command.

**Options:**
- `-s`, `--source PATH`: **(Required)** The source directory to scan.
- `-d`, `--destination PATH`: **(Required)** The root destination directory.
- `--duplicates [skip|replace|append_number]`: Sets the duplicate handling strategy. Defaults to `append_number`.
- `--dry-run`: A flag to perform a simulation without moving files.
- `--config PATH`: Path to a custom `file_types.json`. Defaults to the one in the project.
- `--help`: Shows all options.

**Examples:**

```bash
# A safe first run
python -m smart_classifier.main cli -s ./my_mess -d ./my_sorted --dry-run

# A real run, skipping duplicates
python -m smart_classifier.main cli -s ./my_mess -d ./my_sorted --duplicates skip
