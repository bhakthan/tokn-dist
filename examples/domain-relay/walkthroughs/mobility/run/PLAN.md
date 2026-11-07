# PLAN.md — Functional-safety release gate for FN-AEB, FN-LKA, FN-ACC, FN-TJA, FN-APA

Planner stage. This plan has NOT been executed. Every input value below is copied verbatim from `inputs/`. Every threshold comes either from `BRIEF.md` or from a value that a tool returns at execution time. No number is taken from memory of ISO 26262.

Sources read by the Planner: `BRIEF.md`, `CAPABILITIES.md`, `inputs/asil_decomposition.json`, `inputs/fmeda_metrics.json`, `inputs/vv_evidence.json`, `tokn-self/DOMAIN-README.md`, `tokn-self/introspect-slice.json`.

## Objective

For each of the five ADAS functions (FN-AEB, FN-LKA, FN-ACC, FN-TJA, FN-APA), run `asil_decompose_verify`, then `fmea_fta_engine`, then `safety_validation_report` on the records in `inputs/`. Assign exactly one status per function (`release_candidate`, `decomposition_invalid`, `hw_metrics_fail`, `vv_incomplete`) using the first-failing-check rule. Record the results in `result.json` and `RESULT.md` as a DRAFT for safety-manager review.

## Steps

### General execution rules (apply to every step)

- **G1. Field mapping.** Pass the tool's documented input fields, with values copied **verbatim** from the matching input record. Do not normalise, re-letter, round or annotate any value. For example, `child_asils` stays `["B","C"]`, not `["B(D)","C(D)"]`. The `function` key is not a tool field. Do not pass it. Use it only to label the result. This is how the Planner reads the brief's "exactly as given": the values are exact and the fields are the tool's own.
- **G2. Run all three checks for every item.** Call all three tools for all five items, even after an earlier check has failed, so the evidence record is complete. Results from later checks are recorded as `informational` and never change the status (Brief rule 1).
- **G3. Capture the raw output.** Save each tool's full raw output (or full error text) under `evidence.<tool>.<function>` in `result.json`. Any number in `RESULT.md` must trace to one of these outputs or to `inputs/` (Brief rule 5).
- **G4. No retries that change inputs.** If a call errors, you may retry it once with identical input, to rule out a transient error. If it errors again, record the error. Do not change any input to make a call pass.
- **G5. No other tools.** Do not use `hara_automate`, `safety_case_build`, `tara_engine` or any other tool that `CAPABILITIES.md` lists as not applicable.

---

### Step 1 — ASIL decomposition check (covers all five items; Gate: ASIL Decomposition)

Tool: **`asil_decompose_verify`**. Make one call per item, in the order AEB, LKA, ACC, TJA, APA. Source: `inputs/asil_decomposition.json` → `decompositions[]`.

**1a. FN-AEB**
```json
{
  "safety_req": {"id": "SG-AEB-01", "text": "Avoid unintended full braking at speeds above 10 km/h", "asil": "D"},
  "architecture": {"channels": ["camera-radar fusion ECU", "independent radar plausibility monitor"], "diversity": "different SoC vendors and software teams"},
  "independence_claims": ["separate power supplies", "separate CAN segments", "no shared software modules", "dependent failure analysis DFA-AEB-03 complete"],
  "decomposed_requirements": ["FSR-AEB-01a: fusion ECU limits brake request (ASIL B(D))", "FSR-AEB-01b: radar monitor vetoes implausible brake request (ASIL C(D))"],
  "parent_asil": "D",
  "child_asils": ["B", "C"]
}
```

**1b. FN-LKA**
```json
{
  "safety_req": {"id": "SG-LKA-01", "text": "Avoid unintended steering torque above 3 Nm", "asil": "D"},
  "architecture": {"channels": ["lane-keeping controller", "steering torque limiter"], "diversity": "different algorithms on separate cores"},
  "independence_claims": ["separate cores with hypervisor partitioning", "independent torque sensor", "dependent failure analysis DFA-LKA-02 complete"],
  "decomposed_requirements": ["FSR-LKA-01a: controller bounds torque request (ASIL B(D))", "FSR-LKA-01b: limiter clamps torque above 3 Nm (ASIL A(D))"],
  "parent_asil": "D",
  "child_asils": ["B", "A"]
}
```

