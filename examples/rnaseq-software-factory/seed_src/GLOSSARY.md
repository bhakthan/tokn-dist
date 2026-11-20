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
- **Welch t-test** — two-sample t-test without equal-variance assumption.
- **BH-FDR** — Benjamini–Hochberg adjusted p-values (`padj`). Calls use
  padj < 0.05 and |log2FC| ≥ 1.
- **Confounding** — when condition and batch coincide (no batch holds both
  conditions) the effect is not identifiable; the pipeline must refuse.
- **subject_ref** — a SYNTHETIC subject identifier (`SUBJ-####`). It is
  patient-adjacent metadata: it never leaves the sample sheet and never appears
  in any output.
