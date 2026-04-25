"""
Two-Phase Solver (Fixed Openers + Entropy)
===========================================
Phase 1 — scripted openers (always guessed regardless of feedback):
  Move 1: CRANE  (C, R, A, N, E)
  Move 2: LOTUS  (L, O, T, U, S)
  Together these 10 letters cover the most common English letters.
  No computation needed for the first two guesses.

Phase 2 — entropy-based selection over the remaining candidates:
  From move 3 onward, use Shannon entropy to pick the best guess.

Why two openers before adapting?
  A single opener (CRANE) identifies ~5 letters.  A carefully chosen second
  opener that shares no letters with CRANE identifies 5 more, giving the
  solver rich feedback before any adaptive computation begins.
  This mirrors how many competitive human players approach Wordle: commit to
  a fixed two-word "script" that covers 10 letters, then solve from context.

CRANE + LOTUS coverage: A, C, E, L, N, O, R, S, T, U — 10 of the most
  frequent letters in English 5-letter words.  After two openers the solver
  typically has narrowed the candidate set to under 50 words.

Performance characteristic:
  Slightly slower on easy games (wastes move 2 on an opener that may not be
  needed) but more consistent on hard games because the 10-letter scaffold
  eliminates large parts of the search space before entropy kicks in.

Characteristics:
- Deterministic in Phase 1, information-optimal in Phase 2
- Average ~3.8–4.5 guesses
- O(1) for first two moves; O(N²) or O(sample×N) for subsequent moves
"""

import math
import random
from collections import Counter
from core.feedback import compute_feedback, is_consistent

OPENER_1 = "CRANE"   # C, R, A, N, E
OPENER_2 = "LOTUS"   # L, O, T, U, S  — no overlap with CRANE

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
    """Phase 1: always play CRANE then LOTUS.  Phase 2: entropy."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    word_set = {w.upper() for w in word_list}
    candidates = [w.upper() for w in word_list]
    attempts = 0

    # Map opener names to actual words in the list (fallback if not present)
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
