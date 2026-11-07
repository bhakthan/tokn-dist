# CAPABILITIES — transcriptomics QC gate (Scout stage)

Scope: items S01–S06 from BRIEF.md. This file records what TOKN can do for the brief. It does not assess any item.

Evidence sources read: BRIEF.md; inputs/qc_metrics.json (protocol polyA, 6 samples, S05 has no `rin` key); inputs/design.json (batches and conditions for S01–S06); tokn-self/introspect-slice.json; tokn-self/DOMAIN-README.md; live outputs of `list_qc_metrics` and `recommend_qc_thresholds` (protocol polyA).

## Domain tools that apply

| tool (exact name) | applies to | input fields needed | present in inputs/? |
|---|---|---|---|
| assess_rnaseq_quality | each of S01–S06 (one call per sample) | `sample` (id); `metrics` (that sample's map, passed unchanged) | yes for S01–S04, S06. S05 lacks `rin`, so a required-metric INCOMPLETE is expected; do not impute |
| compare_samples | all six samples, batch-level view | `samples` map of sample_id → metrics | yes |
| check_batch_confound | full design, and retained design (only include/flag_for_review samples) | `batches` (sample → batch); `conditions` (sample → treated/ctrl) | yes, both in inputs/design.json |
| recommend_qc_thresholds | protocol context for the whole study | `protocol` = polyA | yes (`protocol` in qc_metrics.json) |
| list_qc_metrics | reference of the metric grammar used to check verdicts | none | n/a |
| explain_qc_metric | optional explanation of any metric key that a verdict names | `metric` key | n/a |

Tool names above were checked against my visible tool list. All six exist. The README's "6 tools" count matches.

## Gates and rules that will constrain the answer

Thresholds, quoted from the live `list_qc_metrics` output (protocol polyA; inclusive):

| metric | direction | pass | warn | hard gate | required |
|---|---|---|---|---|---|
| rin | higher is better | ≥ 7 | ≥ 6 | yes | yes |
| unique_mapping_rate (%) | higher is better | ≥ 80 | ≥ 60 | yes | yes |
| rrna_rate (%) | lower is better | ≤ 10 | ≤ 15 | no | no |
| duplication_rate (%) | lower is better | ≤ 20 | ≤ 50 | no | no |
| nrf | higher is better | ≥ 0.8 | ≥ 0.5 | no | no |
| exonic_rate (%) | higher is better | ≥ 60 | ≥ 50 | no | no |
| genes_detected | higher is better | ≥ 15000 | ≥ 10000 | no | no |

Verdict rules, from the README and the brief (the code itself is not visible to me, so these are stated, not checked):
- INCOMPLETE dominates. A missing required metric (rin, unique_mapping_rate) gives INCOMPLETE and blocks certification. Missing values are not imputed.
- Overall verdict is the worst per-metric verdict. A FAIL on a hard gate quarantines the sample.
- Brief status mapping: include = PASS (ANALYSIS_READY); flag_for_review = WARN (FLAGGED); exclude = FAIL (QUARANTINED, including any non-hard-gate metric in its fail band); cannot_certify = INCOMPLETE.
- Status follows from the tool's `overall` verdict alone. No metric is added, rounded or imputed.
- check_batch_confound: a `hard_block` on the retained design means a DE contrast on it is not interpretable as it stands. Run it on both full and retained designs and report both.

Calibrated language and confidence:
- PASS means fitness for analysis, not proof of biological signal.
- Confidence hierarchy (README, not verified in a tool): measured 1.00 > derived 0.90 > imputed 0.60 > modeled 0.40. Any verdict that rests on a non-measured value is capped accordingly.
- Protocol: polyA. The README says only ffpe and ribo_deplete relax thresholds, so the base grammar above applies unchanged.

Discrepancies recorded:
- README and live tool outputs agree on every threshold listed above. No conflict found.
- The live rin rationale text reads "RIN<6 is a hard gate", while the grammar's pass/warn bands are 7/6. Both are stated above. The grammar's bands are the ones the tool applies.

## Gaps

No tool in my list covers these. They must be handled by reasoning and stated as such:
1. ProtocolConsistencyGate (e.g. high rRNA in a polyA library implies failed selection) and DataCompletenessGate are listed in the README but are not exposed as tools. Any protocol-consistency statement must be reasoned, not tool-verified.
2. DownstreamGate and the PreToolUse hook that blocks DE on non-ANALYSIS_READY samples: no DE tool is in my list, so neither can be exercised here.
3. Cross-domain compbio:multiple_testing_corrected gate: no DE run is requested, and no compbio tool is in my list. Not applicable to this stage.
4. Paired-end layout: the brief says paired-end, but no input field records library layout, and no tool checks it. Taken from the brief text only.
5. S05 `rin` is absent (noted in the input file itself). The required-metric rule makes this INCOMPLETE. No tool is provided to recover or impute it, and the brief forbids imputation. It stays cannot_certify unless a measured value appears.
6. Confidence tiers (measured/derived/imputed/modeled) are not exposed through any tool. They must be applied by reasoning.
7. Batch-condition confounding is only a yes/no verdict from check_batch_confound. Its magnitude and any effect-size estimate are not available from a tool.
8. Dataset-level DE interpretability beyond the batch check (power, replicate counts per condition after exclusions) is not covered by any tool. Replicate counts must be taken from design.json and reported as counts.
