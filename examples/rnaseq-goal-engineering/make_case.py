#!/usr/bin/env python3
"""Generate a bulk RNA-seq case instance (deterministic; numpy + stdlib only).

Usage:
    python make_case.py                          # default seed, writes into this folder
    python make_case.py --seed 7 --replicates 4 --out instance-s7

Writes, relative to --out (default: this file's directory):
    case/counts.tsv          genes x samples raw integer counts
    case/samples.tsv         sample_id, condition, batch
    case/TASK.md             the case brief (same text for every instance)
    answer_key/truth.tsv     gene_id, is_de, true_log2fc   (NOT for the solver)

Generative model (all synthetic; no real subjects or data)
    count_gj ~ NegBin(mean = mu_gj, dispersion = phi_g)   [Var = mu + phi*mu^2]
    mu_gj    = base_g * depth_j * 2^( lfc_g * [treated_j] + bfx_g * [batch B_j] )
  * base_g  : two populations, "expressed" (log-normal, median ~90) and
              "low" (log-normal, median ~0.4) that should be filtered out.
  * phi_g   : mean-dispersion trend (higher for low counts) x log-normal scatter.
  * depth_j : log-normal library-size factor.
  * bfx_g   : batch B vs A log2 shift; 60% of genes have a sizeable effect.
  * lfc_g   : non-zero only for the truly DE genes (drawn among expressed genes).
  Design is balanced: N control + N treated in each of 2 batches, so batch is
  orthogonal to condition but still inflates variance if ignored.

Re-running with the same seed, replicates and numpy major version reproduces
byte-identical files. A SHA-256 of each output is printed.
"""
import argparse
import hashlib
import os

import numpy as np

DEFAULT_SEED = 20240607
N_GENES = 4000
N_DE = 280                     # truly DE genes
FRAC_LOW = 0.25                # fraction of genes that are lowly expressed
DE_MIN_BASE = 10.0             # DE genes are drawn among genes with base >= this

