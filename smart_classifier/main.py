# smart_classifier/main.py

import click

# We import the main command group from our advanced CLI module.
from smart_classifier.cli.main import sfc
# We import the main entry point for our advanced GUI module.
from smart_classifier.gui.main_window import run_gui

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
def main():
    """
    Smart File Classifier v3.0: A Dual Mode (CLI + GUI) File Organizer.

    This is the main entry point for the application. To run the graphical
    interface, use the 'gui' command. For the command-line tool, use the
    'cli' command followed by its own sub-commands.

    Example (GUI): python -m smart_classifier.main gui
    Example (CLI): python -m smart_classifier.main cli --help
    """
    pass

@click.command()
def gui():
    """🎨 Launches the professional graphical user interface."""
    run_gui()

# --- Command Registration ---
# We register our two primary commands, 'gui' and 'cli', to the main group.
# The 'cli' command itself is a group that contains our powerful sub-commands
# like 'classify' and 'knowledge'.
main.add_command(gui)
main.add_command(sfc, name='cli')

if __name__ == '__main__':
    # This block allows the script to be run directly and is the
    # standard entry point for Python applications.
    main()