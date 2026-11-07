# CAPABILITIES — mobility release gate (5 ADAS functions)

Scout stage. Nothing here assesses FN-AEB, FN-LKA, FN-ACC, FN-TJA or FN-APA.
Sources read: BRIEF.md; inputs/asil_decomposition.json; inputs/fmeda_metrics.json;
inputs/vv_evidence.json; tokn-self/introspect-slice.json; tokn-self/DOMAIN-README.md;
my live tool list.

## Domain tools that apply

| tool (exact name) | applies to | input fields needed, and whether present in inputs/ |
|---|---|---|
| `asil_decompose_verify` | Check 1 (decomposition) for all 5 functions, from `asil_decomposition.json` | `safety_req`, `architecture`, `independence_claims`, `decomposed_requirements`, `parent_asil`, `child_asils`. All present in every record. Schema is loose (`{}`), so pass each record unchanged. |
| `fmea_fta_engine` | Check 2 (hardware metrics) for all 5 functions, from `fmeda_metrics.json` | `architecture`, `failure_rates`, `asil_req`. All present in every record. Tool description says it returns PMHF, SPFM, LFM. |
| `safety_validation_report` | Check 3 (V&V) for all 5 functions, from `vv_evidence.json` | `all_evidence`, `safety_case`, `vv_report_path`, `requirements_covered_pct`, `defects_open`. All present in every record. |

Not used for this brief (no matching input in `inputs/`): `hara_automate`, `safety_case_build`,
`sotif_odd_coverage`, `tara_engine`, and the simulation, V2X, EV/BMS, UAM and regulatory tools.

Tool list vs README: the README says 22 tools. I count 22 mobility tools in my list, so the total agrees.
I did not check the README's per-category breakdown against the tool names.

## Gates and rules that will constrain the answer

From BRIEF.md (the run's controlling rules):
- Order is fixed: decomposition, then hardware metrics, then V&V. The first failing check sets the status.
- Decomposition: a tool error counts as rejection. Child ASILs that do not cover the parent per ISO 26262-9 §5 give `decomposition_invalid`.
- Hardware metrics: "PMHF passes when it is at most the target. SPFM and LFM pass when they are at least the target." Targets are programme-wide ASIL-D values, to be taken from the tool output (`pmhf_target` in FIT, `spfm_target` and `lfm_target` in %).
- V&V: `safety_validation_report` "accepts only `requirements_covered_pct` of at least 95 and `defects_open` of 0". A tool error counts as rejection.
- Report every number from a tool call or an input file, not from memory of the standard.
- Status vocabulary, exactly one per item: `release_candidate`, `decomposition_invalid`, `hw_metrics_fail`, `vv_incomplete`. `release_candidate` is still a DRAFT for safety-manager review.
- Calibrated language: "Passing these gates is evidence for a release decision, not proof that a function is safe."

From DOMAIN-README.md (secondary; conflicts noted under Gaps):
- "PMHF gate: probabilistic metric <10 FIT for ASIL-D components"
- "ASIL decomposition tracking (SPFM ≥99%, LFM ≥90% for ASIL-D)"
- Six domain gates named: HARA, Safety Concept, ASIL Decomposition, PMHF, V&V, Release. Only the first three checks are callable as tools; the gates themselves are not tools.

Reversibility: all three checks are T0 (read-only analysis tools). Writing the result files is T1.

## Gaps

1. **Targets are not documented by any tool.** BRIEF says `fmea_fta_engine` returns `pmhf_target`, `spfm_target` and `lfm_target`. The tool description only says it returns PMHF, SPFM, LFM. Targets must be read from the actual tool output, and the field names checked on the first call.
2. **Threshold conflict.** README gives PMHF `<10 FIT` (strict) and SPFM ≥99%, LFM ≥90%. BRIEF gives PMHF "at most the target" (≤). Values come from the tool; I will record any difference between the README and the tool output rather than choose between them.
3. **Which FMEDA values get compared is unclear.** Each `fmeda_metrics.json` record contains `pmhf_fit`, `spfm_pct`, `lfm_pct`, but `fmea_fta_engine` takes only `architecture`, `failure_rates`, `asil_req`. BRIEF says to compare "the FMEDA values" with targets. The stage must state whether it compares input values or recomputed values, and report any mismatch.
4. **Open safety goals are not checked by any tool.** FN-APA's `safety_case` has `open_goals: 1`. `safety_validation_report` takes `safety_case` as an untyped object, but BRIEF's rule 4 accepts only `requirements_covered_pct` and `defects_open`, and does not mention open goals. This is a reasoning gap. It cannot change the status by the rules as written, but it must be reported.
5. **Independence claims are not validated.** `asil_decompose_verify` is documented as checking child-versus-parent coverage. Claims such as "dependent failure analysis ... complete" are taken as stated. No tool verifies DFA evidence.
6. **README vs tool list.** The README's per-category counts are not verified against tool names. Hooks (8), commands (16) and subagents (3) are not visible to me and are unverified. I trust my tool list.
7. **Tool schema looseness.** `asil_decompose_verify` and `safety_validation_report` accept `{}`/untyped inputs, so field validation is done by the tool, not by a schema I can check beforehand.
8. **Not covered by any tool:** SOTIF known/unknown analysis for these functions, ODD definitions, and any cybersecurity assessment. None are in the brief's checks, so none are assessed here.