**1c. FN-ACC**
```json
{
  "safety_req": {"id": "SG-ACC-01", "text": "Avoid unintended acceleration above 2 m/s^2", "asil": "C"},
  "architecture": {"channels": ["ACC controller", "powertrain torque monitor"], "diversity": "monitor runs on powertrain ECU"},
  "independence_claims": ["separate ECUs", "separate supply rails", "dependent failure analysis DFA-ACC-01 complete"],
  "decomposed_requirements": ["FSR-ACC-01a: controller limits acceleration request (ASIL B(C))", "FSR-ACC-01b: torque monitor cuts excess torque (ASIL A(C))"],
  "parent_asil": "C",
  "child_asils": ["B", "A"]
}
```

**1d. FN-TJA**
```json
{
  "safety_req": {"id": "SG-TJA-01", "text": "Avoid unintended lateral or longitudinal motion in traffic-jam assist", "asil": "D"},
  "architecture": {"channels": ["TJA planner", "safety supervisor"], "diversity": "supervisor uses a simplified kinematic model"},
  "independence_claims": ["separate SoCs", "separate power supplies", "dependent failure analysis DFA-TJA-04 complete"],
  "decomposed_requirements": ["FSR-TJA-01a: planner bounds trajectory (ASIL C(D))", "FSR-TJA-01b: supervisor triggers minimal-risk manoeuvre (ASIL B(D))"],
  "parent_asil": "D",
  "child_asils": ["C", "B"]
}
```

**1e. FN-APA**
```json
{
  "safety_req": {"id": "SG-APA-01", "text": "Avoid unintended vehicle motion above 7 km/h during automated parking", "asil": "B"},
  "architecture": {"channels": ["parking controller", "speed limiter"], "diversity": "limiter on brake ECU"},
  "independence_claims": ["separate ECUs", "independent wheel-speed source", "dependent failure analysis DFA-APA-01 complete"],
  "decomposed_requirements": ["FSR-APA-01a: controller limits speed request (ASIL A(B))", "FSR-APA-01b: brake ECU limiter caps speed (ASIL A(B))"],
  "parent_asil": "B",
  "child_asils": ["A", "A"]
}
```

**Record per item:** `accepted` (true/false), matched decomposition scheme, child ranks, independence-claim count, whether a DFA is referenced, and the raw output or error text.

**Result that changes status:** if the tool returns an error, or returns output that explicitly says the children do not cover the parent, the decomposition is rejected and the status becomes `decomposition_invalid` (rule D1). Otherwise the item moves on to Step 2.

---

### Step 2 — Hardware metrics check (covers all five items; Gate: PMHF / hardware metrics)

Tool: **`fmea_fta_engine`**. Make one call per item. Source: `inputs/fmeda_metrics.json` → `fmeda[]`. Pass the explicit FMEDA results (`pmhf_fit`, `spfm_pct`, `lfm_pct`) as supplied. Do **not** invent `failure_modes`, `lifetime_h`, `fault_tree` or `fmea_rows`. None of these exist in `inputs/` (see CAPABILITIES.md, Gap 2).

