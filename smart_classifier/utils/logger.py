# smart_classifier/utils/logger.py

import logging
import logging.handlers
from pathlib import Path

# --- NEW: Encapsulated LoggerManager Class ---
# By placing all the setup logic inside a class, we follow a professional
# Object-Oriented Programming (OOP) pattern. This makes the code more organized,
# reusable, and prevents potential conflicts in a larger application.
class LoggerManager:
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
    """A manager class to configure the application's logging system."""

    def __init__(self, log_file_name: str = 'app.log', log_level=logging.DEBUG):
        """
        Initializes the manager.

        Args:
            log_file_name: The name of the log file to be created in the project root.
            log_level: The base logging level to capture (e.g., DEBUG, INFO).
        """
        self.log_file_path = Path(__file__).resolve().parents[2] / log_file_name
        self.log_level = log_level
        self.root_logger = logging.getLogger()

    def setup(self):
        """
        Configures and attaches handlers to the root logger.
        This is the main method that sets up the entire logging system.
        """
        # We only set up handlers if none have been configured yet.
        # This is a crucial safety check to prevent adding duplicate handlers
        # if this function is accidentally called more than once.
        if self.root_logger.hasHandlers():
            return

        self.root_logger.setLevel(self.log_level)

        # Create and add the console handler.
        console_handler = self._create_console_handler()
        self.root_logger.addHandler(console_handler)

        # Create and add the file handler.
        file_handler = self._create_file_handler()
        self.root_logger.addHandler(file_handler)

        logging.info("Logging configured successfully. All future events will be captured.")

    def _create_console_handler(self) -> logging.StreamHandler:
        """Creates a handler for logging messages to the console."""
        # This handler shows real-time feedback to the user running the app.
        # It's typically set to INFO level to avoid cluttering the console.
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        return handler

    def _create_file_handler(self) -> logging.handlers.RotatingFileHandler:
        """Creates a rotating file handler for persistent logging."""
        # This handler writes detailed logs to a file for debugging and auditing.
        # It's set to DEBUG level to capture everything.
        # The 'RotatingFileHandler' is a smart choice: it prevents the log file
        # from growing infinitely large by creating new files (backups) when
        # the current one reaches a size limit (e.g., 5MB).
        handler = logging.handlers.RotatingFileHandler(
            self.log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
        )
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s'
        )
        handler.setFormatter(formatter)
        return handler

# --- REPLACED: The New, Clean Public Entry Point ---
# This is the only function that other parts of our application will ever need to call.
# It hides all the complex setup logic inside our new class, which is a great design pattern.
def setup_logging():
    """Initializes and configures the application-wide logging system."""
    manager = LoggerManager()
    manager.setup()