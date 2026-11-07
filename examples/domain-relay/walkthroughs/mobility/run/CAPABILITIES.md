# CAPABILITIES.md — Scout report, mobility functional-safety release gate

Scope: items FN-AEB, FN-LKA, FN-ACC, FN-TJA, FN-APA. This file records what tools and rules exist. It does not assess any item.

Sources read: `BRIEF.md`; `inputs/asil_decomposition.json`, `inputs/fmeda_metrics.json`, `inputs/vv_evidence.json`; `tokn-self/introspect-slice.json`; `tokn-self/DOMAIN-README.md`; my live tool list.

Consistency check: the README says "22 LLM tools". My live mobility tool list has 22 tools, so the count matches. The README gives no tool names, so the category split (4/4/5/2/2/1/2/2) could not be verified.

## Domain tools that apply

| tool (exact name) | item(s) / input file it applies to | input fields needed and present in `inputs/` |
|---|---|---|
| `asil_decompose_verify` | all five items; `inputs/asil_decomposition.json` | `safety_req`, `architecture`, `independence_claims` (non-empty), `decomposed_requirements`, `parent_asil`, `child_asils`. All present in every record. |
| `fmea_fta_engine` | all five items; `inputs/fmeda_metrics.json` | Brief rule 3 supplies `architecture`, `failure_rates`, `asil_req`, `pmhf_fit`, `spfm_pct`, `lfm_pct`. Present. `lifetime_h` is NOT present (see Gaps). `failure_modes` is NOT present (see Gaps). |
| `safety_validation_report` | all five items; `inputs/vv_evidence.json` | `all_evidence`, `safety_case`, `vv_report_path`, `requirements_covered_pct`, `defects_open`. All present. Not `requirements` or `defects` arrays. |

Not applicable to this brief (listed so the answer does not use them by mistake): `hara_automate` (no HARA input), `safety_case_build` (brief does not ask for a GSN case), `tara_engine`, `sotif_odd_coverage`, `sensor_coverage_analyze`, `hd_map_validate`, `fusion_evaluate`, `digital_twin_validate`, `carla_scenario_execute`, `openscenario_catalog_build`, `v2x_*`, `v2i_infrastructure_simulate`, `ev_charging_plan`, `battery_electrochemical_model`, `utm_simulate`, `evtol_safety_assess`, `regulatory_compliance_track`, `sumo_traffic_generate`. None has inputs in `inputs/`.

## Gates and rules that will constrain the answer

From `BRIEF.md` (the governing rules for this release gate):
- Order is fixed: decomposition, then hardware metrics, then V&V. "The first failing check sets the status, however good the later evidence looks."
- Rule 2: "A tool error is a rejection" (for `asil_decompose_verify`).
- Rule 3: PMHF passes when "at most the target" (FIT). SPFM and LFM pass when "at least the target" (%). Targets come from the `fmea_fta_engine` return, and the brief says to apply the programme-wide ASIL-D targets to every function.
- Rule 4: `safety_validation_report` accepts only `requirements_covered_pct` of "at least 95" and `defects_open` of "0". "A tool error is a rejection."
- Rule 5: every number reported must come from a tool call or an input file.
- Rule 6: calibrated language. "Passing these gates is evidence for a release decision, not proof that a function is safe."
- Status vocabulary, use exactly one per item: `release_candidate`, `decomposition_invalid`, `hw_metrics_fail`, `vv_incomplete`.
- `release_candidate` report is "still a DRAFT for safety-manager review."

From `tokn-self/DOMAIN-README.md` (the domain plug's own documentation):
- "ASIL decomposition tracking (SPFM ≥99%, LFM ≥90% for ASIL-D)"
- "PMHF gate: probabilistic metric <10 FIT for ASIL-D components"
- Six domain gates named: HARA, Safety Concept, ASIL Decomposition, PMHF, V&V, Release.

Conflicts between these sources (must be recorded in the answer):
- README gives PMHF `<10 FIT` (strict). The brief uses `pmhf_target` returned by the tool, with "at most" (≤). The brief governs for this gate; the tool's returned value is the threshold actually applied.
- README gives SPFM ≥99% and LFM ≥90%. The brief uses `spfm_target` and `lfm_target` as returned by the tool. These may differ from the README; use the tool's values and note any difference.
- README says the gates are "for ASIL-D". The brief applies ASIL-D targets to every item, including FN-ACC (ASIL C) and FN-APA (ASIL B). Follow the brief, and flag this as a judgement the safety manager should confirm.
- Only the README's six gate names appear here. The Release gate and Safety Concept gate are not used by this brief's status vocabulary and are not assessed.

## Gaps

1. **Dependent-failure analysis is asserted, not checked.** Each record says a DFA is "complete" (e.g. DFA-AEB-03). No tool reads DFA documents. Independence claims are counted by `asil_decompose_verify`, not verified. Handle by reasoning, and state that DFA is taken from the input text.
2. **FMEDA values cannot be recomputed.** `fmea_fta_engine` gets `pmhf_fit`, `spfm_pct`, `lfm_pct` as supplied, but the inputs have no `failure_modes` (safe fraction, DC, single-point flags) and no `lifetime_h`. The engine can check the supplied values against targets but cannot re-derive them. Handle by reasoning, and say the metrics are taken as given.
3. **Target mismatch risk.** The brief says apply programme-wide ASIL-D targets to all five items. The engine's own targets may be per-ASIL. Use the brief's instruction and report any difference.
4. **ASIL notation.** Input `child_asils` use plain letters (e.g. `["B","C"]`). The tool example uses annotated form (e.g. `"B(D)"`). The brief says pass records "exactly as given", so no rewriting. Possible tool behaviour difference is unverified until the call is made.
5. **Requirement-level V&V detail is absent.** `safety_validation_report` takes only aggregate percentages and counts. Brief rule 4 uses those, so this is not a blocker, but per-requirement traceability cannot be checked.
6. **Evidence paths are illustrative.** `vv_report_path` values point to files not in `inputs/`. The brief marks them as illustrative. Existence cannot be verified here.
7. **FN-APA open safety-case goal.** `vv_evidence.json` has `open_goals: 1` and `defects_open: 1` for FN-APA. The brief's V&V rule uses only the two numeric fields, so `safety_case.open_goals` is not a gate input. Flag it in the answer; do not decide on it.
8. **Scope-limited tools.** No tool in the list covers SOTIF, cybersecurity (TARA inputs absent), or a release-board decision. None is requested by the brief.
