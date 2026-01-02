import csv

from wordfreq import zipf_frequency

WORDLIST = "example.txt"
NORMALIZED_WORDLIST = "example.csv"


def main():
    normalized_words = []

    with open(WORDLIST, "r") as f:
        for word in f.readlines():
            word = word.strip()
            normalized_words.append((word, zipf_frequency(word, "en")))

    with open(NORMALIZED_WORDLIST, "w") as f:
        csv.writer(f).writerows(normalized_words)


if __name__ == "__main__":
    main()
