# REFLECTION — appsec relay: triaging a static-analysis queue before the release review

## What each stage contributed
- **0-discover — claude-haiku-5-5** (29,610 tokens, 33.8 s, 7 calls: read_file 6, list_directory 1, 0 errors). Wrote CAPABILITIES.md. It mapped 11 appsec tools to the inputs, named 9 tools as not applicable, and listed 10 gaps. Two gaps mattered most: no tool produces the status "blocked", and no tool confirmed it enforces identity rules.
- **1-plan — claude-opus-5-5** (19,781 tokens, 46.8 s, $0.3516, 6 calls, 0 errors). Wrote PLAN.md: 11 steps, decision rules D1–D5 with identity rules I1–I5, gates G1–G8, and 8 acceptance criteria. It predicted the final 2/2/2 split correctly (AS-03 blocked by `L214`, AS-06 by `1187`).
- **2-execute — Kimi-K3.1-Pro** (1,033,549 tokens, 920.0 s, 54 calls, 3 tool errors, 14 blocked or denied). Wrote result.v1.json with the correct six statuses. But no disposition, proof gap or finalize call was saved, and it reported confidence 0.8.
- **3-critique — FW-GLM-5.3** (920,896 tokens, 517.2 s, 39 calls, 1 error, 4 blocked). Wrote critique.json: 7 findings (C1–C3 major, C4–C7 minor). It reran the traces and controls, and confirmed against the run transcript that all six statuses were correct.
- **4-decide — Microsoft-Decision-1** (1,782 input / 3 output tokens, 1.1 s). Wrote decision.json: needs_revision 0.349, overclaimed_validation 0.004, unstable_identity_reported 0.007, routed to "light-revision".
- **5-revise — gpt-6.1-sol** (291,194 tokens, 204.2 s, $0.2031, 45 calls, 1 error, 7 blocked). Wrote result.json and answered all 7 findings as "fixed". The statuses did not change.

## What changed between the first and final answer
- **Item statuses:** no change. AS-01 and AS-04 are reportable, AS-02 and AS-05 suppressed, AS-03 and AS-06 blocked. C1 said "No status changes".
- **Per-item fields (C1):** each item now has explicit `rule_id`, `anchor`, `surface`, `sanitized` and `effective` (null for AS-03 and AS-06). Blocked items gained `identity_violation` (I3/`L214`, I4/`1187`). Suppressed items gained `suppression_rationale`. Reportable items gained `trust_boundary` plus `trust_boundary_assumption: true`, `validation` and `proof_gap`.
- **Top-level fields (C1):** added `service`, `coverage: partial`, `finalize_completeness: partial`, `finalize_persisted: false`, `dynamic_validation: false` and `counts`.
- **Coverage status (C1, C3):** v1 reported `scoped/4/4/4`. The final file keeps that as `executor_coverage_status` with `review_count_valid: false`. The new `coverage_status` is the reviser's own reading, `initialized/4/4/0`.
- **Confidence (C2):** lowered from 0.8 to 0.6, with a new `confidence_basis` describing it as "conservative subjective medium".
- **Limitations (C3, C4):** now state that executor step 16 marked four paths as reviewed without inspecting them, and that api/uploads and api/session were never marked.
- **Gate G5 (C5):** changed from fail to pass. G3 stays fail.
- **G3 wording (C6):** now explains that four `candidate_logged` results did not move the lifecycle to `candidates_logged`.
- **Tool lists (C7):** added `tools_called` (the field name in PLAN.md) next to `tools_used`, plus a new `rejected_tools` array.
- **Critique response:** `critique_response` went from an empty list to seven entries, all marked "fixed".

