# Wordle Algorithm Study Notes

A field guide to all 20 solvers implemented in this project — how they work,
why they make the choices they do, and what each one teaches about search,
optimisation, and information theory.

---

## How Wordle Works (Quick Recap)

Each game starts with a secret 5-letter word drawn from a list of 14,855 words.
You guess a word and receive letter-by-letter feedback:

| Symbol | Meaning |
|--------|---------|
| `G` | Right letter, right position |
| `Y` | Right letter, wrong position |
| `W` | Letter not in the word |

A solver wins by accumulating feedback and using it to narrow down the candidate
set until only one word remains — or until it guesses the answer directly.

**Score** = `word_list_size − attempts`. Fewer guesses = higher score.

---

## The Core Primitive: Constraint Filtering

Every non-brute-force solver relies on one function:

```python
def is_consistent(word, guess, feedback):
    return compute_feedback(guess, word) == feedback
```

After each guess, keep only candidates `w` where `is_consistent(w, guess, feedback)` is `True`.
This filter is the engine of every smart solver. What differentiates solvers is
**how they choose the next guess** from the surviving candidates.

---

## Algorithm Taxonomy

```
All Solvers
├── Baseline (no heuristic)
│   ├── brute_force              random pick, NO filter, WITH replacement
│   ├── brute_force_random_start random pick, NO filter, no replacement
│   ├── sequential               alphabetical order, WITH filter
│   ├── dictionary / deterministic  fixed order, NO filter
│   └── random_filtered          random pick, WITH filter
│
├── Greedy / Frequency
│   ├── greedy                   letter frequency over candidates
│   ├── positional_greedy        per-position letter frequency
│   ├── frequency_prior          fixed English letter frequency table
│   ├── statistical              top-5 freq coverage → positional
│   └── bayesian                 positional frequency MAP estimate
│
├── Information-Theoretic
│   ├── entropy                  Shannon entropy maximisation
│   ├── expected_remaining       minimise E[candidates left]
│   └── entropy_freq             entropy + familiarity weight
│
├── Search / Metaheuristic
│   ├── dfs                      commit to most constrained branch
│   ├── bfs                      minimax: minimise worst-case partition
│   ├── genetic                  evolutionary population over entropy
│   ├── simulated_annealing      SA over entropy landscape
│   ├── beam_search              2-level entropy lookahead
│   └── beam_search_3            3-level entropy lookahead
│
└── Hybrid / Multi-Phase
    ├── two_phase                CRANE+LOTUS openers → entropy
    ├── two_phase_tuned          SLATE+CRONY openers → entropy (empirically best)
    └── vowel_first              ADIEU+STORY openers → positional greedy
```

---

## Benchmark Results (sample=1000, seed=42)

| Rank | Solver | Avg Attempts | Median | Variance |
|------|--------|-------------|--------|----------|
| 1 | two_phase | 4.59 | 4.0 | 1.83 |
| 2 | entropy | 4.68 | 4.0 | 2.08 |
| 3 | expected_remaining | 4.73 | 4.0 | 2.48 |
| 4 | genetic | 4.76 | 4.0 | 2.74 |
| 5 | simulated_annealing | 4.76 | 4.0 | 2.46 |
| 6 | bfs | 4.79 | 5.0 | 2.38 |
| 7 | beam_search | 4.85 | 5.0 | 2.43 |
| 8 | statistical | 4.87 | 4.0 | 2.97 |
| 9 | greedy | 4.90 | 5.0 | 2.60 |
| 10 | vowel_first | 4.92 | 5.0 | 2.61 |
| 11 | positional_greedy | 5.11 | 5.0 | 2.74 |
| 12 | frequency_prior | 5.11 | 5.0 | 2.91 |
| 13 | bayesian | 5.14 | 5.0 | 2.87 |
| 14 | random_filtered | 5.24 | 5.0 | 2.70 |
| 15 | dfs | 5.57 | 5.0 | 2.50 |
| 16 | sequential | 5.71 | 5.0 | 3.39 |
| 17 | dictionary | 19.68 | 19.0 | 68.5 |
| 18 | deterministic | 21.34 | 21.0 | 12.2 |
| 19 | brute_force_random_start | 7,452 | 7,459 | ~19M |
| 20 | brute_force | 15,071 | 10,757 | ~217M |

