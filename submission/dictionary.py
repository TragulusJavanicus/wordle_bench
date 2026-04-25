"""
Example submission: Dictionary Iteration Solver
================================================
This is the simplest possible solver — it tries candidates in alphabetical
order, filtering by feedback after each guess.  It's intentionally naive so
you can see the baseline performance before optimising.

To create your own solver, copy this file and implement your strategy inside
the solve() function below.  The only requirement is the function signature:

    def solve(word_list: list[str], feedback_fn) -> int

Rules:
  - Call feedback_fn(guess) for every guess you make.
  - feedback_fn returns a string of G/Y/W characters:
        G = correct letter, correct position
        Y = correct letter, wrong position
        W = letter not in the word (at this position/count)
  - Keep guessing until feedback_fn returns all G's (e.g. "GGGGG").
  - Return the number of guesses you made.
  - Your guess must be a 5-letter word from word_list.
"""

from core.feedback import is_consistent


def solve(word_list: list[str], feedback_fn) -> int:
    """Guess the first remaining candidate each turn."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        guess = candidates[0]
        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
