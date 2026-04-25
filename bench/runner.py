"""Benchmark runner: loads a solver module, runs it against N sampled words,
and returns per-game results together with timing and memory statistics."""

import importlib.util
import random
import sys
import threading
import time
import tracemalloc
from pathlib import Path
from typing import Callable

from core.feedback import compute_feedback
from core.scorer import compute_score
from bench.metrics import compute_metrics


# Hard cap: solver is killed if it exceeds this per-word (seconds)
TIMEOUT_PER_WORD = 30


def load_solver(path: str):
    """Dynamically import a solver module from an arbitrary file path."""
    solver_path = Path(path).resolve()
    if not solver_path.exists():
        raise FileNotFoundError(f"Solver file not found: {solver_path}")

    spec = importlib.util.spec_from_file_location("_user_solver", solver_path)
    module = importlib.util.module_from_spec(spec)
    # Ensure solver can import from project root
    project_root = str(solver_path.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    spec.loader.exec_module(module)
    return module


def _run_with_timeout(fn: Callable, args: tuple, timeout: float):
    """Execute fn(*args) in a daemon thread; raise TimeoutError if it stalls."""
    result_box: list = [None]
    error_box: list = [None]

    def _target():
        try:
            result_box[0] = fn(*args)
        except Exception as exc:
            error_box[0] = exc

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise TimeoutError(f"Solver exceeded {timeout:.0f}s timeout")
    if error_box[0] is not None:
        raise error_box[0]
    return result_box[0]


def _make_feedback_fn(target: str, call_counter: list[int]):
    """Return a feedback function that counts calls and returns G/Y/W strings."""
    target_upper = target.upper()

    def feedback_fn(guess: str) -> str:
        call_counter[0] += 1
        return compute_feedback(guess, target_upper)

    return feedback_fn


def run_benchmark(
    solver_path: str,
    word_list: list[str],
    sample_size: int,
    seed: int,
    user: str,
    progress_cb: Callable[[int, int], None] | None = None,
) -> tuple[list[dict], float, float]:
    """Run the solver against `sample_size` randomly-chosen words.

    Returns:
        results    — list of per-game dicts with keys: target, attempts, score
        elapsed    — total wall-clock seconds
        peak_mb    — peak RSS memory increase in MB (tracemalloc)
    """
    solver = load_solver(solver_path)

    if not hasattr(solver, "solve"):
        raise AttributeError(f"Solver '{solver_path}' must define a solve(word_list, feedback_fn) function.")

    norm_words = [w.strip().upper() for w in word_list if len(w.strip()) == 5]
    rng = random.Random(seed)
    sample = rng.sample(norm_words, min(sample_size, len(norm_words)))

    results: list[dict] = []
    tracemalloc.start()
    start_time = time.perf_counter()

    for idx, target in enumerate(sample):
        counter: list[int] = [0]
        feedback_fn = _make_feedback_fn(target, counter)

        def _solve():
            return solver.solve(norm_words, feedback_fn)

        try:
            returned_attempts = _run_with_timeout(_solve, (), TIMEOUT_PER_WORD)
        except TimeoutError as exc:
            results.append({
                "target": target,
                "attempts": TIMEOUT_PER_WORD,
                "score": compute_score(len(norm_words), TIMEOUT_PER_WORD),
                "error": str(exc),
            })
            if progress_cb:
                progress_cb(idx + 1, len(sample))
            continue
        except Exception as exc:
            results.append({
                "target": target,
                "attempts": 9999,
                "score": 0,
                "error": str(exc),
            })
            if progress_cb:
                progress_cb(idx + 1, len(sample))
            continue

        # Trust call_counter as the authoritative attempt count
        actual_attempts = counter[0]
        results.append({
            "target": target,
            "attempts": actual_attempts,
            "score": compute_score(len(norm_words), actual_attempts),
        })

        if progress_cb:
            progress_cb(idx + 1, len(sample))

    elapsed = time.perf_counter() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return results, elapsed, peak / (1024 * 1024)
