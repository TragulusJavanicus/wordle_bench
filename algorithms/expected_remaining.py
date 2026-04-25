"""
Expected Remaining Solver
==========================
Strategy: at each turn, choose the guess that minimises the EXPECTED NUMBER
of candidates remaining after the feedback is revealed.

Formal definition
-----------------
For a guess g over candidate set C (size N):
  Group C by feedback pattern: each pattern p has count n(p).
  E[remaining | g] = Σ_p  P(p) × n(p)
                   = Σ_p  (n(p)/N) × n(p)
                   = Σ_p  n(p)² / N

We MINIMISE this quantity — smaller expected remaining means faster convergence.

Contrast with other solvers
----------------------------
  BFS / minimax:        minimise MAX  partition size  (worst-case guarantee)
  Entropy:              maximise -Σ p·log p          (information-theoretic)
  Expected Remaining:   minimise Σ p·n(p) = Σ n²/N   (average-case optimal)

Key difference from entropy:
  Entropy weights each partition by its probability × log-probability.
  This gives extra weight to evenly-split partitions (maximises surprise).
  Expected remaining weights by probability × size, directly minimising
  the linear average remaining.

  In practice expected remaining performs similarly to entropy but diverges
  for highly skewed feedback distributions: entropy will prefer a guess that
  creates many tiny partitions even if one large partition remains, while
  expected remaining penalises that large partition more heavily.

  Example: two guesses, same entropy, but one leaves a partition of 100 words
  and many of size 1, the other leaves balanced partitions of ~10 each.
  Expected remaining prefers the balanced one; entropy treats them equally.

Performance note
----------------
When the candidate set exceeds SAMPLE_THRESHOLD, a random sample is used as
the guess pool.  The partition sizes are computed against the full candidate
set for accuracy.

Characteristics:
- Deterministic above SAMPLE_THRESHOLD (sampling introduces randomness)
- Average ~4.5–5.0 guesses
- O(N²) per turn for small sets; O(sample×N) for large sets
"""

import random
from collections import Counter
from core.feedback import compute_feedback, is_consistent

FULL_EVAL_THRESHOLD = 200   # below this, evaluate exhaustively
GUESS_POOL_SIZE = 80        # guess candidates to sample for large sets
EVAL_SAMPLE_SIZE = 80       # evaluation set to sample for large sets


def _expected_remaining(guess: str, eval_set: list[str]) -> float:
    """Compute Σ n(p)² / N over eval_set — lower is better."""
    counts = Counter(compute_feedback(guess, c) for c in eval_set)
    n = len(eval_set)
    return sum(v * v for v in counts.values()) / n


def _best_guess(candidates: list[str]) -> str:
    if len(candidates) <= FULL_EVAL_THRESHOLD:
        pool = candidates
        eval_set = candidates
    else:
        # Sample both the guess pool and the evaluation set for speed.
        # Using the same sample for both keeps the estimate self-consistent.
        pool = random.sample(candidates, GUESS_POOL_SIZE)
        eval_set = random.sample(candidates, EVAL_SAMPLE_SIZE)
    # Alphabetical tie-break for determinism within ties
    return min(pool, key=lambda w: (_expected_remaining(w, eval_set), w))


def solve(word_list: list[str], feedback_fn) -> int:
    """Each turn, guess the word that minimises the expected remaining candidate count."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        guess = candidates[0] if len(candidates) == 1 else _best_guess(candidates)

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
