"""
Brute-Force Random-Start Solver (No Feedback Filtering)
=========================================================
Strategy: shuffle the word list once, then iterate through it in that random
order until the correct word is found by chance.  Feedback is ignored.

Difference from brute_force.py
-------------------------------
  brute_force.py          — random.choice() WITH replacement each turn
                            → the same word can be picked multiple times
                            → E[attempts] = N  (geometric, p = 1/N)

  brute_force_random_start.py — random.shuffle() once, then scan linearly
                            → every word is tried EXACTLY once before repeating
                            → E[attempts] = (N + 1) / 2  ≈ 7,428

Both solvers ignore all feedback, but the random-start variant eliminates
repeated guesses.  Since repetition is the only inefficiency in the pure
random baseline, this solver should average ~2× fewer guesses.

Why compare them?
  The gap shows the effect of de-duplication in its purest form: the only
  difference is whether we allow the same guess twice.  No constraint
  propagation, no heuristics — just "don't repeat yourself."

  Compare with random_filtered.py (~5 guesses): that solver DOES use
  feedback for filtering, which cuts the remaining set roughly in half
  each turn and collapses ~7,428 guesses down to ~5.

Expected performance:
  Avg attempts  ≈  7,428   (vs brute_force.py:  ≈ 14,855)
  Variance will be high: best case 1, worst case N.

WARNING: Benching this solver with large sample sizes will be very slow.
  Use --sample=5 or --sample=10 when testing.
"""

import random


def solve(word_list: list[str], feedback_fn) -> int:
    """Shuffle once, then iterate in that order — no filtering, no repeats."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length

    # One-time shuffle: guarantees each word is tried at most once per cycle
    shuffled = list(word_list)
    random.shuffle(shuffled)

    attempts = 0
    for guess in shuffled:
        feedback = feedback_fn(guess)
        attempts += 1
        if feedback == win:
            return attempts

    # Should never reach here for a valid word list (target is always in list)
    return attempts
