# smart_classifier/cli/main.py

import logging
from pathlib import Path
import click
from tqdm import tqdm
from smart_classifier.utils.logger import setup_logging

from smart_classifier.core.classification_engine import ClassificationEngine
from smart_classifier.core.file_operations import DuplicateStrategy
from smart_classifier.core.undo_manager import UndoManager

# --- Basic Logging Setup ---
# This configures a simple logger that prints messages to the console.
# More advanced logging (e.g., to a file) will be handled in the utils.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Helper Mapping ---
# Click works with strings, but our engine uses an Enum for type safety.
# This dictionary safely bridges the gap between the user's input and our core logic.
STRATEGY_MAP = {
    'skip': DuplicateStrategy.SKIP,
    'replace': DuplicateStrategy.REPLACE,
    'append_number': DuplicateStrategy.APPEND_NUMBER,
}

# --- The Main CLI Command ---
@click.command()
@click.option(
    '--source', '-s',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path),
    required=True,
    help="The source directory containing the files to classify."
)
@click.option(
    '--destination', '-d',
    type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=Path),
    required=True,
    help="The destination directory where classified folders will be created."
)
@click.option(
    '--duplicates',
    type=click.Choice(['skip', 'replace', 'append_number'], case_sensitive=False),
    default='append_number',
    show_default=True,
    help="Strategy for handling files that already exist in the destination."
)
@click.option(
    '--dry-run',
    is_flag=True,
    help="Simulate the classification without moving any files. Highly recommended for first-time use."
)
@click.option(
    '--config',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path),
    default=Path(__file__).resolve().parents[2] / 'config' / 'file_types.json',
    show_default=True,
    help="Path to the custom file_types.json configuration file."
)
def classify(source: Path, destination: Path, duplicates: str, dry_run: bool, config: Path):
    """
    Scans a source directory and intelligently classifies files into a
    structured destination directory based on predefined rules.
    """
    setup_logging()
    click.echo(click.style("🚀 Starting Smart File Classifier v3.0 🚀", fg='cyan', bold=True))

    try:
        # Step 1: Initialize the core engine.
        # If the config is invalid, this will raise an exception and stop immediately.
        engine = ClassificationEngine(config_path=config)
        duplicate_strategy = STRATEGY_MAP[duplicates]

        # Step 2: Scan the source directory to find all files.
        files_to_classify = engine.scan_directory(source_dir=source)
        if not files_to_classify:
            click.echo(click.style("✅ Source directory is empty or contains no files. Nothing to do.", fg='green'))
            return

        click.echo(f"🔍 Found {len(files_to_classify)} files to classify.")

        # Step 3: Generate the classification plan.
        plan = engine.generate_plan(files=files_to_classify, dest_dir=destination)

        # Step 4: Handle Dry Run mode.
        if dry_run:
            click.echo(click.style("\n--- 📜 DRY RUN MODE 📜 ---", fg='yellow', bold=True))
            click.echo("The following operations would be performed:")
            for src, dest in plan:
                click.echo(f"  [PLAN] Move '{src.name}' TO '{dest}'")
            click.echo(click.style("\nNo files were moved. Run without --dry-run to execute.", fg='yellow'))
            return

        # Step 5: Confirm with the user before making changes. A crucial safety net.
        click.confirm(
            click.style(f"\nReady to move {len(plan)} files. Do you want to proceed?", bold=True),
            abort=True # If the user says 'no', the script will stop here.
        )

        # Step 6: Execute the plan with a progress bar.
        with tqdm(total=len(plan), desc="Classifying Files", unit="file", ncols=100) as pbar:
            def progress_callback(percentage, file_name, status):
                # This inner function updates the progress bar description for each file.
                pbar.set_description(f"Processing: {file_name} [{status}]")
                pbar.update(1)

            engine.execute_plan(
                plan=plan,
                duplicate_strategy=duplicate_strategy,
                progress_callback=progress_callback
            )

        click.echo(click.style(f"\n🎉 Classification complete! All files have been organized.", fg='green', bold=True))

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Initialization Error: {e}")
        click.echo(click.style(f"❌ ERROR: A critical error occurred during setup. {e}", fg='red', bold=True))
    except click.exceptions.Abort:
        click.echo(click.style("\n🛑 Operation cancelled by user.", fg='red'))
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        click.echo(click.style(f"❌ ERROR: An unexpected error occurred: {e}", fg='red', bold=True))


@click.command()
def undo():
    """Reverts the last classification operation by moving files back."""
    click.echo(click.style("⏪ Starting Undo Operation ⏪", fg='yellow', bold=True))

    # This dummy tqdm bar will be updated by our callback.
    with tqdm(total=100, desc="Preparing undo...", unit="file", ncols=100) as pbar:
        def undo_callback(processed: int, total: int, message: str):
            # The first time the callback runs, we set the correct total.
            if pbar.total == 100 and total > 0:
                pbar.total = total

            pbar.set_description(message)
            pbar.update(1 if processed > 0 else 0)

        UndoManager.undo_last_operation(progress_callback=undo_callback)

    click.echo(click.style("\n✅ Undo complete.", fg='green', bold=True))