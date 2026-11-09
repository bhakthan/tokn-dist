# Task: functional-safety release gate for five ADAS functions

You are a functional-safety engineer on an ISO 26262 programme. Five driver-assistance functions are proposed for the next software release. The safety manager wants a mechanical gate review of each one before the release board meets: is the ASIL decomposition valid, do the hardware metrics meet the programme targets, and is the V&V evidence complete?

The data is synthetic but realistic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/asil_decomposition.json` | Per function: safety requirement, architecture, independence claims, decomposed requirements, `parent_asil` and `child_asils` |
| `demo-input/fmeda_metrics.json` | Per function: architecture, failure rates, `asil_req`, and the FMEDA results `pmhf_fit`, `spfm_pct`, `lfm_pct` |
| `demo-input/vv_evidence.json` | Per function: evidence list, safety-case summary, `vv_report_path`, `requirements_covered_pct`, `defects_open` |

## Items to assess

`FN-AEB`, `FN-LKA`, `FN-ACC`, `FN-TJA`, `FN-APA`

## Status vocabulary (use exactly one per item)

- `release_candidate`: decomposition accepted, hardware metrics meet every target, and V&V completion accepted. The report is still a DRAFT for safety-manager review.
- `decomposition_invalid`: `asil_decompose_verify` rejects the ASIL decomposition (child ASILs do not cover the parent per ISO 26262-9 §5).
- `hw_metrics_fail`: decomposition accepted, but PMHF is above the target or SPFM or LFM is below its target.
- `vv_incomplete`: decomposition and hardware metrics pass, but `safety_validation_report` rejects V&V completion.

## Rules

1. Apply the checks in order: decomposition, then hardware metrics, then V&V. The first failing check sets the status, however good the later evidence looks.
2. Call `asil_decompose_verify` with each function's record exactly as given. A tool error is a rejection.
3. Call `fmea_fta_engine` with each function's record and compare the FMEDA values with the targets the tool returns (`pmhf_target` in FIT, `spfm_target` and `lfm_target` in %). These are programme-wide ASIL-D targets; apply them to every function. PMHF passes when it is at most the target. SPFM and LFM pass when they are at least the target.
4. Call `safety_validation_report` with each function's V&V record exactly as given. It accepts only `requirements_covered_pct` of at least 95 and `defects_open` of 0. A tool error is a rejection.
5. Every number you report must come from a tool call or the input files, not from memory of the standard.
6. Use calibrated language. Passing these gates is evidence for a release decision, not proof that a function is safe.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"FN-AEB": "<status>"}`.
