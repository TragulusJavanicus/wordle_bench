"""
English Letter Frequency Prior Solver
=======================================
Strategy: score candidate words by how closely their letter distribution
matches standard English letter frequencies — an EXTERNAL, fixed knowledge
source independent of the remaining candidate set.

How it differs from greedy.py
-------------------------------
  greedy.py:            score = Σ freq(letter in REMAINING CANDIDATES)
  frequency_prior.py:   score = Σ freq(letter in ENGLISH LANGUAGE)  (fixed table)

Greedy adapts its scoring to whatever letters happen to remain.  This solver
uses a pre-baked English frequency table that never changes.  The difference
matters when the remaining candidate set is biased:

  Example: after several guesses, only words containing X, Z, Q remain.
  Greedy now rates X, Z, Q as very valuable.  frequency_prior still rates
  E, T, A, O, I as most valuable — it "knows" these are rare target words
  and prefers guesses that maximize coverage of common-letter positions,
  even if those letters aren't in many remaining candidates.

The fixed prior also encodes a "soft common-word preference": because common
English letters naturally appear in common words, this solver implicitly
ranks common words higher than obscure ones.

English letter frequency source (approximate, standard reference):
  E  T  A  O  I  N  S  H  R  D  L  C  U  M  W  F  G  Y  P  B  V  K  J  X  Q  Z

Additional heuristics stacked on top of letter frequency:
  1. No-repeat bonus: words with 5 unique letters score extra — each unique
     letter gives independent information.
  2. Position-harmony bonus: slight bonus for placing common letters in their
     most natural English positions (e.g. S at start/end, E at end).

Characteristics:
- Deterministic (fixed frequency table, no randomness)
- Average ~4.5–5.5 guesses
- Useful baseline for external-knowledge-guided solving
- O(N) per turn (simple scoring)
"""

from core.feedback import is_consistent

# Standard English letter frequencies (per 10,000 characters, rounded)
_LETTER_FREQ: dict[str, float] = {
    "E": 1270, "T":  906, "A":  817, "O":  751, "I":  697,
    "N":  675, "S":  633, "H":  609, "R":  599, "D":  425,
    "L":  403, "C":  278, "U":  276, "M":  241, "W":  236,
    "F":  223, "G":  202, "Y":  197, "P":  193, "B":  149,
    "V":   98, "K":   77, "J":   15, "X":   15, "Q":   10, "Z":    7,
}

# Slight positional biases derived from common English word patterns
# (S common at 0 and 4; E common at 4; Y common at 4 as plural/adverb ending)
_POS_BONUS: dict[str, list[float]] = {
    "S": [1.3, 1.0, 1.0, 1.0, 1.4],
    "E": [1.0, 1.0, 1.0, 1.0, 1.5],
    "Y": [1.0, 1.0, 1.0, 1.0, 1.4],
    "A": [1.2, 1.0, 1.0, 1.0, 1.0],
    "I": [1.0, 1.2, 1.0, 1.0, 1.0],
}


def _word_score(word: str) -> float:
    """Score using English frequency + positional bonus + unique-letter bonus."""
    seen: set[str] = set()
    score = 0.0
    for i, ch in enumerate(word):
        base = _LETTER_FREQ.get(ch, 0)
        pos_mult = _POS_BONUS.get(ch, [1.0] * 5)[i]
        # Penalise repeated letters: second occurrence of a letter gives half credit
        repeat_mult = 1.0 if ch not in seen else 0.5
        score += base * pos_mult * repeat_mult
        seen.add(ch)
    return score


def solve(word_list: list[str], feedback_fn) -> int:
    """Each turn, pick the candidate with the highest English-frequency score."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        else:
            # Alphabetical tie-break for determinism
            guess = max(candidates, key=lambda w: (_word_score(w), w))

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