TASK_MD = r"""# Case study: treatment effect in a two-batch bulk RNA-seq experiment

## Scientific question
A synthetic bulk RNA-seq experiment compares **treated** vs **control** samples.
Libraries were prepared in two batches (A and B). Which genes respond to
treatment, in which direction, and by how much (log2 fold change, treated vs
control)?

All data are synthetic (no real subjects). Nothing in this brief or in the data
files reveals which genes are truly responsive; you must infer that from the data.

## Files you are given (in this `case/` directory)
| File | Content |
|---|---|
| `counts.tsv` | Tab-separated, genes x samples. Header: `gene_id` then one column per sample. Values are **raw integer read counts** (not normalised). |
| `samples.tsv` | Tab-separated. Columns: `sample_id`, `condition` (`control`/`treated`), `batch` (`A`/`B`). |

Each sample is one independent biological replicate (no technical repeats, no pairing).
Design facts you should verify yourself from `samples.tsv` and report in the QC section:
number of samples, replicates per condition x batch cell, and whether batch is
confounded with condition.

## Constraints
- Python 3 with **numpy and the standard library only** (no scipy, pandas, statsmodels, R).
  You must implement the statistics yourself (including any p-value distribution function).
- Deterministic: if your method uses randomness, fix the seed.
- Do not edit the input files. Write outputs to a new directory `solution/` next to `case/`
  (i.e. `solution/results.tsv`, `solution/report.md`, and your code, e.g. `solution/analysis.py`).
- Do not look for or use any file outside `case/`.

## Required analysis steps
1. **Library-size normalisation** of the raw counts (e.g. median-of-ratios, TMM, or
   another documented method). Report the per-sample size factors in the QC section.
2. **Low-count filtering** before testing. State the rule you used and how many genes it removed.
3. **Batch-aware differential expression test** for condition (treated vs control),
   with `batch` included as a covariate in the model (a count model such as a
   negative-binomial GLM, or a linear model on suitably transformed normalised
   counts, are both acceptable). Provide a two-sided p-value per tested gene.
4. **Benjamini-Hochberg FDR** adjustment across all genes that were tested.
5. A **results table** and a short **report** (schemas below).

## Required outputs

### `solution/results.tsv`
Tab-separated, one row per gene in `counts.tsv` (all 4000 genes, each exactly once,
same `gene_id` strings). Exact header, in this order:

| Column | Meaning |
|---|---|
| `gene_id` | gene identifier as in `counts.tsv` |
| `baseMean` | mean of size-factor-normalised counts across all samples |
| `log2FoldChange` | estimated log2(treated / control), adjusted for batch; `NA` if not tested |
| `pvalue` | raw two-sided p-value in [0, 1]; `NA` if not tested |
| `padj` | Benjamini-Hochberg adjusted p-value in [0, 1]; `NA` if not tested |

Genes removed by your low-count filter must have `NA` in `log2FoldChange`, `pvalue`
and `padj`. A gene's `padj` must never be smaller than its `pvalue`.
`log2FoldChange` must be on the **log2** scale and signed so that positive means
higher in treated.

### `solution/report.md`
A short Markdown report (at least 150 words) containing, at minimum, a heading that
contains the word **QC** (for example `## QC`) with:
- design summary (samples per condition x batch, confounding check);
- library sizes and size factors, and any outlier samples you saw;
- the low-count filter rule and number of genes kept / removed;
- a check of whether batch affects expression (e.g. PCA or a count of genes with a
  large batch coefficient) and how you handled it;
- the p-value histogram or another calibration check.

Plus a **Results** section giving the number of genes with `padj < 0.05`, split into
up- and down-regulated, and the top 10 genes by adjusted p-value; and a
**Limitations** section (replicate number, model assumptions, anything unassessed).

## Acceptance criteria (objective; checked numerically)
A call is a gene with `padj < 0.05`. Your `results.tsv` is graded against a hidden
per-gene truth. All of the following must hold:

| # | Criterion | Threshold |
|---|---|---|
| 1 | Schema: all five required columns present | required |
| 2 | Integrity: every `gene_id` known and unique; `pvalue`, `padj` within [0, 1]; `padj >= pvalue` for every row | required |
| 3 | Number of calls at `padj < 0.05` | >= 20 |
| 4 | Precision of calls (true positives / calls) | >= 0.80 (i.e. empirical FDR <= 0.10) |
| 5 | Recall (true positives / all truly responsive genes) | >= 0.70 |
| 6 | Coverage: share of truly responsive genes that receive a finite `padj` (i.e. were not filtered out) | >= 0.95 |
| 7 | Pearson correlation of estimated vs true log2 fold change over truly responsive genes | >= 0.90 |
| 8 | Filtering: among genes whose mean raw count across samples is < 1, share that receive a finite `padj` | <= 0.25 |
| 9 | Report: has a heading containing "QC" and is at least 150 words | required |

Criteria 3-8 are evaluated on `results.tsv`; criterion 9 on `report.md`. Note the
tension between criteria 6 and 8: filter too aggressively and you lose true signal,
too leniently and you test uninformative genes.

## Self-check before submitting
- Re-run your code from scratch and confirm identical output.
- Confirm `results.tsv` has 4000 data rows plus the header, and that `padj` is monotone
  with `pvalue` among tested genes.
- Confirm your statements in the report match your `results.tsv` (counts of calls, etc.).
"""


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--replicates", type=int, default=3,
                    help="samples per condition x batch cell (default 3, i.e. 12 samples)")
    ap.add_argument("--out", default=None,
                    help="output folder (default: this script's folder)")
    a = ap.parse_args()
    here = a.out or os.path.dirname(os.path.abspath(__file__))

    rng = np.random.default_rng(a.seed)
    G = N_GENES

    # ---- samples: balanced 2 conditions x 2 batches, shuffled IDs ----------
    cells = [(c, b) for c in ("control", "treated") for b in ("A", "B")
             for _ in range(a.replicates)]
    order = rng.permutation(len(cells))
    cells = [cells[i] for i in order]
    J = len(cells)
    sample_ids = [f"S{j + 1:02d}" for j in range(J)]
    cond = np.array([1 if c == "treated" else 0 for c, _ in cells])
    batch = np.array([1 if b == "B" else 0 for _, b in cells])

    # ---- gene-level parameters ---------------------------------------------
    low = rng.random(G) < FRAC_LOW
    base = np.where(low,
                    rng.lognormal(np.log(0.4), 0.9, G),
                    np.clip(rng.lognormal(np.log(90.0), 1.4, G), 2.0, 8000.0))
    trend = 0.03 + 1.0 / base
    phi = np.clip(trend * rng.lognormal(0.0, 0.4, G), 0.01, 2.0)

    big_batch = rng.random(G) < 0.60
    bfx = np.where(big_batch, rng.normal(0, 1.0, G), rng.normal(0, 0.1, G))

    eligible = np.flatnonzero((~low) & (base >= DE_MIN_BASE))
    de_idx = rng.choice(eligible, size=N_DE, replace=False)
    lfc = np.zeros(G)
    mag = np.clip(0.75 + rng.exponential(0.6, N_DE), 0.75, 3.5)
    sign = np.where(rng.random(N_DE) < 0.55, 1.0, -1.0)
    lfc[de_idx] = sign * mag
    is_de = np.zeros(G, dtype=int)
    is_de[de_idx] = 1

    # ---- library depth and counts ------------------------------------------
    depth = np.clip(np.exp(rng.normal(0.0, 0.35, J)), 0.5, 2.0)
    log2mu = (np.log2(base)[:, None] + np.log2(depth)[None, :]
              + lfc[:, None] * cond[None, :] + bfx[:, None] * batch[None, :])
    mu = 2.0 ** log2mu
    shape = 1.0 / phi[:, None]
    lam = rng.gamma(shape, mu / shape)          # gamma mean = mu, var = phi*mu^2
    counts = rng.poisson(lam).astype(np.int64)

    # ---- write ---------------------------------------------------------------
    os.makedirs(os.path.join(here, "case"), exist_ok=True)
    os.makedirs(os.path.join(here, "answer_key"), exist_ok=True)
    gene_ids = [f"GENE{i + 1:05d}" for i in range(G)]

    cpath = os.path.join(here, "case", "counts.tsv")
    with open(cpath, "w", newline="\n") as fh:
        fh.write("gene_id\t" + "\t".join(sample_ids) + "\n")
        for g in range(G):
            fh.write(gene_ids[g] + "\t" + "\t".join(str(v) for v in counts[g]) + "\n")

    spath = os.path.join(here, "case", "samples.tsv")
    with open(spath, "w", newline="\n") as fh:
        fh.write("sample_id\tcondition\tbatch\n")
        for j in range(J):
            fh.write(f"{sample_ids[j]}\t{cells[j][0]}\t{cells[j][1]}\n")

    bpath = os.path.join(here, "case", "TASK.md")
    with open(bpath, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(TASK_MD)

    tpath = os.path.join(here, "answer_key", "truth.tsv")
    with open(tpath, "w", newline="\n") as fh:
        fh.write("gene_id\tis_de\ttrue_log2fc\n")
        for g in range(G):
            fh.write(f"{gene_ids[g]}\t{is_de[g]}\t{lfc[g]:.6f}\n")

    # ---- summary -------------------------------------------------------------
    lib = counts.sum(axis=0)
    print(f"seed={a.seed} replicates={a.replicates} genes={G} samples={J} "
          f"DE={int(is_de.sum())} low-expressed={int(low.sum())}")
    print("library sizes:", lib.tolist(), f"(max/min = {lib.max() / lib.min():.2f})")
    for p in (cpath, spath, bpath, tpath):
        print(f"sha256 {os.path.relpath(p, here)}: {sha256(p)}")


if __name__ == "__main__":
    main()
