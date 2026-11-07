# REFLECTION — mobility relay: functional-safety release gate for five ADAS functions

## What changed between the first and final answer

None of the five statuses changed. Both versions give FN-AEB and FN-ACC `release_candidate`, FN-LKA `decomposition_invalid`, FN-TJA `hw_metrics_fail` and FN-APA `vv_incomplete`. Both keep `confidence: 0.98`. The changes were structural and about provenance:

| Change from v1 to final | Caused by |
|---|---|
| Every item gained `deciding_rule` (R1, D1a, R1, H3, V1). The AEB and ACC rationales now open with "R1: D2, H5 and V3 all held". | C1 |
| One-line paraphrased `evidence` strings were replaced by full tool responses in `items[].raw_evidence.<tool>.<function>`. The PLAN-vs-shape layout conflict is now disclosed in `limitations`. | C2 |
| The FN-APA claim that "the permitted retry with verbatim identical input returned this same error" was removed. V1 now "rests on the recorded error, without any historical retry claim". | C3 |
| FN-AEB and FN-TJA gained a `flags` entry: `matched_scheme C(D)+A(D)` disagrees with the returned children B+C and C+B. A matching limitation was added. | C4 |
| `limitations` is now explicitly named as the discrepancies record. The README `<10 FIT` vs `<=10 FIT` difference, the per-ASIL ISO targets and the H2 agreement are stated there. | C5 |
| `applied_targets` (10 FIT / 99 / 90, with source calls) was added inside the PMHF gate. `summary` {2,1,1,1} was added inside the Release gate rather than at top level. | C6 |
| Each item gained `draft`, `informational_after_failure` and `flags`. The reviser set APA to `informational_after_failure=false`, against the critic's suggestion, and cited PLAN.md's definition. | C7 |
| Each item gained `input_trace` (safety_req id and text, per-element failure rates, evidence list, safety_case). `failure_rates_total_fit` 345/275/220/390/170 was added to `hw_metrics`. | C8 |
| Gate details were relabelled as "Explicit release-set roll-up: one … out of five". | C9 |
| A limitation was added saying 0.98 covers only reproducibility of the mechanical statuses, not vehicle safety or independence, DFA, FMEDA or evidence quality. | C10 |
| New disclosures were added: `review_artifact` reported missing `producing_code`, and the first reviser calls included a function label and were redone. | No finding. These are reviser self-disclosures. |

## Where TOKN's harness helped

- **`asil_decompose_verify`** (5 calls in Execute, 5 in Critique, 10 in Revise) caught FN-LKA: "child ASILs [B A] (sum 3) do not cover parent D (4) per ISO 26262-9 §5". It returned an error, which PLAN rule D1a and Brief rule 2 treat as a rejection. Its `limits` field also said that "independence and freedom from interference are not verified", which gave the C10 confidence caveat a tool-sourced basis.
- **`fmea_fta_engine`** (5 / 5 / 10 calls) caught FN-TJA with `programme_verdict.failures=["SPFM 98.9% below 99%"]`. It returned the programme targets (10 / 99 / 90) on every call, which settled the target conflict CAPABILITIES.md had flagged. It also returned per-ASIL `iso_targets` for ACC (C) and APA (B), so the stricter ASIL-D choice could be disclosed with numbers. Decide's `spfm_rounded_up` question (0.0013) confirms that 98.9 was not rounded up to a pass.
- **`safety_validation_report`** (6 / 5 / 5 calls) caught FN-APA: "1 open defects remain — all safety-critical defects must be resolved before V&V completion". It also stamped `report_status=DRAFT` and `release_authority=safety_manager_review_required` on every accepted item, which enforces Brief rule 6's calibrated language at the tool level.
- **Fail-closed gate ordering** held from start to finish. Decide's `positive_despite_rejected_decomposition` = 0.0025 confirms that no rejected decomposition was promoted.
- **Reproducibility.** Because all three tools return deterministic results, the critic could re-run the 15 calls and confirm every v1 number, and the reviser could confirm them again. This is why the light-revision routing was safe.
- **`review_artifact`** (1 call in Revise) reported missing `producing_code` and provenance. This stopped the reviser from claiming an automated validation pass.

## Proposed /teach rule

In mobility release-gate briefs, write each domain tool's raw JSON response or error to `evidence/<tool>/<function>.json` right after each call, including retries, and in `result.json` cite those files instead of paraphrasing tool output or claiming calls that were not saved.
