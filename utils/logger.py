"""High-score persistence: append-only JSON log with leaderboard queries."""

import json
import os
from datetime import datetime
from pathlib import Path

HIGHSCORES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "highscores.json")


def load_scores() -> list[dict]:
    """Load all scores from the highscores file."""
    if not os.path.exists(HIGHSCORES_FILE):
        return []
    with open(HIGHSCORES_FILE, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_score(entry: dict) -> None:
    """Append a new score entry to the highscores file."""
    scores = load_scores()
    scores.append(entry)
    with open(HIGHSCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)


def get_leaderboard(user: str | None = None, solver: str | None = None) -> list[dict]:
    """Return scores sorted by avg_score descending, with optional filters."""
    scores = load_scores()
    if user:
        scores = [s for s in scores if s.get("user", "").upper() == user.upper()]
    if solver:
        solver_lower = solver.lower()
        scores = [s for s in scores if solver_lower in s.get("solver", "").lower()]
    return sorted(scores, key=lambda x: x.get("avg_score", 0), reverse=True)


def build_score_entry(
    user: str,
    solver_path: str,
    metrics: dict,
    elapsed: float,
    peak_memory_mb: float,
) -> dict:
    """Construct a score entry dict from benchmark results."""
    return {
        "user": user,
        "solver": Path(solver_path).name,
        "avg_score": round(metrics["avg_score"], 2),
        "avg_attempts": round(metrics["avg_attempts"], 2),
        "median": metrics["median_attempts"],
        "variance": round(metrics["variance"], 4),
        "time": round(elapsed, 2),
        "memory": round(peak_memory_mb, 1),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
