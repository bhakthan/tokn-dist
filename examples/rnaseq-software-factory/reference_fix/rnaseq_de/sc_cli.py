"""Single-cell annotation service CLI.

python -m rnaseq_de.sc_cli --sc-counts data/sc/counts.tsv --cells data/sc/cells.tsv \
    --c2s-url http://127.0.0.1:8091 --out OUT [--workers 4] [--model-sha256 HEX]

Exit codes: 0 ok; 2 invalid input (nothing sent to the model, nothing written);
4 C2S model unavailable or invalid completion (fail closed: nothing written).
Outputs are staged in a sibling temp directory and published atomically.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

from . import sc

B_PANEL = ["MS4A1", "CD79A", "CD79B", "CD19", "BANK1"]


def _sample_quantiles(counts, cells, pm):
    out = {}
    lib, det = counts.sum(axis=0), (counts > 0).sum(axis=0)
    for sid, g in cells.groupby("sample_id", sort=True):
        ids = list(g.index)
        q = lambda s: [round(float(x), 2) for x in np.percentile(s[ids], [10, 50, 90])]  # noqa: E731
        out[sid] = {"n_barcodes": len(ids), "umi_q10_50_90": q(lib), "genes_q10_50_90": q(det), "pct_mito_q10_50_90": q(pm)}
    return out


def _report(qcj, comp, de_res, support, pooled, within_b):
    ccomp = comp[comp["level"] == "condition_pooled"].set_index(["condition", "cell_type"])
    lines = [
        "# Single-cell annotation report",
        "",
        "Input is SYNTHETIC. Cell-type labels are proposed by a local Cell2Sentence (C2S-Scale) model and",
        "accepted only when the controlled-vocabulary alias table maps them AND marker evidence supports them.",
        "No clinical or real-cohort performance is claimed; annotation accuracy is unknown without labels.",
        "",
        "## QC attrition (before any model call)",
        f"- barcodes in: {qcj['n_input']}; low quality (MT > {sc.MAX_PCT_MITO:g}%): {len(qcj['excluded_low_quality'])};"
        f" heterotypic doublets: {len(qcj['doublets'])}; sent to the model: {qcj['n_sent']}",
        f"- completions: {qcj['model']['completions']} (attempts {qcj['model']['attempts']});"
        f" assigned {qcj['n_annotated']}, unassigned {qcj['unassigned']} (reasons: {qcj['unassigned_reasons']})",
        "",
        "## Composition (abundance, reported separately from expression)",
        "| cell type | control | treated |",
        "|---|---|---|",
    ]
    for t in (*sc.VOCAB, sc.UNASSIGNED):
        lines.append(f"| {t} | {ccomp.loc[('control', t), 'fraction']:.3f} | {ccomp.loc[('treated', t), 'fraction']:.3f} |")
    lines += ["", "Pooled fractions over post-QC cells; per-sample counts and donor-mean fractions are in composition.tsv.",
              "This is relative abundance; there is no absolute cell count.", "",
              "## Within-type differential expression (donor pseudobulk, moderated t, BH per type)"]
    for t, s in support.items():
        n = int(de_res[(de_res["cell_type"] == t) & de_res["called"]].shape[0]) if len(de_res) else 0
        lines.append(f"- {t}: {s['status']}; donors {s['donors_control']} control / {s['donors_treated']} treated;"
                     f" cells {s['cells']}; calls {n}")
    top = de_res[de_res["called"]].sort_values(["cell_type", "padj", "gene"]).head(20) if len(de_res) else de_res
    if len(top):
        lines += ["", "| cell type | gene | log2FC | padj |", "|---|---|---|---|"]
        lines += [f"| {r.cell_type} | {r.gene} | {r.log2fc:+.2f} | {r.padj:.2e} |" for r in top.itertuples()]
    lines += ["", "## Negative control: all-cell pooled pseudobulk (do not use for inference)",
              "Pooling every cell per donor conflates abundance with expression. Mean donor log2FC:",
              "| gene | pooled log2FC | within-B log2FC |", "|---|---|---|"]
    lines += [f"| {g} | {pooled.get(g, float('nan')):+.2f} | {within_b.get(g, float('nan')):+.2f} |" for g in B_PANEL]
    lines += ["", "## Provenance", "```json", json.dumps(qcj["provenance"], indent=2), "```", ""]
    return "\n".join(lines)


def run(args):
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise sc.InputError(f"output directory {out} is not empty; refusing to overwrite results")
    client = sc.C2SClient(args.c2s_url)
    counts, cells = sc.load(args.sc_counts, args.cells)
    low, dbl, pm = sc.qc(counts)
    eligible = [c for c in counts.columns if c not in set(low) | set(dbl)]
    t0 = time.time()
    annot = sc.annotate(counts[eligible], client, workers=args.workers) if eligible else \
        pd.DataFrame(columns=["cell_id", "candidate", "cell_type", "verified", "reason", "marker_hits"])
    secs = round(time.time() - t0, 1)

    full = cells[["cell_id", "sample_id", "condition"]].copy()
    full["qc_status"] = "pass"
    full.loc[low, "qc_status"] = "low_quality"
    full.loc[dbl, "qc_status"] = "doublet"
    full = full.join(annot[["candidate", "cell_type", "verified", "reason", "marker_hits"]], how="left")
    ex = full["qc_status"] != "pass"
    full.loc[ex, "candidate"] = ""
    full.loc[ex, "cell_type"] = "excluded"
    full.loc[ex, "reason"] = full.loc[ex, "qc_status"]
    full.loc[ex, "verified"] = False
    full.loc[ex, "marker_hits"] = 0
    full["marker_hits"] = full["marker_hits"].astype(int)

    post = annot.copy()
    comp = sc.composition(post, cells) if len(post) else pd.DataFrame(
        columns=["level", "sample_id", "condition", "cell_type", "n_cells", "n_total", "fraction"])
    de_res, support = sc.pseudobulk_de(counts[eligible], post, cells) if len(post) else (pd.DataFrame(), {})
    pooled = sc.pooled_effects(counts[eligible], cells.loc[eligible], B_PANEL) if eligible else {}
    bres = de_res[de_res["cell_type"] == "b"].set_index("gene") if len(de_res) else pd.DataFrame()
    within_b = {g: round(float(bres.loc[g, "log2fc"]), 3) for g in B_PANEL if len(bres) and g in bres.index}

    reasons = annot.loc[annot["cell_type"] == sc.UNASSIGNED, "reason"].value_counts().to_dict() if len(annot) else {}
    qcj = {
        "n_input": int(counts.shape[1]), "excluded_low_quality": low, "doublets": dbl,
        "n_sent": len(eligible), "n_annotated": int((annot["cell_type"] != sc.UNASSIGNED).sum()) if len(annot) else 0,
        "unassigned": int((annot["cell_type"] == sc.UNASSIGNED).sum()) if len(annot) else 0,
        "unassigned_reasons": {str(k): int(v) for k, v in reasons.items()},
        "model_calls": client.attempts,
        "model": {"attempts": client.attempts, "completions": client.completions,
                  "retries": client.attempts - client.completions, "inference_seconds": secs},
        "qc_thresholds": {"max_pct_mito": sc.MAX_PCT_MITO, "doublet_min_umi": sc.DOUBLET_MIN_UMI,
                          "doublet_min_markers": sc.DOUBLET_MIN_MARKERS, "lineage_panels": sc.LINEAGE_PANELS},
        "per_sample": _sample_quantiles(counts, cells, pm),
        "de_support": support,
        "provenance": {
            "model_family": "Cell2Sentence C2S-Scale (GGUF via llama.cpp llama-server)",
            "server": client.describe(), "model_sha256": args.model_sha256 or "not supplied",
            "prompt_template_sha256": sc.PROMPT_SHA256, "sentence_rule": "count>0, descending count, ties by symbol",
            "sentence_genes": sc.SENTENCE_GENES, "n_predict": sc.N_PREDICT, "temperature": sc.TEMPERATURE,
            "alias_table": sc.ALIAS_VERSION, "verify_top_n": sc.VERIFY_TOP_N, "verify_min_hits": sc.VERIFY_MIN_HITS,
            "de_method": "donor pseudobulk; log2(CPM+1) with full-library offsets; filter >= "
                         f"{sc.FILTER_MIN_COUNT} UMIs in >= min(arm) donors; moderated t (Smyth 2004); BH per type",
            "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".sc-stage-", dir=out.parent))
    try:
        full[["cell_id", "sample_id", "condition", "qc_status", "candidate", "cell_type", "verified", "reason",
              "marker_hits"]].to_csv(stage / "celltypes.tsv", sep="\t", index=False)
        (stage / "sc_qc.json").write_text(json.dumps(qcj, indent=2, default=str), encoding="utf-8")
        comp.to_csv(stage / "composition.tsv", sep="\t", index=False)
        cols = ["cell_type", "gene", "log2fc", "pvalue", "padj", "called", "n_control", "n_treated", "n_cells"]
        (de_res if len(de_res) else pd.DataFrame(columns=cols)).to_csv(stage / "sc_de.tsv", sep="\t", index=False)
        (stage / "sc_report.md").write_text(_report(qcj, comp, de_res, support, pooled, within_b) if len(post) else
                                           "# Single-cell annotation report\n\nNo QC-passed cells.\n", encoding="utf-8")
        if out.exists():
            out.rmdir()
        os.replace(stage, out)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return qcj


def main(argv=None):
    p = argparse.ArgumentParser(prog="rnaseq_de.sc_cli", description="C2S single-cell annotation + pseudobulk DE")
    p.add_argument("--sc-counts", required=True)
    p.add_argument("--cells", required=True)
    p.add_argument("--c2s-url", required=True, help="loopback llama-server serving a C2S-Scale GGUF")
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--model-sha256", default="", help="sha256 of the GGUF the launcher loaded (provenance)")
    a = p.parse_args(argv)
    try:
        q = run(a)
    except (sc.InputError, FileNotFoundError) as e:
        print(f"invalid input: {e}", file=sys.stderr)
        return 2
    except sc.ModelUnavailableError as e:
        print(f"C2S model unavailable -- no labels were written: {e}\n"
              "Start llama-server with a C2S-Scale GGUF on loopback and retry.", file=sys.stderr)
        return 4
    print(f"annotated {q['n_annotated']}/{q['n_sent']} QC-passed cells "
          f"({q['unassigned']} unassigned; {len(q['excluded_low_quality'])} low-quality and "
          f"{len(q['doublets'])} doublets excluded) -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
