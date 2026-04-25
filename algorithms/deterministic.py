"""
Deterministic Solver — Single-Letter Probing (max 27 guesses)
==============================================================
Strategy: probe every letter in the alphabet using a repeated-letter
"word" (AAAAA, BBBBB, …, ZZZZZ), then assemble and guess the answer.

How it works
-------------
For each letter X in A–Z (in order):
  Guess "XXXXX" (five copies of X).
  Because every character is the same, the only possible feedback values
  per position are:
    G — target[i] == X  (exact match)
    W — X does not appear at position i (given remaining unmatched letters)
  Y is NEVER produced: any X in the target that would be a Y is already
  accounted for by the G positions, so non-G positions always get W.

  So "XXXXX" unambiguously identifies EVERY position that contains X.

After probing all 26 letters, every position in the target word has been
identified at least once (when its letter's probe ran).  We then assemble
the word from our confirmed-position dictionary and submit it as the final
guess.

Example: target = "CRANE"
  AAAAA → WWWGW  (A is at position 3)  → known = {3: A}
  BBBBB → WWWWW  (B not in word)
  CCCCC → GWWWW  (C is at position 0)  → known = {0: C, 3: A}
  ...
  EEEEE → WWWWG  (E is at position 4)  → known = {0:C, 3:A, 4:E}
  ...
  NNNNN → WWWWW  (wait, N IS in CRANE at pos 3)

  Hmm, let me redo: CRANE = C-R-A-N-E
  AAAAA → WWGWW  (A at pos 2)
  CCCCC → GWWWW  (C at pos 0)
  EEEEE → WWWWG  (E at pos 4)
  NNNNN → WWWGW  (N at pos 3)
  RRRRR → WGWWW  (R at pos 1)
  → All 5 positions confirmed after 5 informative probes
  → Final guess: CRANE  → total = 22 probes (A–R) + 1 final = 23 attempts

Early termination
-----------------
As soon as all five positions are confirmed, we stop probing and submit the
assembled answer immediately — no need to continue through the rest of A–Z.

Worst case
----------
A word whose five distinct letters are all near the end of the alphabet
(e.g. a word containing V, W, X, Y, Z) requires 26 probes + 1 final = 27
attempts.

Average case
------------
For a uniform distribution of English letters, the expected position in the
alphabet of the last needed letter is roughly the 24th–25th letter, giving
an average of ~20–25 probes + 1 = ~21–26 attempts.

Why this is interesting
-----------------------
  - Provably correct and fully deterministic: NO feedback-dependency at all
    during the probe phase.  The probe sequence is always A, B, C, …, Z
    regardless of what feedback says.
  - Guaranteed termination in ≤ 27 guesses for any 5-letter target.
  - Uses non-dictionary words ("AAAAA" etc.) — valid in bench mode because
    the feedback function does not validate guesses against the word list.
    In interactive play mode these would be rejected.
  - Demonstrates that even with ZERO adaptive intelligence, a structured
    probing strategy bounds the worst case to a constant (27).

Comparison:
  brute_force.py    — random, no filtering, no structure → ~7,428 avg guesses
  deterministic.py  — THIS FILE — structured probing, no filtering → ≤ 27 guesses
  sequential.py     — alphabetical + filtering → ~5.5–6.5 guesses
"""

from core.feedback import is_consistent


def solve(word_list: list[str], feedback_fn) -> int:
    """Probe A–Z with repeated-letter words; assemble and guess the target."""
    word_length = len(word_list[0]) if word_list else 5
    win = "G" * word_length
    known: dict[int, str] = {}  # position → confirmed letter
    attempts = 0

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if len(known) == word_length:
            break  # all positions confirmed; no need to probe further

        probe = letter * word_length  # e.g. "AAAAA", "BBBBB", …
        feedback = feedback_fn(probe)
        attempts += 1

        if feedback == win:
            return attempts  # only possible if the target itself is all one letter

        # "XXXXX" feedback: G means target[i] == X; W means it doesn't.
        # Y cannot appear (see docstring), so we only need to check for G.
        for i, fb in enumerate(feedback):
            if fb == "G":
                known[i] = letter

    # All 5 positions are now confirmed.  Assemble and submit the answer.
    if len(known) == word_length:
        final = "".join(known[i] for i in range(word_length))
        feedback = feedback_fn(final)
        attempts += 1
        if feedback == win:
            return attempts

    # Fallback: if the assembled word isn't in the word list (shouldn't happen
    # for a clean 5-letter word list), try remaining consistent candidates.
    candidates = [w for w in word_list if all(w[p] == l for p, l in known.items())]
    while candidates:
        guess = candidates[0]
        fb = feedback_fn(guess)
        attempts += 1
        if fb == win:
            return attempts
        candidates = [w for w in candidates if is_consistent(w, guess, fb)]

    return attempts
