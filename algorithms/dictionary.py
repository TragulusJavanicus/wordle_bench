"""
Dictionary Solver — Letter-by-Letter Position Probing
=======================================================
Strategy: solve the word one position at a time, left to right.

For each position 0–4 (in order):
  Try letters A, B, C, … Z in that slot.
  For each letter, find a valid word from the word list that has that
  letter at the target position AND has all already-confirmed letters
  in their confirmed positions.
  Guess the word; if position `pos` comes back G, that slot is confirmed
  and we move to the next position.

Key property — IGNORES Y and W signals:
  A smart solver uses every piece of feedback simultaneously (G, Y, W)
  to constrain all five positions at once.  This solver is intentionally
  dumb: it only acts on G responses and discards the rich information
  that Y ("present but misplaced") and W ("absent") provide.
  It discovers the word one slot at a time, like solving a crossword
  column by column while ignoring the row clues.

Free G bonus:
  Although we ignore Y and W, we DO collect G feedback from ALL five
  positions in every guess — not just the position we're currently probing.
  Lucky alignment means earlier guesses can confirm later positions for
  free, reducing the total guess count.

Comparison to neighbours:
  sequential.py  — alphabetical scan WITH full feedback filtering (~5.5–6.5 guesses)
  dictionary.py  — THIS FILE — position probe, ignores Y/W  (~15–30 guesses)
  deterministic.py — "AAAAA"…"ZZZZZ", ignores ALL positions (~20–27 guesses)

Characteristics:
- Deterministic (same result for same word list and target)
- Average ~15–30 guesses per game (much worse than sequential)
- Shows the cost of discarding partial-match (Y) information
"""

from collections import defaultdict
from core.feedback import is_consistent

# Module-level position index: _pos_index[i][letter] = [words with letter at pos i]
# Built once per word list (cached by list identity).
_pos_index: dict | None = None
_cached_list_id: int = 0


def _ensure_index(word_list: list[str]) -> None:
    global _pos_index, _cached_list_id
    if id(word_list) == _cached_list_id:
        return
    idx: dict = defaultdict(lambda: defaultdict(list))
    for word in word_list:
        for i, ch in enumerate(word):
            idx[i][ch].append(word)
    _pos_index = idx
    _cached_list_id = id(word_list)


def _find_probe(pos: int, letter: str, known: dict[int, str]) -> str | None:
    """Return the first word with `letter` at `pos` that satisfies all known positions."""
    assert _pos_index is not None
    for word in _pos_index[pos].get(letter, []):
        if all(word[p] == l for p, l in known.items()):
            return word
    return None


def solve(word_list: list[str], feedback_fn) -> int:
    """Probe each position left-to-right, trying A–Z until G is confirmed per slot."""
    _ensure_index(word_list)

    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    known: dict[int, str] = {}
    attempts = 0

    for pos in range(word_length):
        if pos in known:
            continue  # already confirmed by a previous probe's G in another slot

        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            probe = _find_probe(pos, letter, known)
            if probe is None:
                continue  # no valid word has this letter at this pos with current constraints

            feedback = feedback_fn(probe)
            attempts += 1

            if feedback == win:
                return attempts

            # Collect G from ALL positions — free information we'd be foolish to waste
            # (We still ignore Y and W, which is what makes this solver "dumb")
            for i, (ch, fb) in enumerate(zip(probe, feedback)):
                if fb == "G":
                    known[i] = ch

            if pos in known:
                break  # this position confirmed, move to next

    # Fallback: if any positions are still unknown (edge case with unusual word lists),
    # fall back to a filtered alphabetical scan over matching candidates.
    if len(known) < word_length:
        candidates = [w for w in word_list if all(w[p] == l for p, l in known.items())]
        while candidates:
            guess = candidates[0]
            fb = feedback_fn(guess)
            attempts += 1
            if fb == win:
                return attempts
            candidates = [w for w in candidates if is_consistent(w, guess, fb)]

    return attempts
