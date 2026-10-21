import unittest

from pricing import apply_discount, order_total


class ApplyDiscountTests(unittest.TestCase):
    def test_ten_percent_off(self):
        self.assertEqual(apply_discount(1000, 10), 900)

    def test_rounds_down_to_whole_cents(self):
        self.assertEqual(apply_discount(999, 33), 669)

    def test_rejects_out_of_range_percent(self):
        with self.assertRaises(ValueError):
            apply_discount(1000, 101)


class OrderTotalTests(unittest.TestCase):
    def test_sums_all_items(self):
        self.assertEqual(order_total([100, 250, 399]), 749)

    def test_empty_order_is_zero(self):
        self.assertEqual(order_total([]), 0)


if __name__ == "__main__":
    unittest.main()
