#!/usr/bin/env python3
"""Offline check of synthetic quantum experiment plans.

Reads devices.json and experiments.json next to this file. Standard library
only; no network. Applies the public gate rules used by TOKN's quantumsci
domain:
  - error budget: fidelity = (1 - p2)^gates; accumulated error = 1 - fidelity.
    > 50 % CRITICAL, > 10 % WARNING.
  - decoherence: execution time = depth x gate time; > 50 % of T2 CRITICAL,
    > 10 % WARNING.
  - shots: < 1000 CRITICAL; < 10000 WARNING (publication-grade).
  - tier label must be [EXACT-SIM], [NOISY-SIM], [HARDWARE:...] or [ANALOG-SIM].
  - ZNE: >= 3 scale factors, each within 1.0 to 3.0; Richardson/polynomial fit
    is CRITICAL when the accumulated error exceeds 10 %.
  - fault-tolerant claim: two-qubit fidelity >= 0.999 and >= 100 physical
    qubits per logical qubit, else CRITICAL.
Exit code 1 if any CRITICAL is found.
"""
import json
import sys
from pathlib import Path


def check(exp, dev):
    issues = []
    fid = (1 - dev["two_qubit_error"]) ** exp["gate_count"]
    err = 1 - fid
    if err > 0.50:
        issues.append(("CRITICAL", f"accumulated error {err:.1%} > 50%"))
    elif err > 0.10:
        issues.append(("WARNING", f"accumulated error {err:.1%} > 10%"))

    exec_us = exp["depth"] * dev["two_qubit_gate_time_us"]
    frac = exec_us / dev["t2_us"]
    if frac > 0.50:
        issues.append(("CRITICAL", f"execution {exec_us:.1f} us = {frac:.0%} of T2"))
    elif frac > 0.10:
        issues.append(("WARNING", f"execution {exec_us:.1f} us = {frac:.0%} of T2"))

    if exp["shots"] < 1000:
        issues.append(("CRITICAL", f"{exp['shots']} shots < 1000"))
    elif exp["shots"] < 10000:
        issues.append(("WARNING", f"{exp['shots']} shots < 10000 publication-grade"))

    tier = exp.get("tier_label")
    valid = ("[EXACT-SIM]", "[NOISY-SIM]", "[HARDWARE:", "[ANALOG-SIM]")
    if not tier:
        issues.append(("CRITICAL", "missing tier label"))
    elif not tier.startswith(valid):
        issues.append(("CRITICAL", f"invalid tier label {tier}"))

    z = exp.get("zne")
    if z:
        sf = z["scale_factors"]
        if len(sf) < 3:
            issues.append(("CRITICAL", f"ZNE has {len(sf)} scale factors, need >= 3"))
        if any(s < 1.0 or s > 3.0 for s in sf):
            issues.append(("CRITICAL", "ZNE scale factor outside 1.0-3.0"))
        if z["fit"] in ("richardson", "polynomial") and z["accumulated_error_at_1x"] > 0.10:
            issues.append(("CRITICAL", "Richardson/polynomial fit with accumulated error > 10%"))

    ft = exp.get("ft_claim")
    if ft:
        if ft["two_qubit_fidelity"] < 0.999:
            issues.append(("CRITICAL", f"FT claim: two-qubit fidelity {ft['two_qubit_fidelity']} < 0.999"))
        per_logical = ft["physical_qubits"] / ft["logical_qubits"]
        if per_logical < 100:
            issues.append(("CRITICAL", f"FT claim: {per_logical:.0f} physical qubits per logical < 100"))
    return fid, issues


def main():
    here = Path(__file__).resolve().parent
    devices = {d["id"]: d for d in json.loads((here / "devices.json").read_text(encoding="utf-8"))["devices"]}
    plans = json.loads((here / "experiments.json").read_text(encoding="utf-8"))["experiments"]

    critical = False
    for exp in plans:
        fid, issues = check(exp, devices[exp["device"]])
        print(f"{exp['id']} ({exp['device']}): fidelity={fid:.4f}")
        if not issues:
            print("  no issues")
        for level, msg in issues:
            print(f"  [{level}] {msg}")
            critical = critical or level == "CRITICAL"
    return 1 if critical else 0


if __name__ == "__main__":
    sys.exit(main())
