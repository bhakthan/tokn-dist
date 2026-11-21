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
  sc_ok                    1 when the single-cell (C2S) feature is not yet required
                           (--requirements says {"sc": false}) or every sc_* check
                           passes; see grade_sc() for the individual checks
RH/Lagarias stress gate (stress.py + checks/lagarias_stress_gate.py):
  lagarias_min_gap         smallest relative gap over the stress ladder (designs the
                           shipped case does not contain); <= 0 fails, < 0.05 is a near miss
  off_line_exponent        a_hat from the log2FC error trend over N = 24..192; > 0.55 fails
                           (a fixture-specific screen, not a diagnosis of confounding)
  min_criterion_margin     tightest (bound - observed)/bound over recall, precision and
                           each tier's empirical FDR; catches near misses the compound gap hides
  c2s_euler_discrepancy    in-vocabulary C2S labels that marker evidence rejects; > 0.25 fails
  c2s_invalid_token_rate   gene tokens on the wire outside the locked gene index; > 0 fails
  gguf_anchor_kl           only with --c2s-url and --c2s-anchor: label-distribution KL of
                           this GGUF vs a reference-quant run (report-only Observer signal)
  observer_signals         lagarias_gap_erosion / off_line_zero_detected / c2s_gguf_quant_drift ...
Exit 0 for passing hard checks, 1 for a failed criterion, 2 for invalid inputs.

Single-cell checks never touch a real model: the candidate's CLI is pointed at an
in-process recording oracle (fake_c2s.py, kept next to this grader and outside the
candidate), so gates are deterministic and offline. --c2s-url additionally runs the
candidate once against a REAL loopback llama-server (C2S-Scale GGUF) and reports
live_* metrics; showcase verification separately checks the live wrong-label rate.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import stress  # noqa: E402  (grader-side ladder; lives next to this file, outside the candidate)
from checks import lagarias_stress_gate as lsg  # noqa: E402

SCRATCH = ".grade_out"
SC_VOCAB = ("cd4_t", "cd8_t", "b", "nk", "monocyte")
SC_FILES = ("celltypes.tsv", "sc_qc.json", "composition.tsv", "sc_de.tsv", "sc_report.md")
# The model-card completion prompt, fixed by the glossary. Kept here independently of
# the candidate so the expected wire traffic is recomputed, never read from the candidate.
C2S_PROMPT = ("The following is a list of {n} gene names ordered by descending expression level in a Homo sapiens "
              "cell. Your task is to give the cell type which this cell belongs to based on its gene expression.\n"
              "Cell sentence: {genes}.\nThe cell type corresponding to these genes is:")
SENTENCE_GENES = 200


