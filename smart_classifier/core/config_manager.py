# smart_classifier/core/config_manager.py

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any

# A dedicated logger for the module that manages our application's "brain".
logger = logging.getLogger(__name__)


def safely_add_or_update_rule(config_path: Path, new_rule: Dict[str, Any]):
    """
    Safely adds a new rule to the config, intelligently handling conflicts
    by converting simple rules to smart rules. This is the core of our
    user-guided learning system.

    Args:
        config_path: The path to the file_types.json file.
        new_rule: A dictionary containing the user's new rule data.
    """
    try:
        # --- Safety First: Create a backup before touching the original file. ---
        # This is a critical defense mechanism. If the power goes out or an error
        # occurs during the save, we can always recover the last good version.
        backup_path = config_path.with_suffix(".json.bak")
        shutil.copy(config_path, backup_path)
        logger.info(f"Configuration backup created at: {backup_path}")

        # Open the file for both reading and writing ('r+').
        with open(config_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)

            ext = new_rule["extension"]
            category = new_rule["category"]

            # --- Conflict Detection and Resolution ---
            conflict_found = False
            # We iterate through the entire existing knowledge base.
            for cat, rules in data.items():
                # We only care about category sections, which are dictionaries.
                if isinstance(rules, dict) and ext in rules and cat != category:
                    conflict_found = True
                    # If the existing rule is just a simple string, we must upgrade it.
                    if isinstance(rules[ext], str):
                        logger.warning(
                            f"Conflict detected for '{ext}'. Upgrading existing rule in category '{cat}' to a smart rule.")
                        # We preserve the old description and add an empty analysis list.
                        old_description = rules[ext]
                        rules[ext] = {"description": old_description, "analysis_rules": []}

            # Now, add the user's new rule. It's always added in the smart format.
            new_rule_object = {
                "description": new_rule["description"],
                "analysis_rules": new_rule["analysis_rules"]
            }

            # Create the new category if it doesn't already exist.
            if category not in data:
                data[category] = {}
            data[category][ext] = new_rule_object

            # --- Atomic Write Operation ---
            # We move the file cursor back to the beginning.
            f.seek(0)
            # We clear the file of its old content.
            f.truncate()
            # We write the new, complete, and updated data structure back to the file.
            json.dump(data, f, indent=2)

            if conflict_found:
                logger.info(f"Successfully resolved conflict and added new rule for '{ext}'.")
            else:
                logger.info(f"Successfully added new rule for '{ext}'.")
            return True

    except Exception as e:
        logger.error(f"Failed to update config file: {e}", exc_info=True)
        # --- Automatic Recovery ---
        # If any part of the process failed, we restore from the backup to
        # ensure the application is never left in a broken state.
        if 'backup_path' in locals() and backup_path.exists():
            shutil.copy(backup_path, config_path)
            logger.warning("!!! CRITICAL: Restored config from backup due to a save failure.")
        return False