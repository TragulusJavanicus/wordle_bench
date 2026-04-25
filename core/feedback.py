"""Wordle feedback computation: G (correct position), Y (wrong position), W (not in word)."""


def compute_feedback(guess: str, target: str) -> str:
    """Return the G/Y/W feedback string for a guess against a target word.

    Uses standard Wordle rules: exact matches (G) are resolved first,
    then remaining letters are checked for presence elsewhere (Y vs W).
    Handles duplicate letters correctly via slot-by-slot accounting.
    """
    guess = guess.upper()
    target = target.upper()
    length = len(guess)
    result = ["W"] * length
    target_remaining = list(target)

    # First pass: exact matches
    for i in range(length):
        if guess[i] == target[i]:
            result[i] = "G"
            target_remaining[i] = None

    # Second pass: wrong-position matches
    for i in range(length):
        if result[i] == "G":
            continue
        if guess[i] in target_remaining:
            result[i] = "Y"
            target_remaining[target_remaining.index(guess[i])] = None

    return "".join(result)


def is_consistent(word: str, guess: str, feedback: str) -> bool:
    """Return True if word is consistent with the feedback received for a guess.

    Simulates what feedback we'd get if word were the target, and checks
    whether it matches the actual feedback. This is the canonical filter step
    used by all solvers to prune the candidate set after each guess.
    """
    return compute_feedback(guess, word) == feedback
