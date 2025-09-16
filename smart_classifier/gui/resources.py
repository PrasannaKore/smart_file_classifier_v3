# smart_classifier/gui/resources.py

import logging
import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

# Get a logger for this specific module
logger = logging.getLogger(__name__)


# --- THE BULLETPROOF RESOURCE PATH RESOLVER ---
def get_resource_path(relative_path: str) -> Path:
    """
    Gets the absolute path to a resource, working for both development (source)
    and production (PyInstaller bundled executable). This is the definitive way.
    """
    try:
        # PyInstaller creates a temp folder and stores its path in sys._MEIPASS.
        base_path = Path(sys._MEIPASS)
        # This log is helpful when running the bundled .exe file.
        logger.info(f"Running in a bundled (PyInstaller) environment. Base path: {base_path}")
    except AttributeError:
        # If not bundled, the base path is the project root (3 levels up from this file).
        base_path = Path(__file__).resolve().parent.parent.parent
        # This log is helpful when running from source code.
        logger.info(f"Running from source. Base path: {base_path}")

    resource_path = base_path / relative_path
    # This print statement is a powerful debugging tool to confirm the final path.
    print(f"DEBUG: Resolving '{relative_path}' to '{resource_path}'")
    return resource_path


# --- Constants defined using the new resolver ---
ASSETS_PATH = get_resource_path('assets')
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

# A cache to avoid reloading icons from disk repeatedly, improving performance.
_icon_cache = {}


# --- FUNCTIONS ---

def validate_assets():
    """Checks for the presence of all required assets at startup."""
    logger.info("Validating GUI assets...")
    try:
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
            return ""
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading stylesheet: {e}", exc_info=True)
        return ""


def get_icon(name: str) -> QIcon:
    """
    Creates and caches a QIcon from an SVG file.
    Includes robust logging and a fallback mechanism.
    """
    if name in _icon_cache:
        return _icon_cache[name]

    try:
        icon_path = ICONS_PATH / f"{name}.svg"

        if not icon_path.exists():
            # Log the exact path we were looking for, which is critical for debugging.
            logger.warning(f"Icon file not found at expected path: '{icon_path}'. Using fallback.")

            # Use the fallback to prevent crashing.
            if name == FALLBACK_ICON_NAME:
                return QIcon()  # Return an empty icon if the fallback itself is missing.
            return get_icon(FALLBACK_ICON_NAME)

        # If the file exists, create the icon and add it to the cache.
        icon = QIcon(str(icon_path))
        _icon_cache[name] = icon
        return icon

    except Exception as e:
        logger.error(f"An unexpected error occurred while loading icon '{name}': {e}", exc_info=True)
        return QIcon()