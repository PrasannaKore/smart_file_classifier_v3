# smart_classifier/cli/main.py

import logging
from pathlib import Path
import click
# The 'rich' library is our tool for creating a beautiful, modern CLI experience.
from rich.console import Console
from rich.table import Table

# We import all the necessary components from our robust core engine.
from smart_classifier.core.classification_engine import ClassificationEngine
from smart_classifier.core.file_operations import DuplicateStrategy
from smart_classifier.core.undo_manager import UndoManager
from smart_classifier.core.bulk_importer import BulkImporter

# --- Setup ---
# We create a single Console object to manage all rich-formatted output.
console = Console()
logger = logging.getLogger(__name__)

# A simple, safe mapping from user-friendly string choices to our internal Enum.
STRATEGY_MAP = {
    'skip': DuplicateStrategy.SKIP,
    'replace': DuplicateStrategy.REPLACE,
    'append': DuplicateStrategy.APPEND_NUMBER,
}


# --- Main Command Group ---
# This is the root of our entire CLI. Using @click.group() makes our CLI
# extensible, like a folder that can hold other commands.
@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version="3.0", prog_name="Smart File Classifier")
def sfc():
    """
    🗂️ Smart File Classifier v3.0 - A Professional Tool for Intelligent File Organization.

    This CLI provides a powerful and scriptable interface to the core classification engine.
    Use `[COMMAND] --help` for more information on a specific command.
    """
    pass


# --- Classification Command ---
# This command is attached to our main 'sfc' group.
@sfc.command()
# Each @click.option defines a command-line flag, complete with type checking,
# help text, and default values, creating a self-documenting interface.
@click.option('-s', '--source',
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path),
              required=True, help="The source directory to scan.")
@click.option('-d', '--destination', type=click.Path(file_okay=False, dir_okay=True, path_type=Path), required=True,
              help="The destination for sorted files.")
@click.option('--duplicates', type=click.Choice(['skip', 'replace', 'append'], case_sensitive=False), default='append',
              show_default=True, help="Strategy for handling duplicate files.")
@click.option('--dry-run', is_flag=True, help="Simulate the classification without moving any files.")
@click.option('--config', type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path), default=None,
              help="Path to a custom file_types.json.")
def classify(source: Path, destination: Path, duplicates: str, dry_run: bool, config: Path):
    """🧠 Scans and intelligently classifies files from a source to a destination."""

    # Using rich's console.print with markup for beautiful, clear output.
    console.print(f"[bold cyan]🚀 Starting Classification...[/bold cyan]")
    console.print(f"Source: [bright_magenta]{source}[/bright_magenta]")
    console.print(f"Destination: [bright_magenta]{destination}[/bright_magenta]")

    if dry_run:
        console.print("[yellow]Running in Dry Run mode. No files will be moved.[/yellow]")

    try:
        # The logic remains the same: instantiate the engine and get the plan.
        config_path = config if config else Path(__file__).resolve().parents[2] / 'config' / 'file_types.json'
        engine = ClassificationEngine(config_path)
        duplicate_strategy = STRATEGY_MAP[duplicates]

        console.print("Scanning for items...")
        # Our new, smarter scan_directory now returns both files and project folders.
        items_to_process = engine.scan_directory(source)

        if not items_to_process:
            console.print("[bold green]✅ No items found to classify. Operation complete.[/bold green]")
            return

        console.print(f"Found {len(items_to_process)} items. Generating plan...")
        plan = engine.generate_plan(items_to_process, destination)

        # --- REPLACED: The Dry Run logic is now smarter ---
        if dry_run:
            # We create a rich Table for a beautiful, professional preview.
            table = Table(title="Classification Plan Preview", style="cyan", title_style="bold magenta")
            table.add_column("Item Name", style="green", no_wrap=True)
            table.add_column("Item Type", style="blue")
            table.add_column("Will be Moved To", style="yellow")

            # We now intelligently check if the item is a directory (our project signal).
            for src, dest in plan[:20]:  # Preview first 20 for brevity
                item_type = "[bold]Project Folder[/bold]" if src.is_dir() else "File"
                table.add_row(src.name, item_type, str(dest))

            console.print(table)
            if len(plan) > 20:
                console.print(f"...and {len(plan) - 20} more items.")
            return
        # --- END REPLACEMENT ---

        # A crucial safety net: confirm with the user before making changes.
        click.confirm(f"\nReady to move {len(plan)} items. Do you want to proceed?", abort=True)

        # The powerful, pausable engine is called here.
        # Note: A CLI progress bar for the producer-consumer is complex.
        # For now, we let the existing INFO logs show the progress.
        engine.execute_plan(plan, duplicate_strategy)

        console.print("[bold green]🎉 Classification complete! All items have been organized.[/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ An unexpected error occurred: {e}[/bold red]")
        logger.error("CLI classify command failed.", exc_info=True)


# --- The following commands are PRESERVED in their final, correct state ---
# No changes are needed for the undo and knowledge base commands.

@sfc.command()
def undo():
    """⏪ Reverts the last classification operation."""
    console.print("[bold yellow]Starting Undo Operation...[/bold yellow]")
    click.confirm("This will move files from the last operation back to their original locations. Are you sure?",
                  abort=True)
    UndoManager.undo_last_operation()
    console.print("[bold green]✅ Undo operation complete.[/bold green]")


@sfc.group()
def knowledge():
    """📚 Manage the application's knowledge base (file_types.json)."""
    pass


@knowledge.command(name="import")
@click.argument('csv_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path))
@click.option('--config', type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path), default=None,
              help="Path to the file_types.json to update.")
def bulk_import(csv_path: Path, config: Path):
    """📥 Bulk imports new file type rules from a CSV file."""
    console.print(f"[bold cyan]Starting bulk import from '{csv_path.name}'...[/bold cyan]")
    try:
        config_path = config if config else Path(__file__).resolve().parents[2] / 'config' / 'file_types.json'
        importer = BulkImporter(config_path)
        importer.process_csv(csv_path)
        report = importer.report
        console.print("[bold green]✅ Import process complete.[/bold green]")
        table = Table(title="Import Summary", show_header=False)
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="bold magenta")
        if report["added"]: table.add_row("New Rules Added", str(len(report["added"])))
        if report["updated"]: table.add_row("Conflicts Resolved", str(len(report["updated"])))
        if report["duplicates"]: table.add_row("Duplicates Skipped", str(len(report["duplicates"])))
        if report["errors"]: table.add_row("[red]Errors Encountered[/red]", str(len(report["errors"])))
        console.print(table)
        console.print("See [yellow]app.log[/yellow] for detailed information.")
    except Exception as e:
        console.print(f"[bold red]❌ A critical error occurred during import: {e}[/bold red]")
        logger.error("CLI knowledge import command failed.", exc_info=True)