# Glossary (transcriptomics / RNA-seq DE)

- **Counts** — reads assigned to each gene per sample. Non-negative integers; a
  float matrix (TPM, NumReads) is not counts and must be rejected.
- **CPM** — counts per million: counts / library size × 1e6. DE runs on log2(CPM + 1).
- **TMM** — trimmed mean of M-values; a composition-robust library-size factor.
- **RIN** — RNA Integrity Number (1–10). Libraries with RIN < 6 are degraded and
  are excluded before DE.
- **Strandedness** — which strand a stranded library reports. A library counted
  on the wrong strand has almost all reads on the opposite strand; infer it from
  the sense/opposite ratio (`data/counts_opposite.tsv`), never from
  `strandedness_declared` alone.
- **Welch t-test** — two-sample t-test without equal-variance assumption. It
  ignores batch, so it is unbiased only when every batch holds the conditions in
  the same proportion.
- **Batch-adjusted model** — per-gene linear model `expression ~ condition + batch`
  with a Student t on the condition coefficient. Required once batches are
  partially imbalanced across conditions: otherwise part of the batch effect leaks
  into log2FC and the error stops shrinking as samples are added (the stress gate's
  `off_line_exponent`).
- **BH-FDR** — Benjamini–Hochberg adjusted p-values (`padj`). Calls use
  padj < 0.05 and |log2FC| ≥ 1.
- **Confounding** — when condition and batch coincide (no batch holds both
  conditions) the effect is not identifiable; the pipeline must refuse.
- **subject_ref** — a SYNTHETIC subject identifier (`SUBJ-####`). It is
  patient-adjacent metadata: it never leaves the sample sheet and never appears
  in any output.

## Single-cell (C2S) service

Applies once the single-cell service is requested (`rnaseq_de/sc.py`, `sc_cli.py`).
The data is synthetic: a reduced PBMC panel of five cell types (`cd4_t`, `cd8_t`, `b`,
`nk`, `monocyte`) from four donors per arm.

- **UMI counts**: integer counts per gene (rows, unique HGNC-style symbols, never
  Ensembl IDs) by cell barcode (columns). Reject duplicates, floats and empty
  barcodes with exit 2, before anything goes to the model.
- **QC before the model**: drop cells whose mitochondrial (`MT-`) fraction is
  above 20% (`qc_status=low_quality`), and heterotypic doublets, where two or more
  lineage panels (T, B, myeloid) are detected (`qc_status=doublet`). The model
  never sees a dropped cell.
- **Cell sentence**: the genes with count > 0, ordered by descending count (ties
  broken by symbol), top 200, sent in the model-card prompt verbatim at
  temperature 0. Only gene symbols go on the wire, never a cell, sample or
  subject identifier.
- **C2S-Scale**: Cell2Sentence, a Gemma-2 model trained on cell sentences, served
  locally as a GGUF by llama.cpp `llama-server`. Endpoints are loopback only.
- **The model proposes, the guardrail disposes**: the completion is matched
  against an anchored, versioned alias table. The mapped label must then be
  supported by at least 2 of its own markers in the sentence's top 100 genes, with
  no stronger rival panel. Anything else becomes `unassigned` with a reason
  (`unmapped`, `ambiguous`, `unsupported`). A label is never inferred from markers.
- **Fail closed**: if the endpoint is unreachable or a completion is invalid, exit 4
  with no outputs. Never fabricate a label.
- **Composition**: cell-type fractions per sample and per condition, reported
  separately from expression. An abundance shift is not differential expression.
- **Donor pseudobulk DE**: sum each (donor, cell type) with at least 3 cells, and
  require at least 3 donors per arm. Then apply library offsets, a declared
  direction-blind expression filter, a moderated t, and BH within each cell type.
  Never pool cells as if they were replicates.
- **Outputs** (written atomically to `--out`):
  - `celltypes.tsv`: `cell_id sample_id condition qc_status candidate cell_type verified reason marker_hits`
  - `composition.tsv`: `level` is `sample`, `condition_pooled` or `condition_donor_mean`, then `sample_id condition cell_type n_cells n_total fraction`
  - `sc_de.tsv`: `cell_type gene log2fc pvalue padj`
  - `sc_qc.json`, `sc_report.md`