---

---

# Part 1 — Baseline Solvers

---

## 1. `brute_force.py` — Random Guess, No Memory

**Strategy:** Pick a uniformly random word from the **full** word list every turn. Ignore all feedback completely.

**Key idea:** This is the worst possible strategy that still terminates. It demonstrates what happens when you have zero intelligence and zero memory.

**How it works:**
```
loop forever:
    guess = random.choice(full_word_list)   # can repeat!
    if feedback == GGGGG: return attempts
    # feedback is discarded — not used at all
```

**Why it's slow:** Because it samples *with replacement*, it can pick the same word multiple times. The expected number of guesses follows a **geometric distribution** with `p = 1/N`:

```
E[attempts] = 1/p = N ≈ 14,855
```

On average you need to try the entire word list before landing on the answer by chance.

**Score note:** Because avg attempts (~15,071) *exceeds* N (14,855), the score formula `N − attempts` gives a **negative score** (−216). This is the only solver that can score negative — a direct consequence of sampling with replacement.

**What it teaches:** The power of constraint filtering. Random-filtered.py achieves ~5.2 guesses using *the same random selection* but *with* feedback filtering — a ~2,900× improvement from the filter alone.

---

## 2. `brute_force_random_start.py` — Shuffle Once, No Memory

**Strategy:** Shuffle the full word list once, then iterate through it in that shuffled order. Ignore all feedback.

**Key idea:** Same as brute_force but without repetition. Each word is tried exactly once per cycle.

**How it works:**
```
shuffled = random.shuffle(word_list)   # one-time shuffle
for word in shuffled:
    if feedback == GGGGG: return attempts
    # feedback still ignored
```

**Why it's 2× faster than brute_force:** The shuffled iteration guarantees **no repeats**. The expected position of the target word in a randomly shuffled list follows a **uniform distribution** over [1, N]:

```
E[attempts] = (N + 1) / 2 ≈ 7,428
```

That's exactly half of brute_force's `N` — the sole improvement comes from de-duplication.

**Comparison table:**

| Solver | Sampling | E[attempts] | Can repeat? |
|--------|----------|-------------|-------------|
| brute_force | with replacement | N = 14,855 | Yes |
| brute_force_random_start | without replacement | (N+1)/2 ≈ 7,428 | No |
| random_filtered | without replacement + filter | ~5.2 | No |

**What it teaches:** De-duplication alone halves the brute-force cost. But it still can't compete with *any* filtered solver — feedback filtering does the real work.

---

## 3. `random_filtered.py` — Random Pick with Filtering

**Strategy:** At each turn, pick a uniformly random word from the *remaining candidates* (words still consistent with all feedback received so far).

**How it works:**
```
candidates = full_word_list
loop:
    guess = random.choice(candidates)
    feedback = ask(guess)
    if feedback == GGGGG: return
    candidates = [w for w in candidates if is_consistent(w, guess, feedback)]
```

**Why it works:** Each guess (even a random one) produces feedback that typically eliminates a large fraction of candidates. For a random split, each guess halves the candidate set on average, so convergence is exponential:

```
After 1 guess: ~14,855 → ~7,427
After 2 guesses: ~7,427 → ~3,713
...
After k guesses: ~14,855 / 2^k candidates remain
```

The filter is doing almost all the work — zero intelligence is needed. This is why **~5.2 guesses** is achievable with zero strategy.

**What it teaches:** Constraint propagation is the single most powerful tool in Wordle solving. Every solver above rank 14 in the benchmark uses the same filter — the difference is purely in *which word they choose to guess*.

---

## 4. `sequential.py` — Alphabetical Scan with Filtering

**Strategy:** Always guess the alphabetically-first remaining candidate.

**How it works:** Identical to random_filtered, except the guess selection is deterministic: `guess = candidates[0]` (alphabetically first after sorting).

**Why it underperforms random_filtered:** Words starting with 'A' are disproportionately represented near the start of the alphabet. Words like AAHED, AALII, ABACI use rare letter combinations that produce very uneven feedback partitions — eliminating few candidates per guess. Random picks are more "average" and eliminate more per guess on expectation.

