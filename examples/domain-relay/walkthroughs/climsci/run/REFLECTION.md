# REFLECTION — climsci relay: plausibility and likelihood check of CL-01..CL-05

Sources: `TRACE.json`, `CAPABILITIES.md`, `PLAN.md`, `critique.json` (plus `CRITIQUE.md`), `decision.json`, `result.v1.json`, `result.json` (plus `revise_report.py`, which `result.json` names as its producing code).
Total tokens across stages: 85,683 + 88,141 + 1,539,071 + 662,290 + 2,695 + 669,333 = **3,047,213**. The Executor used 50.5 % of them.

## What each stage contributed

- **0-DISCOVER (claude-haiku-5-5).** 56.8 s, 85,683 tokens, 11 tool calls, 0 errors. It wrote `CAPABILITIES.md` (79 lines). The file maps 4 applicable tools to input fields, lists the tolerance bands (tas 164–356 K, pr −0.0020011–0.0220001, tos 265.5–319.5 K), records 6 gaps and 7 README tool names that do not exist, and flags that KIOST-ESM is unmapped. It did not call the catalog tools ("Live tool liveness ... not called at this stage").
- **1-PLAN (claude-opus-5-5).** 101.5 s, 88,141 tokens, $0.6981, 9 tool calls, 0 errors. It wrote `PLAN.md`: 6 steps with exact per-item arguments, decision rules in precedence order, an exact-fraction boundary rule (p = 0.90 goes to "very likely"), 4 gates and a named-field acceptance schema.
- **2-EXECUTE (Kimi-K3.1-Pro).** 1,070.3 s, 1,539,071 tokens, 57 tool calls, **18 tool errors, 2 blocked/denied, exit_code 3, status "blocked", empty `final`**. It still produced `result.v1.json`. All five statuses were correct (the Critic confirmed this independently). The output did not follow the plan's schema, and it recorded no `review_artifact` output.
- **3-CRITIQUE (FW-GLM-5.3).** 572.2 s, 662,290 tokens, 38 tool calls, 12 tool errors. It wrote `critique.json` with 7 findings (C1 blocking, C2–C3 major, C4–C7 minor). It re-ran `validate_physical` ×5, the catalog and ensemble tools ×5 each, and `review_artifact` ×1, and recomputed N_fam (10, 7, 8, 4, 6) and A_fam (9, 4, 7, 4, 4) from `inputs/`.
- **4-DECIDE (Microsoft-Decision-1).** 1.2 s, 2,692 input / 3 output tokens, no tools. It produced `decision.json`: needs_revision = 0.023, cl02_likely_kept = 0.0086, cl04_enough_families = 0.0015, routing "full-revision".
- **5-REVISE (gpt-6.1-sol).** 254.9 s, 669,333 tokens, $0.3619, 41 tool calls, 10 tool errors, 2 blocked/denied. It rewrote `result.json` and `RESULT.md` with `revise_report.py`, marked all seven findings "fixed", and left the statuses unchanged.

## What changed between the first and final answer

**The statuses did not change.** CL-01 supported, CL-02 miscalibrated, CL-03 implausible, CL-04 insufficient_ensemble, CL-05 supported, in both files. The decision rules that fired (4, 3, 1, 2, 4) are also the same. No critique finding challenged a status. C7 states: "I independently recomputed every status ... and got identical results."

Item-level changes:

| Change (v1 → final) | Caused by |
|---|---|
| `evidence` changed from an array of prose strings to an object with `family_map`, `family_agreement`, `n_independent_families`, `n_agreeing_families`, `p` {fraction, reduced_fraction, decimal}, `derived_term`, `ar6_probability_range`, `band_check`, `catalog_query`, `ensemble_stats`, `tool_errors`, `decision_rule_fired`, `gates`, `request_labels`, `notes` | C2 |
| `item`, verbatim `claim` and `stated_likelihood` added at item level. `id` kept. | C2 |
| `rationale` shortened to a template ("Band check passes; 9/10 families agree, p=0.9000 ...") | rewrite in `revise_report.py` (no finding asked for it) |
| CL-03 and CL-04 claim text written from the input bytes (ASCII hyphen in "2081-2100") | C6 |

Top-level changes:

| Change (v1 → final) | Caused by |
|---|---|
| `provenance` added: input files with SHA-256, `tools_called`, `data_layer: "L2-model-output"`, `synthetic_inputs: true`, `producing_code`, `code_hash`, `environment` (Python 3.14.10, Windows-11) | C3, C1 |
| `provenance.review_artifact` recorded: `passed: true`, "review passed with advisories: 14 high", plus a `review_advisory_response` | C1 |
| Physical-plausibility gate detail: "corrected summary-mode" → "rerun summary-mode" | C5 |
| Gate status "n/a" → "not_applicable" | PLAN acceptance wording (bundled in the same script edit) |
| `limitations[1]` reworded to "All ten live catalog/statistics reruns failed ...". The banned word "could" was removed from RESULT.md. | C4 |
| `confidence_scope` added. `confidence` is still 0.97. | C7 |
| `critique_response` changed from `[]` to 7 entries, all `"action": "fixed"` | C1–C7 |

How completely each finding was fixed:
- **C1 is only partly closed.** The Critic's fix said to *declare* the flagged numbers as traceable values. Revise did not. It explained the 14 "high" advisories in prose instead, and its own note says "The hash-only tool request was scanner-blocked; no claim of full tool-based code-drift verification is made."
- **C3 is fixed.**
- **C2's "item" requirement is only partly met.** `id` was kept alongside the new `item` key.

## Where TOKN's harness helped

