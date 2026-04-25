"""
Greedy Letter-Frequency Solver
================================
Strategy: At each turn, score every remaining candidate by how many of the
most-common letters across all candidates it covers. Pick the highest-scoring
word as the next guess.

This is a greedy local heuristic — it maximises immediate information gain
by targeting the letters that appear most frequently, without looking ahead.

Characteristics:
- Typically 3.5–4.5 average guesses
- Fast: O(N) letter scoring + O(N) word scoring per turn
- May get stuck when few distinct letters remain at the top; doesn't
  consider inter-position structure or conditional probabilities
- Great pedagogical contrast to entropy (global vs local optimisation)
"""

from collections import Counter
from core.feedback import is_consistent


def _letter_scores(candidates: list[str]) -> Counter:
    """Count how many candidate words contain each letter (unique per word)."""
    counts: Counter = Counter()
    for word in candidates:
        for ch in set(word):
            counts[ch] += 1
    return counts


def _word_score(word: str, letter_scores: Counter) -> int:
    """Sum letter-frequency scores for unique letters in the word."""
    return sum(letter_scores[ch] for ch in set(word))


def solve(word_list: list[str], feedback_fn) -> int:
    """Guess the candidate that covers the most frequent unseen letters."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        else:
            scores = _letter_scores(candidates)
            # Break ties by alphabetical order for determinism
            guess = max(candidates, key=lambda w: (_word_score(w, scores), w))

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