**Result:** ~5.71 avg vs ~5.24 avg for random_filtered — a deterministic ordering is slightly worse than random.

---

## 5. `dictionary.py` / `deterministic.py` — Fixed Order, No Filter

**Strategy:** Iterate through the word list in a fixed order without filtering by feedback.

**Result:** ~19–21 avg attempts. The lack of filtering means the solver wastes guesses on words that feedback already ruled out.

---

---

# Part 2 — Greedy / Frequency Solvers

These solvers score each candidate word by some measure of *how useful* it would be to guess, and pick the highest-scoring one. No lookahead — purely local optimisation.

---

## 6. `greedy.py` — Letter Frequency Greedy

**Strategy:** Score each candidate by the total frequency of its unique letters across all remaining candidates. Pick the highest-scoring word.

**Intuition:** If letter 'E' appears in 800 of the 1,000 remaining candidates, guessing a word containing 'E' will either:
- Confirm E is in the word (Y or G) → narrows by ~200
- Reveal E is absent (W) → narrows by ~800

Either way, we learn the most about 'E' because it's the most common letter.

**Scoring formula:**
```python
letter_score[ch] = number of remaining candidates containing ch
word_score(w) = sum(letter_score[ch] for ch in set(w))  # unique letters only
```

**Why unique letters?** Including repeated letters would double-count a letter's information — if a word has two E's, we don't learn twice as much about E's presence.

**Complexity:** O(N) to compute letter scores, O(N) to score all words → O(N) per turn.

**Limitation:** Treats all positions as equal. A word scoring high on letter frequency might place common letters at unlikely positions, giving Y feedback (present, wrong place) rather than G (correct place) — Y feedback narrows the candidate set less effectively than G.

---

## 7. `positional_greedy.py` — Per-Position Letter Frequency

**Strategy:** Like greedy, but score each letter by how many candidates have it at **that specific position**, not just anywhere.

**Scoring formula:**
```python
pos_counts[i][ch] = number of candidates with letter ch at position i
word_score(w) = sum(pos_counts[i][ch] for i, ch in enumerate(w))
```

**Why it beats greedy:** Placing 'S' at position 0 (where it's common: STONE, STARE…) is more valuable than placing it at position 2 (where it's rare). Positional scoring rewards guesses likely to produce G feedback rather than just Y feedback.

**Example:**
```
Remaining candidates: STONE, STALE, STORE, STOVE, STAKE
Positional score for STALE:
  S at pos 0: 5 (all have S there)
  T at pos 1: 5 (all have T there)
  A at pos 2: 2 (STALE, STAKE)
  L at pos 3: 1 (STALE)
  E at pos 4: 4 (STONE, STALE, STORE, STOVE)
  Total: 17
```

**Result:** ~5.11 avg vs ~4.90 for greedy — modest improvement from position-awareness.

---

## 8. `frequency_prior.py` — Fixed English Letter Frequencies

**Strategy:** Score every candidate using a *fixed* English letter frequency table that never changes, regardless of what candidates remain.

**The frequency table (per 10,000 chars):**
```
E:1270  T:906  A:817  O:751  I:697  N:675  S:633  H:609  R:599  D:425
L:403   C:278  U:276  M:241  W:236  F:223  G:202  Y:197  P:193  B:149
V:98    K:77   J:15   X:15   Q:10   Z:7
```

**Key difference from greedy.py:**

| Solver | Letter weights |
|--------|---------------|
| greedy | Dynamic — updates every turn based on *remaining candidates* |
| frequency_prior | Static — fixed English frequency table, never changes |

**When greedy adapts but frequency_prior doesn't:** If after several guesses only words containing X, Z, Q remain — greedy now rates X, Z, Q as very valuable. frequency_prior still rates E, T, A as most valuable, "knowing" the remaining words are unusual and treating them accordingly.

**Additional heuristics stacked on top:**
- **No-repeat bonus:** words with 5 unique letters score higher (each gives independent information)
- **Position-harmony bonus:** common letters score extra at their most natural positions (S at start/end, E at the end, etc.)

**Complexity:** O(N) per turn — no candidate-set computation needed at all.

---