- **`validate_physical` (summary mode).** Called 11× in Execute, 6× in Critique and 5× in Revise. It independently caught CL-03 ("Variable 'pr' values [0, 18.4] exceed the plausible physical range [-1e-06, 0.02] kg m⁻² s⁻¹ (with 10% tolerance)"). It returned `tolerance_range` values identical to the brief's bands, which settles CAPABILITIES' "Unverified: validate_physical's internal band". It also passed CL-05's 265.8 K minimum, which is below the untoleranced 270 K bound.
- **`review_artifact`.** This was the gate that did the most work. The Critic's single call returned `passed=false`, "2 critical, 8 high" (code_artifact_drift, incomplete_provenance). That turned a deliverable whose statuses were correct but which could not be audited into the blocking finding C1. As a result, `result.json` now carries producing code, a code hash, the runtime environment and input hashes.
- **`query_cmip6_catalog` / `compute_ensemble_stats`.** They produced no data. Their failures were still recorded verbatim (`ModuleNotFoundError: No module named 'intake'`), as rule 1 requires, and correctly had no effect on status.
- **Planning discipline.** PLAN's exact-fraction rule handled both boundary cases (CL-01 p = 9/10 → very likely; CL-05 p = 2/3 → likely). The Critic called these "the two subtle boundary cases" and confirmed them.
- **The independent Critic re-run pattern.** Critique re-ran every decisive tool instead of trusting the Executor. That is how the missing Step 6 output was discovered.

## Where TOKN fell short

1. **A missing dependency hit 30 identical failing calls.** `intake` is not installed, so all 5 + 5 catalog/ensemble calls failed in Execute, again in Critique and again in Revise. These failures explain 10 of Execute's 18 errors, 10 of Critique's 12 and all 10 of Revise's errors. DISCOVER chose not to test whether the tools work, so nobody learned about the missing dependency before the Executor ran. The harness then let each later stage repeat the same failure.
2. **The Executor did not finish cleanly.** It ran for 1,070.3 s, used 1.54 M tokens, and ended with exit_code 3, "blocked" and an empty `final`. The trace does not explain the other 8 errors or the 2 blocked/denied calls. It made 11 `validate_physical` calls for 5 items, and v1 says "corrected summary-mode". ASSUMPTION (not shown in the files): early calls used the wrong mode and were repeated.
3. **The Executor called `review_artifact` 4 times but recorded none of the output.** v1 lists only four tools per item, yet RESULT.md claimed `review_artifact` was used. The gate ran, but its result never reached the artifact. Critique flagged this as blocking (C1).
4. **The final `validate_physical` verdict was recreated by a script, not copied from the tool.** `revise_report.py` builds `verdict` from the manual `ok` flag (`'overall_status':'PASS' if ok else 'FAIL'`). It hard-codes the detail strings ("NetCDF file passes CF compliance ..." and the CL-03 `pr` violation text). It also copies the catalog errors from v1's evidence strings rather than from its own reruns. The values match what the tools returned, but in `result.json` the "tool verdict" and the "manual check" are no longer independent. `check_derivation` was called once in Execute and never on `revise_report.py`, which is exactly the kind of file it targets.
5. **`review_artifact` misread the evidence.** It flagged bracketed extrema such as "[268.1, 312.6]" as 13 `unresolved_citation` findings, and parsed the hyphen in "2081-2100" as the number "-2100". Both the Critic and Revise had to spend effort arguing these advisories away.
6. **DECIDE asked the wrong question.** `needs_revision` asked whether "at least one item['s] status is wrong". The answer, 0.023, was correct: no status was wrong. But the routing was still "full-revision". The real reason to revise, the blocking finding C1, was not one of the three questions. The trace does not show what drove the routing.
7. **Gaps that CAPABILITIES.md recorded and that are still open:**
   - No IPCC calibrated-language validator exists as a tool (Gap 3). The `ar6_confidence_gate` is only cited from the session log, so C4's banned "could" was caught by a model reading the text, not by a gate.
   - No tool for family deduplication against the input map (Gap 2) or for likelihood derivation (Gap 1).
   - Season and baseline have no tool parameters (Gap 5).
   - How the region string is handled is unverified (Gap 6), and the failed tools left it unverified.
   - DOMAIN-README names 7 tools that do not exist (e.g. `read_netcdf`, `validate_provenance`).
8. **2 blocked/denied calls in Revise:** one was the scanner blocking the hash-only `review_artifact` request. As a result, the code-drift check could not be completed through the tool.

## Proposed /teach rule

/teach climsci: copy every domain-tool verdict (validate_physical, review_artifact, query_cmip6_catalog and compute_ensemble_stats errors) into result.json verbatim from that stage's own tool output; never regenerate a tool verdict or error string from your own computation or from a previous stage's file.

## Next run

1. **DISCOVER checks each catalog tool works with one call.** Call `query_cmip6_catalog` and `compute_ensemble_stats` once each and write the outcome (e.g. the `intake` ModuleNotFoundError) into CAPABILITIES.md. PLAN then reuses that recorded error instead of having Execute, Critique and Revise each make 10 failing calls. That saves 20+ calls; alternatively, fix the environment before the run.
2. **Plan change: Step 6 and `check_derivation` become blocking.** Make Step 6 (`review_artifact`) a blocking pre-handoff step whose verbatim JSON output must appear in `result.json.provenance`. Pass the field extrema and band edges as `traceable` values up front so the citation false positives do not appear. Run `check_derivation` on any script that writes the deliverable (here `revise_report.py`).
3. **Roster and prompt changes for DECIDE and Execute.**
   - Add a DECIDE question that matches the critique's actual blocking finding, e.g. "Does any blocking finding remain that prevents the deliverable from being final?". The routing then follows a stated probability.
   - Give the Executor a token or step budget, and require it to write a non-empty `final`. It ended "blocked" after 1.54 M tokens with no summary.
