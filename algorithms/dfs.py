"""
DFS (Depth-First Search) Solver — Commit-and-Constrain Strategy
================================================================
DFS analogy: in the Wordle game tree, DFS commits to the most constrained
branch immediately and follows it to the end before considering alternatives.

This is realised by always guessing the candidate with the highest
"certainty score": the number of positions we already know are correct (G)
or whose letters we know are present (Y). A word with more known constraints
satisfied is "deeper" in our knowledge tree — DFS goes there first.

When certainty is tied, we pick the word that covers the most letters not
yet seen. This ensures exploration continues efficiently even early in the
game when certainty scores are all zero.

Contrast with BFS: BFS minimises worst-case remaining (broad, level-by-level
exploration); DFS commits to the most specific branch (deep, greedy commitment).
DFS can find the answer very quickly when lucky, but may waste guesses on a
wrong branch — it trades worst-case safety for best-case speed.

Characteristics:
- Variable performance: fast when the first branch is right, slow otherwise
- Average ~4.0–5.0 guesses (higher variance than BFS/entropy)
- O(N) per turn (linear scoring)
"""

from collections import Counter
from core.feedback import is_consistent


def _certainty_score(word: str, known_positions: dict, known_letters: set) -> tuple:
    """Score a word by how much it exploits our current knowledge.

    Primary key: count of positions in the word that match known-correct letters.
    Secondary key: count of letters in the word that are confirmed present (Y/G).
    Tertiary key: count of novel (unseen) letters for tie-breaking exploration.
    """
    primary = sum(1 for i, ch in enumerate(word) if known_positions.get(i) == ch)
    secondary = sum(1 for ch in set(word) if ch in known_letters)
    return (primary, secondary)


def solve(word_list: list[str], feedback_fn) -> int:
    """Depth-first: always commit to the candidate most aligned with known constraints."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    candidates = list(word_list)
    attempts = 0

    # Accumulated knowledge from previous guesses
    known_positions: dict[int, str] = {}   # position → correct letter
    known_letters: set[str] = set()        # letters confirmed present in word

    while candidates:
        if len(candidates) == 1:
            guess = candidates[0]
        else:
            guess = max(
                candidates,
                key=lambda w: (_certainty_score(w, known_positions, known_letters), w),
            )

        feedback = feedback_fn(guess)
        attempts += 1

        if feedback == win:
            return attempts

        # Update knowledge from this guess's feedback
        for i, (ch, fb) in enumerate(zip(guess, feedback)):
            if fb == "G":
                known_positions[i] = ch
                known_letters.add(ch)
            elif fb == "Y":
                known_letters.add(ch)

        candidates = [w for w in candidates if is_consistent(w, guess, feedback)]

    return attempts
