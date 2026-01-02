from collections import Counter
from math import log2

from src.models import Guess
from .base import Strategy


class EntropyStrategy(Strategy):
    """
    Use information theory to maximize information gain (bits) for each guess.
    Calculates expected bits for every known word, using whether it is still a
    possible answer as a tiebreaker.
    """

    def _calculate_entropy(self, guess: str, possible_answers: list[str]) -> float:
        """
        Calculate the entropy (expected information gain) for a candidate guess.
        Higher entropy = more evenly distributed feedback patterns = better guess.
        """
        pattern_counts: Counter[str] = Counter()
        for answer in possible_answers:
            pattern = self._get_feedback_pattern(guess, answer)
            pattern_counts[pattern] += 1

        total = len(possible_answers)
        entropy = 0.0
        for count in pattern_counts.values():
            probability = count / total
            entropy -= probability * log2(probability)

        return entropy

    def execute(self, guesses: list[Guess], n: int = 1) -> list[str]:
        remaining_words = self._get_remaining_words(guesses)
        if len(remaining_words) == 0:
            raise RuntimeError("No known remaining words")
        if len(remaining_words) == 1:
            return [remaining_words[0][0].upper()]

        possible_answers = [word for word, _ in remaining_words]
        possible_set = set(possible_answers)

        # Calculate entropy for all candidates and rank them
        scored: list[tuple[str, float, bool]] = []
        for candidate, _ in self.wordlist:
            entropy = self._calculate_entropy(candidate, possible_answers)
            is_possible = candidate in possible_set
            scored.append((candidate, entropy, is_possible))

        # Sort by entropy (desc), then by is_possible (True first)
        scored.sort(key=lambda x: (-x[1], not x[2]))

        return [word.upper() for word, _, _ in scored[:n]]
