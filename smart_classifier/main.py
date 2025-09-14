# smart_classifier/main.py

import click

# We import the 'classify' and 'undo' command functions from our CLI module
# and the 'run_gui' function from our GUI module.
from smart_classifier.cli.main import classify, undo
from smart_classifier.gui.main_window import run_gui

@click.group()
def main():
    """
    Smart File Classifier v3.0: A Dual Mode (CLI + GUI) File Organizer.

    Choose a mode to launch: 'gui' for the graphical interface,
    'cli' for the command-line tool, or 'undo' to revert the last operation.
    """
    # This main function acts as a container for our commands.
    pass

@click.command()
def gui():
    """Launches the graphical user interface."""
    run_gui()

# --- Command Registration ---
# We add our three commands, 'gui', 'cli', and 'undo', to the main group.
main.add_command(gui)
main.add_command(classify, name='cli')
main.add_command(undo)

if __name__ == '__main__':
    # This is the standard Python entry point.
    main()