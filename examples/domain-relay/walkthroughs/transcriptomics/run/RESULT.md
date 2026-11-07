# RNA-seq QC gate — execution report

## Scope and evidence basis

**Question and intended use.** Can each synthetic bulk RNA-seq library S01–S06 advance under the local pre-differential-expression (DE) QC policy, and does the retained treated-versus-control design remain interpretable? The unit of analysis is one library/sample identifier; no cell-level, technical-replicate, or donor-level independence is inferred. BRIEF.md describes treated and control cell lines with poly(A)-selected, paired-end libraries; the input notes establish synthetic teaching data, units, and S05's unrecorded RIN.

**Provenance.** Metrics and protocol come from `inputs/qc_metrics.json`; batches and conditions come from `inputs/design.json`. Both files explicitly identify the data as **synthetic teaching data**, not measurements from a real study. Rates are percentages, NRF is a fraction, and detected genes are counts. S05's RIN is absent and was not imputed.

**Protocol context.** `recommend_qc_thresholds(protocol="polyA")` and `list_qc_metrics` returned the same grammar:

| Metric | PASS band | WARN band | Required | Hard gate |
|---|---:|---:|:---:|:---:|
| rin | ≥ 7 | ≥ 6 | yes | yes |
| unique_mapping_rate (%) | ≥ 80 | ≥ 60 | yes | yes |
| rrna_rate (%) | ≤ 10 | ≤ 15 | no | no |
| duplication_rate (%) | ≤ 20 | ≤ 50 | no | no |
| nrf | ≥ 0.8 | ≥ 0.5 | no | no |
| exonic_rate (%) | ≥ 60 | ≥ 50 | no | no |
| genes_detected | ≥ 15,000 | ≥ 10,000 | no | no |

These thresholds and statuses are TOKN local policy for this run, not universal biological suitability rules. Item statuses below follow only `assess_rnaseq_quality`; a QC PASS means fitness for analysis under that policy, not proof of biological signal, protein abundance, pathway activity, or causation.

## S01 — `include`

**Tool evidence.** `assess_rnaseq_quality` returned `verdict=PASS`, `phase=ANALYSIS_READY`, `analyzable=true`, `blockers=null`, and `missing=null`. The exact input was `rin=8.4`, `unique_mapping_rate=88.2%`, `rrna_rate=3.1%`, `duplication_rate=14.0%`, `nrf=0.86`, `exonic_rate=71.0%`, `genes_detected=16850`; all seven returned per-metric verdicts were PASS. No metric value was added or changed (`inputs/qc_metrics.json`).

**Gate outcomes.** `data_completeness=pass` (“all required metrics supplied”) and `protocol_consistency=pass`. RIN and unique mapping therefore both cleared the assessor's hard-gate QC, and no supplied metric was in a warn or fail band. This supports inclusion for QC purposes only; it is not a biological validation.

## S02 — `include`

**Tool evidence.** `assess_rnaseq_quality` returned `verdict=PASS`, `phase=ANALYSIS_READY`, `analyzable=true`, `blockers=null`, and `missing=null`. RIN `7.0` and unique mapping `80.0%` both returned PASS with `hardGate=true`, at the inclusive pass thresholds returned by the protocol tools. The other supplied values—`rrna_rate=4.8%`, `duplication_rate=18.5%`, `nrf=0.83`, `exonic_rate=68.2%`, `genes_detected=16120`—also returned PASS. All input values are exactly those in `inputs/qc_metrics.json`.

**Gate outcomes.** `data_completeness=pass` and `protocol_consistency=pass`. Both required hard gates returned PASS, and no metric entered a warn or fail band. The assessor's threshold-boundary result is preserved without independent reclassification; inclusion remains a local QC decision, not evidence of treatment biology.

## S03 — `exclude`

**Tool evidence.** `assess_rnaseq_quality` returned `verdict=FAIL`, `phase=QUARANTINED`, `analyzable=false`, and `missing=null`. The sole per-metric FAIL was `rin=5.9`, with `hardGate=true`. The blocker was: “RNA Integrity Number = 5.9 1-10 is a HARD-GATE failure: RNA degradation biases expression quantification; RIN<6 is a hard gate (ENCODE/GTEx).” Unique mapping (`91.5%`), rRNA (`2.4%`), duplication (`12.0%`), NRF (`0.90`), exonic rate (`74.1%`), and genes detected (`18900`) returned PASS, but those values do not override the hard-gate failure. Inputs are unchanged from `inputs/qc_metrics.json`.

