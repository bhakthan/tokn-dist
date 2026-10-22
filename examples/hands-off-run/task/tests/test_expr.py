import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from expr import ExprError, evaluate  # noqa: E402


class EvaluateTests(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7.0)

    def test_parentheses(self):
        self.assertEqual(evaluate("(1 + 2) * 3"), 9.0)

    def test_division(self):
        self.assertEqual(evaluate("10 / 4"), 2.5)

    def test_unary_minus_binds_looser_than_power(self):
        self.assertEqual(evaluate("-2^2"), -4.0)

    def test_power_is_right_associative(self):
        self.assertEqual(evaluate("2^3^2"), 512.0)

    def test_leading_decimal_and_whitespace(self):
        self.assertEqual(evaluate("  .75 *  4 "), 3.0)

    def test_unary_plus(self):
        self.assertEqual(evaluate("+5 - -1"), 6.0)

    def test_left_associative_subtraction(self):
        self.assertEqual(evaluate("10 - 4 - 3"), 3.0)


class ErrorTests(unittest.TestCase):
    def assertRaisesExpr(self, text):
        with self.assertRaises(ExprError):
            evaluate(text)

    def test_empty(self):
        self.assertRaisesExpr("")
        self.assertRaisesExpr("   ")

    def test_unknown_character(self):
        self.assertRaisesExpr("2 % 3")
        self.assertRaisesExpr("a + 1")

    def test_unbalanced_parentheses(self):
        self.assertRaisesExpr("(1 + 2")
        self.assertRaisesExpr("1 + 2)")

    def test_missing_operand(self):
        self.assertRaisesExpr("3 +")
        self.assertRaisesExpr("* 4")

    def test_division_by_zero(self):
        self.assertRaisesExpr("1 / 0")
        self.assertRaisesExpr("1 / (2 - 2)")


if __name__ == "__main__":
    unittest.main()
