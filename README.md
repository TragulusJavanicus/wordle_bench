# Wordle Algorithm Playground

A command-line Wordle game that doubles as an algorithm benchmarking platform.
Play unlimited games, submit your own solvers, compare performance, and climb the leaderboard.

---

## Features

- **Play Mode** — interactive Wordle with colored terminal feedback
- **Bench Mode** — benchmark one solver, a directory, or all built-ins at once
- **Leaderboard** — persistent high-score file, filterable by user or solver
- **20 built-in solvers** — from naive brute-force to two-phase entropy
- **CI/CD integration** — GitHub Actions auto-benchmarks every solver PR

---

## Quick Start

```bash
git clone <repo>
cd wordle-bench
python run_wordle.py --play
```

No third-party dependencies — pure Python 3.11+ stdlib.

---

## Play Mode

```bash
python run_wordle.py --play
```

```
  Wordle  —  guess the 5-letter word

>> ARISE
  W  Y  W  Y  Y
>> ROUTE
  G  W  Y  W  Y
>> REBUS
  G  G  G  G  G

  Solved in 3 guesses!
  Score: 14852  (word list size 14855 - 3 attempts)
```

**Feedback key:**

| Symbol | Meaning |
|--------|---------|
| `G` | Correct letter, correct position |
| `Y` | Correct letter, wrong position |
| `W` | Letter not in word |

**Score** = `len(word_list) − attempts`. Fewer guesses = higher score.

> **Why can scores go negative?**
> `brute_force.py` samples the full list *with replacement* — it can pick the same word
> multiple times, so it may take more than N attempts to stumble upon the answer.
> When `attempts > 14,855`, `score = 14,855 − attempts` goes negative.
> The random-start variant avoids this by shuffling once (no repeats), capping attempts at N.

---

## Bench Mode

### Single solver

```bash
python run_wordle.py --bench=algorithms/entropy.py
python run_wordle.py --bench=submission/my_solver.py --user=ALICE --sample=500 --seed=7
```

```
  Benchmarking 'entropy.py' for user 'ADMIN'
  Sample: 1000 words  |  Seed: 42

  [##############################] 1000/1000

  === BENCH RESULT ===
  User:    ADMIN
  Solver:  entropy.py

  Sample Size:   1000

  Avg Attempts:  4.68
  Median:        4.0
  Variance:      2.0797

  Avg Score:     14850
  Execution Time:255.7s
  Peak Memory:   2.1 MB
```

### Run all built-in algorithms at once

```bash
python run_wordle.py --bench=all
python run_wordle.py --bench=all --sample=200 --seed=99
```

### Run a directory of solvers

```bash
python run_wordle.py --bench=submission/
```

Benchmarks every `.py` file in `submission/` and prints the same ranked comparison table.

Each solver's result is also saved to `highscores.json` as it finishes.

---

## Leaderboard

```bash
python run_wordle.py --leaderboard
python run_wordle.py --leaderboard --filter-user=ADMIN
python run_wordle.py --leaderboard --filter-solver=entropy.py
```

---

## Benchmark Results

Full run: `--bench=all --sample=1000 --seed=42` against the 14,855-word list.

