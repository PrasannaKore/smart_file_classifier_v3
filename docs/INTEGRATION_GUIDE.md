# Integration Guide: Smart File Classifier v3.0

This guide provides developers with instructions on how to integrate the Smart File Classifier into their own applications, scripts, and automated workflows. The project's modular design offers two primary methods for integration.

---

## Method 1: CLI Integration (Subprocess)

This is the simplest and most language-agnostic method. You can call the classifier's Command-Line Interface (CLI) as a subprocess from any programming language.

### Key Concepts

*   **Command Structure**: `python -m smart_classifier.main [COMMAND] [OPTIONS]`
*   **Exit Codes**: The script uses standard exit codes. A return code of `0` indicates success, while any non-zero code indicates an error.
*   **Output**: The script logs detailed information to `stdout` and `stderr`, which can be captured by your parent process.

### Step-by-Step Example (Python)

This example shows how to run the classifier from another Python script using the `subprocess` module.

```python
import subprocess
import sys

def run_classifier(source_dir: str, dest_dir: str):
    """
    Runs the Smart File Classifier as a subprocess.
    
    Args:
        source_dir: The source directory to classify.
        dest_dir: The destination for the sorted files.
    """
    command = [
        sys.executable,  # This ensures we use the same Python interpreter
        "-m", "smart_classifier.main",
        "cli",
        "-s", source_dir,
        "-d", dest_dir,
        "--duplicates", "skip" # Example option
    ]
    
    print(f"Running command: {' '.join(command)}")
    
    try:
        # Run the command, capture output, and check for errors
        result = subprocess.run(
            command,
            check=True,         # Raises an exception if the return code is non-zero
            capture_output=True,# Captures stdout and stderr
            text=True           # Decodes output as text
        )
        print("Classifier ran successfully!")
        print("Output:\n", result.stdout)
    except FileNotFoundError:
        print("Error: 'python' command not found. Is Python in your system's PATH?")
    except subprocess.CalledProcessError as e:
        print(f"Error: The classifier exited with a non-zero status code: {e.returncode}")
        print("STDERR:\n", e.stderr)
```
# --- Usage ---
# run_classifier("/path/to/your/messy_folder", "/path/to/your/sorted_folder")
Example (Bash Script)
```Bash
#!/bin/bash

SOURCE_DIR="./my_downloads"
DEST_DIR="./my_archive"

echo "Starting file classification..."

python -m smart_classifier.main cli -s "$SOURCE_DIR" -d "$DEST_DIR"

if [ $? -eq 0 ]; then
    echo "Classification completed successfully."
else
    echo "Classification failed with an error."
fi
```
## Method 2: Library Integration (Direct Import in Python)
For Python-based projects, this is the most powerful and flexible method. You can directly import and use the core classification engine.
Key Concepts
The Engine: All core logic resides in the smart_classifier.core.classification_engine.ClassificationEngine class.
UI-Agnostic: This engine is completely independent of the GUI and CLI, making it perfectly safe to import.
Progress Callback: The execute_plan method accepts an optional progress_callback function, allowing your application to receive real-time updates.
Step-by-Step Example

```Python

from pathlib import Path
from smart_classifier.core.classification_engine import ClassificationEngine
from smart_classifier.core.file_operations import DuplicateStrategy

def my_custom_progress_callback(percentage: int, file_name: str, status: str):
    """A custom function to receive progress updates from the engine."""
    print(f"[{percentage}%] - {status}: {file_name}")

def integrate_classifier_as_library(source_dir_path: str, dest_dir_path: str):
    """
    Demonstrates how to use the ClassificationEngine as a library.
    """
    try:
        # 1. Define paths. The engine uses pathlib.Path objects.
        source_dir = Path(source_dir_path)
        dest_dir = Path(dest_dir_path)
        config_path = Path("./config/file_types.json") # Adjust if needed

        # 2. Instantiate the engine.
        # This will load and parse the classification rules from the JSON file.
        engine = ClassificationEngine(config_path=config_path)

        # 3. Scan the source directory to get a list of files.
        files_to_process = engine.scan_directory(source_dir=source_dir)
        if not files_to_process:
            print("No files found to process.")
            return

        print(f"Found {len(files_to_process)} files.")

        # 4. Generate a classification plan (this is the "Dry Run" step).
        plan = engine.generate_plan(files=files_to_process, dest_dir=dest_dir)

        # 5. Execute the plan.
        # This will start the multi-threaded file moving operation and call
        # our custom callback function with real-time updates.
        print("\nStarting classification...")
        engine.execute_plan(
            plan=plan,
            duplicate_strategy=DuplicateStrategy.APPEND_NUMBER,
            progress_callback=my_custom_progress_callback
        )
        print("\nClassification finished!")

    except FileNotFoundError as e:
        print(f"Error: A required file or directory was not found. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
``` 
# --- Usage ---
# integrate_classifier_as_library("./my_messy_folder", "./my_sorted_folder")
Dependency Handling
When integrating the classifier as a library, you must ensure that its dependencies are also installed in your project's environment. You can achieve this by including the contents of requirements.txt in your own project's requirements file.
code
Code
# Your project's requirements.txt
your_other_dependency==1.2.3

# Dependencies from Smart File Classifier
pyside6
click
tqdm