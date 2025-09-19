# smart_classifier/utils/thread_manager.py

import logging
import os

logger = logging.getLogger(__name__)

# --- NEW: Self-Documenting Constants ---
# By defining these as constants, we replace "magic numbers" with clear,
# understandable explanations. This makes the code easier to maintain and tune.

# For I/O-bound tasks, it's common to use more threads than CPU cores, as threads
# will spend time waiting for the disk. A factor of 2 is a sensible default.
IO_BOUND_MULTIPLIER = 2

# To prevent creating an excessive number of threads on high-end CPUs (e.g., servers
# with 64 or 128 cores), we set a reasonable upper limit. 32 is a robust cap that
# provides excellent performance without risking resource exhaustion.
MAX_WORKER_THREADS = 32


# --- REPLACED: The New, More Readable Function ---
def get_optimal_thread_count() -> int:
    """
    Determines the optimal number of worker threads for I/O-bound tasks.

    This function is based on the best practice of over-subscribing CPU cores
    for I/O-heavy workloads to ensure the disk is always saturated with work,
    while capping the total number of threads to maintain system stability.

    Returns:
        The recommended number of threads to use for our ThreadPoolExecutor.
    """
    # os.cpu_count() safely returns the number of logical CPUs, or 1 if it cannot be determined.
    cpu_count = os.cpu_count() or 1

    # Calculate the ideal number of threads based on our multiplier.
    ideal_threads = cpu_count * IO_BOUND_MULTIPLIER

    # Choose the smaller value between our ideal number and our safety cap.
    # On a 4-core machine: min(4 * 2, 32) -> min(8, 32) -> 8 threads.
    # On a 32-core machine: min(32 * 2, 32) -> min(64, 32) -> 32 threads (our cap in action).
    optimal_threads = min(ideal_threads, MAX_WORKER_THREADS)

    logger.info(f"System has {cpu_count} CPU cores. Optimal thread count set to {optimal_threads}.")
    return optimal_threads