```
  #    Solver                        Avg Att  Median  Variance  Avg Score    Time  Mem MB
  ---------------------------------------------------------------------------------------
  1    two_phase.py                     4.59     4.0    1.8281      14850   61.2s     2.1
  2    entropy.py                       4.68     4.0    2.0797      14850  255.7s     2.1
  3    expected_remaining.py            4.73     4.0    2.4771      14850   90.0s     0.3
  4    genetic.py                       4.76     4.0    2.7422      14850  114.6s     0.3
  5    simulated_annealing.py           4.76     4.0    2.4609      14850   72.8s     0.3
  6    bfs.py                           4.79     5.0    2.3794      14850   77.5s     0.3
  7    beam_search.py                   4.85     5.0    2.4312      14850  190.0s     2.2
  8    statistical.py                   4.87     4.0    2.9670      14850  159.8s     0.3
  9    greedy.py                        4.90     5.0    2.5966      14850   92.9s     0.3
  10   vowel_first.py                   4.92     5.0    2.6060      14850   47.9s     1.5
  11   positional_greedy.py             5.11     5.0    2.7386      14850   80.8s     0.3
  12   frequency_prior.py               5.11     5.0    2.9059      14850  108.7s     0.3
  13   bayesian.py                      5.14     5.0    2.8668      14850   78.4s     0.4
  14   random_filtered.py               5.24     5.0    2.7041      14850   43.5s     0.4
  15   dfs.py                           5.57     5.0    2.5010      14849  108.4s     0.4
  16   sequential.py                    5.71     5.0    3.3873      14849   43.6s     0.3
  17   dictionary.py                   19.68    19.0   68.4757      14835   14.3s     0.8
  18   deterministic.py                21.34    21.0   12.2437      14834    0.4s     0.2
  19   brute_force_random_start.py   7452.18  7459.5     1.9e7       7403   26.8s     0.3
  20   brute_force.py               15071.28 10757.0     2.2e8       -216   48.6s     0.2
```

**Key takeaways:**

- `two_phase.py` is the top performer: CRANE+LOTUS openers give rich early signal, then entropy finishes the job. Best avg (4.59) *and* lowest variance (1.83) — the most consistent solver.
- `entropy.py` is 2nd in avg attempts but 4× slower than two_phase, since it computes entropy from scratch on move 1.
- `brute_force.py` can go **negative score** — it samples with replacement so it sometimes exceeds 14,855 attempts. `brute_force_random_start.py` shuffles once (no repeats) and halves expected attempts to ~7,428.
- The jump from rank 16 (`sequential`, 5.71) to rank 17 (`dictionary`, 19.68) marks the gap between *filtered* solvers (use feedback to prune candidates) and *unfiltered* ones (iterate blindly).

---

## Built-in Algorithms

| # | File | Strategy | Category |
|---|------|----------|----------|
| 1 | `two_phase.py` | Fixed openers (CRANE+LOTUS), then entropy | Hybrid |
| 2 | `entropy.py` | Shannon entropy maximization | Information-theoretic |
| 3 | `expected_remaining.py` | Minimize expected candidate count (Σn²/N) | Information-theoretic |
| 4 | `genetic.py` | Evolutionary population, crossover + mutation | Metaheuristic |
| 5 | `simulated_annealing.py` | SA over entropy landscape | Metaheuristic |
| 6 | `bfs.py` | Minimax: minimize worst-case partition size | Minimax |
| 7 | `beam_search.py` | 2-level lookahead over top-5 entropy beam | Lookahead |
| 8 | `statistical.py` | Top-5 letter coverage → positional greedy | Statistical |
| 9 | `greedy.py` | Letter-frequency greedy over candidates | Greedy |
| 10 | `vowel_first.py` | Scripted vowel openers, then positional greedy | Hybrid |
| 11 | `positional_greedy.py` | Per-position letter frequency greedy | Greedy |
| 12 | `frequency_prior.py` | Fixed English letter frequency table | Prior-based |
| 13 | `bayesian.py` | Positional letter-frequency MAP estimate | Prior-based |
| 14 | `random_filtered.py` | Random pick from remaining candidates | Random |
| 15 | `dfs.py` | Commit to most-constrained candidate (DFS) | Search |
| 16 | `sequential.py` | Alphabetical scan with filtering | Naive |
| 17 | `dictionary.py` | Alphabetical scan, no filtering | Naive |
| 18 | `deterministic.py` | Fixed alphabetical order, no heuristic | Naive |
| 19 | `brute_force_random_start.py` | Shuffle once, iterate — no filtering | Brute-force |
| 20 | `brute_force.py` | Random pick with replacement — no filtering | Brute-force |

> **Note on word list size:** Results are for the full 14,855-word list.
> Classic Wordle uses only 2,315 answer words where entropy achieves ~3.4–3.6.
> With 14,855 words, the information needed is log₂(14,855) ≈ 13.9 bits
> vs log₂(2,315) ≈ 11.2 bits, so all solvers need roughly 2 extra guesses on average.

