# transcriptomics-de (SYNTHETIC fixture)

A small RNA-seq differential-expression pipeline over **generated** data
(`make_case.py` in TOKN's `rnaseq-software-factory`). No real samples or
subjects. `subject_ref` values are synthetic placeholders.

```
python -m rnaseq_de.cli --counts data/counts.tsv --counts-opposite data/counts_opposite.tsv \
    --samples data/samples.tsv --out results
python -m rnaseq_de.sc_cli --sc-counts data/sc/counts.tsv --cells data/sc/cells.tsv \
    --c2s-url http://127.0.0.1:8091 --out results_sc   # single-cell prototype
python -m pytest -q
```

Invariants: integer counts; RIN ≥ 6; strandedness inferred from data; BH-FDR;
confounded designs refused; no `subject_ref` in outputs. See `GLOSSARY.md`.
`data/` and `golden/` are inputs. Do not edit them.