def bh(p: np.ndarray) -> np.ndarray:
    n = p.size
    order = np.argsort(p, kind="mergesort")
    r = p[order] * n / np.arange(1, n + 1)
    r = np.minimum.accumulate(r[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(r, 1.0)
    return out


def run_cli(repo: Path, out: Path, samples: str, counts: str = "data/counts.tsv",
            opposite: str = "data/counts_opposite.tsv", timeout: int = 300):
    cmd = [sys.executable, "-m", "rnaseq_de.cli", "--counts", counts,
           "--counts-opposite", opposite, "--samples", samples, "--out", str(out)]
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
            raise ValueError("protected fixture modified; refusing to run candidate: " + ", ".join(bad))

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
                vals = res[["log2fc", "pvalue", "padj"]].to_numpy(dtype=float)
                if not np.isfinite(vals).all() or (vals[:, 1:] < 0).any() or (vals[:, 1:] > 1).any():
                    raise ValueError("de_results.tsv: non-finite effects or probabilities outside [0,1]")
                calls = res[(res["padj"] < th["fdr"]) & (res["log2fc"].abs() >= th["min_abs_log2fc"])]
                truth = key["de_genes"]
                tp = len({g for g, l in zip(calls["gene"], calls["log2fc"]) if g in truth and np.sign(l) == np.sign(truth[g])})
                m["recall"] = tp / len(truth)
                m["precision"] = tp / len(calls) if len(calls) else 0.0
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

        # RH/Lagarias stress ladder: extra synthetic designs, generated here, never in data/.
        ladder = stress.run_ladder(
            lambda out, s, c, o: run_cli(repo, out, s, counts=c, opposite=o), scratch / "stress")
        m["_ladder"] = ladder
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


# ---------------------------------------------------------------- single-cell (C2S)
SC_CHECKS = ("sc_prompts_exact", "sc_no_ids_on_wire", "sc_lq_exact", "sc_doublets_ok", "sc_correct_ok",
             "sc_wrong_ok", "sc_oov_unassigned", "sc_guardrail", "sc_fail_closed", "sc_non_loopback_refused",
             "sc_input_validation", "sc_row_shuffle", "sc_composition_consistent", "sc_de_bh",
             "sc_isg_recall_ok", "sc_false_calls_ok", "sc_pii_clean")


def _oracle():
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import fake_c2s  # the GRADER's copy; the candidate's tests/fake_c2s.py is never trusted here
    return fake_c2s


def run_sc(repo: Path, out: Path, url: str, counts: str, cells: str, timeout: int = 900):
    cmd = [sys.executable, "-m", "rnaseq_de.sc_cli", "--sc-counts", counts, "--cells", cells,
           "--c2s-url", url, "--out", str(out), "--workers", "4"]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        p = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-2000:]
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def _with_oracle(scratch: Path, name: str, mode: str, fn):
    """Run fn(url) against a fresh recording oracle; returns (fn result, logged requests)."""
    log = scratch / f"{name}.requests.jsonl"
    srv, url = _oracle().serve(0, mode, str(log))
    try:
        res = fn(url)
    finally:
        srv.shutdown()
        srv.server_close()
    reqs = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
    return res, reqs


def _read_counts(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", index_col=0)


def _expected_prompt(col: pd.Series) -> str:
    nz = col[col > 0]
    genes = sorted(nz.index, key=lambda g: (-int(nz[g]), g))[:SENTENCE_GENES]
    return C2S_PROMPT.format(n=len(genes), genes=" ".join(genes))


def _labels(out: Path) -> pd.DataFrame | None:
    p = out / "celltypes.tsv"
    if not p.is_file():
        return None
    df = pd.read_csv(p, sep="\t", dtype=str, keep_default_na=False)
    if {"cell_id", "cell_type"} - set(df.columns) or df["cell_id"].duplicated().any():
        return None
    if "qc_status" not in df.columns:  # no QC at all: every barcode was treated as passing
        df["qc_status"] = "pass"
    return df.set_index("cell_id")


def _no_output(out: Path) -> bool:
    return not out.exists() or not any(out.iterdir())


def _label_scores(lab: pd.DataFrame, sk: dict) -> tuple[float, float, int]:
    truth, skip = sk["truth"], set(sk["examples"]) | set(sk["low_quality"]) | set(sk["doublets"])
    known = [c for c, t in truth.items() if t in SC_VOCAB and c not in skip]
    got = lab["cell_type"].reindex(known).fillna("")
    ok = sum(got[c] == truth[c] for c in known)
    wrong = sum(got[c] in SC_VOCAB and got[c] != truth[c] for c in known)
    return ok / len(known), wrong / len(known), len(known)


def _sentence_tokens(prompt: str) -> list[str]:
    i = prompt.find("Cell sentence:")
    if i < 0:
        return []
    return prompt[i + len("Cell sentence:"):].split("\n", 1)[0].strip().rstrip(".").split()


MARKER_PANELS = {
    "cd4_t": ["CD4", "IL7R", "CCR7", "LEF1", "TCF7", "SELL", "MAL"],
    "cd8_t": ["CD8A", "CD8B", "GZMK"],
    "b": ["MS4A1", "CD79A", "CD79B", "CD19", "BANK1", "TCL1A"],
    "nk": ["GNLY", "KLRF1", "KLRD1", "PRF1", "FCGR3A", "GZMB"],
    "monocyte": ["CD14", "LYZ", "S100A8", "S100A9", "FCN1", "VCAN", "CSF1R"],
}


def _euler_discrepancy(lab: pd.DataFrame, counts: pd.DataFrame) -> float:
    if "candidate" not in lab or set(lab.index) != set(counts.columns):
        return 1.0
    post = lab[(lab["qc_status"] == "pass") & lab["candidate"].isin(SC_VOCAB)]
    unsupported = 0
    for cell, candidate in post["candidate"].items():
        col = counts[cell]
        top = set(sorted(col[col > 0].index, key=lambda g: (-int(col[g]), g))[:100])
        hits = {k: len(top.intersection(panel)) for k, panel in MARKER_PANELS.items()}
        unsupported += hits[candidate] < 2 or hits[candidate] < max(hits.values())
    return unsupported / len(post) if len(post) else 1.0


def _label_dist(lab: pd.DataFrame) -> dict[str, float]:
    labels = lab.loc[lab["qc_status"] == "pass", "cell_type"]
    if labels.empty or not labels.isin((*SC_VOCAB, "unassigned")).all():
        raise ValueError("live labels missing or outside the agreed vocabulary")
    return {t: float((labels == t).mean()) for t in (*SC_VOCAB, "unassigned")}


def _distribution(d):
    if not isinstance(d, dict) or set(d) != {*SC_VOCAB, "unassigned"}:
        raise ValueError("label_dist must contain the five vocabulary labels and unassigned")
    a = np.array([d[k] for k in (*SC_VOCAB, "unassigned")])
    if a.dtype.kind not in "fiu" or not np.isfinite(a).all() or (a < 0).any() or not np.isclose(a.sum(), 1, atol=5e-6, rtol=0):
        raise ValueError("label_dist must be finite, non-negative probabilities summing to one")
    return a


def _kl(p, q, eps=1e-4):
    a, b = _distribution(p) + eps, _distribution(q) + eps
    a, b = a / a.sum(), b / b.sum()
    return max(0.0, float(np.sum(a * np.log(a / b))))


def grade_sc(repo: Path, key: dict, scratch: Path, live_url: str = "",
             anchor: dict | None = None) -> tuple[dict, list[str], list[str]]:
    sk, th = key["sc"], key["sc"]["thresholds"]
    m: dict = {}
    fails: list[str] = []
    notes: list[str] = []
    counts_rel, cells_rel = sk["counts"], sk["cells"]
    counts = _read_counts(repo / counts_rel)
    ids = set(counts.columns) | {c.split("_")[0] for c in counts.columns}

    out = scratch / "sc_main"
    (rc, log), reqs = _with_oracle(scratch, "main", "normal", lambda u: run_sc(repo, out, u, counts_rel, cells_rel))
    lab = _labels(out) if rc == 0 else None
    if lab is None:
        notes.append(f"sc_cli failed or wrote no valid celltypes.tsv (exit {rc}): {log.strip()[-400:]}")
        for k in SC_CHECKS:
            m[k] = False
        m["sc_correct"] = m["sc_wrong"] = 0.0
        m["c2s_euler_discrepancy"] = m["c2s_invalid_token_rate"] = 1.0
        return m, [f"{k} is false" for k in SC_CHECKS], notes

    # QC before the model
    lq = sorted(lab.index[lab["qc_status"] == "low_quality"])
    dbl = set(lab.index[lab["qc_status"] == "doublet"])
    m["sc_lq_exact"] = lq == sorted(sk["low_quality"])
    hit, fp = len(dbl & set(sk["doublets"])), len(dbl - set(sk["doublets"]))
    m["sc_doublet_recall"], m["sc_doublet_fp"] = round(hit / len(sk["doublets"]), 4), fp
    m["sc_doublets_ok"] = m["sc_doublet_recall"] >= th["doublet_recall"] and fp <= th["doublet_fp"]

    # Wire traffic: exact prompt multiset for cells that should reach the model, nothing else.
    send = [c for c in counts.columns if c not in set(sk["low_quality"]) and c not in dbl]
    want = collections.Counter(_expected_prompt(counts[c]) for c in send)
    got = collections.Counter(r["prompt"] for r in reqs)
    m["sc_prompts_exact"] = want == got and all(r.get("temperature") in (0, 0.0) for r in reqs)
    if not m["sc_prompts_exact"]:
        notes.append(f"sc prompts: expected {sum(want.values())} cell sentences, got {sum(got.values())}; "
                     f"{sum((want - got).values())} missing, {sum((got - want).values())} unexpected "
                     "(order genes by descending count, ties by symbol, top 200, template verbatim, temperature 0)")
    toks = {t.strip(".,:;[]()/") for r in reqs for t in r["prompt"].split()}
    m["sc_no_ids_on_wire"] = not (toks & ids) and not any(key.get("pii_pattern", "SUBJ-") in r["prompt"] for r in reqs)
    # Every gene token sent must exist in the locked gene index (the counts file the grader holds).
    sent = [t for r in reqs for t in _sentence_tokens(r["prompt"])]
    m["c2s_invalid_token_rate"] = (sum(t not in counts.index for t in sent) / len(sent) if sent else 1.0)

    # Labels (oracle)
    m["sc_correct"], m["sc_wrong"], _ = _label_scores(lab, sk)
    m["c2s_euler_discrepancy"] = _euler_discrepancy(lab, counts)
    m["sc_n_pass"] = int((lab["qc_status"] == "pass").sum())
    m["sc_correct_ok"] = m["sc_correct"] >= th["correct"]
    m["sc_wrong_ok"] = m["sc_wrong"] <= th["wrong"]
    m["sc_oov_unassigned"] = all(lab["cell_type"].get(c, "") not in SC_VOCAB for c in sk["oov"])

    # Composition: recompute from celltypes.tsv; the planted B-cell shift must point the right way.
    comp_ok = False
    cp = out / "composition.tsv"
    if cp.is_file():
        comp = pd.read_csv(cp, sep="\t", dtype={"sample_id": str}, keep_default_na=False)
        pooled = comp[comp.get("level", pd.Series(dtype=str)) == "condition_pooled"] if "level" in comp else comp.iloc[0:0]
        cells_df = pd.read_csv(repo / cells_rel, sep="\t", dtype=str).set_index("cell_id")
        post = lab[lab["qc_status"] == "pass"].join(cells_df[["condition"]], rsuffix="_sheet")
        cond_col = "condition_sheet" if "condition_sheet" in post else "condition"
        comp_ok = len(pooled) > 0
        frac = {}
        for cond in ("control", "treated"):
            pc = post[post[cond_col] == cond]
            for t in (*SC_VOCAB, "unassigned"):
                mine = float((pc["cell_type"] == t).mean()) if len(pc) else 0.0
                row = pooled[(pooled["condition"] == cond) & (pooled["cell_type"] == t)]
                if len(row) != 1 or abs(float(row["fraction"].iloc[0]) - mine) > 0.001:
                    comp_ok = False
                frac[(cond, t)] = mine
        comp_ok = comp_ok and frac.get(("treated", "b"), 0) > frac.get(("control", "b"), 1)
    m["sc_composition_consistent"] = comp_ok

    # Within-type DE
    de_ok, isg_hits, false_calls = False, 0, 99
    dp = out / "sc_de.tsv"
    if dp.is_file():
        de = pd.read_csv(dp, sep="\t")
        if {"cell_type", "gene", "log2fc", "pvalue", "padj"} <= set(de.columns):
            de_ok = len(de) > 0 and not de.duplicated(["cell_type", "gene"]).any()
            for _, g in de.groupby("cell_type"):
                p, q = g["pvalue"].to_numpy(dtype=float), g["padj"].to_numpy(dtype=float)
                de_ok = de_ok and bool(np.allclose(q, bh(p), rtol=1e-4, atol=1e-8))
            calls = de[(de["padj"] < key["thresholds"]["fdr"]) & (de["log2fc"].abs() >= key["thresholds"]["min_abs_log2fc"])]
            mono = calls[calls["cell_type"] == sk["isg_type"]]
            isg_hits = int(((mono["gene"].isin(sk["isgs"])) & (mono["log2fc"] > 0)).sum())
            allowed = set(sk["isgs"]) | set(sk["isgs_secondary"])
            false_calls = int(len(calls) - ((calls["cell_type"] == sk["isg_type"]) & calls["gene"].isin(allowed)).sum())
    m["sc_de_bh"] = de_ok
    m["sc_isg_recall"], m["sc_false_calls"] = isg_hits, false_calls
    m["sc_isg_recall_ok"] = isg_hits >= th["isg_recall"]
    m["sc_false_calls_ok"] = false_calls <= th["false_calls"]

    pat = key.get("pii_pattern", "SUBJ-")
    leaks = [f.name for f in out.rglob("*") if f.is_file() and pat in f.read_text(encoding="utf-8", errors="replace")]
    m["sc_pii_clean"] = not leaks
    if leaks:
        notes.append("subject_ref leaked into sc outputs: " + ", ".join(sorted(leaks)))

    # Guardrail: an adversarial model must not get a wrong label accepted.
    fo = scratch / "sc_flip"
    (rc, _), _ = _with_oracle(scratch, "flip", "flip", lambda u: run_sc(repo, fo, u, counts_rel, cells_rel))
    fl = _labels(fo) if rc == 0 else None
    m["sc_guardrail"] = fl is not None and _label_scores(fl, sk)[1] == 0.0
    if not m["sc_guardrail"]:
        notes.append(f"guardrail: adversarial completions were accepted or the run failed (exit {rc})")

    # Fail closed: model dies mid-run, returns garbage, or is not there at all.
    # A correct service aborts within seconds; the 90 s cap only bounds a fail-open
    # prototype that retries every cell, and later probes are skipped once one fails.
    closed = True
    for mode in ("die_after:30", "invalid"):
        if not closed:
            break
        o = scratch / f"sc_{mode.split(':')[0]}"
        (rc, _), _ = _with_oracle(scratch, mode.split(":")[0], mode, lambda u, o=o: run_sc(repo, o, u, counts_rel, cells_rel, timeout=90))
        closed = closed and rc == 4 and _no_output(o)
    if closed:
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        dead = f"http://127.0.0.1:{s.getsockname()[1]}"
        s.close()
        o = scratch / "sc_dead"
        rc, _ = run_sc(repo, o, dead, counts_rel, cells_rel, timeout=90)
        closed = rc == 4 and _no_output(o)
    m["sc_fail_closed"] = closed
    o = scratch / "sc_remote"
    rc, _ = run_sc(repo, o, "http://example.com:8091", counts_rel, cells_rel, timeout=60)
    m["sc_non_loopback_refused"] = rc == 2 and _no_output(o)

    # Input validation: rejected before ANY model traffic.
    lines = (repo / counts_rel).read_text(encoding="utf-8").splitlines()
    dup = scratch / "dup_genes.tsv"
    dup.write_text("\n".join(lines + [lines[5]]) + "\n", encoding="utf-8")
    ens = scratch / "ensembl.tsv"
    ens.write_text("\n".join([lines[0], "ENSG00000000003" + lines[1][lines[1].index("\t"):]] + lines[2:]) + "\n",
                   encoding="utf-8")
    valid = True
    for bad in (dup, ens):
        o = scratch / f"sc_{bad.stem}"
        (rc, _), rq = _with_oracle(scratch, bad.stem, "normal", lambda u, o=o, b=bad: run_sc(repo, o, u, str(b), cells_rel))
        valid = valid and rc == 2 and not rq and _no_output(o)
    m["sc_input_validation"] = valid

    # Gene-row order must not change any label.
    shuf = scratch / "shuffled.tsv"
    body = lines[1:]
    np.random.default_rng(11).shuffle(body)
    shuf.write_text("\n".join([lines[0]] + body) + "\n", encoding="utf-8")
    so = scratch / "sc_shuffled"
    (rc, _), _ = _with_oracle(scratch, "shuffled", "normal", lambda u: run_sc(repo, so, u, str(shuf), cells_rel))
    sl = _labels(so) if rc == 0 else None
    m["sc_row_shuffle"] = sl is not None and sl["cell_type"].reindex(lab.index).equals(lab["cell_type"])

    for k in SC_CHECKS:
        if not m.get(k):
            fails.append(f"{k} is false")
    if m["c2s_invalid_token_rate"] > 0:
        fails.append(f"c2s_invalid_token_rate {m['c2s_invalid_token_rate']} > 0: a gene token outside the locked index went on the wire")
    if m["c2s_euler_discrepancy"] > lsg.MAX_C2S_EULER:
        fails.append(f"c2s_euler_discrepancy {m['c2s_euler_discrepancy']} > {lsg.MAX_C2S_EULER}")

    # Report-only: the REAL model, if the caller started one.
    if live_url:
        lo = scratch / "sc_live"
        t0 = time.time()
        rc, log = run_sc(repo, lo, live_url, counts_rel, cells_rel, timeout=3600)
        m["live_rc"], m["live_seconds"] = rc, round(time.time() - t0, 1)
        ll = _labels(lo) if rc == 0 else None
        if ll is None or set(ll.index) != set(counts.columns):
            fails.append(f"live C2S run failed (exit {rc}): {log.strip()[-300:]}")
        else:
            m["live_correct"], m["live_wrong"], _ = _label_scores(ll, sk)
            post = ll[ll["qc_status"] == "pass"]
            m["live_unassigned"] = int((post["cell_type"] == "unassigned").sum())
            m["live_euler_discrepancy"] = _euler_discrepancy(ll, counts)
            m["live_label_dist"] = _label_dist(ll)
            selected = sorted(post.index)
            cohort = json.dumps([key["data_sha256"][counts_rel], selected], separators=(",", ":"))
            m["anchor_cohort"] = hashlib.sha256(cohort.encode()).hexdigest()
            if anchor is not None:
                if anchor.get("anchor_cohort") != m["anchor_cohort"]:
                    raise ValueError("anchor cohort differs or is missing: re-run the reference quant on these counts and QC-passing cells")
                # Quantisation drift: the same cells, this GGUF vs a recorded anchor run
                # (for example the Q8_0 of the same model). Not gated: an Observer signal.
                m["gguf_anchor_kl"] = _kl(m["live_label_dist"], anchor["label_dist"])
            if m["live_wrong"] > 0.05:
                fails.append(f"live C2S wrong-label rate {m['live_wrong']} > 0.05")
    return m, fails, notes


def stress_gate(m: dict, key: dict, sc_required: bool) -> list[str]:
    """Fold the ladder (and the sc Euler-dual case) into the RH/Lagarias gate. Mutates m."""
    th = key["thresholds"]
    ladder = m.pop("_ladder", None)
    if not ladder or ladder["problems"]:
        m.update(lagarias_min_gap=-1.0, off_line_exponent=1.0, min_criterion_margin=-1.0, observer_signals=[])
        return ladder["problems"] if ladder else ["stress ladder did not run"]
    cases = list(ladder["stress_cases"])
    if sc_required:
        cases.append({"case_id": "sc_c2s_euler_dual", "stress_tier_n": max(2, int(m.get("sc_n_pass", 2))),
                      "emp_fdr": 0.0, "target_fdr": th["fdr"],
                      "c2s_euler_discrepancy": float(m.get("c2s_euler_discrepancy", 1.0)),
                      "note": "C2S label vs marker evidence on QC-passing cells (fake_c2s oracle)"})
    rep = lsg.evaluate_suite(cases, ladder["scaling_trace"], min_recall=th["recall"])
    worst = rep["worst_stress_case"]
    m["lagarias_min_gap"] = worst["relative_gap"]
    m["lagarias_worst_case"] = worst["case_id"]
    m["off_line_exponent"] = rep["estimated_critical_exponent_a"]
    m["scaling_trace"] = rep["scaling_trace"]
    m["stress_cases"] = [{k: c.get(k) for k in ("recall", "case_id", "stress_tier_n", "relative_gap", "emp_fdr", "batch_leak",
                                                  "c2s_euler_discrepancy") if k in c} for c in rep["ranked_stress_cases"]]
    margins = {"recall": lsg.criterion_margin(m.get("recall", 0.0), th["recall"], upper=False),
               "precision": lsg.criterion_margin(m.get("precision", 0.0), th["precision"], upper=False)}
    margins.update(rep["criterion_margins"])
    m["criterion_margins"] = margins
    tight = min(margins, key=margins.get)
    m["min_criterion_margin"] = margins[tight]
    m["min_criterion_margin_at"] = tight
    m["observer_signals"] = rep["observer_signals"]
    fails = []
    if margins[tight] <= 0:
        fails.append(f"criterion has no positive margin: {tight} (relative margin {margins[tight]:.5g})")
    if worst["relative_gap"] <= 0:
        fails.append(f"Lagarias counterexample: relative gap {worst['relative_gap']} <= 0 on {worst['case_id']}")
    if rep["estimated_critical_exponent_a"] > lsg.MAX_OFF_LINE_A:
        fails.append(f"off-line zero: error exponent {rep['estimated_critical_exponent_a']:.5g} > {lsg.MAX_OFF_LINE_A} "
                     "(slower error decay than the fixture cutoff; inspect the batch adjustment)")
    # 0 < gap < 0.05 and small criterion margins are near misses: the factory's needs_human band, not a failure here.
    return fails


def input_error(reason):
    defaults = dict(recall=0, precision=0, pii_clean=0, confounded_refused=0, data_intact=0,
                    sc_ok=0, lagarias_min_gap=-1, off_line_exponent=1, min_criterion_margin=-1,
                    c2s_euler_discrepancy=1, c2s_invalid_token_rate=1)
    for k, v in defaults.items():
        print(f"TOKN_METRIC {k}={v}")
    print(json.dumps({"pass": False, "error": str(reason), **defaults}))
    return 2


def main(argv=None) -> int:
    try:
        return _main(argv)
    except SystemExit as exc:
        if exc.code != 2:
            raise
        return input_error("invalid grader arguments; see --help")
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        return input_error(f"cannot grade the supplied inputs or candidate outputs: {exc}")


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--key", default=os.environ.get("FACTORY_RNASEQ_KEY", ""), help="answer_key.json (or $FACTORY_RNASEQ_KEY)")
    ap.add_argument("--repo", default=".", type=Path, help="candidate worktree (default: cwd)")
    ap.add_argument("--requirements", default=os.environ.get("FACTORY_RNASEQ_REQUIREMENTS", ""),
                    help='requirements.json kept OUTSIDE the candidate; {"sc": true} turns on the single-cell checks')
    ap.add_argument("--c2s-url", default="", help="optional loopback llama-server with a real C2S GGUF (report-only)")
    ap.add_argument("--c2s-anchor", default="",
                    help="optional c2s-showcase.json (label_dist and anchor_cohort) from the same cells and model family; "
                         "with --c2s-url, reports gguf_anchor_kl (quantisation drift, report-only)")
    a = ap.parse_args(argv)
    if not a.key:
        return input_error("no answer key: pass --key or set FACTORY_RNASEQ_KEY")
    kp = Path(a.key)
    if not kp.is_file():
        return input_error(f"answer key not found: {kp}")
    repo = a.repo.resolve()
    if repo in kp.resolve().parents:
        return input_error("answer key is inside the candidate repo; refusing")
    key = json.loads(kp.read_text(encoding="utf-8"))
    req = {}
    if a.requirements:
        rp = Path(a.requirements)
        if not rp.is_file() or repo in rp.resolve().parents:
            return input_error(f"requirements file missing or inside the candidate repo: {rp}")
        req = json.loads(rp.read_text(encoding="utf-8"))
    anchor = None
    if a.c2s_anchor:
        try:
            if not a.c2s_url:
                return input_error("--c2s-anchor requires --c2s-url")
            anchor = json.loads(Path(a.c2s_anchor).read_text(encoding="utf-8"))
            _distribution(anchor["label_dist"])
        except (OSError, KeyError, ValueError, TypeError) as e:
            return input_error(f"unreadable --c2s-anchor: {e}")
    if not isinstance(req, dict) or (a.requirements and type(req.get("sc")) is not bool):
        return input_error("requirements must contain a boolean sc flag")
    if (req.get("sc") and "sc" not in key) or (a.c2s_url and not req.get("sc")):
        return input_error("single-cell grading needs sc: true in requirements and an sc answer key")
    if a.c2s_url:
        from run import loopback_url
        if not loopback_url(a.c2s_url, plain_http=True):
            return input_error("--c2s-url must be a plain-HTTP loopback URL without credentials, query or fragment")
    metrics, problems = grade(repo, key)
    sc_required = bool(req.get("sc")) and "sc" in key
    metrics["sc_required"] = sc_required
    if sc_required:
        scratch = repo / (SCRATCH + "_sc")
        shutil.rmtree(scratch, ignore_errors=True)
        scratch.mkdir(parents=True)
        try:
            sm, sfails, snotes = grade_sc(repo, key, scratch, a.c2s_url, anchor)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        metrics.update(sm)
        metrics["sc_ok"] = not sfails
        problems += sfails + [f"note: {n}" for n in snotes]
    else:
        metrics["sc_ok"] = True
        # No single-cell service yet: no model traffic, nothing to disagree. Same convention as sc_ok.
        metrics["c2s_euler_discrepancy"] = metrics["c2s_invalid_token_rate"] = 0.0
    problems += stress_gate(metrics, key, sc_required)
    kl = metrics.get("gguf_anchor_kl")
    if isinstance(kl, float) and kl > lsg.MAX_GGUF_KL:
        metrics.setdefault("observer_signals", []).append(
            {"type": "c2s_gguf_quant_drift", "severity": "medium", "gguf_kl_div": kl,
             "action": "check anchor comparability and decoding before changing quantisation"})
    failures = [p for p in problems if not p.startswith("note: ")]
    # Factory metric protocol: thresholds in factory.yaml read these lines.
    # They precede the JSON line, which callers parse as the LAST line.
    for k in ("recall", "precision", "n_called", "sc_correct", "sc_wrong", "sc_isg_recall", "sc_false_calls",
              "live_correct", "live_wrong", "lagarias_min_gap", "off_line_exponent", "min_criterion_margin",
              "c2s_euler_discrepancy", "c2s_invalid_token_rate", "gguf_anchor_kl"):
        if isinstance(metrics.get(k), (int, float)) and not isinstance(metrics.get(k), bool):
            print(f"TOKN_METRIC {k}={metrics[k]}")
    for k in ("rin_filtered", "strandedness_detected", "confounded_refused", "bh_applied",
              "integer_counts_enforced", "pii_clean", "data_intact", "sc_ok"):
        print(f"TOKN_METRIC {k}={1 if metrics.get(k) else 0}")
    print(json.dumps({**metrics, "pass": not failures, "failures": problems}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
