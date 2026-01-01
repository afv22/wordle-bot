from src.session import Guess
from .base import Strategy


class EntropyStrategy(Strategy):

    def execute(self, guesses: list[Guess]) -> str:
        return "SLATE"