## 9. `statistical.py` — Top-5 Coverage then Positional

**Strategy:** Two phases based on statistical analysis of the remaining candidate set.

**Phase 1 — Cover the top-5 most frequent unprobed letters:**
```
freq_order = letters sorted by how many candidates contain them
top_targets = first 5 letters not yet guessed
pick word that covers the most top_targets letters
```

**Phase 2 — Positional greedy (once all top-5 are probed):**
Switch to per-position frequency scoring (same as positional_greedy.py).

**Why top-5 specifically?** Letter presence/absence is a *global* filter — it eliminates words regardless of position. The top-5 letters by frequency provide the highest information density per guess early in the game. After they're identified, position information becomes the bottleneck.

**How the phases interact:**
- Phase 1 typically lasts 1–2 guesses
- Phase 2 takes over for the remaining 2–4 guesses
- Both phases adapt to the *current* candidate set, so the top-5 change as candidates are eliminated

**Result:** ~4.87 avg — beats greedy (4.90) and positional_greedy (5.11) by adapting frequency analysis to each game state.

---

## 10. `bayesian.py` — Positional Frequency MAP Estimate

**Strategy:** Build a probability distribution P(word) over candidates using a positional letter-frequency prior, then pick the word with the highest posterior probability (MAP estimate).

**The prior:**
```python
P(word) ∝ ∏ freq(word[i], position=i)
```

where `freq(letter, position)` counts how often that letter appears at that position across the *full* word list. This encodes structural knowledge about what 5-letter English words look like.

**Bayesian update:** After observing feedback F for guess G:
```
P(word | F, G) ∝ P(F | word, G) × P(word)
                = 1 × P(word)  if is_consistent(word, G, F)
                = 0            otherwise
```

So the posterior is just the prior renormalized to consistent words — identical to the constraint filter, but weighted by prior probability rather than uniform.

**Guess selection:** Pick the word with the highest P(word) given current feedback — the *Maximum A Posteriori* (MAP) estimate.

**Difference from entropy:** Bayesian picks the most *likely* answer. Entropy picks the guess that maximally *partitions* the remaining candidates. When the answer is a common word pattern, Bayesian gets there faster. When it's unusual, it may struggle.

**Result:** ~5.14 avg — lower than entropy (4.68) because MAP picks the most probable answer rather than optimising for information gain. It's a more "human-like" strategy.

---

---

# Part 3 — Information-Theoretic Solvers

These solvers reason explicitly about information content — how much each guess reduces uncertainty about the answer.

---

## Key Concept: Shannon Entropy

Shannon entropy measures the *average uncertainty* of a probability distribution:

```
H = -∑ p(x) × log₂ p(x)
```

In Wordle terms: for a guess `g` over remaining candidates `C`, group `C` by the feedback pattern each candidate would produce. Each group has probability `n(pattern) / |C|`. The entropy of `g` is:

```
H(g) = -∑ (n(p) / N) × log₂(n(p) / N)
```

**Higher entropy = more even partition = more information per guess.**

Maximum entropy for N candidates occurs when every feedback pattern appears equally often (perfect split). A guess that eliminates only 1 candidate in a group of 1,000 has very low entropy — it's almost certain to leave you in the same position.

---

## 11. `entropy.py` — Shannon Entropy Maximisation

**Strategy:** Each turn, pick the candidate that maximises the Shannon entropy of the feedback distribution over remaining candidates.

**Scoring:**
```python
def entropy(guess, candidates):
    counts = Counter(compute_feedback(guess, c) for c in candidates)
    total = len(candidates)
    return -sum((n/total) * log2(n/total) for n in counts.values())

best_guess = max(candidates, key=lambda w: entropy(w, candidates))
```

**First guess fixed to CRANE:** Computing entropy for all 14,855 words against all 14,855 candidates on move 1 would be ~220M operations. CRANE is a strong empirical opener (high entropy over the full word list). Fixing it avoids this cost with negligible quality loss.

**Large-set sampling:** When candidates > 200, sample 100 random candidates as the guess pool. Entropy is still computed against the *full* remaining set (not a sample) to maintain accuracy.

**Complexity:** O(GUESS_POOL × N) per turn — each candidate in the pool scores against all N remaining candidates.

