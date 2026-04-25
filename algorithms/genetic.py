"""
Genetic Algorithm Solver
=========================
Uses evolutionary principles to evolve a population of candidate guesses
toward information-optimal choices.

Each "individual" in the population is a word from the remaining candidate set.
Fitness is the Shannon entropy of the word against the remaining candidates —
higher entropy means the guess partitions the candidate space more evenly,
revealing more information regardless of the actual answer.

Evolutionary loop per turn:
  1. Initialise: random sample of POPULATION_SIZE candidates
  2. Evaluate: compute entropy fitness for each individual
  3. Select:   tournament selection (best of TOURNAMENT_K random individuals)
  4. Crossover: character-level uniform crossover between two parents,
                repaired to the nearest valid candidate by position overlap
  5. Mutate:   with probability MUTATION_RATE, replace one individual with
               a random candidate (exploration step)
  6. Elitism:  always keep the best individual from the previous generation
  7. Repeat for GENERATIONS generations; return the best individual found

The GA explores the guess space in a biologically-inspired way. For very
small candidate sets (≤ POPULATION_SIZE), it falls back to exhaustive search
since evolution offers no advantage over just evaluating everything.

Characteristics:
- Stochastic: results vary between runs (use a fixed seed for reproducibility)
- Typically 3.8–4.5 average guesses
- More expensive than greedy per turn but explores better in mid-game
- Demonstrates selection pressure, crossover, mutation, and elitism
"""

import math
import random
from collections import Counter
from core.feedback import compute_feedback, is_consistent

POPULATION_SIZE = 20
GENERATIONS = 6
MUTATION_RATE = 0.25
TOURNAMENT_K = 3


# ---------------------------------------------------------------------------
# GA primitives
# ---------------------------------------------------------------------------

MAX_FITNESS_SAMPLE = 60  # Max candidates to evaluate for fitness (speed vs accuracy)
GA_THRESHOLD = 300       # Only run GA when candidate set is below this size


def _entropy(guess: str, candidates: list[str]) -> float:
    """Shannon entropy of this guess's partition over the remaining candidates.

    When the candidate set is large, samples MAX_FITNESS_SAMPLE words to keep
    each fitness evaluation O(1) rather than O(N).
    """
    if not candidates:
        return 0.0
    sample = (
        candidates
        if len(candidates) <= MAX_FITNESS_SAMPLE
        else random.sample(candidates, MAX_FITNESS_SAMPLE)
    )
    counts = Counter(compute_feedback(guess, c) for c in sample)
    total = len(sample)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def _tournament_select(population: list[str], fitnesses: list[float]) -> str:
    """Return the fittest individual from a random tournament of size TOURNAMENT_K."""
    contestants = random.sample(range(len(population)), min(TOURNAMENT_K, len(population)))
    winner = max(contestants, key=lambda i: fitnesses[i])
    return population[winner]


def _crossover(p1: str, p2: str) -> str:
    """Uniform crossover: independently pick each character from p1 or p2."""
    return "".join(a if random.random() < 0.5 else b for a, b in zip(p1, p2))


def _repair(child: str, candidates: list[str]) -> str:
    """Map an arbitrary string to the closest valid candidate by position overlap.

    Needed after crossover/mutation may produce a non-word string.
    Samples up to 80 candidates to keep this step O(1) in practice.
    """
    pool = random.sample(candidates, min(80, len(candidates)))
    return max(pool, key=lambda w: sum(a == b for a, b in zip(w, child)))


def _evolve(candidates: list[str]) -> str:
    """Run the GA and return the best guess found."""
    if len(candidates) <= POPULATION_SIZE:
        # Exhaustive evaluation is better than evolution at tiny scales
        return max(candidates, key=lambda w: _entropy(w, candidates))

    # Initialise population
    population = random.sample(candidates, POPULATION_SIZE)

    best_word = population[0]
    best_fitness = -1.0

    for _gen in range(GENERATIONS):
        fitnesses = [_entropy(ind, candidates) for ind in population]

        # Track global best across generations (elitism)
        gen_best_idx = max(range(len(population)), key=lambda i: fitnesses[i])
        if fitnesses[gen_best_idx] > best_fitness:
            best_fitness = fitnesses[gen_best_idx]
            best_word = population[gen_best_idx]

        # Build next generation
        new_pop: list[str] = [best_word]  # Elitism: carry over champion
        while len(new_pop) < POPULATION_SIZE:
            p1 = _tournament_select(population, fitnesses)
            p2 = _tournament_select(population, fitnesses)
            child = _crossover(p1, p2)
            child = _repair(child, candidates)

            # Mutation: replace with random candidate at MUTATION_RATE probability
            if random.random() < MUTATION_RATE:
                child = random.choice(candidates)

            new_pop.append(child)

        population = new_pop

    return best_word


# ---------------------------------------------------------------------------
# Solver interface
# ---------------------------------------------------------------------------

def solve(word_list: list[str], feedback_fn) -> int:
    """Evolve a population of guesses toward high-entropy choices each turn."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        elif len(candidates) > GA_THRESHOLD:
            # Greedy fallback for large sets: GA offers little advantage over
            # letter-frequency scoring when thousands of candidates remain.
            counts: Counter = Counter(ch for w in candidates for ch in set(w))
            guess = max(candidates, key=lambda w: sum(counts[ch] for ch in set(w)))
        else:
            guess = _evolve(candidates)

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
