"""Deterministic endpoint-provenance checker for the VTX-417 example.

Reads only ./analysis-package/endpoint-register.json (local file).
No network access, no credentials, no environment variables.

Usage:
    python check_gate.py [path/to/endpoint-register.json]

Exit code 0 = every claim marked green_light is LAWFUL.
Exit code 1 = at least one green-light claim is QUARANTINED.
"""
import json
import sys
from pathlib import Path

DEFAULT = Path("analysis-package") / "endpoint-register.json"


def reasons_for(claim):
    """Return the list of rules a claim fails. Empty list means LAWFUL."""
    fails = []
    if not claim.get("is_primary"):
        fails.append("not the primary endpoint")
    if claim.get("population") != "ITT":
        fails.append("not ITT population")
    if claim.get("blinded") is not True:
        fails.append("not blinded")
    if claim.get("sdv") != "full":
        fails.append("SDV not full")
    if claim.get("sap_prespecified") is not True:
        fails.append("not pre-specified in SAP")
    if claim.get("posthoc") is True:
        fails.append("post-hoc analysis")
    if claim.get("uses_biomarker") and claim.get("assay_qualified") is not True:
        fails.append("biomarker assay not qualified")
    p = claim.get("p_value")
    if not isinstance(p, (int, float)) or p >= 0.05:
        fails.append("p-value not below 0.05")
    return fails


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.exists():
        print(f"missing: {path} (run the analysis first, then re-check)")
        return 2
    claims = json.loads(path.read_text(encoding="utf-8"))
    blocked = 0
    for claim in claims:
        fails = reasons_for(claim)
        status = "LAWFUL" if not fails else "QUARANTINED"
        proposed = "green-light" if claim.get("green_light") else "report-only"
        print(f"{claim.get('id', '?'):<12} {status:<12} proposed={proposed:<12} "
              + ("; ".join(fails) if fails else "all rules met"))
        if claim.get("green_light") and fails:
            blocked += 1
    if blocked:
        print(f"\nFAIL: {blocked} green-light claim(s) are quarantined.")
        return 1
    print("\nPASS: no quarantined claim is marked green-light.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
