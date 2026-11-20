#!/usr/bin/env python3
"""Grade an RNA-seq DE candidate against the hidden answer key.

Run INSIDE the candidate worktree (it is the factory's test-gate command):

    python grade.py --key <abs path to answer_key.json> [--repo .]

The key path comes from --key, else $FACTORY_RNASEQ_KEY. --key exists because
the factory runs gate commands with an allow-listed environment that drops
FACTORY_RNASEQ_KEY.

Prints one JSON object with:
  recall, precision        DE calls (padj < fdr, |log2FC| >= min) vs the planted truth
  rin_filtered             qc.json excludes exactly the low-RIN sample(s)
  strandedness_detected    qc.json calls the reversed batch "reverse" and the rest "forward"
  confounded_refused       samples_confounded.tsv => non-zero exit, no de_results.tsv
  bh_applied               padj == BH(pvalue)
  integer_counts_enforced  a non-integer counts file => non-zero exit
  pii_clean                no subject_ref value in any output
  data_intact              data/ and golden/ match the generated hashes
Exit 0 only when every check passes; 1 otherwise; 2 on a usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRATCH = ".grade_out"


def bh(p: np.ndarray) -> np.ndarray:
    n = p.size
    order = np.argsort(p, kind="mergesort")
    r = p[order] * n / np.arange(1, n + 1)
    r = np.minimum.accumulate(r[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(r, 1.0)
    return out


def run_cli(repo: Path, out: Path, samples: str, counts: str = "data/counts.tsv", timeout: int = 300):
    cmd = [sys.executable, "-m", "rnaseq_de.cli", "--counts", counts,
           "--counts-opposite", "data/counts_opposite.tsv", "--samples", samples, "--out", str(out)]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    try:
        p = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-2000:]
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def grade(repo: Path, key: dict) -> tuple[dict, list[str]]:
    th = key["thresholds"]
    m: dict = {}
    notes: list[str] = []
    scratch = repo / SCRATCH
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    try:
        bad = [rel for rel, h in key["data_sha256"].items()
               if not (repo / rel).is_file() or hashlib.sha256((repo / rel).read_bytes()).hexdigest() != h]
        m["data_intact"] = not bad
        if bad:
            notes.append("input data modified: " + ", ".join(bad))

        main_out = scratch / "main"
        rc, log = run_cli(repo, main_out, "data/samples.tsv")
        res_path = main_out / "de_results.tsv"
        if rc != 0 or not res_path.is_file():
            notes.append(f"pipeline failed (exit {rc}): {log.strip()[-400:]}")
            m.update(recall=0.0, precision=0.0, bh_applied=False, rin_filtered=False, strandedness_detected=False)
        else:
            res = pd.read_csv(res_path, sep="\t")
            missing = {"gene", "log2fc", "pvalue", "padj"} - set(res.columns)
            if missing:
                notes.append(f"de_results.tsv missing columns {sorted(missing)}")
                m.update(recall=0.0, precision=0.0, bh_applied=False)
            else:
                dup = res["gene"][res["gene"].duplicated()].unique().tolist()
                if dup:
                    notes.append(f"de_results.tsv has duplicate gene rows: {sorted(map(str, dup))[:5]}")
                    m.update(recall=0.0, precision=0.0, bh_applied=False, n_called=0)
                    res = None
            if res is not None and not missing:
                calls = res[(res["padj"] < th["fdr"]) & (res["log2fc"].abs() >= th["min_abs_log2fc"])]
                truth = key["de_genes"]
                tp = len({g for g, l in zip(calls["gene"], calls["log2fc"]) if g in truth and np.sign(l) == np.sign(truth[g])})
                m["recall"] = round(tp / len(truth), 4)
                m["precision"] = round(tp / len(calls), 4) if len(calls) else 0.0
                m["n_called"] = int(len(calls))
                p = res["pvalue"].to_numpy(dtype=float)
                padj = res["padj"].to_numpy(dtype=float)
                m["bh_applied"] = bool(np.allclose(padj, bh(p), rtol=1e-4, atol=1e-8) and not np.allclose(padj, p))
            qc_path = main_out / "qc.json"
            qcj = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.is_file() else {}
            m["rin_filtered"] = sorted(qcj.get("excluded_samples", [])) == sorted(key["low_rin_samples"])
            strand = qcj.get("strandedness", {})
            m["strandedness_detected"] = (all(strand.get(s) == "reverse" for s in key["reversed_strand_samples"])
                                          and all(strand.get(s) == "forward" for s in key["forward_strand_samples"]))
            pat = key.get("pii_pattern", "SUBJ-")
            leaks = [f.name for f in main_out.rglob("*") if f.is_file() and pat in f.read_text(encoding="utf-8", errors="replace")]
            m["pii_clean"] = not leaks
            if leaks:
                notes.append("subject_ref leaked into: " + ", ".join(sorted(leaks)))

        conf_out = scratch / "confounded"
        rc, log = run_cli(repo, conf_out, key.get("confounded_design", "data/samples_confounded.tsv"))
        m["confounded_refused"] = rc != 0 and not (conf_out / "de_results.tsv").exists() and "confound" in log.lower()
        if not m["confounded_refused"]:
            notes.append(f"confounded design not refused (exit {rc})")

        bad_counts = scratch / "float_counts.tsv"
        txt = (repo / "data" / "counts.tsv").read_text(encoding="utf-8").splitlines()
        cells = txt[1].split("\t")
        cells[1] = cells[1] + ".5"
        txt[1] = "\t".join(cells)
        bad_counts.write_text("\n".join(txt) + "\n", encoding="utf-8")
        rc, _ = run_cli(repo, scratch / "float", "data/samples.tsv", counts=str(bad_counts))
        m["integer_counts_enforced"] = rc != 0 and not (scratch / "float" / "de_results.tsv").exists()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    fails = []
    if m.get("recall", 0) < th["recall"]:
        fails.append(f"recall {m.get('recall')} < {th['recall']}")
    if m.get("precision", 0) < th["precision"]:
        fails.append(f"precision {m.get('precision')} < {th['precision']}")
    for k in ("rin_filtered", "strandedness_detected", "confounded_refused", "bh_applied",
              "integer_counts_enforced", "pii_clean", "data_intact"):
        if not m.get(k):
            fails.append(f"{k} is false")
    return m, fails + [f"note: {n}" for n in notes]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--key", default=os.environ.get("FACTORY_RNASEQ_KEY", ""), help="answer_key.json (or $FACTORY_RNASEQ_KEY)")
    ap.add_argument("--repo", default=".", type=Path, help="candidate worktree (default: cwd)")
    a = ap.parse_args(argv)
    if not a.key:
        print(json.dumps({"error": "no answer key: pass --key or set FACTORY_RNASEQ_KEY"}))
        return 2
    kp = Path(a.key)
    if not kp.is_file():
        print(json.dumps({"error": f"answer key not found: {kp}"}))
        return 2
    repo = a.repo.resolve()
    if repo in kp.resolve().parents:
        print(json.dumps({"error": "answer key is inside the candidate repo; refusing"}))
        return 2
    key = json.loads(kp.read_text(encoding="utf-8"))
    metrics, problems = grade(repo, key)
    failures = [p for p in problems if not p.startswith("note: ")]
    # Factory metric protocol: thresholds in factory.yaml read these lines.
    # They precede the JSON line, which callers parse as the LAST line.
    for k in ("recall", "precision", "n_called"):
        if isinstance(metrics.get(k), (int, float)):
            print(f"TOKN_METRIC {k}={metrics[k]}")
    for k in ("rin_filtered", "strandedness_detected", "confounded_refused", "bh_applied",
              "integer_counts_enforced", "pii_clean", "data_intact"):
        print(f"TOKN_METRIC {k}={1 if metrics.get(k) else 0}")
    print(json.dumps({**metrics, "pass": not failures, "failures": problems}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
