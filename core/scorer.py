"""Score calculation: rewards solving in fewer attempts against a large word space."""


def compute_score(word_list_length: int, attempts: int) -> int:
    """Return score as word_list_length minus attempts used.

    A higher score means fewer guesses were needed. This rewards efficient
    solvers relative to the total size of the search space.
    """
    return word_list_length - attempts
