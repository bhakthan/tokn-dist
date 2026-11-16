# How this case was authored

The case in `case/` and `answer_key/` comes from a generator (`make_case.py`) that
was written to a short brief. The brief fixes the deliverables and constraints but
leaves the science to the author. The design choices are below so you can judge
whether the case fits your own experiments.

## Design

- **Synthetic counts, fixed seed.** Gene means are log-normal in two populations:
  expressed genes (median count about 90) and lowly expressed genes (median about
  0.4). Counts are negative-binomial, with a dispersion trend that rises as the mean
  falls. Library sizes vary by several-fold.
- **Balanced batch design.** Each condition has the same number of samples in each
  batch. Batch is therefore not confounded with condition, but it still inflates
  the residual variance of any test that ignores it. About 60% of genes carry a
  batch shift.
- **Planted signal.** 280 genes are truly differentially expressed, with
  |log2 fold change| between 0.75 and 3.5, drawn only from expressed genes. The
  rest are null.
- **Replicates are the parameter that changes between instances.** The default
  instance has 3 samples per condition-by-batch cell. A 4-per-cell instance is
  used to show that a stated method has to adapt to the design.

## Why the answer key is separate

`answer_key/truth.tsv` holds the planted truth. Anyone who can read it can
reproduce the grade without doing the analysis. So the key must stay outside the
folder the solver works in. `case/` holds only what a solver is allowed to see:
the counts, the sample sheet and the brief. `answer_key/grade.py` checks a results
table against the truth, and its thresholds are the same as the criteria in
`case/TASK.md`.

## Limits of the case

- It is synthetic. It tests whether the statistics are correct on data with a known
  answer. It does not show how a method behaves on real assays.
- A grade of PASS on one seed is one sample. Generate a few seeds before you trust
  a method.