**Why it's near-optimal:** Maximising entropy is the information-theoretically optimal *one-step-ahead* heuristic. It doesn't guarantee the minimum total guesses (that would require full game-tree search), but it's the best local choice given only the current state.

**Result:** ~4.68 avg — second best overall, beaten only by two_phase.

---

## 12. `expected_remaining.py` — Minimise Expected Candidates Remaining

**Strategy:** Pick the guess that minimises the *expected number of candidates remaining* after feedback.

**Formula:**
```
E[remaining | g] = ∑_p P(p) × n(p)
                 = ∑_p (n(p)/N) × n(p)
                 = ∑_p n(p)² / N
```

where `n(p)` is the number of candidates in partition `p` and `N` is total candidates.

**Difference from entropy:**

| Criterion | Formula | Weights |
|-----------|---------|---------|
| Entropy | −∑ p·log₂p | Favours even splits |
| Expected remaining | ∑ n²/N | Penalises large partitions |

Both measure partition quality, but with different emphasis:
- **Entropy** cares about the *shape* of the distribution (surprisingness)
- **Expected remaining** cares about the *size* of partitions left behind

**When they differ:** Suppose two guesses have equal entropy but one leaves a partition of 100 words and many of size 1, while the other leaves balanced partitions of ~10 each. Expected remaining prefers the balanced one. Entropy treats them the same.

**Result:** ~4.73 avg — third best, slightly worse than entropy in practice.

---

## 13. `entropy_freq.py` — Entropy + Word Familiarity

**Strategy:** Combines Shannon entropy with a word-familiarity score based on English letter frequencies.

**Combined score:**
```python
score(guess) = entropy(guess, candidates) + 0.15 × normalized_familiarity(guess)
```

where `familiarity(word) = sum of English letter frequencies for unique letters in word`.

**Motivation:** Pure entropy treats all remaining candidates as equally likely answers. In practice, Wordle answer lists are biased toward common English words. The familiarity term up-weights guesses that are themselves common words, giving a slight advantage when the answer is common.

**Weight choice (0.15):** At most 0.15 bits of familiarity bonus — small enough that entropy dominates almost all decisions, but large enough to break ties in favour of familiar words.

**When it helps:** Games where the answer is a common word (CRANE, STONE, PLATE) — familiarity nudges toward the answer ~0.03 guesses faster.
**When it hurts:** Games where the answer is obscure — negligible cost since the entropy term dominates.

**Opener fixed to SLATE:** A strong empirical opener for this solver (found from the same opener comparison that produced two_phase_tuned).

---

---

# Part 4 — Search and Metaheuristic Solvers

These solvers use classical search algorithms or optimisation metaheuristics, mapping Wordle's guess selection onto frameworks from computer science.

---

## 14. `dfs.py` — Depth-First Search (Commit-and-Constrain)

**Analogy:** In a game tree where nodes are game states (remaining candidate sets) and edges are guesses, DFS commits to the *most promising branch* immediately and follows it to the end.

**Implementation:** Always guess the candidate with the highest *certainty score*:
1. **Primary:** count of positions already known to be correct (G matches)
2. **Secondary:** count of letters confirmed present (G or Y)

```python
def certainty_score(word, known_positions, known_letters):
    primary = sum(1 for i, ch in enumerate(word) if known_positions.get(i) == ch)
    secondary = sum(1 for ch in set(word) if ch in known_letters)
    return (primary, secondary)
```

**DFS philosophy:** Exploit what you know immediately. If position 2 is confirmed 'A', guess words that have A at position 2 first. This is "going deeper" in the knowledge tree.

**Trade-off vs BFS:**
- DFS wins when the first committed branch contains the answer (few guesses)
- DFS loses when the committed branch is wrong — it may waste guesses before backtracking
- BFS guarantees bounded worst-case; DFS offers better best-case

**Result:** ~5.57 avg — higher than BFS (4.79) due to higher variance. DFS is the right analogy but *certainty scoring* is a weaker heuristic than minimax.

---

## 15. `bfs.py` — Breadth-First Search (Minimax)

