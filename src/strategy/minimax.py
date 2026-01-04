from collections import defaultdict
from math import log2
from typing import Optional

from src.exceptions import BotException
from src.models import Guess
from src.strategy.base import Strategy


class MinimaxStrategy(Strategy):
    """
    Minimize expected number of guesses to solve the puzzle.

    Uses depth-limited search with a heuristic at leaf nodes.
    - depth=0: Use log₂(group_size) heuristic immediately
    - depth=1: One level of lookahead, then heuristic
    - depth=2+: Deeper recursive search (expensive)

    Uses entropy-based pruning to limit candidates at each recursive level.
    """

    @property
    def name(self) -> str:
        return "Minimax"

    def __init__(
        self,
        filename: str = "normalized_scrabble_wordlist.csv",
        max_words: Optional[int] = None,
        depth: int = 0,
        prune_k: int = 50,
    ) -> None:
        super().__init__(filename=filename, max_words=max_words)
        self.depth = depth
        self.prune_k = prune_k

    def _group_by_pattern(
        self, guess: str, possible_answers: list[str]
    ) -> dict[str, list[str]]:
        """Group possible answers by the feedback pattern they would produce."""
        groups: dict[str, list[str]] = defaultdict(list)
        for answer in possible_answers:
            pattern = self._get_feedback_pattern(guess, answer)
            groups[pattern].append(answer)
        return groups

    def _get_top_entropy_candidates(
        self, possible_answers: list[str], k: int
    ) -> list[str]:
        """Get top-k candidates by entropy for pruning."""
        scored: list[tuple[str, float]] = []
        for candidate, _ in self.wordlist:
            entropy = self._calculate_entropy(candidate, possible_answers)
            scored.append((candidate, entropy))

        scored.sort(key=lambda x: -x[1])
        return [word for word, _ in scored[:k]]

    def _expected_guesses(
        self,
        possible_answers: list[str],
        depth: int,
    ) -> float:
        """
        Calculate the minimum expected guesses to solve from this state.
        """
        if len(possible_answers) == 0:
            return 0
        if len(possible_answers) == 1:
            return 1

        # At depth 0, use heuristic: log₂(n) guesses to solve n possibilities
        if depth == 0:
            return log2(len(possible_answers))

        # Prune: only try top-K candidates by entropy
        candidates = self._get_top_entropy_candidates(possible_answers, self.prune_k)

        best_expected = float("inf")
        for candidate in candidates:
            expected = self._expected_guesses_for_guess(
                candidate, possible_answers, depth
            )
            best_expected = min(best_expected, expected)

        return best_expected

    def _expected_guesses_for_guess(
        self,
        guess: str,
        possible_answers: list[str],
        depth: int,
    ) -> float:
        """Calculate expected guesses if we make this guess."""
        groups = self._group_by_pattern(guess, possible_answers)
        total = len(possible_answers)
        expected = 0.0

        for pattern, group in groups.items():
            probability = len(group) / total

            if pattern == "11111":
                # Correct guess - costs 1 guess
                expected += probability * 1
            else:
                # Recurse with reduced depth
                expected += probability * (1 + self._expected_guesses(group, depth - 1))

        return expected

    def execute(self, guesses: list[Guess], n: int = 1) -> list[str]:
        remaining_words = self._get_remaining_words(guesses)
        if len(remaining_words) == 0:
            raise BotException("No known remaining words")
        if len(remaining_words) == 1:
            return [remaining_words[0][0]]

        possible_answers = [word for word, _ in remaining_words]
        possible_set = set(possible_answers)

        # Prune candidates at top level using entropy heuristic
        candidates = self._get_top_entropy_candidates(possible_answers, self.prune_k)

        scored: list[tuple[str, float, bool]] = []
        for candidate in candidates:
            expected = self._expected_guesses_for_guess(
                candidate, possible_answers, self.depth
            )
            is_possible = candidate in possible_set
            scored.append((candidate, expected, is_possible))

        # Sort by expected guesses (asc), then by is_possible (True first as tiebreaker)
        scored.sort(key=lambda x: (x[1], not x[2]))

        return [word for word, _, _ in scored[:n]]
