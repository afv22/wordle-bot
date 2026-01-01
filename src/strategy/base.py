from abc import ABC, abstractmethod
from collections import Counter

from src.session import Guess
from src.wordlist import load_wordlist


class Strategy(ABC):
    def __init__(self) -> None:
        self.wordlist = load_wordlist(
            filename="normalized_wordlist.csv",
            max_words=500,
        )

    def _get_candidates(self, guesses: list[Guess]) -> list[tuple[str, float]]:
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
