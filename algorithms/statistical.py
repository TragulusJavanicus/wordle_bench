"""
Statistical Frequency Solver
==============================
Strategy: two-phase approach grounded in statistical analysis of the
remaining candidate set.

Phase 1 — Top-5 Letter Coverage
---------------------------------
At each turn, compute the frequency of every letter across all remaining
candidates.  Identify the top-5 most frequent letters that have not yet
been probed (neither confirmed present nor confirmed absent).

Pick the candidate that covers the most of those top-5 unprobed letters.
Ties broken by positional frequency (see Phase 2).

Rationale: the top-5 letters by frequency carry the most information per
guess.  Covering them first collapses the candidate set faster than any
positional heuristic because letter presence/absence is a coarser filter
(it applies to ALL positions simultaneously) while positional placement
only resolves one slot.

Phase 2 — Positional Frequency Scoring
----------------------------------------
Once all top-5 letters have been probed (confirmed or eliminated), switch
to positional scoring: for each position, count how many candidates have
each letter there, and score a word by summing those counts.

This rewards placing confirmed-present letters at their most likely
positions, converting Y (present, wrong place) feedback into G (correct
place) feedback faster.

How the phases interact
------------------------
Phase 1 is short (1–2 guesses in most games): it identifies the letters
that define the shape of the target.  Phase 2 then locks in positions.

Example:
  Remaining candidates have top-5 letters: E, A, R, S, T
  Phase 1 picks a word covering as many of {E, A, R, S, T} as possible.
  After that guess, confirmed letters are known → Phase 2 takes over.

Characteristics:
- Deterministic (no randomness; tie-breaks by alphabetical order)
- Average ~4.5–5.2 guesses
- O(N × word_length) per turn
- Naturally adapts: as candidates shrink, both the top-5 letters and the
  positional counts shift to reflect the surviving word set.
"""

from collections import Counter, defaultdict
from core.feedback import is_consistent

TOP_N = 5   # number of high-frequency letters to target in Phase 1


def _letter_freq(candidates: list[str]) -> list[str]:
    """Return all letters sorted by descending frequency across candidates."""
    counts: Counter = Counter()
    for word in candidates:
        counts.update(set(word))   # count each letter once per word
    return [ch for ch, _ in counts.most_common()]


def _positional_counts(candidates: list[str]) -> dict[int, dict[str, int]]:
    """For each position, count how many candidates have each letter there."""
    pos: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for word in candidates:
        for i, ch in enumerate(word):
            pos[i][ch] += 1
    return pos


def _positional_score(word: str, pos: dict) -> int:
    return sum(pos[i].get(ch, 0) for i, ch in enumerate(word))


def _coverage(word: str, targets: set[str]) -> int:
    """Count how many target letters appear in word (unique matches)."""
    return len(set(word) & targets)


def _probed_letters(history: list[tuple[str, str]]) -> set[str]:
    """Return all letters that have received any feedback so far."""
    return {ch for guess, _ in history for ch in guess}


def solve(word_list: list[str], feedback_fn) -> int:
    """Phase 1: cover top-5 frequent letters.  Phase 2: positional greedy."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0
    history: list[tuple[str, str]] = []

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        else:
            probed = _probed_letters(history)
            freq_order = _letter_freq(candidates)
            # Top-N letters not yet probed
            top_targets = [ch for ch in freq_order if ch not in probed][:TOP_N]
            target_set = set(top_targets)

            pos = _positional_counts(candidates)

            if target_set:
                # Phase 1: maximise coverage of unprobed top letters,
                # break ties by positional score, then alphabetically.
                top_score = max(
                    (_coverage(w, target_set), _positional_score(w, pos))
                    for w in candidates
                )
                tied = [w for w in candidates
                        if (_coverage(w, target_set), _positional_score(w, pos)) == top_score]
                guess = min(tied)   # alphabetically first among ties
            else:
                # Phase 2: all top letters probed — pure positional greedy
                best_pos_score = max(_positional_score(w, pos) for w in candidates)
                tied = [w for w in candidates if _positional_score(w, pos) == best_pos_score]
                guess = min(tied)   # alphabetically first among ties

        feedback = feedback_fn(guess)
        attempts += 1
        history.append((guess, feedback))

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
