"""PROTOTYPE single-cell annotation (notebook port). Not production-ready.

python -m rnaseq_de.sc_cli --sc-counts data/sc/counts.tsv --cells data/sc/cells.tsv \
    --c2s-url http://127.0.0.1:8091 --out OUT

Calls a local Cell2Sentence (C2S-Scale) GGUF model served by llama.cpp `llama-server`
for one cell type per barcode, then compares treated vs control.
"""
from __future__ import annotations

import json
import urllib.request

import numpy as np
import pandas as pd
from scipy import stats

from . import de

PROMPT = ("The following is a list of {n} gene names ordered by descending expression level in a Homo sapiens "
          "cell. Your task is to give the cell type which this cell belongs to based on its gene expression.\n"
          "Cell sentence: {genes}.\nThe cell type corresponding to these genes is:")


def load(counts_path, cells_path):
    counts = pd.read_csv(counts_path, sep="\t", index_col=0)
    cells = pd.read_csv(cells_path, sep="\t", dtype=str).set_index("cell_id", drop=False)
    return counts, cells


def cell_sentence(col, n=200):
    return sorted(col[col > 0].index)[:n]


def ask_model(url, cell_id, subject_ref, genes):
    prompt = f"[{subject_ref}/{cell_id}] " + PROMPT.format(n=len(genes), genes=" ".join(genes))
    req = urllib.request.Request(url.rstrip("/") + "/completion",
                                 json.dumps({"prompt": prompt, "n_predict": 24}).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"].replace("<ctrl100>", "").strip().rstrip(".")
    except Exception:
        return "unknown"


def annotate(counts, cells, url):
    rows = []
    for c in counts.columns:
        label = ask_model(url, c, cells.loc[c, "subject_ref"], cell_sentence(counts[c]))
        rows.append({"cell_id": c, "subject_ref": cells.loc[c, "subject_ref"], "cell_type": label})
    return pd.DataFrame(rows)


def pooled_de(counts, cells):
    cpm = np.log2(counts / counts.sum(axis=0) * 1e6 + 1)
    t = cpm.loc[:, cells.loc[cpm.columns, "condition"] == "treated"]
    c = cpm.loc[:, cells.loc[cpm.columns, "condition"] == "control"]
    _, p = stats.ttest_ind(t, c, axis=1, equal_var=False)
    res = pd.DataFrame({"gene": cpm.index, "log2fc": t.mean(axis=1) - c.mean(axis=1), "pvalue": p})
    res["padj"] = de.bh_fdr(np.nan_to_num(res["pvalue"].to_numpy(), nan=1.0))
    return res