**2a. FN-AEB**
```json
{"architecture": {"elements": ["fusion ECU", "radar monitor", "brake actuator interface"]}, "failure_rates": {"fusion_ecu_fit": 210, "radar_monitor_fit": 95, "brake_if_fit": 40}, "asil_req": "D", "pmhf_fit": 6.2, "spfm_pct": 99.4, "lfm_pct": 92.1}
```
**2b. FN-LKA**
```json
{"architecture": {"elements": ["LKA controller", "torque limiter", "torque sensor"]}, "failure_rates": {"controller_fit": 180, "limiter_fit": 60, "sensor_fit": 35}, "asil_req": "D", "pmhf_fit": 3.1, "spfm_pct": 99.7, "lfm_pct": 96.0}
```
**2c. FN-ACC**
```json
{"architecture": {"elements": ["ACC controller", "torque monitor"]}, "failure_rates": {"controller_fit": 150, "monitor_fit": 70}, "asil_req": "C", "pmhf_fit": 8.0, "spfm_pct": 99.0, "lfm_pct": 90.4}
```
**2d. FN-TJA**
```json
{"architecture": {"elements": ["TJA planner SoC", "safety supervisor", "actuator gateway"]}, "failure_rates": {"planner_fit": 260, "supervisor_fit": 85, "gateway_fit": 45}, "asil_req": "D", "pmhf_fit": 7.5, "spfm_pct": 98.9, "lfm_pct": 91.0}
```
**2e. FN-APA**
```json
{"architecture": {"elements": ["parking controller", "brake ECU limiter"]}, "failure_rates": {"controller_fit": 120, "limiter_fit": 50}, "asil_req": "B", "pmhf_fit": 4.0, "spfm_pct": 99.2, "lfm_pct": 93.5}
```

**Record per item:** the returned `pmhf_target`, `spfm_target` and `lfm_target` (the programme targets, **not** the separately returned "ISO targets"); the tool's own pass/fail; the input `pmhf_fit`, `spfm_pct` and `lfm_pct`; and the three comparison booleans from rule H2.

**Applied-target selection (rule H1):**
- The **applied targets** are the `pmhf_target`, `spfm_target` and `lfm_target` returned by the ASIL-D calls (2a, 2b, 2d).
- If those three calls return identical targets, use them for all five items, including FN-ACC (`asil_req` C) and FN-APA (`asil_req` B). This follows Brief rule 3: "programme-wide ASIL-D targets; apply them to every function".
- If 2c or 2e returns different targets, still apply the ASIL-D targets. Record the difference in `result.json → discrepancies`.
- If the three ASIL-D calls disagree with each other, apply the strictest value of each target: the smallest `pmhf_target`, the largest `spfm_target` and the largest `lfm_target`. Record a discrepancy.
- If no call returns numeric programme targets, every item that reaches this check gets `hw_metrics_fail` (fail closed), and you record that the targets were unavailable.

**Result that changes status:** see rule H2. If any comparison fails, the status becomes `hw_metrics_fail`.

---

### Step 3 — V&V completion check (covers all five items; Gate: V&V)

Tool: **`safety_validation_report`**. Make one call per item. Source: `inputs/vv_evidence.json` → `vv[]`. Map `all_evidence`, `safety_case`, `vv_report_path`, `requirements_covered_pct` and `defects_open` verbatim. Do not use the `requirements` or `defects` array forms.

**3a. FN-AEB**
```json
{"all_evidence": ["HIL campaign HIL-AEB-12", "track test TT-AEB-07", "SIL regression SIL-AEB-31"], "safety_case": {"top_goal": "FN-AEB is acceptably safe within its ODD", "open_goals": 0}, "vv_report_path": "evidence/vv/FN-AEB-vv-report.pdf", "requirements_covered_pct": 97.4, "defects_open": 0}
```
**3b. FN-LKA**
```json
{"all_evidence": ["HIL campaign HIL-LKA-09", "proving-ground test PG-LKA-04", "SIL regression SIL-LKA-22"], "safety_case": {"top_goal": "FN-LKA is acceptably safe within its ODD", "open_goals": 0}, "vv_report_path": "evidence/vv/FN-LKA-vv-report.pdf", "requirements_covered_pct": 99.1, "defects_open": 0}
```
**3c. FN-ACC**
```json
{"all_evidence": ["HIL campaign HIL-ACC-15", "road test RT-ACC-11"], "safety_case": {"top_goal": "FN-ACC is acceptably safe within its ODD", "open_goals": 0}, "vv_report_path": "evidence/vv/FN-ACC-vv-report.pdf", "requirements_covered_pct": 95.0, "defects_open": 0}
```
**3d. FN-TJA**
```json
{"all_evidence": ["HIL campaign HIL-TJA-06", "scenario catalogue run SC-TJA-03"], "safety_case": {"top_goal": "FN-TJA is acceptably safe within its ODD", "open_goals": 0}, "vv_report_path": "evidence/vv/FN-TJA-vv-report.pdf", "requirements_covered_pct": 96.8, "defects_open": 0}
```
**3e. FN-APA**
```json
{"all_evidence": ["HIL campaign HIL-APA-05", "parking-lot test PL-APA-02"], "safety_case": {"top_goal": "FN-APA is acceptably safe within its ODD", "open_goals": 1}, "vv_report_path": "evidence/vv/FN-APA-vv-report.pdf", "requirements_covered_pct": 98.0, "defects_open": 1}
```

