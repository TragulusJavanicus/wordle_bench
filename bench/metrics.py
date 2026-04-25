"""Statistical metrics computed from a list of per-game benchmark results."""

import statistics


def compute_metrics(results: list[dict]) -> dict:
    """Return aggregate statistics over a list of {attempts, score} dicts."""
    if not results:
        return {
            "avg_attempts": 0,
            "median_attempts": 0,
            "variance": 0,
            "avg_score": 0,
        }

    attempts_list = [r["attempts"] for r in results]
    scores_list = [r["score"] for r in results]

    return {
        "avg_attempts": statistics.mean(attempts_list),
        "median_attempts": statistics.median(attempts_list),
        "variance": statistics.variance(attempts_list) if len(attempts_list) > 1 else 0.0,
        "avg_score": statistics.mean(scores_list),
    }
