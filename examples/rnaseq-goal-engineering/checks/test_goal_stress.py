import unittest

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location("goal_stress", Path(__file__).with_name("lagarias_stress_gate.py"))
gate = module_from_spec(spec)
spec.loader.exec_module(gate)


class GoalContract(unittest.TestCase):
    def test_report_mentions_are_scoped(self):
        self.assertTrue(gate.stated_reference("Student t with 9 residual df"))
        self.assertFalse(gate.stated_reference("A student in 2024 used a normal reference, not a Student t."))
        self.assertFalse(gate.DF_RE.search("We used df from 2024, and reported 9 genes."))

    def test_design_df_uses_rank_and_rejects_confounding(self):
        counts = {"A": {"1": 2, "2": 4, "3": 3, "4": 8}}
        samples = {"1": ("control", "a"), "2": ("control", "a"), "3": ("treated", "a"), "4": ("treated", "a")}
        _, df = gate.batch_adjusted_lfc(counts, ["A"], samples)
        self.assertIs(type(df), int)
        self.assertEqual(df, 2)
        samples.update({"3": ("treated", "b"), "4": ("treated", "b")})
        with self.assertRaisesRegex(ValueError, "identifiable"):
            gate.batch_adjusted_lfc(counts, ["A"], samples)