**Record per item:** the tool's evidence tally, computed coverage, open-defect count, gate snapshot, DRAFT status, and the raw output or error text.

**Result that changes status:** if the tool errors or does not accept V&V completion, the status becomes `vv_incomplete` (rule V1). The brief's rule-4 cross-check (V2) can also force `vv_incomplete`.

---

### Step 4 — Assign statuses and write deliverables (covers all five items)

No domain tool is used here. Apply the Decision rules below to the evidence from Steps 1–3. Then write `result.json` and `RESULT.md`. `RESULT.md` must use calibrated language (Brief rule 6): passing these gates is evidence for a release decision, not proof that a function is safe. Every `release_candidate` must be labelled **DRAFT — pending safety-manager review**.

## Decision rules

Apply these rules per item, strictly in order **D → H → V → R**. The first rule that fires sets the status. Rules for later checks are never consulted for status once an earlier one has fired.

**D. Decomposition (Step 1, `asil_decompose_verify`)**
- **D1.** The decomposition is rejected if **any** of these is true. The status is then `decomposition_invalid`. STOP.
  - (a) The call returned an error, including after one identical retry. This follows Brief rule 2: "A tool error is a rejection".
  - (b) The output explicitly reports that the child ASILs do not cover the parent (for example a false validity/coverage flag, or no matched scheme reported as a failure).