**Analogy:** BFS explores the game tree level by level, ensuring the shallowest solution is found first. In Wordle, "shallowest" means "fewest guesses possible in the worst case."

**Implementation:** Minimax — pick the guess that minimises the *maximum* partition size:
```python
worst_case(guess, candidates) = max(
    Counter(compute_feedback(guess, c) for c in candidates).values()
)
best_guess = min(candidates, key=worst_case)
```

**Minimax logic:** For every candidate guess `g`, the adversary picks the feedback pattern that leaves the most candidates remaining. We pick the `g` that minimises that adversarial worst case.

**Comparison with entropy:**

| Criterion | Optimises | Good for |
|-----------|----------|---------|
| Minimax (BFS) | Worst-case partition | Guaranteed upper bound on guesses |
| Entropy | Expected partition quality | Average-case performance |

**Result:** ~4.79 avg with median 5.0 — strong worst-case protection, but entropy wins on average since it's not optimising for average.

---

## 16. `genetic.py` — Evolutionary Algorithm

**Analogy:** Natural selection applied to guess selection. A *population* of candidate guesses "evolves" over several generations toward high-entropy choices.

**Each individual:** A word from the remaining candidate set.
**Fitness:** Shannon entropy of that word against remaining candidates.

**Evolution loop per turn:**
```
1. Initialise: random sample of 20 candidates
2. for 6 generations:
   a. Evaluate: compute entropy(individual) for each word
   b. Select: tournament selection (best of 3 random individuals)
   c. Crossover: uniform character-level crossover between 2 parents
   d. Repair: map offspring to nearest valid candidate (by position overlap)
   e. Mutate: with 25% probability, replace with random candidate
   f. Elitism: always keep the best individual from last generation
3. Return best individual found across all generations
```

**Key mechanisms:**
- **Tournament selection** (K=3): pick the best of 3 random individuals — maintains selection pressure without premature convergence
- **Uniform crossover**: each character independently comes from parent 1 or parent 2 with equal probability
- **Repair step**: crossover/mutation can produce non-words; `_repair()` maps them to the closest valid candidate by character overlap
- **Elitism**: the best individual always survives — prevents losing good solutions

**When GA is bypassed:** If candidates ≤ 20, exhaustive entropy evaluation beats evolution. If candidates > 300, greedy letter-frequency is used (GA adds little value over a random sample when the space is huge).

**Result:** ~4.76 avg — comparable to entropy because fitness is *entropy itself*. GA is essentially a stochastic entropy searcher.

---

## 17. `simulated_annealing.py` — SA over Entropy Landscape

**Analogy:** SA mimics the physical process of slowly cooling a metal. At high temperatures, atoms move freely (exploration). As it cools, they settle into a low-energy state (exploitation).

**Energy function:** `E(word) = −entropy(word, candidates)`. Minimising energy = maximising entropy.

**SA iteration:**
```
current = random candidate
for 40 steps (cooling from T=2.0 to T=0.05):
    neighbor = random candidate
    ΔE = energy(neighbor) - energy(current)
    if ΔE < 0 (neighbor is better):
        accept neighbor
    elif random() < exp(-ΔE / T) (Metropolis criterion):
        accept worse neighbor anyway
    T *= cooling_factor
return best seen across all steps
```

**The Metropolis criterion** is the key insight: accepting worse moves with probability `exp(-ΔE/T)` allows escaping local optima. At high T, almost any move is accepted (exploration). At low T, only improvements are accepted (exploitation).

**Cooling schedule:** `T` decreases geometrically from 2.0 to 0.05 over 40 steps, passing through a controlled transition from exploration to exploitation.

**Why SA over pure entropy:** SA occasionally accepts a word with slightly lower entropy that leads to a *better* partition structure on subsequent turns. This exploratory behavior is cheap with unlimited guesses.

**Result:** ~4.76 avg — tied with genetic, both slightly worse than pure entropy because they're stochastic approximations.

---

## 18. `beam_search.py` — 2-Level Lookahead

**Motivation:** Pure entropy is a *1-level greedy heuristic*. It picks the best guess for the *current* turn without considering what the next turn will look like.

**The problem with 1-level entropy:**
- A guess might have high entropy but leave one large "bad" partition
- Inside that bad partition, no second guess provides much information
- Pure entropy is blind to this; it only sees the first level

