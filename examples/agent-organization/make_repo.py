"""Create the fixture repository for the agent-organization example.

Usage: python make_repo.py <absolute-target-dir>

The repository holds a tiny text-statistics module with three independent
bugs and a unittest suite that exposes them (5 of 7 tests fail). Independent bugs give several
workers something to claim in parallel. Standard library only; needs git.
"""

import os
import subprocess
import sys

TEXTSTATS = '''"""Small text statistics helpers."""


def word_count(text):
    """Number of words, separated by any whitespace."""
    return len(text.split(" "))


def average_word_length(text):
    """Mean length of the words in text; 0.0 for empty text."""
    words = text.split()
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(text)


def top_words(text, n):
    """The n most frequent lower-cased words, most frequent first.

    Ties are broken alphabetically so the result is deterministic.
    """
    counts = {}
    for word in text.lower().split():
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    return [word for word, _ in ranked[: n - 1]]
'''

TESTS = '''import unittest

from textstats import average_word_length, top_words, word_count


class WordCountTest(unittest.TestCase):
    def test_single_spaces(self):
        self.assertEqual(word_count("a b c"), 3)

    def test_mixed_whitespace(self):
        self.assertEqual(word_count("a   b\\tc\\n d"), 4)

    def test_empty(self):
        self.assertEqual(word_count(""), 0)


class AverageWordLengthTest(unittest.TestCase):
    def test_average(self):
        self.assertAlmostEqual(average_word_length("ab abcd"), 3.0)

    def test_empty(self):
        self.assertEqual(average_word_length("   "), 0.0)


class TopWordsTest(unittest.TestCase):
    def test_most_frequent_first(self):
        self.assertEqual(top_words("b a b c b a", 2), ["b", "a"])

    def test_ties_alphabetical(self):
        self.assertEqual(top_words("pear apple fig", 3), ["apple", "fig", "pear"])


if __name__ == "__main__":
    unittest.main()
'''

README = """# textstats

Tiny text statistics helpers. Run the tests with `python -m unittest`.
"""


def git(target, *args):
    subprocess.run(["git", *args], cwd=target, check=True)


def main():
    if len(sys.argv) != 2 or not os.path.isabs(sys.argv[1]):
        sys.exit("usage: python make_repo.py <absolute-target-dir>")
    target = sys.argv[1]
    if os.path.exists(target):
        sys.exit(f"refusing to overwrite existing path: {target}")
    os.makedirs(target)
    files = {
        "textstats.py": TEXTSTATS,
        "test_textstats.py": TESTS,
        "README.md": README,
        ".gitignore": "__pycache__/\n",
    }
    for name, body in files.items():
        with open(os.path.join(target, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    git(target, "init", "-q", "-b", "main")
    git(target, "add", ".")
    git(target, "-c", "user.name=demo", "-c", "user.email=demo@example.invalid",
        "commit", "-q", "-m", "textstats with three known bugs")
    print(f"created {target}")
    print("run 'python -m unittest' there: 5 of 7 tests fail before the organization runs")


if __name__ == "__main__":
    main()
