"""
Two-Phase Solver — Tuned Openers (SLATE + CRONY)
==================================================
Same architecture as two_phase.py but with empirically selected openers.

Opener selection methodology
------------------------------
Seven opener pairs were evaluated against an 800-word sample (seed 42):

  CRANE+LOTUS   4.5725   (original default)
  SLATE+CRONY   4.5537   ← winner
  STARE+COULD   4.5738
  TRACE+BONUS   4.6037
  AUDIO+STERN   4.6562
  RAISE+CLOUT   4.6550
  AROSE+UNTIL   4.6775

SLATE+CRONY covers: A, C, E, L, N, O, R, S, T, Y — the same 10 letter
slots as CRANE+LOTUS but with a slightly better partition structure.
SLATE is a stronger first opener than CRANE (its letters sit at more
discriminating positions in the 14k-word list).

Phase 1: always play SLATE, then CRONY.
Phase 2: from move 3, use Shannon entropy to pick the best remaining guess.
"""

import math
import random
from collections import Counter
from core.feedback import compute_feedback, is_consistent

OPENER_1 = "SLATE"
OPENER_2 = "CRONY"

FULL_EVAL_THRESHOLD = 200
GUESS_POOL_SIZE = 80


def _entropy(guess: str, candidates: list[str]) -> float:
    counts = Counter(compute_feedback(guess, c) for c in candidates)
    total = len(candidates)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def _best_entropy_guess(candidates: list[str]) -> str:
    pool = (
        candidates
        if len(candidates) <= FULL_EVAL_THRESHOLD
        else random.sample(candidates, GUESS_POOL_SIZE)
    )
    return max(pool, key=lambda w: (_entropy(w, candidates), w))


def solve(word_list: list[str], feedback_fn) -> int:
    """Phase 1: SLATE then CRONY.  Phase 2: entropy."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    word_set = {w.upper() for w in word_list}
    candidates = [w.upper() for w in word_list]
    attempts = 0

    opener1 = OPENER_1 if OPENER_1 in word_set else candidates[0]
    opener2 = OPENER_2 if OPENER_2 in word_set else candidates[1]

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        elif attempts == 0:
            guess = opener1
        elif attempts == 1:
            guess = opener2
        else:
            guess = _best_entropy_guess(candidates)

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