**Beam search solution:**
```
1. Phase 1: pick the top BEAM_WIDTH=5 candidates by 1-level entropy (the "beam")
2. Phase 2: for each beam candidate g:
      for each feedback partition p produced by g:
          find the best 1-level entropy guess within p
          weight by probability P(p) = |p| / |candidates|
      score(g) = ∑_p P(p) × best_entropy(p)
3. Return beam candidate with highest lookahead score
```

**Example where it helps:** Two guesses A and B have equal 1-level entropy. Guess A splits into partitions that each have a clear high-entropy follow-up. Guess B creates one large "stuck" partition with low next-level entropy. Beam search picks A; pure entropy is indifferent.

**Computational budget:**
- BEAM_WIDTH=5: only top-5 guesses are evaluated in depth
- EVAL_SAMPLE=80: entropy computed over a 80-word sample for speed
- PARTITION_EVAL=20: level-2 partitions sampled to ≤20 candidates

**Result:** ~4.85 avg — slightly better than most strategies but slower than pure entropy due to 2-level computation.

---

## 19. `beam_search_3.py` — 3-Level Lookahead

**Extension of beam_search.py:** Adds a third level of lookahead.

```
score(g) = ∑_p1 P(p1) × [∑_p2 P(p2|p1) × max_entropy(p2)]
```

The third level detects cases where a good-looking level-2 move still leads to a hard sub-partition on move 4.

**Tighter budget to compensate for depth:**
- BEAM_WIDTH=3 (vs 5)
- PARTITION_EVAL=15 (vs 20)
- SUB_PARTITION_EVAL=8

**Result:** ~4.82 avg — marginal improvement over 2-level (4.85) at ~2× the runtime. The law of diminishing returns: each additional lookahead level yields smaller gains because good candidates become obvious earlier.

---

---

# Part 5 — Hybrid / Multi-Phase Solvers

These solvers combine scripted opening moves with adaptive algorithms.

---

## 20. `two_phase.py` — Fixed Openers (CRANE+LOTUS) → Entropy

**Strategy:**
- **Move 1:** Always play CRANE (C, R, A, N, E)
- **Move 2:** Always play LOTUS (L, O, T, U, S)
- **Move 3+:** Shannon entropy over remaining candidates

**Letter coverage:** CRANE+LOTUS together cover A, C, E, L, N, O, R, S, T, U — 10 of the most frequent letters in English 5-letter words. After two openers, the candidate set typically narrows to <50 words.

**Why fixed openers?**
1. Computing entropy for 14,855 words on move 1 is expensive
2. A strong fixed opener avoids this cost with negligible quality loss
3. Two scripted moves ensure rich feedback before any adaptive computation begins
4. Mirrors competitive human strategy: many players use a fixed 2-word opener

**Why CRANE+LOTUS?** No shared letters (maximum coverage). The 10-letter scaffold eliminates large portions of the search space before entropy even starts.

**Result:** ~4.59 avg with lowest variance (1.83) — best overall solver. The combination of rich opening information and entropy-optimal play from move 3 is extremely effective.

---

## 21. `two_phase_tuned.py` — Fixed Openers (SLATE+CRONY) → Entropy

**Same architecture as two_phase.py, but with empirically selected openers.**

**Opener comparison results (800-word sample, seed 42):**

| Pair | Avg Attempts |
|------|-------------|
| SLATE+CRONY | 4.554 ← winner |
| CRANE+LOTUS | 4.573 |
| STARE+COULD | 4.574 |
| TRACE+BONUS | 4.604 |
| AUDIO+STERN | 4.656 |
| RAISE+CLOUT | 4.655 |
| AROSE+UNTIL | 4.678 |

**Why SLATE beats CRANE as the first word:** SLATE's letters sit at slightly more discriminating positions in the 14k-word list — SLATE produces more evenly-sized feedback partitions than CRANE on the full word list.

**Tournament result (300 words):** SLATE+CRONY wins 67 vs 63 games over CRANE+LOTUS, with average −0.03 attempts difference.

---

## 22. `vowel_first.py` — Vowel Openers → Positional Greedy

