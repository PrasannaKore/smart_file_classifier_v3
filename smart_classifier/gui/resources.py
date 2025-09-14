# smart_classifier/gui/resources.py

import logging
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

# Get a logger for this specific module
logger = logging.getLogger(__name__)

# --- CORE FIX: DEFINE ALL CONSTANTS AT THE TOP LEVEL ---
# All constants are defined here, once, at the module's top level.
# This makes them accessible to all functions within this file.

# This robustly calculates the project's root directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# These paths are now guaranteed to be defined before any function is called.
ASSETS_PATH = PROJECT_ROOT / 'assets'
STYLES_PATH = ASSETS_PATH / 'styles'
ICONS_PATH = ASSETS_PATH / 'icons'

# Master list of all required icons for the application.
REQUIRED_ICONS = [
    "app_icon", "folder-open", "preview", "start",
    "pause", "resume", "cancel", "undo", "down-arrow"
]
# A default icon to use if a specific one is missing.
FALLBACK_ICON_NAME = "app_icon"

# A standard, clean size for toolbar/button icons.
ICON_SIZE = QSize(20, 20)

# A cache to avoid reloading icons from disk repeatedly.
_icon_cache = {}


# --- FUNCTIONS ---

def validate_assets():
    """Checks for the presence of all required assets at startup."""
    logger.info("Validating GUI assets...")
    try:
        # This function now correctly sees the STYLES_PATH and ICONS_PATH constants.
        if not (STYLES_PATH / 'main_style.qss').exists():
            logger.warning("Stylesheet 'main_style.qss' not found in assets/styles.")

        missing_icons = [
            name for name in REQUIRED_ICONS if not (ICONS_PATH / f"{name}.svg").exists()
        ]
        if missing_icons:
            logger.warning(f"Missing required icons in assets/icons: {', '.join(missing_icons)}")
        else:
            logger.info("All required icons found.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during asset validation: {e}", exc_info=True)


def load_stylesheet() -> str:
    """Loads the main QSS stylesheet from the assets folder."""
    try:
        stylesheet_path = STYLES_PATH / 'main_style.qss'
        if stylesheet_path.exists():
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.error("Failed to load stylesheet: file does not exist.")
            return ""  # Return empty string on failure
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading stylesheet: {e}", exc_info=True)
        return ""


def get_icon(name: str) -> QIcon:
    """
    Creates and caches a QIcon from an SVG file.
    Includes robust logging to debug pathing issues.
    """
    if name in _icon_cache:
        return _icon_cache[name]

    try:
        # Calculate the absolute path to the icon.
        icon_path = ICONS_PATH / f"{name}.svg"

        # --- ROBUSTNESS FIX ---
        # Check if the file exists at the calculated path.
        if not icon_path.exists():
            # If it doesn't exist, log the exact path we were looking for.
            # This is the most important debugging information.
            logger.warning(f"Icon file not found at expected path: '{icon_path}'")

            # Use the fallback to prevent crashing.
            if name == FALLBACK_ICON_NAME:
                return QIcon()
            return get_icon(FALLBACK_ICON_NAME)

        # If the file exists, create the icon.
        icon = QIcon(str(icon_path))
        _icon_cache[name] = icon
        return icon

    except Exception as e:
        logger.error(f"An unexpected error occurred while loading icon '{name}': {e}", exc_info=True)
        return QIcon()