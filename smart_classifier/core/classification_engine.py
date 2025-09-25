# smart_classifier/core/classification_engine.py

import json
import logging
import os
import queue
from pathlib import Path
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from PySide6.QtWidgets import QFileDialog, QMessageBox

from .file_operations import DuplicateStrategy, safe_move
from .undo_manager import UndoManager
from smart_classifier.utils.thread_manager import get_optimal_thread_count

logger = logging.getLogger(__name__)

SUPPORTED_CONFIG_VERSION = "2.1"
DEFAULT_UNKNOWN_CATEGORY = "Others"


class ClassificationEngine:
    """
    The main engine for scanning, classifying, and organizing files.
    This is the final, superior version incorporating all advanced features.
    """

    def __init__(self, config_path: Path):
        """
        Initializes the engine and declares ALL of its instance attributes
        in one clean, professional, and sacred location.
        """
        self.config_path = config_path

        # --- Knowledge Base Attributes ---
        self.classification_rules: Dict[str, Dict] = {}
        self.extension_map: Dict[str, List[Dict]] = {}

        # --- State Management Attributes ---
        self._is_cancelled: bool = False
        self._pause_event: threading.Event = threading.Event()
        self._pause_event.set()  # Default to "not paused"

        # --- THE DEFINITIVE FIX: Producer-Consumer State ---
        # By declaring this attribute here, we fulfill the sacred contract
        # of the __init__ method. The warning will be banished forever.
        self._producer_done: bool = False

        # --- User Learning Attribute ---
        self.unresolved_files: List[Path] = []

        # Finally, load the knowledge base.
        self._load_classification_rules()

    def _load_classification_rules(self):
        """
        REPLACED: This is the definitive, superior version. It correctly parses
        the advanced v2.1+ config file, understanding both simple string-based rules
        and the new, intelligent "smart object" rules with analysis_rules.
        """
        logger.info(f"Loading advanced classification rules from: {self.config_path}")
        # Ensure we start with a clean slate for every load.
        self.classification_rules = {}
        self.extension_map = {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            metadata = data.get("_metadata", {})
            version_str = metadata.get("version", "1.0")

            # Use the robust, forward-compatible version check.
            if float(version_str) < float(SUPPORTED_CONFIG_VERSION):
                raise ValueError(
                    f"Unsupported config version: '{version_str}'. This application requires version {SUPPORTED_CONFIG_VERSION} or newer.")

            # --- The Intelligent Parsing Logic ---
            # This loop is now smart enough to handle our advanced knowledge base.
            for category, extensions in data.items():
                if category == "_metadata": continue
                if isinstance(extensions, dict):
                    for ext, details in extensions.items():
                        ext_lower = ext.lower()

                        # This is the crucial compatibility check. If a rule is just a simple
                        # string, we automatically upgrade it to the smart object format internally.
                        if not isinstance(details, dict):
                            details = {"description": details}

                        # We build the complete rule object.
                        rule_obj = {
                            "category": category,
                            "description": details.get("description", "No description"),
                            "analysis_rules": details.get("analysis_rules", [])
                        }

                        # We correctly populate the brain's two memory maps.
                        if not ext.startswith('.'):  # For full filenames like 'Dockerfile'
                            self.classification_rules[ext_lower] = rule_obj
                        else:  # For all extensions like '.pdf' or '.bak'
                            if ext_lower not in self.extension_map:
                                self.extension_map[ext_lower] = []
                            self.extension_map[ext_lower].append(rule_obj)

            logger.info(
                f"Successfully loaded rules for {len(self.extension_map)} extensions from knowledge base version {version_str}.")
        except Exception as e:
            logger.critical(f"Error parsing configuration file: {e}", exc_info=True)
            raise

    def scan_directory(self, source_dir: Path) -> List[Path]:
        """
        REPLACED: This version now intelligently ignores common system-generated
        hidden files like Thumbs.db and .DS_Store.
        """
        logger.info(f"Scanning directory: {source_dir}")
        if not source_dir.is_dir():
            logger.error(f"Source path is not a valid directory: {source_dir}")
            return []

        ignore_list = ['thumbs.db', '.ds_store']
        found_files = []
        try:
            for root, dirs, filenames in os.walk(source_dir):
                # Prune project directories from being scanned further
                project_type = self._is_project_directory(Path(root))
                if project_type:
                    logger.info(f"'{Path(root).name}' is a project. Treating as a single item and not scanning inside.")
                    # We add the project folder itself as a "file" to be moved
                    found_files.append(Path(root))
                    dirs[:] = []  # This is a powerful trick to stop os.walk from going deeper
                    continue

                for filename in filenames:
                    if filename.lower() not in ignore_list:
                        found_files.append(Path(root) / filename)
                    else:
                        logger.debug(f"Ignoring system file: {filename}")
        except Exception as e:
            logger.error(f"An error occurred during directory scan: {e}", exc_info=True)
            return []

        logger.info(f"Scan complete. Found {len(found_files)} items (files and projects).")
        return found_files

    def _is_project_directory(self, dir_path: Path) -> str | None:
        """
        ADDED: This new method intelligently detects if a directory is a software project.
        Returns the detected project type or None.
        """
        project_markers = {
            ".git": "Git Project",
            ".idea": "JetBrains IDE Project",
            ".vscode": "VS Code Project",
            "package.json": "Node.js Project",
            "__pycache__": "Python Project",
            "requirements.txt": "Python Project",
            "setup.py": "Python Project"
        }
        try:
            # We check only the immediate children for markers, for performance.
            for item in os.listdir(dir_path):
                if item in project_markers:
                    project_type = project_markers[item]
                    logger.debug(f"Detected '{dir_path.name}' as a '{project_type}'.")
                    return project_type
        except PermissionError:
            logger.warning(f"Permission denied while checking if '{dir_path.name}' is a project.")
        return None

    def _get_category_by_content(self, file_path: Path, rules: List[Dict]) -> str | None:
        """
        ADDED: This is the crucial missing helper method. It performs advanced,
        content-aware classification for ambiguous file types by dynamically
        applying rules from the JSON knowledge base.
        """
        try:
            # For efficiency, we only read a small header of the file, not the whole thing.
            with open(file_path, 'rb') as f:
                header = f.read(256) # Read the first 256 bytes for analysis.
        except Exception as e:
            logger.warning(f"Could not read file for content analysis '{file_path.name}': {e}")
            return None # We cannot analyze if we cannot read the file.

        # We now iterate through the "smart rules" provided for this extension.
        for rule_obj in rules:
            # We only care about rules that have analysis instructions.
            if not rule_obj.get("analysis_rules"):
                continue

            for analysis_rule in rule_obj["analysis_rules"]:
                rule_type = analysis_rule.get("type")

                # Here we can add many types of analysis. For now, we support "content_contains".
                if rule_type == "content_contains":
                    keyword = analysis_rule.get("contains_str")
                    if keyword and keyword.encode() in header:
                        # Success! We found a match.
                        logger.debug(
                            f"Content analysis for '{file_path.name}': Matched rule for category '{rule_obj['category']}'.")
                        return rule_obj["category"]

        # If after checking all smart rules, no confident match was found, we return None.
        return None

    def generate_plan(self, items: List[Path], dest_dir: Path) -> List[Tuple[Path, Path]]:
        """
        REPLACED: This is the definitive, superior version of the planning method.
        It uses a clean, unified, multi-layered inference pipeline that correctly
        evaluates all evidence before making a final decision. It will now
        correctly identify and flag unresolved files for the learning workflow.
        """
        logger.info("Generating intelligent classification plan...")
        plan = []
        self.unresolved_files = []  # Always start with a clean list of questions.

        for item_path in items:
            category = None  # Initialize the category for this item as unknown.

            # --- 🧠 THE FINAL, SUPERIOR AI PIPELINE 🧠 ---

            # 🏛️ Layer 1: Handle atomic Project Directories first. This is the fastest check.
            if item_path.is_dir():
                category = "Software_Projects"

            # 📄 Layer 2: If it's a file, check for an exact, unambiguous filename match (e.g., 'Dockerfile').
            if not category and item_path.name.lower() in self.classification_rules:
                category = self.classification_rules[item_path.name.lower()]["category"]

            # 🤔 Layer 3: If still no match, analyze the extension. This is the most complex layer.
            if not category:
                ext_lower = item_path.suffix.lower()
                possible_rules = self.extension_map.get(ext_lower, [])

                if len(possible_rules) == 1:
                    # Case A: Simple, unambiguous extension. The fastest path.
                    category = possible_rules[0]["category"]
                elif len(possible_rules) > 1:
                    # Case B: Ambiguous extension. We must perform deep content analysis.
                    logger.debug(f"Ambiguity detected for {item_path.name}. Performing content analysis...")
                    category = self._get_category_by_content(item_path, possible_rules)
                    # If content analysis fails (e.g., zero-byte file), category remains None.

                # ❓ Case C: This is the crucial logic you found was missing.
                # If there are NO possible rules, it is truly unknown.
                if not possible_rules:
                    logger.info(f"Found new, unknown file type: {item_path.name}")
                    self.unresolved_files.append(item_path)
                    category = "_UNRESOLVED"

            # 🤷‍♂️ Layer 4: The Wise Arbiter. This is the final fallback decision.
            # If after all the smart checks, we still have no category, it means
            # content analysis for an ambiguous file failed. This also must be learned.
            if not category:
                logger.info(f"Could not resolve ambiguity for: {item_path.name}")
                self.unresolved_files.append(item_path)
                category = "_UNRESOLVED"

            # --- END PIPELINE ---

            # This final block for creating the path is unchanged and correct.
            extension = item_path.suffix[1:].lower() if item_path.is_file() else "no_extension"
            final_destination_dir = dest_dir / category
            if item_path.is_file():  # Only add extension sub-folder for files
                final_destination_dir = final_destination_dir / extension

            plan.append((item_path, final_destination_dir))

        logger.info(
            f"Generated plan for {len(plan)} operations. Found {len(self.unresolved_files)} unresolved files for learning.")
        return plan

    def generate_advanced_plan(
        self,
        all_items: list[Path],
        selected_items: list[Path],
        dest_dir: Path,
        mode: str
    ) -> list[tuple[Path, Path]]:
        """
        Advanced planning for:
        - 'move_as_is': Move selected items as-is, classify the rest.
        - 'classify_selected_only': Only classify selected items.
        If selected_items is empty, fallback to normal classification.
        This version ensures feature parity with generate_plan, including handling of unknown/ambiguous files and correct folder creation.
        """
        import logging
        plan = []
        skipped_dir = dest_dir / "User_Skipped"
        selected_set = set(selected_items)
        all_set = set(all_items)
        try:
            if mode == "move_as_is":
                # Move selected as-is
                for item in selected_items:
                    plan.append((item, skipped_dir))
                # Classify the rest
                to_classify = list(all_set - selected_set)
                if to_classify:
                    plan.extend(self.generate_plan(to_classify, dest_dir))
            elif mode == "classify_selected_only":
                if selected_items:
                    plan.extend(self.generate_plan(selected_items, dest_dir))
                else:
                    plan.extend(self.generate_plan(all_items, dest_dir))
            else:
                plan.extend(self.generate_plan(all_items, dest_dir))
        except Exception as e:
            logging.error(f"Error in generate_advanced_plan: {e}", exc_info=True)
        return plan

    def pause(self):
        self._pause_event.clear()
        logger.info("Pause signal sent.")

    def resume(self):
        self._pause_event.set()
        logger.info("Resume signal sent.")

    def cancel(self):
        self._is_cancelled = True
        self._pause_event.set()
        logger.info("Cancel signal sent.")

    def reset_state(self):
        self._is_cancelled = False
        self._pause_event.set()

    def execute_plan(
            self,
            plan: List[Tuple[Path, Path]],
            duplicate_strategy: DuplicateStrategy,
            progress_callback: Callable[[int, str, str], None] | None =
            None
    ):
        """
        Executes the plan using a high-performance Producer-Consumer pattern with
        a new, robust, graceful shutdown protocol for cancellation.
        """
        total_files = len(plan)
        if total_files == 0: return

        self.reset_state()
        logger.info(f"Executing hybrid plan for {total_files} files...")
        UndoManager.clear_log()

        task_queue = queue.Queue(maxsize=get_optimal_thread_count() * 2)
        files_processed = 0

        def consumer():
            """The worker function that runs in the thread pool."""
            # The consumer now also checks the cancel flag for a faster exit.
            while not self._is_cancelled:
                try:
                    # We add a timeout to the pause check so it can periodically
                    # re-check the main cancel flag.
                    self._pause_event.wait(timeout=0.1)
                    if self._is_cancelled: break

                    task = task_queue.get(timeout=0.1)
                    if task is None:  # This is our "poison pill" signal to exit.
                        break

                    source_path, dest_dir = task
                    status, final_dest_path = safe_move(source_path, dest_dir, duplicate_strategy)
                    if status == "MOVED":
                        UndoManager.log_move(source_path, final_dest_path)

                    if progress_callback:
                        progress_callback(-1, source_path.name, status)

                    task_queue.task_done()
                except queue.Empty:
                    if self._producer_done:
                        break
                except Exception as e:
                    logger.error(f"Error in consumer thread: {e}", exc_info=True)
                    task_queue.task_done()

        # --- The Producer ---
        self._producer_done = False
        with ThreadPoolExecutor(max_workers=get_optimal_thread_count()) as executor:
            consumers = [executor.submit(consumer) for _ in range(get_optimal_thread_count())]

            try:
                for source_path, dest_dir in plan:
                    self._pause_event.wait()
                    if self._is_cancelled:
                        logger.warning("Cancellation detected in producer.")
                        break

                    task_queue.put((source_path, dest_dir))
                    files_processed += 1
                    if progress_callback:
                        percentage = int((files_processed / total_files) * 100)
                        progress_callback(percentage, "...", "...")
            finally:
                # --- THE DEFINITIVE GRACEFUL SHUTDOWN FIX ---
                self._producer_done = True

                # If the operation was cancelled, the .join() will deadlock.
                # We must manually clear the queue to unblock it.
                if self._is_cancelled:
                    logger.info("Draining task queue for graceful shutdown...")
                    # Empty the queue of any remaining tasks.
                    while not task_queue.empty():
                        try:
                            task_queue.get_nowait()
                            task_queue.task_done()
                        except queue.Empty:
                            break

                # Wait for any "in-flight" tasks to finish.
                task_queue.join()

                # Now, wake up all consumer threads with a "poison pill" so they can exit.
                for _ in consumers:
                    task_queue.put(None)

                # Wait for all consumer threads to fully terminate.
                for future in consumers:
                    future.result()

        logger.info("Execution of plan complete.")
