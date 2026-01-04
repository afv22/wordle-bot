from dataclasses import dataclass, field
from typing import Optional

from src.models import Guess
from src.strategy import EntropyStrategy
from src.strategy.base import Strategy


@dataclass
class GameSession:
    """Stores the state of a Wordle game."""

    guesses: list[Guess] = field(default_factory=list)
    strategy: Strategy = EntropyStrategy()

    def add_guess(self, word: str, result: str) -> None:
        self.guesses.append(Guess(word.upper(), result))

    def reset(self) -> int:
        """Reset the session and return the number of guesses that were made."""
        count = len(self.guesses)
        self.guesses = []
        return count

    def is_won(self) -> bool:
        """Check if the last guess was correct (all greens)."""
        if not self.guesses:
            return False
        return self.guesses[-1].result == "11111"

    def is_complete(self) -> bool:
        """Check if the game is over (won or 6 guesses)."""
        return self.is_won() or len(self.guesses) >= 6


class SessionManager:
    """Manages game sessions keyed by (user_id, chat_id)."""

    def __init__(self):
        self._sessions: dict[tuple[int, int], GameSession] = {}

    def get(self, user_id: int, chat_id: int) -> GameSession:
        """Get or create a session for the user+chat pair."""
        key = (user_id, chat_id)
        if key not in self._sessions:
            self._sessions[key] = GameSession()
        return self._sessions[key]

    def reset(self, user_id: int, chat_id: int) -> int:
        """Reset a session and return the number of guesses that were made."""
        key = (user_id, chat_id)
        if key in self._sessions:
            count = self._sessions[key].reset()
            return count
        return 0


sessions = SessionManager()
