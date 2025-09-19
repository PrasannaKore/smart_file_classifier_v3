# smart_classifier/core/bulk_importer.py

import csv
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any

# We import our new, safe config manager. This is the only way we will
# ever write to the config file, ensuring stability.
from .config_manager import safely_add_or_update_rule

logger = logging.getLogger(__name__)


class BulkImporter:
    """
    An intelligent engine to process bulk rule imports from a user-provided CSV file.
    It handles triage, conflict resolution, and generates a detailed report of its actions.
    """

    def __init__(self, config_path: Path):
        self.config_path = config_path
        # The report is a dictionary that will be populated during the process.
        self.report = {
            "added": [],
            "updated": [],
            "duplicates": [],
            "errors": []
        }

    def _load_current_config(self) -> Dict:
        """A helper to safely load the existing knowledge base."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def process_csv(self, csv_path: Path):
        """
        The main public method to run the entire import and update process.
        It orchestrates the reading, processing, and saving of the new rules.
        """
        config_data = self._load_current_config()

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Using csv.DictReader allows us to access columns by name (e.g., row['extension']).
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    row_num = i + 2  # Add 2 to account for the header row and 0-based index.

                    # Basic validation to ensure the CSV is well-formed.
                    if not all(key in row for key in ['extension', 'category', 'description']):
                        self.report["errors"].append(
                            f"Row {row_num}: Missing required columns (extension, category, description).")
                        continue

                    # Process each row, passing the entire config data structure for analysis.
                    self._process_rule(config_data, row, row_num)

            # After processing all rows, no code for saving is needed here.
            # Our new config_manager handles saving for each rule, which is safer.

        except Exception as e:
            logger.error(f"Failed during bulk import process: {e}", exc_info=True)
            self.report["errors"].append(f"A critical error occurred during import: {e}")

    def _process_rule(self, config_data: Dict, rule_data: Dict, row_num: int):
        """
        The intelligent core of the importer. It analyzes a single rule and
        decides whether to add it, update it, or report it as a duplicate/error.
        """
        # Clean up the user's input data.
        ext = rule_data['extension'].lower().strip()
        if not ext.startswith('.'): ext = '.' + ext
        category = rule_data['category'].strip()
        description = rule_data['description'].strip()
        keyword = rule_data.get('differentiation_keyword', '').strip()

        # --- Conflict Analysis ---
        # Find all existing locations of this extension.
        existing_locations = []
        for cat, rules in config_data.items():
            if isinstance(rules, dict) and ext in rules:
                existing_locations.append(cat)

        # --- Triage Logic ---

        # Case 1: New Rule, No Conflict. The simplest and best case.
        if not existing_locations:
            new_rule = {"extension": ext, "category": category, "description": description, "analysis_rules": []}
            if safely_add_or_update_rule(self.config_path, new_rule):
                self.report["added"].append(f"'{ext}' to category '{category}'.")
            else:
                self.report["errors"].append(f"Row {row_num}: Failed to save new rule for '{ext}'.")
            return

        # Case 2: Harmless Duplicate. The rule already exists in the target category.
        if category in existing_locations:
            self.report["duplicates"].append(f"'{ext}' already exists in category '{category}'.")
            return

        # Case 3: A true Conflict is Detected! We must resolve it.
        if category not in existing_locations:
            logger.warning(
                f"Conflict detected for '{ext}'. New category: '{category}', Existing in: {existing_locations}")

            # A differentiation keyword is mandatory to resolve a conflict.
            if not keyword:
                self.report["errors"].append(
                    f"Row {row_num}: Conflict for '{ext}' but no differentiation_keyword was provided. Skipped.")
                return

            # We create a new "smart rule" with both filename and content analysis for robustness.
            # This is where we solve the "zero-content file" problem.
            new_rule = {
                "extension": ext,
                "category": category,
                "description": description,
                "analysis_rules": [
                    {"type": "filename_contains", "contains_str": keyword},
                    {"type": "content_contains", "contains_str": keyword}
                ]
            }
            if safely_add_or_update_rule(self.config_path, new_rule):
                self.report["updated"].append(f"Resolved conflict for '{ext}' by creating smart rules.")
            else:
                self.report["errors"].append(f"Row {row_num}: Failed to save conflicting rule for '{ext}'.")