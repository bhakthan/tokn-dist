"""Regression checks for the trusted grader, not the candidate worktree."""
import io
import re
import unittest
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import grade
import run
from checks import lagarias_stress_gate as gate


class GateContract(unittest.TestCase):
    def test_invalid_input_still_emits_all_thresholds(self):
        spec = (Path(grade.__file__).parent / "spec" / "factory.yaml").read_text(encoding="utf-8")
        required = set(re.findall(r"metric: (\w+), op:", spec))
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(grade.main(["--key", ""]), 2)
        emitted = dict(re.findall(r"^TOKN_METRIC (\w+)=(\S+)$", output.getvalue(), re.M))
        self.assertTrue(required <= emitted.keys())
        self.assertLess(float(emitted["lagarias_min_gap"]), 0)

    def test_incomplete_or_nonfinite_trace_cannot_pass(self):
        for sizes, rms in (([24, 48, 96], [4, 2, 1]), ([24, 48, 96, 192], [4, 2, float("nan"), 1]),
                           ([24, 48, 48, 192], [4, 2, 1.5, 1]), ([24, 48, 96, 192], [4, 2, 1, 0])):
            with self.subTest(sizes=sizes, rms=rms), self.assertRaises(ValueError):
                gate.estimate_off_line_exponent(sizes, rms)
        m = {"_ladder": {"problems": ["scale_48: pipeline timed out"]}}
        self.assertTrue(grade.stress_gate(m, {"thresholds": {}}, False))
        self.assertLess(m["lagarias_min_gap"], 0)

    def test_kl_is_report_only_and_zero_ceiling_is_exact(self):
        case = dict(case_id="tier", stress_tier_n=12, emp_fdr=0, target_fdr=.05, recall=1, batch_leak=0, gguf_kl_div=4)
        rep = gate.evaluate_suite([case], ([24, 48, 96, 192], [n ** -.5 for n in (24, 48, 96, 192)]))
        self.assertTrue(rep["passed"])
        self.assertEqual([s["type"] for s in rep["observer_signals"]], ["c2s_gguf_quant_drift"])
        case["emp_fdr"] = .05
        edge = gate.evaluate_suite([case], ([24, 48, 96, 192], [n ** -.5 for n in (24, 48, 96, 192)]))
        self.assertFalse(edge["passed"])
        self.assertGreater(edge["worst_stress_case"]["relative_gap"], .05)
        self.assertLess(gate.criterion_margin(1 / 40000, 0, upper=True), 0)
        self.assertGreater(gate.criterion_margin(0, 0, upper=True), 0)

    def test_marker_support_is_not_the_candidate_verification_flag(self):
        lab = pd.DataFrame({"candidate": ["b", "nk"], "qc_status": ["pass"] * 2, "verified": ["true"] * 2}, index=["c1", "c2"])
        counts = pd.DataFrame({"c1": [4, 5], "c2": [4, 5]}, index=["MS4A1", "CD19"])
        self.assertEqual(grade._euler_discrepancy(lab, counts), .5)

    def test_loopback_checks_parse_the_authority(self):
        self.assertTrue(run.loopback_url("http://[::1]:8081", plain_http=True))
        self.assertFalse(run.loopback_url("http://example.invalid/localhost", plain_http=True))
        self.assertFalse(run.loopback_url("https://localhost", plain_http=True))
        self.assertFalse(run.loopback_url("http://localhost:bad"))