**Gate outcomes.** `data_completeness=pass` and `protocol_consistency=pass`, but hard-gate QC failed and the no-fail-band gate failed. The mechanical status is therefore `exclude`; remediation or replacement is a laboratory/design decision for the responsible bioinformatics lead, not something this report authorizes.

## S04 — `flag_for_review`

**Tool evidence.** `assess_rnaseq_quality` returned `verdict=WARN`, `phase=FLAGGED`, `analyzable=true`, `blockers=null`, and `missing=null`. The required warning metrics are **`duplication_rate`** at `34.0%` and **`nrf`** at `0.71`; neither is a hard gate. RIN (`7.6`), unique mapping (`84.0%`), rRNA (`6.2%`), exonic rate (`66.0%`), and genes detected (`15800`) returned PASS. Inputs are unchanged from `inputs/qc_metrics.json`.

**Gate outcomes.** `data_completeness=pass`, `protocol_consistency=pass`, and no per-metric FAIL. The sample is retained in the mechanical retained set but flagged for review of duplication and library complexity before downstream reliance. Its WARN verdict does not establish the cause of those patterns or guarantee reliable DE results.

## S05 — `cannot_certify`

**Tool evidence.** The exact supplied map contained **no `rin` key**: `unique_mapping_rate=89.7%`, `rrna_rate=3.0%`, `duplication_rate=11.2%`, `nrf=0.91`, `exonic_rate=72.5%`, `genes_detected=17640` (`inputs/qc_metrics.json`). `assess_rnaseq_quality` returned `verdict=INCOMPLETE`, `phase=QUARANTINED`, `analyzable=false`, `blockers=null`, and `missing=[rin]`. All six supplied metrics returned PASS, but they cannot substitute for the required RIN measurement. No value was imputed, estimated, or inferred.

**Gate outcomes.** `data_completeness=hard_block`: “required metric(s) missing: [rin] — cannot certify quality on unmeasured evidence.” `protocol_consistency=pass`. The required-metric gate prevents certification; this is not a measured RIN failure. The assessor's stated remediation is to rerun QC with required metrics populated and check FASTQ/BAM integrity and aligner metric outputs, subject to review by the bioinformatics QC lead.

## S06 — `exclude`

**Tool evidence.** `assess_rnaseq_quality` returned `verdict=FAIL`, `phase=QUARANTINED`, `analyzable=false`, `blockers=null`, and `missing=null`. The sole fail-band metric was **`rrna_rate=22.4%`**, with `hardGate=false`; accordingly, `hard_gate_failure=false`. RIN (`8.1`), unique mapping (`86.3%`), duplication (`16.0%`), NRF (`0.84`), exonic rate (`63.0%`), and genes detected (`15400`) returned PASS. Inputs are unchanged from `inputs/qc_metrics.json`.

**Gate outcomes.** `data_completeness=pass`, but the no-fail-band gate failed. `protocol_consistency=fail` with the detail: “polyA library has 22.4% rRNA (>20%): polyA selection likely failed; library identity is suspect.” The assessor suggests repeating poly(A) selection or switching to ribo-depletion, or re-declaring an intentionally total-RNA library and rerunning QC; that protocol change requires study-owner review and is not applied here.

## Sample comparison and design checks

### Worst-first QC ranking

`compare_samples`, called with the complete unchanged six-sample map from `inputs/qc_metrics.json`, returned:

1. S05 — INCOMPLETE, `analyzable=false`
2. S03 — FAIL, `analyzable=false`
3. S06 — FAIL, `analyzable=false`
4. S04 — WARN, `analyzable=true`
5. S01 — PASS, `analyzable=true`
6. S02 — PASS, `analyzable=true`

These verdicts agree with every per-sample assessment, so no comparison mismatch was recorded.

### Full-design batch confound — `pass`

`check_batch_confound` was called with all six batch and condition mappings exactly as supplied in `inputs/design.json`. It returned `gate=batch_confound`, `status=pass`, and “batch and condition are not perfectly confounded.” This full-design result does not override any sample verdict and does not establish that the smaller retained design is valid.

