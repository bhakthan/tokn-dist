"""Create the fixture repository for the loops-and-ship-ready example.

Usage: python make_repo.py <absolute-target-dir>

Writes a tiny pricing module with one bug (3 of 5 tests fail), commits it,
then leaves one untracked runtime log behind so `tokn ship-ready` has
something to flag. Standard library only; needs git.
"""

import os
import subprocess
import sys

PRICING = '''"""Order pricing."""


def apply_discount(total, percent):
    """Return total reduced by percent (0-100), rounded to cents."""
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(total - percent, 2)


def order_total(lines, percent=0):
    """Sum quantity * unit price over (quantity, unit_price) lines, then discount."""
    subtotal = sum(q * p for q, p in lines)
    return apply_discount(subtotal, percent)
'''

TESTS = '''import unittest

from pricing import apply_discount, order_total


class DiscountTest(unittest.TestCase):
    def test_no_discount(self):
        self.assertEqual(apply_discount(80.0, 0), 80.0)

    def test_ten_percent(self):
        self.assertEqual(apply_discount(80.0, 10), 72.0)

    def test_rejects_bad_percent(self):
        with self.assertRaises(ValueError):
            apply_discount(10.0, 120)


class OrderTotalTest(unittest.TestCase):
    def test_lines_and_discount(self):
        self.assertEqual(order_total([(2, 15.0), (1, 20.0)], 25), 37.5)

    def test_small_order(self):
        self.assertEqual(order_total([(1, 4.0)], 50), 2.0)


if __name__ == "__main__":
    unittest.main()
'''


def git(target, *args):
    subprocess.run(["git", *args], cwd=target, check=True)


def write(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)


def main():
    if len(sys.argv) != 2 or not os.path.isabs(sys.argv[1]):
        sys.exit("usage: python make_repo.py <absolute-target-dir>")
    target = sys.argv[1]
    if os.path.exists(target):
        sys.exit(f"refusing to overwrite existing path: {target}")
    os.makedirs(target)
    write(os.path.join(target, "pricing.py"), PRICING)
    write(os.path.join(target, "test_pricing.py"), TESTS)
    write(os.path.join(target, "README.md"), "# pricing\n\nRun `python -m unittest`.\n")
    write(os.path.join(target, ".gitignore"), "__pycache__/\n")
    git(target, "init", "-q", "-b", "main")
    git(target, "add", ".")
    git(target, "-c", "user.name=demo", "-c", "user.email=demo@example.invalid",
        "commit", "-q", "-m", "pricing with a discount bug")
    # Left untracked on purpose: ship-ready's runtime-artifacts check flags it.
    write(os.path.join(target, "server.log"), "synthetic debug output from a local run\n")
    print(f"created {target}")
    print("3 of 5 tests fail, and server.log is untracked on purpose")


if __name__ == "__main__":
    main()