> **Slow solvers:** `brute_force.py` and `brute_force_random_start.py` take thousands of
> guesses per word. Use `--sample=10` when testing them individually.

---

## Writing Your Own Solver

Create a file anywhere (e.g. `submission/my_solver.py`) and implement:

```python
def solve(word_list: list[str], feedback_fn) -> int:
    """
    Returns the number of guesses used to find the correct word.

    feedback_fn(guess: str) -> str
        Call with a 5-letter word from word_list.
        Returns a G/Y/W string (e.g. "GYYWW").
        Keep guessing until you receive "GGGGG".
    """
    win = "G" * len(word_list[0])
    # your algorithm here
    ...
```

Then benchmark it:

```bash
python run_wordle.py --bench=submission/my_solver.py
```

See [submission/dictionary.py](submission/dictionary.py) for a fully-commented template.

---

## Configuration

Edit `config.ini`:

```ini
[PLAY]
COLOR = True          # Colored terminal output

[BENCH]
SAMPLE_SIZE = 1000    # Words per benchmark run
USER = ADMIN          # Your leaderboard name
SEED = 42             # Reproducible random sampling
```

CLI flags override config values:

```bash
python run_wordle.py --bench=all --user=BOB --sample=500 --seed=7
```

---

## Project Structure

```
wordle_bench/
├── run_wordle.py            # Entry point
├── config.ini               # User configuration
├── highscores.json          # Persistent leaderboard data
├── valid-wordle-words.txt   # 14,855 valid 5-letter words
│
├── core/
│   ├── engine.py            # Wordle game engine (play mode)
│   ├── feedback.py          # G/Y/W computation
│   └── scorer.py            # Score formula
│
├── cli/
│   └── main.py              # Argument parsing, mode dispatch
│
├── bench/
│   ├── runner.py            # Benchmark execution, timeout handling
│   └── metrics.py           # Stats: mean, median, variance
│
├── algorithms/              # 20 built-in reference solvers
│   ├── two_phase.py         # Best: fixed openers + entropy
│   ├── entropy.py           # Shannon entropy maximization
│   ├── expected_remaining.py   # Minimize E[candidates remaining]
│   ├── beam_search.py       # 2-level entropy lookahead
│   ├── statistical.py       # Top-5 letter coverage + positional
│   ├── simulated_annealing.py  # SA over entropy landscape
│   ├── genetic.py           # Evolutionary GA
│   ├── bfs.py               # BFS minimax worst-case
│   ├── greedy.py            # Letter-frequency greedy
│   ├── vowel_first.py       # Scripted vowel openers + greedy
│   ├── positional_greedy.py # Per-position frequency greedy
│   ├── frequency_prior.py   # Fixed English frequency table
│   ├── bayesian.py          # Bayesian positional prior
│   ├── random_filtered.py   # Random pick from candidates
│   ├── dfs.py               # DFS commit-and-constrain
│   ├── sequential.py        # Alphabetical scan with filtering
│   ├── dictionary.py        # Alphabetical scan, no filtering
│   ├── deterministic.py     # Fixed order, no heuristic
│   ├── brute_force_random_start.py  # Shuffle once, no filtering
│   └── brute_force.py       # Random with replacement, no filtering
│
├── utils/
│   ├── config.py            # config.ini loader
│   ├── logger.py            # highscores.json read/write
│   └── memory.py            # tracemalloc wrapper
│
├── submission/              # Drop your solver here
│   └── dictionary.py        # Template / example
│
└── .github/workflows/
    └── benchmark.yml        # CI: auto-bench on submission PR
```

---

## CI/CD

Any pull request touching `submission/` triggers an automatic benchmark.
Results are posted as a PR comment and the workflow fails if the solver
crashes or averages more than 15 guesses.

See [.github/workflows/benchmark.yml](.github/workflows/benchmark.yml).

