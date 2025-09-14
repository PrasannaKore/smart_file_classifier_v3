# smart_classifier/utils/logger.py

import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    """
    Configures a robust, application-wide logging system.

    This setup creates two log handlers:
    1. Console Handler: For real-time, color-coded (in supported terminals)
       feedback during execution. It logs messages of INFO level and above.
    2. Rotating File Handler: For persistent, detailed logging. It creates a
       log file that rotates after reaching a certain size, preventing it
       from growing indefinitely. It logs messages of DEBUG level and above,
       capturing much more detail for diagnostics.
    """
    # Define the log file path in the project root for easy access.
    log_file_path = Path(__file__).resolve().parents[2] / 'app.log'

    # Get the root logger. Configuring this means all loggers created with
    # logging.getLogger(__name__) will inherit this configuration.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages.

    # --- Console Handler ---
    # Logs INFO level messages and above to the console.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # --- Rotating File Handler ---
    # Logs DEBUG level messages and above to 'app.log'.
    # Rotates the log file when it reaches 5MB, keeping up to 5 old log files.
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Add the handlers to the root logger.
    # We check if handlers already exist to prevent duplication if this
    # function is ever called more than once.
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    logging.info("Logging configured successfully. All future events will be captured.")