### Overall gate summary

| Gate | Status | Evidence |
|---|---|---|
| Protocol context | pass | Both protocol tools returned the same polyA grammar. |
| Required-metric compliance for positive statuses (derived rollup) | held | S01/S02/S04 returned `data_completeness=pass`; S05 returned `hard_block` and received `cannot_certify`, not a positive status. |
| Hard-gate QC | fail | S03 returned `rin=5.9 FAIL`, `hardGate=true`, `phase=QUARANTINED`. |
| No metric in fail band | fail | S03 `rin` and S06 `rrna_rate` returned FAIL. |
| Tool provenance | pass | Every item has a recorded assessor response for its exact input, including S05 without RIN. |
| Protocol consistency | fail | S06 returned `protocol_consistency=fail`; the other five returned pass. |
| Full-design batch confound | pass | The full six-sample design returned `status=pass`. |
| Retained-design batch confound | hard_block | S01/S02/S04 returned `status=hard_block`. |
| Downstream/layout/multiplicity/confidence-cap checks | n/a | Not exercisable with the available inputs and tools; none is claimed as passed. |

### Retained-design batch confound — `hard_block`

The mechanical retained set is **S01, S02, S04**: S01 and S02 are `include`, S04 is `flag_for_review`, and the other samples are not retained. Filtering both maps in `inputs/design.json` to that set gives:

- Batches: S01=B1, S02=B2, S04=B1.
- Conditions: S01=ctrl, S02=treated, S04=ctrl.

`check_batch_confound` returned `status=hard_block`: “batch is perfectly confounded with condition: batch effect and biology are inseparable — differential expression would be uninterpretable.” Therefore **`de_interpretable_as_is=false`** under the plan's decision rule. Treatment and batch cannot be separated in this retained design as it stands.

Counts below are derived directly from `inputs/design.json`, not computed by a tool: among the three retained libraries, there are **2 ctrl and 1 treated**. The batch × condition cells are **B1: 2 ctrl / 0 treated** and **B2: 0 ctrl / 1 treated**. These are library-level counts in the synthetic design, not verified independent biological-replicate counts or an estimate of statistical power.

The tool's remediation is to redesign so each batch contains multiple conditions or add biological replicates across batches before reanalysis. The permitted next step is design remediation and qualified review—not proceeding with a treatment-effect interpretation on the retained samples as-is.

## Overall verdict

S01 and S02 pass the local QC assessor, S04 is analyzable but flagged for duplication and complexity warnings, S03 and S06 are excluded, and S05 cannot be certified without a measured RIN. Although the full six-sample design is not perfectly confounded, the retained S01/S02/S04 design receives `hard_block`; consequently, a treated-versus-control DE contrast on the retained libraries is **not interpretable as-is**. These are mechanical classifications on synthetic inputs, not biological or clinical conclusions.

## Limitations and unassessed checks

- The evidence is explicitly synthetic teaching data. The per-sample `confidence=1` responses are assessor outputs, while this report's overall `confidence=0.9` follows the documented derived tier in `CAPABILITIES.md`; neither is a calibrated probability of biological validity.
- S05's RIN was not recorded. Missingness prevents certification and is neither a PASS nor a measured RIN FAIL; no imputation was performed.
- S04 still requires review of its `duplication_rate=34.0%` and `nrf=0.71` warnings. QC does not establish the cause of those warnings.
- The retained design has no treated library in B1 and no ctrl library in B2. The confound tool provides a status, not a batch-effect magnitude, effect size, or uncertainty.
- No DE model or downstream statistical analysis was run. Raw-count versus normalized-count suitability, annotation/reference validation, dispersion and effect estimates, multiple-testing correction, power, and sensitivity to exclusions remain unassessed.
- DownstreamGate/PreToolUse DE blocking, the compbio multiple-testing gate, paired-end layout validation, and operational confidence-tier caps were not exercisable and are not claimed as passed. Paired-end layout comes only from the brief text.
- Independent biological replication is not established by the sample map. Expression QC alone cannot establish biological signal, protein abundance, pathway activity, cell-composition effects, or causation.

**Responsible next step and reviewer.** The bioinformatics QC lead and study lead should resolve S03 and S06 QC issues, obtain S05's measured RIN, review S04's warnings, and redesign/replicate across batches before requesting DE. A specialized human review remains necessary before any biological interpretation or consequential downstream action.

