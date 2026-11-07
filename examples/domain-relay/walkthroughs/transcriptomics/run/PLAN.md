# PLAN — RNA-seq library QC gate before differential expression (transcriptomics)

Planner stage. Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/qc_metrics.json`, `inputs/design.json`.
Nothing has been executed. Every tool verdict below is still to be obtained by the Executor.

## Objective

Give each of S01–S06 exactly one status (include / flag_for_review / exclude / cannot_certify), based only on the `overall` verdict from `assess_rnaseq_quality`. Then use `compare_samples` and two `check_batch_confound` calls (full design and retained design) to report whether a treated-vs-ctrl DE contrast is still interpretable.

## Steps

General rules for every step:
- Copy input values exactly from `inputs/`. Do not add, impute, round or reformat any metric. Numbers stay as JSON numbers, e.g. `7.0` and `80.0` stay as they are.
- Save every tool response verbatim, in full, for use in `result.json` (see Acceptance criteria).
- Do not call any tool that is not named here. If a named tool turns out to be unavailable, stop and record it as a gap. Do not substitute another tool.

### Step 0 — Protocol context (all items; does not change any status)
- Items: S01–S06 (study-level context).
- Tool: `recommend_qc_thresholds`
- Input: `{"protocol": "polyA"}` (from `inputs/qc_metrics.json` → `protocol`).
- Also call `list_qc_metrics` with `{"input": {}}` to record the metric grammar the verdicts were checked against.
- What would change status: nothing directly. If the returned polyA thresholds differ from the table in CAPABILITIES.md, record the difference under `discrepancies` in `result.json`. Sample statuses still follow the `assess_rnaseq_quality` verdict alone (Brief rule 1).

### Steps 1–6 — Per-sample QC (one call per sample)
Tool: `assess_rnaseq_quality`. Call it once per sample with exactly these inputs:

1. **S01**
   `{"sample": "S01", "metrics": {"rin": 8.4, "unique_mapping_rate": 88.2, "rrna_rate": 3.1, "duplication_rate": 14.0, "nrf": 0.86, "exonic_rate": 71.0, "genes_detected": 16850}}`
2. **S02**
   `{"sample": "S02", "metrics": {"rin": 7.0, "unique_mapping_rate": 80.0, "rrna_rate": 4.8, "duplication_rate": 18.5, "nrf": 0.83, "exonic_rate": 68.2, "genes_detected": 16120}}`
   Note: RIN and unique_mapping_rate sit exactly on the pass thresholds. Brief rule 2 says thresholds are inclusive (≥). Accept the tool's verdict as given. If the tool gives a non-PASS verdict for a value that is at the threshold, keep the tool's status and also log a `discrepancy` that cites the per-metric result.
3. **S03**
   `{"sample": "S03", "metrics": {"rin": 5.9, "unique_mapping_rate": 91.5, "rrna_rate": 2.4, "duplication_rate": 12.0, "nrf": 0.90, "exonic_rate": 74.1, "genes_detected": 18900}}`
4. **S04**
   `{"sample": "S04", "metrics": {"rin": 7.6, "unique_mapping_rate": 84.0, "rrna_rate": 6.2, "duplication_rate": 34.0, "nrf": 0.71, "exonic_rate": 66.0, "genes_detected": 15800}}`
5. **S05**
   `{"sample": "S05", "metrics": {"unique_mapping_rate": 89.7, "rrna_rate": 3.0, "duplication_rate": 11.2, "nrf": 0.91, "exonic_rate": 72.5, "genes_detected": 17640}}`
   Do **not** add a `rin` key. It is absent in the input, and the input note says "S05's RIN was not recorded."
6. **S06**
   `{"sample": "S06", "metrics": {"rin": 8.1, "unique_mapping_rate": 86.3, "rrna_rate": 22.4, "duplication_rate": 16.0, "nrf": 0.84, "exonic_rate": 63.0, "genes_detected": 15400}}`

What changes each item's status: only the returned `overall` verdict (PASS/WARN/FAIL/INCOMPLETE), mapped by the Decision rules below. Record these alongside it: `phase`, `blockers`, and the per-metric results. For WARN, also record the names of the metrics at WARN. For FAIL, also record the names of the metrics at FAIL and whether any of them is a hard gate. For INCOMPLETE, also record which required metrics are missing.

### Step 7 — Batch-level ranking (all items; does not change any status)
- Tool: `compare_samples`
- Input: the full `samples` object from `inputs/qc_metrics.json`, unchanged:
  `{"samples": {"S01": {"rin": 8.4, "unique_mapping_rate": 88.2, "rrna_rate": 3.1, "duplication_rate": 14.0, "nrf": 0.86, "exonic_rate": 71.0, "genes_detected": 16850}, "S02": {"rin": 7.0, "unique_mapping_rate": 80.0, "rrna_rate": 4.8, "duplication_rate": 18.5, "nrf": 0.83, "exonic_rate": 68.2, "genes_detected": 16120}, "S03": {"rin": 5.9, "unique_mapping_rate": 91.5, "rrna_rate": 2.4, "duplication_rate": 12.0, "nrf": 0.90, "exonic_rate": 74.1, "genes_detected": 18900}, "S04": {"rin": 7.6, "unique_mapping_rate": 84.0, "rrna_rate": 6.2, "duplication_rate": 34.0, "nrf": 0.71, "exonic_rate": 66.0, "genes_detected": 15800}, "S05": {"unique_mapping_rate": 89.7, "rrna_rate": 3.0, "duplication_rate": 11.2, "nrf": 0.91, "exonic_rate": 72.5, "genes_detected": 17640}, "S06": {"rin": 8.1, "unique_mapping_rate": 86.3, "rrna_rate": 22.4, "duplication_rate": 16.0, "nrf": 0.84, "exonic_rate": 63.0, "genes_detected": 15400}}}`
- What changes status: nothing. Statuses come from Steps 1–6. Cross-check rule: if `compare_samples` gives any sample a verdict that differs from that sample's Step 1–6 `overall`, keep the Step 1–6 status and record the mismatch under `discrepancies`.

### Step 8 — Confound check, full design (study-level)
- Tool: `check_batch_confound`
- Input (copied from `inputs/design.json`):
  `{"batches": {"S01": "B1", "S02": "B2", "S03": "B2", "S04": "B1", "S05": "B1", "S06": "B2"}, "conditions": {"S01": "ctrl", "S02": "treated", "S03": "ctrl", "S04": "ctrl", "S05": "treated", "S06": "treated"}}`
- What changes: no sample status. Record the verdict and any `hard_block` flag verbatim.

### Step 9 — Confound check, retained design (study-level)
- Run this only after Steps 1–6 are complete.
- Build the retained set R mechanically: R = every sample whose final status is `include` or `flag_for_review`. Keep the order S01…S06.
- Tool: `check_batch_confound`
- Input: `batches` and `conditions` from `inputs/design.json`, filtered to the keys in R. Values are copied unchanged. Both maps must have the same key set.
- Call it even if R has fewer than 2 samples or only one condition. Record what the tool returns. If the tool errors, record the error verbatim; do not invent a verdict.
- What changes: no sample status. If the result contains `hard_block` (true, or a verdict equal to `hard_block`), set `de_interpretable_as_is = false`. Otherwise set it to `true`, subject to the reasoned caveats in the Gates section.
- Also report, from design.json and R only, how many retained samples there are per condition and per batch × condition cell. These counts are reasoned, not tool-verified (CAPABILITIES gap 8).

### Optional Step 10 — Metric explanations (no status change)
- Tool: `explain_qc_metric`, with `{"metric": "<key>"}`.
- Call it once for each distinct metric key that appears as WARN or FAIL in Steps 1–6. Use the output only for explanatory text in RESULT.md.

## Decision rules

Sample status is a function of the `assess_rnaseq_quality` `overall` field for that sample, and of nothing else.

| `overall` returned | status | required accompanying fields |
|---|---|---|
| `PASS` | `include` | phase (expected `ANALYSIS_READY`) |
| `WARN` | `flag_for_review` | phase (expected `FLAGGED`); list of every metric whose per-metric verdict is WARN |
| `FAIL` | `exclude` | phase (`QUARANTINED` if a hard gate failed, otherwise as returned); list of FAIL metrics; `hard_gate_failure` true/false |
| `INCOMPLETE` | `cannot_certify` | list of missing required metrics; statement that no value was imputed |
| tool error, no response, or an `overall` value outside these four | `cannot_certify` | `reason: "tool_error"` plus the verbatim error. Retry exactly once with identical input before applying this rule |

Tie-breakers and invariants:
- Do not override a verdict by your own threshold arithmetic. If your reading of the thresholds disagrees with the tool, the tool verdict sets the status and the disagreement goes under `discrepancies`.
- If the returned phase does not match the expected phase for that verdict (e.g. PASS but not ANALYSIS_READY), keep the status from `overall` and log a discrepancy.
- Never mark a sample `include` unless its `overall` is literally `PASS`.
- Study-level: `de_interpretable_as_is = false` if and only if the Step 9 result signals `hard_block`. Step 8's result is reported but does not determine this field.
- Protocol-consistency observations are reasoned, not tool-verified (CAPABILITIES gap 1), and never change status. One example: a high rRNA rate in a polyA library may indicate failed poly(A) selection. Label any such note `reasoned`.

## Gates

These must hold before any positive status (`include` or `flag_for_review`) is given:
1. **Required-metric gate (DataCompleteness):** `rin` and `unique_mapping_rate` are both present in the input map as measured values. A missing one gives INCOMPLETE → `cannot_certify` (this applies to S05). No imputation.
2. **Hard-gate QC:** neither RIN nor unique_mapping_rate is in its FAIL band, as reported by the tool. A hard-gate FAIL gives QUARANTINED → `exclude`.
3. **No metric in a fail band:** any per-metric FAIL makes `overall` FAIL → `exclude`, including non-hard-gate metrics such as `rrna_rate`.
4. **Tool provenance:** the status must rest on a recorded `assess_rnaseq_quality` response for that exact sample and exact input. No response means no positive status.

Before any statement that DE is interpretable:
5. **Batch-confound gate (retained design):** Step 9 must not return `hard_block`. If it does, RESULT.md must say that the treated-vs-ctrl contrast on the retained samples cannot be separated from batch as it stands.
6. **Not exercisable here (record as unassessed):** DownstreamGate / the PreToolUse DE block, the compbio multiple-testing gate, the library-layout (paired-end) check, and the confidence-tier caps (CAPABILITIES gaps 2, 3, 4, 6). None of these may be claimed as passed.

Language rule: a status of `include` means the sample is fit for analysis under TOKN local QC policy. It is not evidence of biological signal, and it is not a universal suitability claim.

## Acceptance criteria

`result.json` is complete only if it contains all of the following:
1. `items`: exactly six entries, keys S01–S06, each with:
   - `status`: one of `include` | `flag_for_review` | `exclude` | `cannot_certify`
   - `overall`, `phase` and `blockers`, copied from the tool response
   - `per_metric`: the tool's per-metric results, verbatim
   - `warn_metrics`: required when status is `flag_for_review`, must be non-empty
   - `fail_metrics` and `hard_gate_failure`: required when status is `exclude`
   - `missing_required`: required when status is `cannot_certify` due to INCOMPLETE
   - `input_metrics`: the exact map that was passed, identical to `inputs/qc_metrics.json`
2. `compare_samples`: the full response, including the worst-first ranking.
3. `batch_confound_full`: the input and the verbatim response from Step 8.
4. `batch_confound_retained`: `retained_samples` (list R), the filtered input, and the verbatim response from Step 9.
5. `de_interpretable_as_is`: a boolean derived by the rule above, plus `replicate_counts` (per condition, and per batch × condition, for R), labelled `source: "derived from design.json"`.
6. `protocol_context`: the outputs of `recommend_qc_thresholds` (polyA) and `list_qc_metrics`.
7. `discrepancies`: a list; it may be empty, but the key must be present.
8. `unassessed_checks`: a list containing at least the items in Gates §6.
9. `provenance`: for every number in `result.json` and RESULT.md, the tool call or input file it came from. No number may lack a source. Data must be noted as synthetic (per the input notes).

Consistency checks the Executor must run before finishing:
- Each `status` matches its `overall` per the Decision rules table.
- R equals the set of `include` ∪ `flag_for_review` samples.
- No `input_metrics` map contains a key or value that is absent from or different to the input file. In particular, S05 has no `rin`.
- `RESULT.md` reports both confound verdicts and uses calibrated language (QC PASS = fitness for analysis).
