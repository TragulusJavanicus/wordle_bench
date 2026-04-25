#!/usr/bin/env python3
"""Entry point for the Wordle Algorithm Playground.

Usage:
    python3 run_wordle.py --play
    python3 run_wordle.py --bench=submission/my_solver.py
    python3 run_wordle.py --leaderboard
    python3 run_wordle.py --leaderboard --filter-user=ADMIN
    python3 run_wordle.py --leaderboard --filter-solver=entropy.py
    python3 run_wordle.py --bench=submission/my_solver.py --user=ALICE --sample=500 --seed=7
"""

import sys
import os

# Add project root to path so all subpackages resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

from cli.main import main

if __name__ == "__main__":
    main()
