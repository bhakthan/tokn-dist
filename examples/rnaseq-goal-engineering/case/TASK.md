# Case study: treatment effect in a two-batch bulk RNA-seq experiment

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
| 4 | Precision of calls (true positives / calls) | >= 0.80, and empirical false discovery proportion <= 0.10 (the latter requires precision >= 0.90) |
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
