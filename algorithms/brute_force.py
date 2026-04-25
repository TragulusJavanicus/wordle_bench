"""
Brute-Force Random Solver (No Feedback Filtering)
===================================================
Strategy: pick a completely random word from the FULL word list every turn,
with no use of feedback whatsoever.  Keep guessing until the correct word
is found by chance.

This is the absolute naive baseline — it completely ignores all feedback.
Every guess is independently drawn from the entire 14,855-word list, so
the expected number of guesses is:

    E[attempts] = (N + 1) / 2  ≈  7,428  for N = 14,855

In other words: on average you need to try half the word list before
accidentally guessing the right answer.

Why include it?
  This solver exists purely as a teaching contrast to random_solver.py:

    random_solver.py  (random + filtering)  →  ~5  guesses
    brute_force.py    (random, no filtering) →  ~7,428 guesses

  That ~1,500× gap illustrates the power of constraint propagation:
  the feedback alone — even with zero heuristic intelligence about
  which word to pick — reduces the problem from impossibly hard to
  easily solvable.

  It also maps directly to the "brute-force letter discovery" family
  described in Mastermind-style analysis: probing with no memory is
  the worst possible strategy.

WARNING: Benching this solver with large sample sizes will be very slow.
  Use --sample=5 or --sample=10 when testing.
  Expected time per word: (N/2) × ~0.001 ms ≈ 7 seconds.
  Do NOT run with sample=1000.
"""

import random


def solve(word_list: list[str], feedback_fn) -> int:
    """Guess randomly from the full word list, ignoring all feedback."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    attempts = 0

    while True:
        guess = random.choice(word_list)
        feedback = feedback_fn(guess)
        attempts += 1
        if feedback == win:
            return attempts
        # Feedback is intentionally ignored — no candidate pruning.
