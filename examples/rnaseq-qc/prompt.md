# Task: RNA-seq library QC gate before differential expression

You are the bioinformatics QC lead for a bulk RNA-seq study comparing treated and control cell lines (poly(A)-selected libraries, paired-end). Six libraries have been sequenced across two batches. Before the analyst starts differential expression (DE), the study lead needs a mechanical QC decision for every sample and a statement on whether the design is still interpretable after excluding samples.

The data is synthetic but realistic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/qc_metrics.json` | `protocol` and, per sample, the QC metrics map: `rin`, `unique_mapping_rate`, `rrna_rate`, `duplication_rate`, `nrf`, `exonic_rate`, `genes_detected` (rates in %) |
| `demo-input/design.json` | `batches` (sample → sequencing batch) and `conditions` (sample → treated/ctrl) |

## Items to assess

`S01`, `S02`, `S03`, `S04`, `S05`, `S06`

## Status vocabulary (use exactly one per item)

- `include`: `assess_rnaseq_quality` returns overall verdict PASS (phase ANALYSIS_READY).
- `flag_for_review`: overall verdict WARN (phase FLAGGED). The sample is analyzable, but the warning metrics must be named.
- `exclude`: overall verdict FAIL, whether from a hard-gate metric (phase QUARANTINED) or from any other metric in its fail band.
- `cannot_certify`: overall verdict INCOMPLETE, because a required metric is missing. Do not guess the missing value.

## Rules

1. Call `assess_rnaseq_quality` once per sample with `{"sample": <id>, "metrics": <that sample's map>}` exactly as given. Do not add, impute or round any metric. The status follows from the tool's `overall` verdict alone, as mapped above.
2. The tool's thresholds are inclusive: a higher-is-better metric passes when it is at least the pass threshold (RIN ≥ 7, unique mapping ≥ 80%). RIN and unique mapping rate are required hard gates.
3. Call `compare_samples` with the full `samples` map to report the batch-level view.
4. Call `check_batch_confound` twice: on the full design, and on the retained design (only samples you marked `include` or `flag_for_review`). Report both verdicts. They do not change sample statuses, but a `hard_block` on the retained design means a DE contrast on it is not interpretable as it stands.
5. Every number you report must come from a tool call or the input files. Use calibrated language: QC PASS is fitness for analysis, not proof of biological signal.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"S01": "<status>"}`.
