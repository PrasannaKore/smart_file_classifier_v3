# smart_classifier/gui/resources.py

import logging
import sys
import json
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

logger = logging.getLogger(__name__)


# --- THE BULLETPROOF RESOURCE PATH RESOLVER (Unchanged and Correct) ---
def get_resource_path(relative_path: str) -> Path:
    """Gets the absolute path to a resource, working for both dev and prod."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).resolve().parent.parent.parent
    return base_path / relative_path


# --- Constants ---
ASSETS_PATH = get_resource_path('assets')
STYLES_PATH = ASSETS_PATH / 'styles'
ICONS_PATH = ASSETS_PATH / 'icons'
CONFIG_PATH = get_resource_path('config')
SETTINGS_FILE_PATH = CONFIG_PATH / 'settings.json'

REQUIRED_ICONS = [
    "app_icon", "folder-open", "preview", "start", "pause", "resume",
    "cancel", "undo", "down-arrow", "settings", "import", "success",
    "skip", "error", "info"
]
FALLBACK_ICON_NAME = "app_icon"
ICON_SIZE = QSize(20, 20)
_icon_cache = {}


# --- Asset Management Functions ---

def validate_assets():
    """
    REPLACED: This version now intelligently validates the existence of the
    'themes' directory instead of a single, hard-coded stylesheet file.
    """
    logger.info("Validating GUI assets...")

    themes_dir = STYLES_PATH / 'themes'
    if not themes_dir.is_dir():
        logger.warning(f"Themes directory not found at: {themes_dir}")

    missing_icons = [name for name in REQUIRED_ICONS if not (ICONS_PATH / f"{name}.svg").exists()]
    if missing_icons:
        logger.warning(f"Missing required icons in '{ICONS_PATH}': {', '.join(missing_icons)}")
    else:
        logger.info("All required icons found.")


def get_current_theme() -> str:
    """Reads the settings.json file to find the user's current theme choice."""
    # (This function is correct and requires no changes)
    try:
        if SETTINGS_FILE_PATH.exists():
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get("theme", "dark_theme.qss")
    except (IOError, json.JSONDecodeError):
        logger.warning("Could not read settings.json, defaulting to dark theme.")
    return "dark_theme.qss"


def set_current_theme(theme_filename: str):
    """Saves the user's new theme choice to settings.json."""
    # (This function is correct and requires no changes)
    try:
        settings = {"theme": theme_filename}
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return True
    except IOError:
        logger.error(f"Could not write to settings file at: {SETTINGS_FILE_PATH}")
        return False


def load_stylesheet() -> str:
    """Loads the stylesheet for the theme currently specified in settings.json."""
    # (This function is correct and requires no changes)
    current_theme_file = get_current_theme()
    theme_path = STYLES_PATH / 'themes' / current_theme_file
    if theme_path.exists():
        logger.info(f"Loading theme: {current_theme_file}")
        with open(theme_path, 'r', encoding='utf-8') as f:
            return f.read()
    logger.error(f"Failed to load theme file: {theme_path}")
    return ""


def get_icon(name: str) -> QIcon:
    """Creates and caches a QIcon from an SVG file."""
    # (This function is correct and requires no changes)
    if name in _icon_cache:
        return _icon_cache[name]
    icon_path = ICONS_PATH / f"{name}.svg"
    if not icon_path.exists():
        logger.warning(f"Icon '{name}.svg' not found. Using fallback.")
        if name == FALLBACK_ICON_NAME: return QIcon()
        return get_icon(FALLBACK_ICON_NAME)
    icon = QIcon(str(icon_path))
    _icon_cache[name] = icon
    return icon