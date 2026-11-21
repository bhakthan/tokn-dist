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
Exit 0 only when every check passes; 1 otherwise; 2 on a usage error.

Single-cell checks never touch a real model: the candidate's CLI is pointed at an
in-process recording oracle (fake_c2s.py, kept next to this grader and outside the
candidate), so gates are deterministic and offline. --c2s-url additionally runs the
candidate once against a REAL loopback llama-server (C2S-Scale GGUF) and reports
live_* metrics; those are evidence, not gates.
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
    return round(ok / len(known), 4), round(wrong / len(known), 4), len(known)


def grade_sc(repo: Path, key: dict, scratch: Path, live_url: str = "") -> tuple[dict, list[str], list[str]]:
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

    # Labels (oracle)
    m["sc_correct"], m["sc_wrong"], _ = _label_scores(lab, sk)
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

    # Report-only: the REAL model, if the caller started one.
    if live_url:
        lo = scratch / "sc_live"
        t0 = time.time()
        rc, log = run_sc(repo, lo, live_url, counts_rel, cells_rel, timeout=3600)
        m["live_rc"], m["live_seconds"] = rc, round(time.time() - t0, 1)
        ll = _labels(lo) if rc == 0 else None
        if ll is None:
            fails.append(f"live C2S run failed (exit {rc}): {log.strip()[-300:]}")
        else:
            m["live_correct"], m["live_wrong"], _ = _label_scores(ll, sk)
            post = ll[ll["qc_status"] == "pass"]
            m["live_unassigned"] = int((post["cell_type"] == "unassigned").sum())
            if m["live_wrong"] > 0.05:
                fails.append(f"live C2S wrong-label rate {m['live_wrong']} > 0.05")
    return m, fails, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--key", default=os.environ.get("FACTORY_RNASEQ_KEY", ""), help="answer_key.json (or $FACTORY_RNASEQ_KEY)")
    ap.add_argument("--repo", default=".", type=Path, help="candidate worktree (default: cwd)")
    ap.add_argument("--requirements", default=os.environ.get("FACTORY_RNASEQ_REQUIREMENTS", ""),
                    help='requirements.json kept OUTSIDE the candidate; {"sc": true} turns on the single-cell checks')
    ap.add_argument("--c2s-url", default="", help="optional loopback llama-server with a real C2S GGUF (report-only)")
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
    req = {}
    if a.requirements:
        rp = Path(a.requirements)
        if not rp.is_file() or repo in rp.resolve().parents:
            print(json.dumps({"error": f"requirements file missing or inside the candidate repo: {rp}"}))
            return 2
        req = json.loads(rp.read_text(encoding="utf-8"))
    metrics, problems = grade(repo, key)
    sc_required = bool(req.get("sc")) and "sc" in key
    metrics["sc_required"] = sc_required
    if sc_required:
        scratch = repo / (SCRATCH + "_sc")
        shutil.rmtree(scratch, ignore_errors=True)
        scratch.mkdir(parents=True)
        try:
            sm, sfails, snotes = grade_sc(repo, key, scratch, a.c2s_url)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        metrics.update(sm)
        metrics["sc_ok"] = not sfails
        problems += sfails + [f"note: {n}" for n in snotes]
    else:
        metrics["sc_ok"] = True
    failures = [p for p in problems if not p.startswith("note: ")]
    # Factory metric protocol: thresholds in factory.yaml read these lines.
    # They precede the JSON line, which callers parse as the LAST line.
    for k in ("recall", "precision", "n_called", "sc_correct", "sc_wrong", "sc_isg_recall", "sc_false_calls",
              "live_correct", "live_wrong"):
        if isinstance(metrics.get(k), (int, float)) and not isinstance(metrics.get(k), bool):
            print(f"TOKN_METRIC {k}={metrics[k]}")
    for k in ("rin_filtered", "strandedness_detected", "confounded_refused", "bh_applied",
              "integer_counts_enforced", "pii_clean", "data_intact", "sc_ok"):
        print(f"TOKN_METRIC {k}={1 if metrics.get(k) else 0}")
    print(json.dumps({**metrics, "pass": not failures, "failures": problems}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
