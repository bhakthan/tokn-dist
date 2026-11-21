#!/usr/bin/env python3
"""Deterministic generator for the RNA-seq Agent Factory live-test fixture.

    python make_case.py --out <dir>/seed --key <dir>/answer_key.json --seed 7 [--intake <dir>/intake]

Writes a SEED git-repo directory (not git-initialised; run.py does that):
  rnaseq_de/            stub package with deliberate gaps (see seed_src/)
  tests/                pytest invariants, several FAIL on the seed
  data/counts.tsv       genes x samples integer counts, counted on the DECLARED strand
  data/counts_opposite.tsv  the same libraries counted on the opposite strand
  data/samples.tsv      sample_id, condition, batch, rin, strandedness_declared, subject_ref
  data/samples_confounded.tsv  a variant design where condition == batch
  golden/de_golden.tsv  public acceptance examples (a subset of the planted DE genes)
Planted truth: ~5% DE genes with known log2FC; batch B2 libraries are really
reverse-stranded although declared forward; one sample has RIN < 6.

The answer key goes to --key, which must be OUTSIDE --out: the candidate never
sees it. --intake writes the generated Observer intake records (CI replay and
an incident), also outside the seed. Everything is SYNTHETIC; subject_ref values
are placeholders (SUBJ-####). Same --seed => byte-identical output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED_SRC = HERE / "seed_src"

N_GENES = 2000
DE_FRACTION = 0.05
DISPERSION = 0.05
LOW_RIN_SAMPLE = "S05"
SAMPLES = [  # sample_id, condition, batch
    ("S01", "control", "B1"), ("S02", "control", "B1"), ("S03", "control", "B1"),
    ("S04", "treated", "B1"), ("S05", "treated", "B1"), ("S06", "treated", "B1"),
    ("S07", "control", "B2"), ("S08", "control", "B2"), ("S09", "control", "B2"),
    ("S10", "treated", "B2"), ("S11", "treated", "B2"), ("S12", "treated", "B2"),
]
REVERSED_BATCH = "B2"
THRESHOLDS = {"recall": 0.9, "precision": 0.9, "fdr": 0.05, "min_abs_log2fc": 1.0}
# Single-cell (C2S) feature loop. Gates are graded against the deterministic offline
# oracle (fake_c2s.py); a real C2S-Scale run is reported, not gated (see grade.py).
SC_THRESHOLDS = {"correct": 0.90, "wrong": 0.02, "doublet_recall": 0.85, "doublet_fp": 2,
                 "composition_tol": 0.05, "isg_recall": 6, "false_calls": 3}
REQUEST_AT = "2026-11-21T10:00:00Z"
N_GOLDEN = 20
CI_CREATED_AT = "2026-11-20T09:30:00Z"
INCIDENT_AT = "2026-11-20T15:05:00Z"
FAKE_SHA = "0" * 40

SEED_GITIGNORE = ".nospace/\n.tokn/\n.grade_out/\n.pytest_out/\n.pytest_cache/\n__pycache__/\nresults/\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matrix_tsv(genes, sample_ids, mat) -> str:
    lines = ["gene\t" + "\t".join(sample_ids)]
    for g, row in zip(genes, mat):
        lines.append(g + "\t" + "\t".join(str(int(v)) for v in row))
    return "\n".join(lines) + "\n"


def generate(seed: int, samples=None, low_rin=(LOW_RIN_SAMPLE,), reversed_ids=None,
             rin_override: dict | None = None, lib_scale: float = 1.0) -> dict:
    """Simulate counts. Returns matrices plus the planted truth.

    The defaults reproduce the shipped 12-sample case byte for byte. The stress ladder
    (stress.py, grader-side) passes other designs: a sample list, which samples are
    degraded (RIN < 6), which libraries are really reverse-stranded (default: batch B2),
    fixed RIN values (borderline 6.0-6.5) and a library-size scale (dropout).
    """
    samples = SAMPLES if samples is None else samples
    rng = np.random.default_rng(seed)
    genes = [f"GENE{i:05d}" for i in range(1, N_GENES + 1)]
    mu = np.clip(np.exp(rng.normal(np.log(200.0), 1.2, N_GENES)), 5, 50000)
    eligible = np.flatnonzero(mu >= 80)
    n_de = int(round(N_GENES * DE_FRACTION))
    de_idx = np.sort(rng.choice(eligible, n_de, replace=False))
    lfc = np.zeros(N_GENES)
    lfc[de_idx] = rng.choice([-1.0, 1.0], n_de) * rng.uniform(1.5, 3.0, n_de)
    batch_eff = rng.normal(0.0, 0.25, N_GENES)
    lib = rng.uniform(0.7, 1.4, len(samples)) * lib_scale
    # Opposite-strand background: expression-independent, a few % of sense.
    anti_level = np.exp(rng.normal(np.log(200.0), 1.2, N_GENES)) * 0.02
    rins = np.round(rng.uniform(7.0, 9.6, len(samples)), 1)
    low_rin = set(low_rin)

    sense = np.zeros((N_GENES, len(samples)), dtype=np.int64)
    anti = np.zeros_like(sense)
    for j, (sid, cond, batch) in enumerate(samples):
        m = mu * lib[j]
        if cond == "treated":
            m = m * np.power(2.0, lfc)
        if batch == "B2":
            m = m * np.power(2.0, batch_eff)
        if sid in low_rin:
            m = m * np.exp(rng.normal(0.0, 1.2, N_GENES)) * 0.6  # degraded library
            rins[j] = 4.1
        elif rin_override and sid in rin_override:
            rins[j] = rin_override[sid]
        lam = rng.gamma(1.0 / DISPERSION, m * DISPERSION)
        sense[:, j] = rng.poisson(lam)
        anti[:, j] = rng.poisson(anti_level * lib[j])

    counts = sense.copy()
    opposite = anti.copy()
    flip = (set(reversed_ids) if reversed_ids is not None
            else {sid for sid, _, batch in samples if batch == REVERSED_BATCH})
    rev = []
    for j, (sid, _, _) in enumerate(samples):
        if sid in flip:  # declared forward, really reverse
            counts[:, j], opposite[:, j] = anti[:, j], sense[:, j]
            rev.append(sid)

    de_genes = {genes[i]: round(float(lfc[i]), 4) for i in de_idx}
    strength = mu[de_idx] * np.abs(lfc[de_idx])
    golden_idx = de_idx[np.argsort(-strength, kind="mergesort")[:N_GOLDEN]]
    golden = sorted((genes[i], "up" if lfc[i] > 0 else "down") for i in golden_idx)
    return {
        "genes": genes, "counts": counts, "opposite": opposite, "rins": rins,
        "de_genes": de_genes, "golden": golden, "reversed": rev,
        "lfc": lfc, "batch_eff": batch_eff, "mu": mu,
    }


def samples_tsv(rins, confounded: bool) -> str:
    lines = ["sample_id\tcondition\tbatch\trin\tstrandedness_declared\tsubject_ref"]
    for j, (sid, cond, batch) in enumerate(SAMPLES):
        if confounded:
            batch = "B1" if cond == "control" else "B2"
        lines.append(f"{sid}\t{cond}\t{batch}\t{rins[j]:.1f}\tforward\tSUBJ-{j + 1:04d}")
    return "\n".join(lines) + "\n"


def ci_replay_record(head_sha: str = FAKE_SHA) -> dict:
    """GENERATED replay of a failing CI run (local-ci intake format, schema 2)."""
    return {
        "schema": 2, "databaseId": 7001, "attempt": 1, "headSha": head_sha, "headBranch": "main",
        "workflowName": "rnaseq-de",
        "displayTitle": "[generated] DE golden check failed: invariants violated (RIN, strandedness, BH-FDR, integer counts)",
        "url": "https://ci.example.invalid/example-lab/transcriptomics-de/runs/7001",
        "conclusion": "failure", "createdAt": CI_CREATED_AT, "repo": "example-lab/transcriptomics-de",
        "failingJob": "invariants", "jobs": [{"name": "invariants", "conclusion": "failure"}],
        "log": ("GENERATED REPLAY DATA (not a real CI run). pytest -q: FAILED "
                "test_counts_reject_non_integer, test_low_rin_samples_excluded, test_bh_fdr_reference_values, "
                "test_strandedness_inferred_from_data; batch B2 libraries look antisense "
                "(sense fraction < 0.1) although strandedness_declared=forward; S05 has RIN 4.1 and "
                "entered DE; padj equals the raw p-value. Stress replay: with batches imbalanced 2:1 "
                "across conditions the log2FC error does not shrink as samples are added (batch leaks "
                "into the condition effect)."),
    }


def incident_record() -> dict:
    """GENERATED staging incident, appended by run.py after v1 ships."""
    return {
        "kind": "incident", "id": "INC-RNASEQ-0001", "severity": "sev2", "at": INCIDENT_AT,
        "title": "[generated] staging DE report exposes subject identifiers; confounded design not refused",
        "body": ("GENERATED INCIDENT (synthetic). On staging, report.md listed the subject_ref column "
                 "(SUBJ-#### values are synthetic placeholders) and a run with data/samples_confounded.tsv "
                 "(condition == batch) produced DE calls instead of refusing. Expected: no subject_ref in any "
                 "output; ConfoundedDesignError and a non-zero exit for confounded designs."),
        "attrs": {"generated": "true", "service": "rnaseq-de", "environment": "staging"},
    }


def feature_request_record() -> dict:
    """GENERATED product request (kind "issue" => a Feature work item), appended after the incident ships."""
    return {
        "kind": "issue", "id": "REQ-SC-0001", "severity": "sev3", "at": REQUEST_AT,
        "title": "[generated] productionise the single-cell C2S annotation prototype into a hardened service",
        "body": (
            "GENERATED PRODUCT REQUEST (synthetic). rnaseq_de/sc.py + sc_cli.py are a notebook port that asks a "
            "local Cell2Sentence (C2S-Scale GGUF, llama.cpp llama-server) model for one cell type per barcode, then "
            "runs a pooled treated-vs-control t-test. Turn it into a service that meets every single-cell invariant "
            "in GLOSSARY.md and factory.yaml: validate inputs; QC (mitochondrial fraction, heterotypic doublets) "
            "BEFORE the model; descending-count cell sentences with no identifiers on the wire; anchored alias "
            "mapping plus marker verification (unmapped/unsupported => unassigned with a reason); fail closed "
            "(exit 4, nothing written) when the model is unreachable or returns an invalid completion; loopback-only "
            "endpoint; composition reported separately; per-cell-type donor pseudobulk DE with BH per type; atomic "
            "outputs celltypes.tsv, sc_qc.json, composition.tsv, sc_de.tsv, sc_report.md. Offline tests use "
            "tests/fake_c2s.py. Acceptance examples: golden/sc_celltypes_examples.tsv. Data: data/sc/."),
        "attrs": {"generated": "true", "service": "rnaseq-sc", "requester": "product"},
    }


def _copy_seed_src(out: Path) -> None:
    for src in sorted(SEED_SRC.rglob("*")):
        if src.is_dir() or "__pycache__" in src.parts or src.suffix == ".pyc":
            continue
        rel = src.relative_to(SEED_SRC)
        text = src.read_text(encoding="utf-8")
        _write(out / rel, text)


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def make_case(out: Path, key: Path, seed: int, intake: Path | None = None) -> dict:
    out, key = out.resolve(), key.resolve()
    if _inside(key, out):
        raise SystemExit(f"--key {key} is inside --out {out}: the answer key must stay outside the candidate repo")
    if intake is not None and _inside(intake.resolve(), out):
        raise SystemExit(f"--intake {intake} is inside --out {out}: intake records must stay outside the candidate repo")
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"--out {out} exists and is not empty")
    out.mkdir(parents=True, exist_ok=True)

    g = generate(seed)
    sample_ids = [s for s, _, _ in SAMPLES]
    _copy_seed_src(out)
    _write(out / ".gitignore", SEED_GITIGNORE)
    _write(out / "data" / "counts.tsv", _matrix_tsv(g["genes"], sample_ids, g["counts"]))
    _write(out / "data" / "counts_opposite.tsv", _matrix_tsv(g["genes"], sample_ids, g["opposite"]))
    _write(out / "data" / "samples.tsv", samples_tsv(g["rins"], confounded=False))
    _write(out / "data" / "samples_confounded.tsv", samples_tsv(g["rins"], confounded=True))
    _write(out / "golden" / "de_golden.tsv",
           "gene\tdirection\n" + "".join(f"{gn}\t{d}\n" for gn, d in g["golden"]))

    import sc_case  # same directory; numpy-only
    s = sc_case.generate(seed)
    _write(out / "data" / "sc" / "counts.tsv", sc_case.counts_tsv(s["genes"], s["cells"], s["counts"]))
    _write(out / "data" / "sc" / "cells.tsv", sc_case.cells_tsv(s["cells"]))
    _write(out / "golden" / "sc_celltypes_examples.tsv",
           "cell_id\tcell_type\n" + "".join(f"{c}\t{t}\n" for c, t in sc_case.golden_celltypes(s)))
    _write(out / "tests" / "fake_c2s.py", (HERE / "fake_c2s.py").read_text(encoding="utf-8"))

    protected = ["data/counts.tsv", "data/counts_opposite.tsv", "data/samples.tsv",
                 "data/samples_confounded.tsv", "golden/de_golden.tsv",
                 "data/sc/counts.tsv", "data/sc/cells.tsv", "golden/sc_celltypes_examples.tsv"]
    answer = {
        "schema": 1,
        "generated": True,
        "note": "SYNTHETIC answer key for rnaseq-software-factory; never place inside the candidate repo",
        "seed": seed,
        "n_genes": N_GENES,
        "de_genes": g["de_genes"],
        "low_rin_samples": [LOW_RIN_SAMPLE],
        "reversed_strand_samples": g["reversed"],
        "forward_strand_samples": [s for s in sample_ids if s not in g["reversed"]],
        "confounded_design": "data/samples_confounded.tsv",
        "pii_pattern": "SUBJ-",
        "thresholds": THRESHOLDS,
        "data_sha256": {rel: _sha256(out / rel) for rel in protected},
        "sc": {
            "counts": "data/sc/counts.tsv", "cells": "data/sc/cells.tsv",
            "truth": s["truth"], "low_quality": s["low_quality"], "doublets": s["doublets"], "oov": s["oov"],
            "examples": [c for c, _ in s["examples"]], "composition": s["composition"],
            "b_shift": "up", "isgs": s["isgs"], "isgs_secondary": s["isgs_secondary"],
            "isg_type": "monocyte", "thresholds": SC_THRESHOLDS,
        },
    }
    _write(key, json.dumps(answer, indent=2, sort_keys=True) + "\n")

    if intake is not None:
        _write(intake / "ci-replay.jsonl", json.dumps(ci_replay_record(), sort_keys=True) + "\n")
        _write(intake / "incident.pending.jsonl", json.dumps(incident_record(), sort_keys=True) + "\n")
        _write(intake / "request.pending.jsonl", json.dumps(feature_request_record(), sort_keys=True) + "\n")
        _write(intake / "requirements.json", json.dumps({"sc": False}) + "\n")
    return answer


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path, help="seed repo directory to create (must be empty)")
    ap.add_argument("--key", required=True, type=Path, help="answer key path, OUTSIDE --out")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--intake", type=Path, default=None, help="directory for generated intake records (outside --out)")
    a = ap.parse_args(argv)
    ans = make_case(a.out, a.key, a.seed, a.intake)
    print(json.dumps({"seed_repo": str(a.out.resolve()), "answer_key": str(a.key.resolve()),
                      "de_genes": len(ans["de_genes"]), "low_rin": ans["low_rin_samples"],
                      "reversed": ans["reversed_strand_samples"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
