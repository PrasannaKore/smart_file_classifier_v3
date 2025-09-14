# smart_classifier/utils/thread_manager.py

import logging
import os

logger = logging.getLogger(__name__)


def get_optimal_thread_count() -> int:
    """
    Determines the optimal number of worker threads for I/O-bound tasks.

    It defaults to the number of logical CPU cores available, which is a
    sensible default for parallelizing I/O operations without overwhelming
    the system. Adds a cap to prevent excessive threads on high-core-count systems.

    Returns:
        The recommended number of threads to use.
    """
    # os.cpu_count() returns the number of logical CPUs.
    cpu_count = os.cpu_count() or 1  # Default to 1 if cpu_count() returns None

    # For I/O tasks, a good starting point is the number of cores.
    # We can cap it to prevent creating too many threads on server-grade CPUs.
    optimal_threads = min(cpu_count * 2, 32)

    logger.info(f"System has {cpu_count} CPU cores. Optimal thread count set to {optimal_threads}.")
    return optimal_threads