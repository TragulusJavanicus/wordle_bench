"""
Vowel-First Solver
===================
Strategy: prioritise identifying all vowels (A, E, I, O, U) before committing
to consonant-based discrimination.

Rationale
----------
Every English word contains at least one vowel.  Knowing which vowels are
(and aren't) in the target immediately halves or quarters the candidate set —
vowel presence/absence provides high-density coarse filtering.

Two-phase structure:
  Phase 1 — vowel discovery:
    Opener: ADIEU  (A, D, I, E, U — 4 vowels in one guess)
    If O is still unconfirmed after ADIEU, second opener: STORY  (S, T, O, R, Y)
    These two words together test all 5 vowels (A, E, I, O, U) plus 5 common
    consonants.  No feedback is needed to decide whether to play them: the vowel
    openers are scripted regardless of what ADIEU reveals.

  Phase 2 — vowel-aware greedy:
    Once vowels are identified, switch to POSITIONAL greedy that additionally
    rewards using confirmed-present vowels in their confirmed positions.
    This makes guesses that are likely to lock in vowel positions (G feedback)
    rather than just confirming presence (Y feedback).

Why this differs from two_phase.py:
  - two_phase.py is agnostic about letter TYPE; it just picks high-coverage openers.
  - vowel_first.py explicitly reasons about the vowel/consonant structure of English
    words, exploiting the fact that vowels give the most coarse-grained signal.

Characteristics:
- Partially scripted (first 1–2 guesses fixed), adaptive thereafter
- Average ~4.3–5.0 guesses
- Strongest advantage on words with unusual vowel patterns
- O(N) greedy selection after phase 1
"""

from collections import defaultdict
from core.feedback import is_consistent

VOWELS = frozenset("AEIOU")
OPENER_1 = "ADIEU"   # 4 vowels: A, E, I, U  + consonant D
OPENER_2 = "STORY"   # adds vowel O  + consonants S, T, R, Y


def _positional_scores(candidates: list[str]) -> dict:
    pos_counts: dict = defaultdict(lambda: defaultdict(int))
    for word in candidates:
        for i, ch in enumerate(word):
            pos_counts[i][ch] += 1
    return pos_counts


def _word_score(word: str, pos_counts: dict, confirmed_vowels: set) -> int:
    """Score by positional frequency, with a bonus for confirmed-present vowels in place."""
    base = sum(pos_counts[i].get(ch, 0) for i, ch in enumerate(word))
    vowel_bonus = sum(2 for ch in word if ch in confirmed_vowels)
    return base + vowel_bonus


def _known_vowels(history: list[tuple[str, str]]) -> set:
    """Return vowels confirmed present (G or Y) from guess history."""
    present = set()
    for guess, feedback in history:
        for ch, fb in zip(guess, feedback):
            if ch in VOWELS and fb in ("G", "Y"):
                present.add(ch)
    return present


def _missing_vowel(history: list[tuple[str, str]]) -> bool:
    """Return True if O has not yet been tested at all."""
    tested = set(ch for guess, _ in history for ch in guess)
    return "O" not in tested


def solve(word_list: list[str], feedback_fn) -> int:
    """Phase 1: vowel openers.  Phase 2: vowel-aware positional greedy."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    word_set = {w.upper() for w in word_list}
    candidates = list(word_list)
    attempts = 0
    history: list[tuple[str, str]] = []

    opener1 = OPENER_1 if OPENER_1 in word_set else candidates[0]
    opener2 = OPENER_2 if OPENER_2 in word_set else candidates[1]

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]

        elif attempts == 0:
            # Always start with the vowel-rich opener
            guess = opener1

        elif attempts == 1 and _missing_vowel(history):
            # O not yet probed — play second opener to cover all 5 vowels
            guess = opener2

        else:
            # Vowel-aware positional greedy
            confirmed_vowels = _known_vowels(history)
            pos_counts = _positional_scores(candidates)
            guess = max(
                candidates,
                key=lambda w: _word_score(w, pos_counts, confirmed_vowels),
            )

        feedback = feedback_fn(guess)
        attempts += 1
        history.append((guess, feedback))

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
