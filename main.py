# smart_classifier/main.py

import click

# We import the 'classify' command function from our CLI module
# and the 'run_gui' function from our GUI module.
# This is a perfect example of our modular design in action. The main entry
# point does not contain any application logic itself; it only directs traffic.
from smart_classifier.cli.main import classify
from smart_classifier.gui.main_window import run_gui

@click.group()
def main():
    """
    Smart File Classifier v3.0: A Dual Mode (CLI + GUI) File Organizer.

    Choose a mode to launch: 'gui' for the graphical interface,
    or 'cli' for the command-line tool.
    """
    # This main function acts as a container for our commands.
    # When the script is run, this function's docstring is shown
    # as the main help text.
    pass

@click.command()
def gui():
    """Launches the graphical user interface."""
    # This command is simple: it just calls the function that starts
    # the entire PySide6 application.
    run_gui()

# --- Command Registration ---
# We add our two commands, 'gui' and 'cli', to the main group.
main.add_command(gui)
main.add_command(classify, name='cli') # We explicitly name the CLI command 'cli'

if __name__ == '__main__':
    # This is the standard Python entry point.
    # When you run 'python -m smart_classifier.main', this block is executed.
    main()