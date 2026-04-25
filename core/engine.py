"""Wordle game engine: manages game state for interactive play mode."""

import random
from .feedback import compute_feedback


class WordleEngine:
    """Manages a single Wordle game session."""

    def __init__(self, word_list: list[str], word_length: int = 5, hard_mode: bool = False):
        self.word_list = [w.strip().upper() for w in word_list if len(w.strip()) == word_length]
        self.word_set = set(self.word_list)
        self.word_length = word_length
        self.hard_mode = hard_mode
        self.target: str = ""
        self.attempts: int = 0
        self.history: list[tuple[str, str]] = []  # (guess, feedback)
        self.solved: bool = False

    def new_game(self, target: str | None = None, seed: int | None = None) -> None:
        """Start a new game. Picks a random word unless target or seed is given."""
        if seed is not None:
            random.seed(seed)
        self.target = target.strip().upper() if target else random.choice(self.word_list)
        self.attempts = 0
        self.history = []
        self.solved = False

    def _hard_mode_error(self, word: str) -> str:
        """Return an error message if word violates hard mode constraints, else ''."""
        for prev_guess, prev_fb in self.history:
            for i, (ch, fb) in enumerate(zip(prev_guess, prev_fb)):
                if fb == "G" and word[i] != ch:
                    return f"Hard mode: position {i+1} must be '{ch}' (was green)."
                if fb == "Y" and ch not in word:
                    return f"Hard mode: '{ch}' must be used (was yellow)."
        return ""

    def guess(self, word: str) -> tuple[str, str]:
        """Submit a guess; returns (feedback, error_message).

        feedback is a G/Y/W string on success, empty string on error.
        error_message is empty on success.
        """
        if self.solved:
            return "", "Game already solved. Start a new game."

        word = word.strip().upper()
        if len(word) != self.word_length:
            return "", f"Guess must be {self.word_length} letters long."
        if word not in self.word_set:
            return "", f"'{word}' is not in the word list."

        if self.hard_mode:
            err = self._hard_mode_error(word)
            if err:
                return "", err

        self.attempts += 1
        feedback = compute_feedback(word, self.target)
        self.history.append((word, feedback))

        if feedback == "G" * self.word_length:
            self.solved = True

        return feedback, ""
