# smart_classifier/gui/resources.py

import logging
import sys
import json
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

# A dedicated logger for asset-related events. This is crucial for debugging
# issues with missing icons or themes.
logger = logging.getLogger(__name__)


# --- THE BULLETPROOF RESOURCE PATH RESOLVER ---
# This is the most critical function in this file. It guarantees that our
# application can find its assets, no matter how it is run (from source or as a
# bundled .exe file).
def get_resource_path(relative_path: str) -> Path:
    """
    Gets the absolute path to a resource, working for both development (source)
    and production (PyInstaller bundled executable).
    """
    try:
        # PyInstaller creates a temporary folder and stores its path in `sys._MEIPASS`.
        # This is the "inside the backpack" scenario.
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # If `sys._MEIPASS` doesn't exist, we are running from source code.
        # The base path is the project root (3 levels up from this file).
        # This is the "house address" scenario.
        base_path = Path(__file__).resolve().parent.parent.parent

    return base_path / relative_path


# --- Constants defined using our new, reliable resolver ---
ASSETS_PATH = get_resource_path('assets')
STYLES_PATH = ASSETS_PATH / 'styles'
ICONS_PATH = ASSETS_PATH / 'icons'
CONFIG_PATH = get_resource_path('config')
SETTINGS_FILE_PATH = CONFIG_PATH / 'settings.json'

# This master list defines all icons the application expects to exist.
# It is used by the validation function to provide clear error messages.
REQUIRED_ICONS = [
    "app_icon", "folder-open", "preview", "start", "pause", "resume",
    "cancel", "undo", "down-arrow", "settings", "import", "success",
    "skip", "error", "info"
]
# A default icon to use if a specific one is missing, preventing crashes.
FALLBACK_ICON_NAME = "app_icon"
ICON_SIZE = QSize(20, 20)

# A simple cache to avoid repeatedly loading the same icon from the disk.
# This provides a small but professional performance optimization.
_icon_cache = {}


# --- Asset Management Functions ---

def validate_assets():
    """
    Checks for the presence of all required assets at application startup.
    This provides early warnings to developers if the project is not set up correctly.
    """
    logger.info("Validating GUI assets...")

    # We now intelligently check for the 'themes' directory, not a single file.
    themes_dir = STYLES_PATH / 'themes'
    if not themes_dir.is_dir():
        logger.warning(f"Themes directory not found at: {themes_dir}")

    # Check if all required icon files exist.
    missing_icons = [name for name in REQUIRED_ICONS if not (ICONS_PATH / f"{name}.svg").exists()]
    if missing_icons:
        logger.warning(f"Missing required icons in '{ICONS_PATH}': {', '.join(missing_icons)}")
    else:
        logger.info("All required icons found.")


def get_current_theme() -> str:
    """Reads the settings.json file to find the user's current theme choice."""
    try:
        if SETTINGS_FILE_PATH.exists():
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get("theme", "dark_theme.qss")  # Default to dark theme if key is missing
    except (IOError, json.JSONDecodeError):
        logger.warning("Could not read settings.json, defaulting to dark theme.")
    return "dark_theme.qss"


def set_current_theme(theme_filename: str) -> bool:
    """Saves the user's new theme choice to settings.json."""
    try:
        settings = {"theme": theme_filename}
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        logger.info(f"User theme changed and saved to: {theme_filename}")
        return True
    except IOError:
        logger.error(f"Could not write to settings file at: {SETTINGS_FILE_PATH}")
        return False

def load_stylesheet() -> str:
    """
    Loads the stylesheet for the theme currently specified in settings.json.
    This is the main function the application will call to style itself.
    """
    """Loads the stylesheet and sets the search path for relative URLs like icons."""
    # --- NEW: Set the search path ---
    # This tells Qt that whenever it sees a relative path like `url("../icons/...")`
    # in the stylesheet, it should start searching from our main assets directory.
    # This is a robust, professional solution to the missing dropdown arrow.
    from PySide6.QtCore import QDir
    QDir.addSearchPath("assets", str(ASSETS_PATH))
    # --- END NEW ---

    current_theme_file = get_current_theme()
    theme_path = STYLES_PATH / 'themes' / current_theme_file
    if theme_path.exists():
        logger.info(f"Loading theme: {current_theme_file}")
        return theme_path.read_text(encoding='utf-8')
    logger.error(f"Failed to load theme file: {theme_path}")
    return ""


def get_icon(name: str) -> QIcon:
    """
    Creates and caches a QIcon from an SVG file.
    Includes a robust fallback mechanism to prevent crashes if an icon is missing.
    """
    if name in _icon_cache:
        return _icon_cache[name]

    icon_path = ICONS_PATH / f"{name}.svg"
    if not icon_path.exists():
        logger.warning(f"Icon '{name}.svg' not found. Using fallback.")
        # If the fallback icon itself is missing, return an empty QIcon to avoid an infinite loop.
        if name == FALLBACK_ICON_NAME:
            return QIcon()
        return get_icon(FALLBACK_ICON_NAME)

    icon = QIcon(str(icon_path))
    _icon_cache[name] = icon
    return icon