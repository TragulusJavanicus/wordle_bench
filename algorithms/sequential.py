"""
Sequential (Alphabetical Scan) Solver
=======================================
Strategy: Maintain a candidate set (initially the full word list). On each
turn, guess the alphabetically-first remaining candidate, receive feedback,
then filter the set to only words consistent with that feedback.

This is the naive alphabetical baseline — it explores the word space in
dictionary order with no heuristic, relying entirely on feedback to prune.

Note: always starting from the front of the alphabet is mildly harmful
because words starting with 'AA…' use rare letter combinations that don't
discriminate well.  The random_filtered.py solver, which also does zero
optimisation, beats this by ~0.5 guesses purely because random picks are
more "average" than always-alphabetically-first picks.

Characteristics:
- Simple and fully deterministic
- Average ~5.5–6.5 guesses per game
- O(N) selection per turn, O(N) filter per turn
- The simplest filtered solver (compare: dictionary.py for dumber, greedy.py for smarter)
"""

from core.feedback import is_consistent


def solve(word_list: list[str], feedback_fn) -> int:
    """Try words alphabetically, pruning by feedback each round."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        guess = candidates[0]  # always the alphabetically-first remaining candidate
        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        # Keep only words that would produce the same feedback pattern if they
        # were the target — this is the core Wordle filter step.
        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
