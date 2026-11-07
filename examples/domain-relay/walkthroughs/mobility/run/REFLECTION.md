# REFLECTION: mobility relay, functional-safety release gate for five ADAS functions

## What changed between the first and final answer
| Item | result.v1.json | result.json | Caused by |
|---|---|---|---|
| FN-AEB | decomposition_invalid (R1: no explicit positive field) | release_candidate, DRAFT | C1, C3: no-error counts as acceptance under BRIEF rule 2; error is the rejection channel |
| FN-LKA | decomposition_invalid (tool error "[B A] (sum 3) do not cover parent D (4)") | decomposition_invalid (unchanged) | none; v1 was already correct |
| FN-ACC | decomposition_invalid, partly argued from the static instruction string not listing C→(B,A) | release_candidate, DRAFT (SPFM 99.0 and coverage 95.0 pass at equality) | C1, C3, C6 (instruction string has no verdict value) |
| FN-TJA | decomposition_invalid (SPFM 98.9 < 99 noted only as a counterfactual) | hw_metrics_fail | C1 |
| FN-APA | decomposition_invalid (V&V "1 open defects remain" treated as non-status-setting) | vv_incomplete, with the retry recorded | C1, C10 (missing mandated retry) |

Changes beyond the item statuses:
- **Gates G1 to G3** changed from `fail` to `mixed` (4 satisfied, 1 not satisfied) because of C9.
- **G4** changed from `warn` to `not satisfied` because no full tool_log was preserved (C4).
- **Confidence** dropped from 0.93 to 0.85, and the unsupported "JSON/decision-comparison validation" claim was removed (C5).
- **Per-item blocks were added**: `first_failing_check`, `draft`, `decomposition`, `hw_metrics`, `vv` and `observations`, together with `targets`, `discrepancies`, `not_assessed`, `summary` and `disclaimer` (C2). The fix is only partial: result.json says the 15-entry `tool_log` is still missing.
- **asil_req is now recorded per function**, the C/B versus D target cross-check is stated, and the README "<10 FIT" difference is moved into D3 (C7).
- **APA open_goals=1** is now listed as a separate observation (C8).

decision.json correctly predicted that no rejected decomposition was promoted (0.033) and that TJA's SPFM was not rounded up (0.005). The final answer agrees with both.

## Where TOKN's harness helped
- **`asil_decompose_verify`** caught the real defect: FN-LKA's "child ASILs [B A] (sum 3) do not cover parent D (4) per ISO 26262-9 §5". The result was deterministic across the executor, critic and reviser. It also rejected the critic's probe C→(A,A), which established the verdict channel.
- **`fmea_fta_engine`** returned `pmhf_target=10`, `spfm_target=99` and `lfm_target=90` on all five calls, including the ASIL-C and ASIL-B records. This gave every number a traceable source and exposed FN-TJA's SPFM 98.9 < 99.
- **`safety_validation_report`** rejected FN-APA with "1 open defects remain". It rejected the 94% probe and accepted exactly 95.0, which settled FN-ACC's boundary case.
- **The CRITIQUE stage plus the DECIDE gate** worked as designed. The critic re-ran the tools instead of only reading the result, and Decision-1 routed `full-revision` at 0.997 in 1.1 s for 3 output tokens. This turned a uniformly wrong answer into a differentiated one.
- **Fail-closed behaviour and the content scanner** stopped the reviser from claiming log preservation it did not have. G4 is honestly marked `not satisfied`.

## Proposed /teach rule
Before writing pass/fail rules for any domain tool, call it once with a known-good and once with a known-bad input, then record the observed verdict channel (e.g. error field vs result field) in PLAN.md and never require a verdict field the tool did not return.
