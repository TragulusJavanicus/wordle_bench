"""
Bayesian Inference Solver
==========================
Strategy: Maintain an explicit probability distribution P(word) over the
remaining candidate words, updated after each guess using Bayes' theorem.

Bayesian update rule
---------------------
After observing feedback F for guess G:

    P(word | F, G) ∝ P(F | word, G) · P(word)

where:
  P(F | word, G) = 1  if compute_feedback(G, word) == F
                   0  otherwise

So the posterior is just the (renormalised) prior restricted to consistent
words — identical to the constraint-filter step used by all solvers.

Where Bayes adds value: the **prior** P(word).
Instead of assuming all remaining words are equally likely (uniform prior),
this solver builds a positional letter-frequency prior from the word list:

    P(word) ∝ ∏ freq(word[i], position=i)

where freq(letter, position) counts how often that letter appears at that
position across the full word list.  Common letters in common positions
get higher prior weight — the solver implicitly "knows" what typical
English 5-letter words look like.

Guess selection: at each turn, choose the candidate that **maximises the
expected posterior probability** of being the correct answer — i.e. the
word with the highest current posterior probability.

This MAP (Maximum A Posteriori) strategy leans toward guessing "likely"
words early, which can solve games faster when the answer happens to be
a common word pattern, but may perform worse on unusual answers.

Characteristics:
- Deterministic given the word list
- Average ~4.0–5.0 guesses
- O(N) per turn
- Pedagogically: shows how prior beliefs shape search strategy
"""

from collections import Counter
from core.feedback import is_consistent


def _build_positional_prior(word_list: list[str]) -> dict[str, dict[int, float]]:
    """Compute P(letter | position) across the full word list.

    Returns a nested dict: prior[letter][position] = normalised frequency.
    """
    word_length = len(word_list[0]) if word_list else 5
    counts: dict[int, Counter] = {i: Counter() for i in range(word_length)}

    for word in word_list:
        for i, ch in enumerate(word):
            counts[i][ch] += 1

    # Normalise per position
    prior: dict[str, dict[int, float]] = {}
    for pos, counter in counts.items():
        total = sum(counter.values())
        for ch, cnt in counter.items():
            if ch not in prior:
                prior[ch] = {}
            prior[ch][pos] = cnt / total

    return prior


def _word_prior_score(word: str, positional_prior: dict) -> float:
    """Compute the unnormalised prior probability of a word."""
    score = 1.0
    for i, ch in enumerate(word):
        score *= positional_prior.get(ch, {}).get(i, 1e-6)
    return score


def solve(word_list: list[str], feedback_fn) -> int:
    """Use a positional letter-frequency prior to select the most probable candidate."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length

    # Build prior once from the full word list
    positional_prior = _build_positional_prior(word_list)

    candidates = list(word_list)
    attempts = 0

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        else:
            # MAP estimate: the candidate with the highest prior probability
            # under the current (implicitly uniform conditional) posterior.
            # Alphabetical tie-break for determinism.
            guess = max(
                candidates,
                key=lambda w: (_word_prior_score(w, positional_prior), w),
            )

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        # Bayesian update: posterior = prior restricted to consistent words
        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