## Numeric provenance index

Every per-sample QC number and verdict above comes from `assess_rnaseq_quality` for that sample, with its unchanged input map from `inputs/qc_metrics.json`. Thresholds come from `recommend_qc_thresholds(protocol="polyA")` and `list_qc_metrics`. Ranking order comes from `compare_samples`; both confound statuses come from `check_batch_confound`. Retained membership follows the per-sample statuses, and retained replicate counts are direct enumeration of `inputs/design.json`. The input files and `BRIEF.md` supply the synthetic-data status, assay description, and intended use. Full structured per-metric responses, exact inputs, gate details, and provenance are preserved in `result.json`.

## Re-verification and observed tool-text tensions

All six exact-input QC re-runs, full-map comparison, both threshold tools and both confound checks matched stored raw responses. No boundary, comparison-verdict or raw-response mismatch was found. The following observations are recorded in `result.json.discrepancies`; none changes a status or relaxes a gate.

- **S06 rRNA wording:** re-run returned `22.4% FAIL` with `pass<=10, warn<=15`, while rationale calls `>15%` a “strong warning.” Returned FAIL governs, not informal warning wording.
- **Separate protocol cut:** S06's `protocol_consistency=fail` uses `>20%` rRNA, absent from metric grammar's `10%/15%` cuts. These are separate checks. Failed selection/library identity is a tool-reported hypothesis, not an observed assay diagnosis.
- **S06 phase:** re-run returned `QUARANTINED` although sole FAIL metric has `hardGate=false`. Derived `hard_gate_failure=false` concerns metric gates, not phase. PLAN explicitly preserves returned phase for non-hard-gate FAIL; S06 remains `exclude`.
- **Capability-documentation gap:** CAPABILITIES.md and PLAN describe protocol consistency as reasoned/not tool-verified, but live assessor returns these gate records. They are observed software outputs, not biological validation of mechanistic explanations.

**Additional limitations.** Optional PLAN Step 10 was skipped: `explain_qc_metric` was not called. Explanations come from assessor rationale strings. External attributions such as ENCODE/GTEx were not independently verified. Generic FASTQ/BAM/aligner remediation does not provide measured RIN: S05 requires its measured RNA integrity assay record before reassessment. Confidence tiers are documented local policy, not independently enforced caps or calibrated probabilities.

**Serialization conventions.** Existing requested shape is retained: `items` is an array with unique sample `id` fields, deliberately equivalent to PLAN sample-key wording. Raw per-sample gate records use `gate`; synthesized study rollups use `name`. Consumers must distinguish schemas. Completeness summary is derived positive-status compliance, not a new tool verdict.

## Final finding and review boundary

**Finding:** retained contrast remains blocked. **Supporting evidence:** all repeated domain checks agree with stored responses. **Counterevidence/limitations:** full design passes the perfect-confounding check, retained design does not; synthetic QC cannot establish biology. **Unassessed checks:** independent biological replication, reference/annotation, strandedness, count representation/model, layout, power, multiplicity, downstream runtime blocks and enforced confidence caps. **Permitted next step and responsible reviewer:** QC lead and study lead should obtain missing measured RIN, review failed/flagged libraries and remediate design before DE interpretation. Confidence is high for mechanical synthesis, not biological validity.

## Response to critique

- **C1 — fixed:** compared input notes with BRIEF.md; corrected assay/study attribution.
- **C2 — fixed:** retained-design re-run returned `hard_block`; both summary fields now preserve it.
- **C3 — fixed:** QC re-runs confirmed completeness passes for all positive statuses and S05's certification block; clarified rollup.
- **C4 — fixed:** S06 QC and threshold re-runs confirmed rationale/band tension and separate protocol cut; recorded both, unchanged `exclude`.
- **C5 — fixed:** documented optional explanation-step skip and attribution to assessor rationale strings.
- **C6 — fixed:** inspected six unique IDs and complete fields; documented deliberate array-with-id representation, preserving requested shape.
- **C7 — fixed:** S06 re-run confirmed quarantine with non-hard-gate FAIL; explained returned phase and distinct hard-gate flag.
- **C8 — fixed:** inspected both gate schemas; documented raw `gate` versus synthesized `name`, preserving requested shape.
