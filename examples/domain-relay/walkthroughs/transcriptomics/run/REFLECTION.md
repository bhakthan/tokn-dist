# REFLECTION: transcriptomics relay, "RNA-seq library QC gate before differential expression"

## What changed between the first and final answer

**Per-sample items (S01–S06): no change.** `status`, `overall`, `phase`, `blockers`, `gates`, `per_metric` and `input_metrics` are the same in both files. None of the critique findings asked for a status change, and none happened.

**Fields that did not change:** `compare_samples`, `batch_confound_full`, `batch_confound_retained`, `de_interpretable_as_is` (still false), `replicate_counts`, `protocol_context`, `overall_verdict`, `confidence` (still 0.9), `limitations` and `unassessed_checks`.

**Changes in the study-level `gates` array:**
- `batch_confound_retained` changed from `"fail"` to `"hard_block"`, the tool's literal status. **Cause: C2.**
- `required_metric_gate_DataCompleteness` changed from `"fail"` to `"pass"`. Its detail now reads "Derived compliance rollup, not a separate tool verdict: held for all positive statuses … S05 returned hard_block and received cannot_certify". **Cause: C3.**

**`discrepancies` grew from `[]` to 4 entries.** Each is marked as causing no status change.
- S06: the rrna_rate rationale says ">15% is a strong warning", but the value falls in the FAIL band. **Cause: C4(a).**
- S06: the protocol_consistency gate uses a ">20%" cut that is not in the metric grammar. **Cause: C4(b).**
- S06: phase is QUARANTINED although its only FAIL metric has `hardGate=false`. **Cause: C7.**
- Overall: CAPABILITIES gap 1 and PLAN said protocol consistency was not tool-verified, but the live assessor output does include data_completeness and protocol_consistency gates. **No critique finding asked for this.** REVISE added it after its own reruns.

**`provenance` gained 4 keys:**
- `serialization_conventions`: documents that `items` is an array with `id` fields, and that per-sample gate records use `gate` while study rollups use `name`. **Cause: C6 and C8.** The fix was documentation; the shape itself was kept.
- `optional_metric_explanations`: records that PLAN Step 10 was skipped and that explanations come from the assessor's rationale strings. **Cause: C5.**
- `revision_verification`: records REVISE's reruns. This answers the decision's routing, not a specific finding.
- `remediation_limit`: says the generic FASTQ/BAM remediation text does not supply a measured RIN. **No critique finding asked for this.**

**`critique_response` grew from `[]` to 8 entries, C1–C8**, all `fixed`.

**C1 (wrong source for the assay description)** was fixed only in RESULT.md, according to `critique_response`. result.json's `provenance.inputs.study_layout` already credited BRIEF.md in v1. I have not checked the RESULT.md edit.

## Where TOKN's harness helped

- **`assess_rnaseq_quality`** made all six status decisions on its own, with no model arithmetic.
  - **data_completeness gate:** returned `hard_block` for S05 ("required metric(s) missing: [rin] — cannot certify quality on unmeasured evidence"). This gave INCOMPLETE → cannot_certify with no imputation, so the fail-closed design worked.
  - **Hard gate on RIN:** S03's rin=5.9 failed the hard gate (blocker: "HARD-GATE failure"), so S03 was excluded even though its other six metrics passed.
  - **protocol_consistency gate:** returned `fail` for S06 ("polyA library has 22.4% rRNA (>20%): polyA selection likely failed"). This is a protocol-level check that CAPABILITIES.md had wrongly listed as a gap.
  - **Inclusive boundaries:** S02's values exactly on the thresholds (rin 7.0, unique_mapping_rate 80.0) returned PASS. PLAN's boundary-discrepancy trigger therefore never fired.
- **`check_batch_confound`** made the most important catch of the run:
  - The full design returned `pass` ("not perfectly confounded").
  - The retained design (S01, S02, S04) returned `hard_block` ("batch effect and biology are inseparable").
  - Without the second call, removing three samples by QC would have quietly produced a confounded DE contrast. PLAN's mechanical rule for building R ("include ∪ flag_for_review") made the call easy to reproduce, and both CRITIQUE and REVISE got the same result.
- **`compare_samples`** cross-checked all six per-sample verdicts. The worst-first ranking (S05, S03, S06, S04, S01, S02) matched, so there was no discrepancy.
- **`list_qc_metrics` and `recommend_qc_thresholds`** let DISCOVER confirm that the README and the live polyA grammar agree. That gave PLAN and CRITIQUE a verified threshold table.
- **DECIDE's gate questions** gave independent confirmation that no gate was bypassed: positive_despite_gate=0.0059 and confounded_contrast_trusted=0.023.
- **Determinism made verification cheap.** The domain tools are deterministic, so CRITIQUE's reruns were a real reproduction check and not just a re-reading of the answer.

## Proposed /teach rule

`/teach In transcriptomics QC runs, copy every gate status verbatim from the tool output (e.g. hard_block, never relabel it fail), and log every tool-internal threshold tension (rationale text vs pass/warn band, protocol_consistency cuts, phase vs hardGate) under discrepancies, marked "no status change".`
