import csv
from pathlib import Path


def load_wordlist(
    filename: Path, max_words: int | None = None
) -> list[tuple[str, float]]:
    """Load the top N words with their normalized frequencies.

    Args:
        filename: Path to the CSV file with word,frequency,normalized_frequency columns
        max_words: Maximum number of words to load. None for all words.

    Returns:
        List of (word, normalized_frequency) tuples, sorted by frequency descending.
    """
    words: list[tuple[str, float]] = []

    with open("wordlists" / filename, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_words is not None and i >= max_words:
                break
            words.append((row["word"].upper(), float(row["normalized_frequency"])))

    return words
