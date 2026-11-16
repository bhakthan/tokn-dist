# Author a reproducible transcriptomics case study

You are authoring a self-contained, well-defined bulk RNA-seq case study that a
*different* agent will later solve without seeing your answer key. Design the
science yourself; this brief only fixes the deliverable shape.

## Constraints
- Python 3 with **numpy and the standard library only** (no scipy, pandas, R).
- Everything deterministic from a fixed seed.
- Realistic biology: negative-binomial counts with gene-wise dispersion, variable
  library sizes, a batch effect partly confounded with nothing (balanced design),
  lowly expressed genes that should be filtered, and a modest number of truly
  differentially expressed genes with known log2 fold changes.

## Deliverables (all in the workspace root)
1. `make_case.py` - generates the data below from a fixed seed; re-runnable.
2. `case/counts.tsv` - genes x samples integer count matrix (gene_id column + samples).
3. `case/samples.tsv` - sample metadata (sample_id, condition, batch).
4. `case/TASK.md` - the solver's brief: the scientific question, the files, the
   required outputs (exact file names and column schemas), and objective,
   numerically checkable acceptance criteria. It must NOT reveal the truth.
   Require at least: library-size normalisation, low-count filtering, a
   batch-aware differential expression test with Benjamini-Hochberg FDR,
   a results table, and a short report with a QC section.
5. `answer_key/truth.tsv` - per-gene truth (gene_id, is_de, true_log2fc).
6. `answer_key/grade.py` - grades a solver's results table against the truth
   (precision, recall, FDR at the solver's threshold, log2FC correlation on true
   DE genes) and prints PASS/FAIL against thresholds stated in `case/TASK.md`.

Run `make_case.py`, then sanity-check by running `grade.py` against a quick
oracle results file you build from truth (it must PASS), and against a
deliberately bad one (it must FAIL). Delete the oracle and bad files afterwards.
Finish with a one-paragraph summary of the case design.
