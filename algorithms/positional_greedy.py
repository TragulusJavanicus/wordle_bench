"""
Positional Greedy Solver
=========================
An enhanced version of the greedy letter-frequency heuristic that weights
each letter by how often it appears at its SPECIFIC POSITION in the remaining
candidate set, rather than anywhere in a word.

Standard greedy (greedy.py):
  score(word) = Σ freq(letter)  for unique letters in word
  freq(letter) = how many remaining words contain this letter anywhere

Positional greedy (this solver):
  score(word) = Σ pos_freq(letter, position)  for i in 0..4
  pos_freq(letter, i) = how many remaining words have this letter at position i

Why position matters
---------------------
Consider the letter S in English Wordle words:
  - S appears very frequently at position 0 (e.g. STONE, STARE, SLIME…)
  - S is also common at position 4 (plural forms: HAIRS, ROPES…)
  - S rarely appears at positions 1-3

Standard greedy gives S the same credit regardless of where it is placed.
Positional greedy gives extra credit for placing S at position 0 or 4,
reflecting that a word like STARE has S where it is most likely to be G
rather than merely Y.

Result: positional greedy makes guesses that are more likely to produce G
feedback (confirmed positions) rather than just Y feedback, which narrows
the candidate set more aggressively.

Characteristics:
- Deterministic (given the remaining candidate set)
- Average ~4.3–5.0 guesses
- Slightly better than greedy.py, especially in later rounds
- O(N × word_length) per turn for scoring
"""

from collections import defaultdict
from core.feedback import is_consistent


def _positional_scores(candidates: list[str]) -> dict[int, dict[str, int]]:
    """For each position, count how many candidates have each letter there."""
    pos_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for word in candidates:
        for i, ch in enumerate(word):
            pos_counts[i][ch] += 1
    return pos_counts


def _word_score(word: str, pos_counts: dict) -> int:
    """Score a word by summing positional letter frequencies at each slot."""
    return sum(pos_counts[i].get(ch, 0) for i, ch in enumerate(word))


def solve(word_list: list[str], feedback_fn) -> int:
    """Guess the word whose letters best match their positional frequency in candidates."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        else:
            pos_counts = _positional_scores(candidates)
            # Alphabetical tie-break for determinism
            guess = max(candidates, key=lambda w: (_word_score(w, pos_counts), w))

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