**Strategy:**
- **Move 1:** Always play ADIEU (tests A, D, I, E, U — 4 vowels)
- **Move 2:** If O is still unconfirmed, play STORY (tests S, T, O, R, Y — vowel O)
- **Move 3+:** Positional greedy with a bonus for confirmed-present vowels

**Rationale:** Every English word contains at least one vowel. Knowing which vowels are present immediately provides coarse-grained filtering applicable across *all* positions. This is different from consonant knowledge, which is position-specific.

**Vowel bonus in phase 2:**
```python
score(word) = positional_score(word) + 2 × (confirmed vowels in word)
```

The bonus encourages placing confirmed vowels at their correct positions, converting Y feedback (present, wrong place) into G feedback (correct place) faster.

**Difference from two_phase:**
- two_phase: agnostic about letter type, just picks high-entropy openers
- vowel_first: explicitly exploits the vowel/consonant structure of English

**Result:** ~4.92 avg — reasonable, but vowel openers (ADIEU, STORY) are not as information-dense as CRANE or SLATE.

---

---

# Part 6 — Key Concepts Summary

## Why Filtering Beats Everything Else

The constraint filter is so powerful that even *random* filtering achieves ~5.2 guesses:

```
No filter   → E[attempts] = N = 14,855   (geometric distribution)
No repeat   → E[attempts] = N/2 = 7,428  (uniform distribution)
With filter → E[attempts] ≈ 5.2          (exponential elimination)
```

The jump from 7,428 to 5.2 (a factor of ~1,400×) comes entirely from constraint propagation, with zero heuristic intelligence.

## The Information Theory Ladder

| Solver | What it optimises | Avg |
|--------|------------------|-----|
| Greedy | Most common letters (count) | 4.90 |
| Positional greedy | Most common letters (by position) | 5.11 |
| Expected remaining | Smallest average partition | 4.73 |
| Entropy | Most even partition (max info gain) | 4.68 |
| Beam search | Best *next* entropy choice too | 4.85 |
| Two-phase | Best fixed opener + entropy | **4.59** |

Two-phase wins not by smarter in-game reasoning, but by providing better *starting information* — the scripted openers give entropy a head start.

## Exploration vs Exploitation

| Solver | Mechanism | Balance |
|--------|-----------|---------|
| DFS | Certainty score | Pure exploitation |
| BFS/minimax | Worst-case bound | Pure exploitation |
| Entropy | Expected info gain | Pure exploitation |
| Simulated annealing | Metropolis criterion | Controlled |
| Genetic algorithm | Crossover + mutation | Controlled |
| Beam search | Lookahead | Lookahead exploitation |

All Wordle solvers lean toward exploitation because there is only one game tree to explore and unlimited guesses — exploration (trying unusual words to learn) is never worth it when you can always exploit known constraints.

## Stochastic vs Deterministic

| Type | Solvers | Implication |
|------|---------|-------------|
| Deterministic | sequential, greedy, positional_greedy, frequency_prior, statistical, bayesian, entropy, bfs, dfs, two_phase | Same result every run |
| Stochastic | random_filtered, simulated_annealing, genetic, beam_search, beam_search_3, expected_remaining (sampling) | Variance in results |

Stochastic solvers use randomness to escape the cost of exhaustive search. The benchmark uses a fixed seed to make comparisons fair.

## Hard Mode

In **hard mode**, every guess must use all previously revealed hints:
- **Green (G):** the same letter must appear at the same position
- **Yellow (Y):** that letter must appear somewhere in the guess

Hard mode forces solvers to always guess *consistent* candidates — they can never sacrifice a guess to probe new letters. This generally increases average guesses by 0.5–1.5 for entropy-based solvers because they can no longer play a high-information word that violates a known constraint.

Enable in play mode:
```bash
python run_wordle.py --play --hard
```

---

## Tournament Mode

Compare any two solvers head-to-head on the same set of words:
```bash
python run_wordle.py --tournament=algorithms/entropy.py,algorithms/two_phase.py --sample=500
```

Output includes:
- Per-solver averages, medians, variances
- Head-to-head win/loss/tie counts
- Average attempts difference

---

*Generated from `algorithms/` in the wordle_bench project.*
