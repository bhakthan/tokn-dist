# REFLECTION — climsci relay: plausibility and likelihood check of CL-01..CL-05

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
- **C1 is only partly closed.** The Critic's fix said to *declare* the flagged numbers as traceable values. Revise did not. It explained the 14 "high" advisories in prose instead, and its own note says "No claim of full tool-based code-drift verification is made."
- **C3 is fixed.**
- **C2's "item" requirement is only partly met.** `id` was kept alongside the new `item` key.

## Where TOKN's harness helped

- **`validate_physical` (summary mode).** Called 11× in Execute, 6× in Critique and 5× in Revise. It independently caught CL-03 ("Variable 'pr' values [0, 18.4] exceed the plausible physical range [-1e-06, 0.02] kg m⁻² s⁻¹ (with 10% tolerance)"). It returned `tolerance_range` values identical to the brief's bands, which settles CAPABILITIES' "Unverified: validate_physical's internal band". It also passed CL-05's 265.8 K minimum, which is below the untoleranced 270 K bound.
- **`review_artifact`.** This was the gate that did the most work. The Critic's single call returned `passed=false`, "2 critical, 8 high" (code_artifact_drift, incomplete_provenance). That turned a deliverable whose statuses were correct but which could not be audited into the blocking finding C1. As a result, `result.json` now carries producing code, a code hash, the runtime environment and input hashes.
- **`query_cmip6_catalog` / `compute_ensemble_stats`.** They produced no data. Their failures were still recorded verbatim (`ModuleNotFoundError: No module named 'intake'`), as rule 1 requires, and correctly had no effect on status.
- **Planning discipline.** PLAN's exact-fraction rule handled both boundary cases (CL-01 p = 9/10 → very likely; CL-05 p = 2/3 → likely). The Critic called these "the two subtle boundary cases" and confirmed them.
- **The independent Critic re-run pattern.** Critique re-ran every decisive tool instead of trusting the Executor. That is how the missing Step 6 output was discovered.

## Proposed /teach rule

/teach climsci: copy every domain-tool verdict (validate_physical, review_artifact, query_cmip6_catalog and compute_ensemble_stats errors) into result.json verbatim from that stage's own tool output; never regenerate a tool verdict or error string from your own computation or from a previous stage's file.
