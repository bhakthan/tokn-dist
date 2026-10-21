import unittest

from calc import average


class AverageTests(unittest.TestCase):
    def test_mean_of_small_list(self):
        self.assertEqual(average([1, 2, 3]), 2)

    def test_mean_is_not_median(self):
        self.assertEqual(average([1, 2, 3, 10]), 4)


if __name__ == "__main__":
    unittest.main()