- **D2.** Otherwise the decomposition is accepted. Go to H.
- **D-note.** The input-schema difference (plain letters vs the tool example's `"B(D)"` form) is not grounds for rewriting the input. Whatever the tool does with the verbatim input decides the outcome. If an error message names the notation as the cause, record that in `discrepancies` for the safety manager, but the status still follows D1.

**H. Hardware metrics (Step 2, `fmea_fta_engine`), using the applied targets from rule H1**
- **H2.** Compute three booleans using the input values from `inputs/fmeda_metrics.json`:
  - `pmhf_pass = pmhf_fit <= pmhf_target` (equality passes)
  - `spfm_pass = spfm_pct >= spfm_target` (equality passes)
  - `lfm_pass = lfm_pct >= lfm_target` (equality passes)
- **H3.** If any boolean is false, the status is `hw_metrics_fail`. STOP.
- **H4.** If the `fmea_fta_engine` call for this item errored, or no applied targets are available, the status is `hw_metrics_fail` (fail closed). STOP.
- **H5.** If all three booleans are true, go to V.
- **H-note.** Status follows the explicit H2 comparison against the applied targets, **not** the tool's own pass/fail field and not the ISO per-ASIL targets. If the tool's pass/fail disagrees with H2, record a discrepancy. Do not use the README values (PMHF "<10 FIT", SPFM "≥99%", LFM "≥90%") as thresholds. If they differ from the tool's programme targets, report them only as a discrepancy.

**V. V&V completion (Step 3, `safety_validation_report`)**
- **V1.** If the call errored (Brief rule 4: "A tool error is a rejection"), or its output does not accept V&V completion, the status is `vv_incomplete`. STOP.
- **V2.** If the tool accepts, cross-check against Brief rule 4 using the input values. If `requirements_covered_pct < 95` or `defects_open != 0`, the status is `vv_incomplete` (fail closed) and you record a discrepancy. `requirements_covered_pct` = 95.0 meets "at least 95".
- **V3.** If the tool accepts and V2 does not fire, go to R.
- **V-note.** `safety_case.open_goals` is not a gate input under Brief rule 4. Report it as a flag in `RESULT.md`, not as a decision input.

**R. Release candidate**
- **R1.** D2, H5 and V3 all held, so the status is `release_candidate`. Mark it `"draft": true` and "pending safety-manager review".

**Tie-break / integrity:** each item gets exactly one status. If evidence for a check is missing, that check counts as failed (fail closed). It never counts as passed.

## Gates

Before any item can receive the only positive status, `release_candidate`, all three domain gates below must pass **for that item**, in this order:

1. **ASIL Decomposition gate.** `asil_decompose_verify` accepts the decomposition (rule D2).
2. **PMHF / hardware-metrics gate.** `fmea_fta_engine` returned programme targets, and PMHF ≤ `pmhf_target`, SPFM ≥ `spfm_target` and LFM ≥ `lfm_target` (rule H5).
3. **V&V gate.** `safety_validation_report` accepts V&V completion, and the input meets coverage ≥ 95 and open defects = 0 (rule V3).

**Not assessed by this plan, to be stated in RESULT.md:** the README's HARA, Safety Concept and Release gates. No inputs or brief rule cover them. Passing the three gates above does **not** pass the Release gate. Release remains a release-board / safety-manager decision.

## Acceptance criteria

`result.json` is complete only if it is valid JSON that contains all of the following:

1. **`items`**: exactly five entries, keyed or ordered `FN-AEB`, `FN-LKA`, `FN-ACC`, `FN-TJA`, `FN-APA`. Each entry contains:
   - `status`: exactly one of `release_candidate`, `decomposition_invalid`, `hw_metrics_fail`, `vv_incomplete`;
   - `deciding_rule`: the rule ID that set the status (e.g. `D1a`, `H3`, `V1`, `R1`);
   - `decomposition`: `{accepted, scheme, child_ranks, independence_claim_count, dfa_referenced, error}` from Step 1;
   - `hw_metrics`: `{pmhf_fit, spfm_pct, lfm_pct, pmhf_target, spfm_target, lfm_target, pmhf_pass, spfm_pass, lfm_pass, tool_pass_fail, error}` from Step 2. The inputs come from `inputs/fmeda_metrics.json` and the targets are the applied values from rule H1;
   - `vv`: `{accepted, requirements_covered_pct, defects_open, evidence_count, error}` from Step 3;
   - `informational_after_failure`: true if a later check was run after the deciding failure;
   - `draft`: true for every item, and explicitly "pending safety-manager review" for any `release_candidate`;
   - `flags`: item-level flags, for example FN-APA `safety_case.open_goals = 1`, the ASIL-D targets applied to an ASIL C/B item (FN-ACC, FN-APA), and boundary values such as FN-ACC coverage = 95.0.
2. **`applied_targets`**: the `pmhf_target`, `spfm_target` and `lfm_target` values used, and which call(s) they came from.
3. **`evidence`**: the raw output or error text of all 15 tool calls (3 tools × 5 items), keyed by tool and function.
4. **`discrepancies`**: a list, empty if there are none, covering README vs tool targets, tool pass/fail vs the H2 comparison, per-ASIL vs ASIL-D target differences, any notation-related tool errors, and any tool-accept vs Brief rule 4 mismatch.
5. **`limitations`**: at least these four:
   - DFA and independence claims are taken from input text and not verified;
   - FMEDA values are taken as given, because there are no `failure_modes` or `lifetime_h`, so they cannot be re-derived;
   - `vv_report_path` files are illustrative and their existence was not checked;
   - the HARA, Safety Concept and Release gates were not assessed.
6. **`summary`**: a count of items per status. The counts must add up to 5.
7. No number appears anywhere in `result.json` that does not trace to `inputs/` or to a recorded tool output.

`RESULT.md` must present the same statuses and numbers as `result.json`, in calibrated language, labelled DRAFT for safety-manager review.
