"""
Simulated Annealing Solver
===========================
Treats guess selection as a combinatorial optimisation problem and applies
Simulated Annealing (SA) to find a high-quality guess at each turn.

Simulated Annealing recap
--------------------------
SA is a metaheuristic inspired by the metallurgical process of slowly cooling
a material to minimise its energy state.  The algorithm:

  1. Start with a random initial "state" (here: a random candidate word)
  2. At temperature T, randomly perturb the state (swap to another candidate)
  3. Accept the new state if it's better, OR with probability exp(-ΔE / T)
     if it's worse (allowing uphill moves to escape local optima)
  4. Gradually reduce T via a cooling schedule
  5. Return the best state seen across all temperatures

Energy function
---------------
E(word) = -H(word, candidates)

where H is the Shannon entropy of the feedback distribution this word induces
over the remaining candidates.  Minimising energy = maximising entropy.

Why SA over greedy entropy?
SA's probabilistic acceptance of worse moves lets it escape local optima in
the entropy landscape — occasionally a word with slightly lower entropy leads
to a much better trajectory in subsequent turns.  With unlimited guesses,
this exploratory behaviour is relatively cheap.

Performance note: SA evaluates entropy for each accepted neighbour, which is
O(N) per evaluation.  With STEPS=40 iterations per turn, this is O(40·N) per
guess.  When candidates are large (>200), the entropy evaluation is over a
random sample (MAX_SAMPLE) to keep the solver fast.

Characteristics:
- Stochastic: results vary between runs
- Average ~3.8–4.5 guesses
- O(STEPS · min(N, MAX_SAMPLE)) per turn
- Demonstrates temperature-driven exploration vs. exploitation trade-off
"""

import math
import random
from collections import Counter

from core.feedback import compute_feedback, is_consistent

T_START = 2.0       # Initial temperature (high → lots of exploration)
T_END = 0.05        # Final temperature (low → pure exploitation)
STEPS = 40          # Number of SA iterations per guess
MAX_SAMPLE = 100    # Max candidates used for entropy evaluation (speed limit)


def _entropy(guess: str, candidates: list[str]) -> float:
    """Shannon entropy of the feedback partition, evaluated over a sample."""
    sample = (
        candidates
        if len(candidates) <= MAX_SAMPLE
        else random.sample(candidates, MAX_SAMPLE)
    )
    counts = Counter(compute_feedback(guess, c) for c in sample)
    total = len(sample)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def _sa_pick(candidates: list[str]) -> str:
    """Run Simulated Annealing to find a high-entropy guess from candidates."""
    current = random.choice(candidates)
    current_e = -_entropy(current, candidates)  # energy = -entropy

    best = current
    best_e = current_e

    T = T_START
    cooling = (T_END / T_START) ** (1.0 / STEPS)

    for _ in range(STEPS):
        neighbor = random.choice(candidates)
        neighbor_e = -_entropy(neighbor, candidates)
        delta = neighbor_e - current_e

        # Accept if better, or probabilistically if worse (Metropolis criterion)
        if delta < 0 or random.random() < math.exp(-delta / T):
            current = neighbor
            current_e = neighbor_e

        # Track global best (not just current — SA can drift away from best)
        if current_e < best_e:
            best_e = current_e
            best = current

        T *= cooling

    return best


def solve(word_list: list[str], feedback_fn) -> int:
    """Use Simulated Annealing to select high-entropy guesses each turn."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        elif len(candidates) <= 3:
            # Exhaustive entropy for tiny sets (SA overhead not worth it)
            guess = max(candidates, key=lambda w: _entropy(w, candidates))
        else:
            guess = _sa_pick(candidates)

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