## Where TOKN's harness helped
- **`appsec_log_candidate` identity checks did real work.** They rejected AS-03 ("ruleId contains a line number") and AS-06 ("anchor is just a number") independently in the executor and reviser runs. This tool-level evidence backed D1, even though CAPABILITIES.md gap 2 had doubted that identity rules were enforced.
- **`appsec_trace_dataflow` and `appsec_check_control`** returned the booleans that decided D2/D3 (executor 5+4 calls, critic 4+4, reviser 4+4). Running them three times gave the same values each time.
- **The lifecycle phase guard** blocked suppress, validate, proof-gap and finalize calls made out of order. That stopped any disposition from being saved without a valid phase. The cost is in the next section.
- **`appsec_finalize_scan`** was only ever called with completeness "partial", so no "complete" claim was ever made.
- **`appsec_coverage_status`** exposed the self-inflicted `reviewed_files=4` (C3), and the critic's fresh reading of `initialized/0/0/0` showed the ledger had been reset.
- **The DECIDE stage** correctly gave low probability to identity and overclaim failures (0.007 and 0.004).

## Where TOKN fell short
- **No decision was ever saved.** Across all stages, no appsec_validate_candidate, appsec_suppress_candidate, appsec_record_proof_gap or appsec_finalize_scan call persisted anything. Recorded errors: "requires phase candidates_logged" and "requires phase reported but lifecycle is at scoped". `appsec_log_candidate` returned `candidate_logged` but the phase never advanced. The relay produced 14+4+7 = 25 blocked or denied calls and 5 tool errors.
- **The ledger does not persist between stages.** The critic's fresh coverage reading was `initialized/0/0/0`, and the reviser had to rebuild the threat model, surfaces and candidates.
- **Wasted executor steps.** The executor called four tools CAPABILITIES.md marked not applicable: appsec_scope_target ×1, appsec_build_inventory ×2, appsec_mark_reviewed ×2, appsec_find_sinks ×3. The mark_reviewed calls inflated `reviewed_files` without any review, which breaks DOMAIN-README gate 2 (C3). It also called appsec_log_candidate 7 times for 6 items, and appsec_coverage_status 4 times.
- **Cost.** The executor and critic together used 1.95M of about 2.29M total tokens, much of it working around lifecycle rejections.
- **`abstention_gate` gave no real check.** C2 found it "merely echoed the supplied number back" (0.8), so the overclaimed confidence went through unchallenged.
- **The plan and stage template disagree.** PLAN.md asks for `tools_called` while the executor template uses `tools_used` (C7), so the plan's own acceptance check could not pass without a revision.
- **Calls the plan expected that were not repeated or did not work.** The reviser never re-ran appsec_record_trust_boundary, appsec_suppress_candidate or appsec_record_proof_gap. Its one appsec_validate_candidate call was rejected at `initialized`. It also made one `run_command` call; its purpose is not recorded in TRACE.json, and G8 denies mutating tools.
- **Routing mismatch.** needs_revision was 0.349 ("light-revision"), yet the critic raised three major findings. DECIDE's questions measure status errors, not missing schema fields or calibration.
- **Gaps CAPABILITIES.md recorded that are still open:**
  - No disposition value for "blocked" (gap 1).
  - No tool maps a candidate to a trust boundary (gap 3), so `trust_boundary_assumption: true` remains.
  - No write path for deliverables (gap 5).
  - The README's claims of 8 hooks and a 12-state lifecycle could not be checked against the tool list (gap 6). That lifecycle is the one that blocked every disposition.

## Proposed /teach rule
In appsec, after logging candidates call appsec_coverage_status, and if the phase is not candidates_logged do not call suppress/validate/proof_gap/finalize again; record the phase failure once, state that statuses come from the rules and are not saved, and never call appsec_mark_reviewed on paths you did not inspect.

## Next run
1. **Plan:** add a phase check step between Step 4 (log) and Step 7 (suppress) that reads appsec_coverage_status and branches on `phase`. Also add a line limiting the executor to the tools CAPABILITIES.md lists as applicable.
2. **Prompts:** use PLAN.md's acceptance schema as the executor's result.json template (`tools_called`, `rejected_tools`, `identity_violation`, the top-level coverage fields), so C1 and C7 cannot come up again. Require `confidence_basis` next to any confidence value.
3. **Roster/harness:** have DECIDE also ask "does result.json fail any PLAN.md acceptance criterion?", and before the next run find out which appsec lifecycle step moves the phase to `candidates_logged` (gap 6). Without that, no stage can save a decision.
