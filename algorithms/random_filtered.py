"""
Random-Filtered (Monte Carlo) Solver
======================================
Strategy: At each turn, pick a uniformly random word from the REMAINING
candidate set (words still consistent with all feedback), collect feedback,
and filter again.

This is the simplest possible filtered solver — it requires no heuristic,
no optimisation, and no lookahead.  The only intelligence is the feedback
filter itself, which guarantees convergence: every guess eliminates at least
the guessed word, and usually many more.

Why include it?
  - Demonstrates that random selection + constraint filtering is far better
    than naive brute-force (no filtering).  Compare:

        random_filtered.py  (random + filtering)    → ~5 guesses
        brute_force.py      (random, NO filtering)  → ~7,428 guesses

    This ~1,500× gap is entirely due to constraint propagation, with zero
    heuristic intelligence.  The feedback alone is doing almost all the work.

  - Outperforms sequential.py (~5.2 vs ~5.7) despite zero optimisation,
    because random picks are more "average" than always-alphabetically-first
    picks (which start with rare 'AA…' words).

Characteristics:
- Non-deterministic (results vary between runs)
- Average ~5–6 guesses per game
- O(N) per turn (random choice + filter)
"""

import random
from core.feedback import is_consistent


def solve(word_list: list[str], feedback_fn) -> int:
    """Guess a random remaining candidate each turn until the word is found."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        guess = random.choice(candidates)
        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        # Prune all candidates inconsistent with the observed feedback.
        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
