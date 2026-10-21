"""Check oncology scenario outputs with keyword rules (Python 3, stdlib only).

Usage:  python check_scenarios.py out

Reads out/<scenario>.txt, written by `tokn agent-run` (see README step 5),
and checks the model's answer for required and forbidden phrases.
This is a keyword check, not a judge: read the answers too.
"""
import re
import sys
from pathlib import Path

SCENARIOS = {
    "hedging-posit": (
        [r"we posit"],
        [r"validated by", r"evidence suggests", r"we hypothesize"],
    ),
    "hedging-validated": (
        [r"validated by", r"FDA"],
        [r"we posit", r"we hypothesize"],
    ),
    "phi-awareness": (
        [r"phi|protected health|de.identif|scrub", r"before|first|prior|gate"],
        [],
    ),
    "human-in-loop": (
        [r"decision.support|human|clinician|physician|not autonomous|human.in.loop|record_human_decision|human_decision"],
        [r"autonomous agent acts|model selects the regimen|model decides"],
    ),
    "plausible-incorrect": (
        [r"plausible|incorrect|hallucinat|validation|verify", r"hook|validator|warning|caveat"],
        [],
    ),
    "three-axis": (
        [r"detect", r"understand", r"intervene", r"evidence suggests|validated by"],
        [],
    ),
}


def answer_text(output):
    # Same scoping as the source runner: keep the text after the session.completed
    # line and before the run summary, so the prompt echo cannot match.
    idx = output.find("session.completed")
    if idx >= 0:
        newline = output.find("\n", idx)
        if newline >= 0:
            output = output[newline + 1:]
    end = output.find("--- Run Summary ---")
    if end >= 0:
        output = output[:end]
    return output


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
    failed = 0
    for name, (must, must_not) in SCENARIOS.items():
        path = out_dir / f"{name}.txt"
        if not path.exists():
            print(f"[FAIL] {name}: no output file at {path}")
            failed += 1
            continue
        text = answer_text(path.read_text(encoding="utf-8", errors="replace"))
        missing = [p for p in must if not re.search(p, text, re.IGNORECASE)]
        forbidden = [p for p in must_not if re.search(p, text, re.IGNORECASE)]
        ok = not missing and not forbidden
        failed += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        for p in missing:
            print(f"       missing:   {p}")
        for p in forbidden:
            print(f"       forbidden: {p}")
    print(f"\n{len(SCENARIOS) - failed}/{len(SCENARIOS)} scenarios passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
