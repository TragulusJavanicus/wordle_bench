"""Memory tracking via tracemalloc (stdlib) with optional psutil fallback."""

import tracemalloc


def start_tracking() -> None:
    tracemalloc.start()


def stop_tracking() -> None:
    tracemalloc.stop()


def peak_memory_mb() -> float:
    """Return peak memory usage in MB since start_tracking() was called."""
    _, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)
