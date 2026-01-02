from abc import ABC, abstractmethod
from collections import Counter

from src.session import Guess
from src.wordlist import load_wordlist


class Strategy(ABC):

    def __init__(
        self,
        filename: str = "normalized_wordlist.csv",
        max_words: int = 1000,
    ) -> None:
        self.wordlist = load_wordlist(
            filename=filename,
            max_words=max_words,
        )

    def _get_feedback_pattern(self, guess: str, answer: str) -> str:
        """
        Compute the feedback pattern for a guess against an answer.
        Returns a string like "01210" where:
          1 = correct position (green)
          2 = wrong position (yellow)
          0 = not in word (grey)
        """
        result = ["0"] * 5
        answer_letter_counts = Counter(answer)

        # First pass: mark greens (correct position)
        for i, letter in enumerate(guess):
            if letter == answer[i]:
                result[i] = "1"
                answer_letter_counts[letter] -= 1

        # Second pass: mark yellows (wrong position)
        for i, letter in enumerate(guess):
            if result[i] == "0" and answer_letter_counts.get(letter, 0) > 0:
                result[i] = "2"
                answer_letter_counts[letter] -= 1

        return "".join(result)

    def _get_remaining_words(self, guesses: list[Guess]) -> list[tuple[str, float]]:
        """
        Filter wordlist using previous guesses.
        """
        candidates: list[tuple[str, float]] = []
        for word, frequency in self.wordlist:
            is_valid = True

            for guess in guesses:
                if not is_valid:
                    break

                letter_counts = Counter(word)

                # First pass: check green letters (exact matches)
                for i, letter in enumerate(guess.word):
                    if guess.result[i] == "1":
                        if word[i] != letter.lower():
                            is_valid = False
                            break
                        letter_counts[letter.lower()] -= 1

                if not is_valid:
                    continue

                # Second pass: check yellow and grey letters
                for i, letter in enumerate(guess.word):
                    if guess.result[i] == "2":
                        # Letter exists but not in this position
                        if word[i] == letter.lower():
                            is_valid = False
                            break
                        if letter_counts.get(letter.lower(), 0) <= 0:
                            is_valid = False
                            break
                        letter_counts[letter.lower()] -= 1

                    elif guess.result[i] == "0":
                        # If we have unaccounted instances of this letter, it's incompatible
                        if letter_counts.get(letter.lower(), 0) > 0:
                            is_valid = False
                            break

            if is_valid:
                candidates.append((word, frequency))

        return candidates

    @abstractmethod
    def execute(self, guesses: list[Guess]) -> str: ...
