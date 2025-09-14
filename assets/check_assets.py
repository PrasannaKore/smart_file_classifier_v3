# scripts/check_assets.py
"""
A utility script to check for the presence of required GUI assets.
This helps developers ensure the project has all necessary icons before running.
"""
from pathlib import Path
import sys

# Add the project root to the Python path to allow importing our modules
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

try:
    from smart_classifier.gui.resources import ICONS_PATH, REQUIRED_ICONS
except ImportError as e:
    print(
        f"Error: Could not import project modules. Ensure you run this script from the project root or have the project installed.")
    print(f"Details: {e}")
    sys.exit(1)


def check_assets():
    """Checks the assets/icons directory for required SVG files."""
    print("--- Asset Sanity Check ---")
    print(f"Checking for icons in: {ICONS_PATH}")

    missing_icons = []
    found_icons = 0

    for icon_name in REQUIRED_ICONS:
        icon_file = ICONS_PATH / f"{icon_name}.svg"
        if icon_file.exists():
            print(f"  [FOUND] {icon_name}.svg")
            found_icons += 1
        else:
            print(f"  [MISSING] {icon_name}.svg")
            missing_icons.append(f"{icon_name}.svg")

    print("\n--- Summary ---")
    if not missing_icons:
        print(f"✅ Success! All {len(REQUIRED_ICONS)} required icons were found.")
    else:
        print(f"❌ Error: Found {found_icons}/{len(REQUIRED_ICONS)} icons.")
        print("The following icons are missing:")
        for icon in missing_icons:
            print(f"  - {icon}")
        # Create a helper file for the user
        with open(ICONS_PATH / "readme.md", "w") as f:
            f.write("# Required Icons\n\n")
            f.write("This file is auto-generated. Please ensure the following SVG icons exist in this directory:\n\n")
            for icon in REQUIRED_ICONS:
                f.write(f"- `{icon}.svg`\n")
        print(f"\nℹ️ A `readme.md` file has been generated in `{ICONS_PATH}` with the list of required icons.")


if __name__ == "__main__":
    check_assets()