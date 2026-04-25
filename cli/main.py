"""CLI entry point: argument parsing and dispatch for play, bench, and leaderboard modes."""

import argparse
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# ANSI color helpers
# ---------------------------------------------------------------------------

_RESET = "\033[0m"
_COLORS = {
    "G": "\033[42m\033[97m",   # green background, white text
    "Y": "\033[43m\033[30m",   # yellow background, dark text
    "W": "\033[47m\033[30m",   # light-grey background, dark text
}


def _colored_feedback(guess: str, feedback: str, use_color: bool) -> str:
    """Return a visually formatted feedback string (colored or plain)."""
    if not use_color:
        return feedback

    parts = []
    for ch, fb in zip(guess.upper(), feedback):
        parts.append(f"{_COLORS[fb]} {ch} {_RESET}")
    return " ".join(parts)


def _supports_color() -> bool:
    """Detect whether the terminal is likely to render ANSI codes."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# ---------------------------------------------------------------------------
# Word list loader
# ---------------------------------------------------------------------------

def _load_word_list(project_root: str) -> list[str]:
    path = os.path.join(project_root, "valid-wordle-words.txt")
    if not os.path.exists(path):
        sys.exit(f"[ERROR] Word list not found: {path}")
    with open(path, encoding="utf-8") as f:
        words = [w.strip().upper() for w in f if len(w.strip()) == 5]
    if not words:
        sys.exit("[ERROR] Word list is empty or has no 5-letter words.")
    return words


# ---------------------------------------------------------------------------
# Play mode
# ---------------------------------------------------------------------------

def run_play(config: dict, word_list: list[str], hard_mode: bool = False) -> None:
    from core.engine import WordleEngine
    from core.scorer import compute_score

    use_color = config["color"] and _supports_color()
    engine = WordleEngine(word_list, hard_mode=hard_mode)
    engine.new_game()
    if hard_mode:
        print("\n  [HARD MODE] Every revealed hint must be used in subsequent guesses.")

    print("\n  Wordle  —  guess the 5-letter word  (type EXIT to quit)\n")

    while not engine.solved:
        try:
            raw = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return

        if raw.upper() == "EXIT":
            print(f"The word was: {engine.target}")
            return

        feedback, error = engine.guess(raw)
        if error:
            print(f"  [!] {error}")
            continue

        print("  " + _colored_feedback(raw.upper(), feedback, use_color))

        if engine.solved:
            score = compute_score(len(word_list), engine.attempts)
            print(f"\n  Solved in {engine.attempts} guess{'es' if engine.attempts != 1 else ''}!")
            print(f"  Score: {score}  (word list size {len(word_list)} − {engine.attempts} attempts)\n")


# ---------------------------------------------------------------------------
# Bench mode (single solver)
# ---------------------------------------------------------------------------

# Excluded from --bench=all: brute_force would run for hours (~7,428 avg guesses),
# deterministic takes ~20-26 guesses and skews the comparison table.
# Benchmark them individually with a small --sample.
# _SLOW_SOLVERS = {"brute_force.py", "deterministic.py"}
_SLOW_SOLVERS = {}


def _collect_algo_files(project_root: str) -> list[str]:
    """Return sorted list of all solver .py files in algorithms/ (excludes slow solvers)."""
    algo_dir = Path(project_root) / "algorithms"
    return sorted(
        str(p) for p in algo_dir.glob("*.py")
        if p.name != "__init__.py" and p.name not in _SLOW_SOLVERS
    )


def _resolve_solver_paths(bench_arg: str, project_root: str) -> list[str]:
    """Expand bench_arg to a list of solver file paths.

    Supports:
      all            -> all algorithms/*.py files
      algorithms/    -> all .py files in that directory
      <file.py>      -> single file (existing behaviour)
    """
    if bench_arg.lower() == "all":
        return _collect_algo_files(project_root)

    path = Path(bench_arg)
    if path.is_dir():
        return sorted(str(p) for p in path.glob("*.py") if p.name != "__init__.py")

    return [bench_arg]


def run_bench(
    solver_path: str,
    config: dict,
    word_list: list[str],
    cli_overrides: dict,
    *,
    quiet: bool = False,
) -> dict | None:
    """Benchmark a single solver.  Returns the metrics dict (for bulk mode)."""
    from bench.runner import run_benchmark
    from bench.metrics import compute_metrics
    from utils.logger import save_score, build_score_entry

    sample_size = cli_overrides.get("sample_size") or config["sample_size"]
    seed = cli_overrides.get("seed") or config["seed"]
    user = cli_overrides.get("user") or config["user"]

    solver_name = Path(solver_path).name

    if not quiet:
        print(f"\n  Benchmarking '{solver_name}' for user '{user}'")
        print(f"  Sample: {sample_size} words  |  Seed: {seed}\n")

    def progress(done: int, total: int) -> None:
        if quiet:
            return
        bar_len = 30
        filled = int(bar_len * done / total)
        bar = "#" * filled + "." * (bar_len - filled)
        print(f"\r  [{bar}] {done}/{total}", end="", flush=True)

    try:
        results, elapsed, peak_mb = run_benchmark(
            solver_path, word_list, sample_size, seed, user, progress_cb=progress
        )
    except (FileNotFoundError, AttributeError) as exc:
        print(f"\n  [ERROR] {solver_name}: {exc}")
        return None
    except Exception as exc:
        print(f"\n  [ERROR] {solver_name}: {exc}")
        return None

    if not quiet:
        print()  # newline after progress bar

    error_results = [r for r in results if "error" in r]
    metrics = compute_metrics(results)
    entry = build_score_entry(user, solver_path, metrics, elapsed, peak_mb)
    save_score(entry)

    if not quiet:
        print()
        print("  === BENCH RESULT ===")
        print(f"  User:    {user}")
        print(f"  Solver:  {solver_name}")
        print()
        print(f"  Sample Size:   {len(results)}")
        print()
        print(f"  Avg Attempts:  {metrics['avg_attempts']:.2f}")
        print(f"  Median:        {metrics['median_attempts']}")
        print(f"  Variance:      {metrics['variance']:.4f}")
        print()
        print(f"  Avg Score:     {metrics['avg_score']:.0f}")
        print(f"  Execution Time:{elapsed:.2f}s")
        print(f"  Peak Memory:   {peak_mb:.1f} MB")

        if error_results:
            errors = [f"{r['target']}: {r['error']}" for r in error_results[:5]]
            print()
            print(f"  Errors ({len(error_results)} games failed):")
            for e in errors:
                print(f"    - {e}")
            if len(error_results) > 5:
                print(f"    ... and {len(error_results) - 5} more")

        print()

    return {"solver": solver_name, "metrics": metrics, "elapsed": elapsed, "peak_mb": peak_mb}


# ---------------------------------------------------------------------------
# Bench mode (all solvers)
# ---------------------------------------------------------------------------

def run_bench_all(
    solver_paths: list[str],
    config: dict,
    word_list: list[str],
    cli_overrides: dict,
) -> None:
    """Run every solver in solver_paths and print a ranked comparison table."""
    sample_size = cli_overrides.get("sample_size") or config["sample_size"]
    seed = cli_overrides.get("seed") or config["seed"]
    user = cli_overrides.get("user") or config["user"]

    total = len(solver_paths)
    print(f"\n  Running {total} solvers | user: {user} | sample: {sample_size} | seed: {seed}\n")
    print(f"  {'Solver':<28} {'Progress':<34} {'Avg Att':>8} {'Time':>7}")
    print("  " + "-" * 80)

    rows: list[dict] = []

    for solver_path in solver_paths:
        solver_name = Path(solver_path).name
        print(f"  {solver_name:<28} ", end="", flush=True)

        from bench.runner import run_benchmark
        from bench.metrics import compute_metrics
        from utils.logger import save_score, build_score_entry

        def progress(done: int, total_words: int) -> None:
            bar_len = 20
            filled = int(bar_len * done / total_words)
            bar = "#" * filled + "." * (bar_len - filled)
            print(f"\r  {solver_name:<28} [{bar}] {done}/{total_words}", end="", flush=True)

        try:
            results, elapsed, peak_mb = run_benchmark(
                solver_path, word_list, sample_size, seed, user, progress_cb=progress
            )
        except Exception as exc:
            print(f"\r  {solver_name:<28} [ERROR] {exc}")
            rows.append({"solver": solver_name, "failed": True})
            continue

        metrics = compute_metrics(results)
        entry = build_score_entry(user, solver_path, metrics, elapsed, peak_mb)
        save_score(entry)
        rows.append({
            "solver": solver_name,
            "metrics": metrics,
            "elapsed": elapsed,
            "peak_mb": peak_mb,
            "failed": False,
        })
        print(
            f"\r  {solver_name:<28} {'done':<34} "
            f"{metrics['avg_attempts']:>8.2f} {elapsed:>6.1f}s"
        )

    # Summary table sorted by avg_attempts ascending (fewer guesses = better)
    good_rows = [r for r in rows if not r.get("failed")]
    good_rows.sort(key=lambda r: r["metrics"]["avg_attempts"])

    print()
    print("  === COMPARISON (sorted by avg attempts) ===")
    print()
    hdr = f"  {'#':<4} {'Solver':<28} {'Avg Att':>8} {'Median':>7} {'Variance':>9} {'Avg Score':>10} {'Time':>7} {'Mem MB':>7}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    for rank, r in enumerate(good_rows, 1):
        m = r["metrics"]
        print(
            f"  {rank:<4} {r['solver']:<28} "
            f"{m['avg_attempts']:>8.2f} {m['median_attempts']:>7} "
            f"{m['variance']:>9.4f} {m['avg_score']:>10.0f} "
            f"{r['elapsed']:>6.1f}s {r['peak_mb']:>7.1f}"
        )

    for r in rows:
        if r.get("failed"):
            print(f"  ---- {r['solver']:<28} FAILED")

    print()


# ---------------------------------------------------------------------------
# Tournament mode (head-to-head)
# ---------------------------------------------------------------------------

def run_tournament(
    solver_path_a: str,
    solver_path_b: str,
    config: dict,
    word_list: list[str],
    cli_overrides: dict,
) -> None:
    """Run two solvers against the same sample and print head-to-head stats."""
    from bench.runner import run_benchmark
    from bench.metrics import compute_metrics

    sample_size = cli_overrides.get("sample_size") or config["sample_size"]
    seed = cli_overrides.get("seed") or config["seed"]
    user = cli_overrides.get("user") or config["user"]

    name_a = Path(solver_path_a).name
    name_b = Path(solver_path_b).name

    print(f"\n  TOURNAMENT  |  user: {user}  |  sample: {sample_size}  |  seed: {seed}")
    print(f"\n  {name_a}  vs  {name_b}\n")

    def _run(path, label):
        print(f"  Running {label}...", end="", flush=True)

        def prog(done, total):
            bar = "#" * int(20 * done / total) + "." * (20 - int(20 * done / total))
            print(f"\r  Running {label}... [{bar}] {done}/{total}", end="", flush=True)

        results, elapsed, _ = run_benchmark(path, word_list, sample_size, seed, user, progress_cb=prog)
        print()
        return results, elapsed

    results_a, time_a = _run(solver_path_a, name_a)
    results_b, time_b = _run(solver_path_b, name_b)

    # Align by target word
    by_target_a = {r["target"]: r for r in results_a}
    by_target_b = {r["target"]: r for r in results_b}
    shared = sorted(set(by_target_a) & set(by_target_b))

    wins_a = wins_b = ties = 0
    diffs = []
    for target in shared:
        att_a = by_target_a[target]["attempts"]
        att_b = by_target_b[target]["attempts"]
        diffs.append(att_a - att_b)
        if att_a < att_b:
            wins_a += 1
        elif att_b < att_a:
            wins_b += 1
        else:
            ties += 1

    metrics_a = compute_metrics(results_a)
    metrics_b = compute_metrics(results_b)
    avg_diff = sum(diffs) / len(diffs) if diffs else 0.0

    print()
    print("  === TOURNAMENT RESULT ===")
    print()
    hdr = f"  {'Metric':<22} {name_a:>24} {name_b:>24}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    rows = [
        ("Avg Attempts",    f"{metrics_a['avg_attempts']:.4f}",   f"{metrics_b['avg_attempts']:.4f}"),
        ("Median",          f"{metrics_a['median_attempts']}",     f"{metrics_b['median_attempts']}"),
        ("Variance",        f"{metrics_a['variance']:.4f}",        f"{metrics_b['variance']:.4f}"),
        ("Time",            f"{time_a:.1f}s",                      f"{time_b:.1f}s"),
    ]
    for label, va, vb in rows:
        print(f"  {label:<22} {va:>24} {vb:>24}")

    total = wins_a + wins_b + ties
    print()
    print(f"  Head-to-head ({total} shared words):")
    print(f"    {name_a} wins: {wins_a}  ({100*wins_a/total:.1f}%)")
    print(f"    {name_b} wins: {wins_b}  ({100*wins_b/total:.1f}%)")
    print(f"    Ties:          {ties}  ({100*ties/total:.1f}%)")
    diff_sign = "+" if avg_diff > 0 else ""
    print(f"    Avg diff ({name_a} - {name_b}): {diff_sign}{avg_diff:.4f} attempts")

    winner = name_a if metrics_a["avg_attempts"] < metrics_b["avg_attempts"] else name_b
    if metrics_a["avg_attempts"] == metrics_b["avg_attempts"]:
        winner = "Tie"
    print(f"\n  Winner: {winner}\n")


# ---------------------------------------------------------------------------
# Leaderboard mode
# ---------------------------------------------------------------------------

def run_leaderboard(user: str | None, solver: str | None) -> None:
    from utils.logger import get_leaderboard

    scores = get_leaderboard(user=user, solver=solver)

    title = "  LEADERBOARD"
    if user:
        title += f"  (user: {user})"
    if solver:
        title += f"  (solver: {solver})"
    print(f"\n{title}\n")

    if not scores:
        print("  No scores recorded yet.")
        print()
        return

    header = f"  {'#':<4} {'User':<12} {'Solver':<22} {'Avg Score':>10} {'Avg Att':>8} {'Median':>7} {'Var':>7} {'Time':>7} {'Mem MB':>7}  {'Timestamp'}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for rank, s in enumerate(scores, 1):
        print(
            f"  {rank:<4} {s.get('user',''):<12} {s.get('solver',''):<22} "
            f"{s.get('avg_score', 0):>10.0f} {s.get('avg_attempts', 0):>8.2f} "
            f"{s.get('median', 0):>7} {s.get('variance', 0):>7.4f} "
            f"{s.get('time', 0):>7.2f} {s.get('memory', 0):>7.1f}  "
            f"{s.get('timestamp', '')}"
        )
    print()


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="run_wordle.py",
        description="Wordle Algorithm Playground - play, bench, or view scores.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--play", action="store_true", help="Play Wordle interactively.")
    group.add_argument(
        "--bench",
        metavar="SOLVER_PATH|all",
        help=(
            "Benchmark a solver file, a directory of solvers, or 'all' to run "
            "every built-in algorithm and print a ranked comparison table."
        ),
    )
    group.add_argument("--leaderboard", action="store_true", help="Show high-score leaderboard.")
    group.add_argument(
        "--tournament",
        metavar="SOLVER_A,SOLVER_B",
        help="Head-to-head comparison of two solvers against the same sample.",
    )

    parser.add_argument("--hard", action="store_true", help="Enable hard mode (play mode only).")
    parser.add_argument("--user", metavar="NAME", help="Override USER in config (bench mode).")
    parser.add_argument("--sample", type=int, metavar="N", help="Override SAMPLE_SIZE (bench mode).")
    parser.add_argument("--seed", type=int, metavar="N", help="Override random seed (bench mode).")
    parser.add_argument("--filter-user", metavar="NAME", help="Filter leaderboard by user.")
    parser.add_argument("--filter-solver", metavar="FILE", help="Filter leaderboard by solver name.")

    args = parser.parse_args()

    # Locate project root (directory containing run_wordle.py)
    project_root = str(Path(__file__).parent.parent.resolve())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from utils.config import load_config, get_play_config, get_bench_config
    cfg = load_config()

    word_list = _load_word_list(project_root)

    if args.play:
        play_cfg = get_play_config(cfg)
        run_play(play_cfg, word_list, hard_mode=args.hard)

    elif args.tournament:
        bench_cfg = get_bench_config(cfg)
        overrides = {"user": args.user, "sample_size": args.sample, "seed": args.seed}
        parts = args.tournament.split(",", 1)
        if len(parts) != 2:
            sys.exit("[ERROR] --tournament expects two comma-separated solver paths.")
        run_tournament(parts[0].strip(), parts[1].strip(), bench_cfg, word_list, overrides)

    elif args.bench:
        bench_cfg = get_bench_config(cfg)
        overrides = {
            "user": args.user,
            "sample_size": args.sample,
            "seed": args.seed,
        }
        solver_paths = _resolve_solver_paths(args.bench, project_root)
        if len(solver_paths) == 1:
            run_bench(solver_paths[0], bench_cfg, word_list, overrides)
        else:
            run_bench_all(solver_paths, bench_cfg, word_list, overrides)

    elif args.leaderboard:
        run_leaderboard(user=args.filter_user, solver=args.filter_solver)
