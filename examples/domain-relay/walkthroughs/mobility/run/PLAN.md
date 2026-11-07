# PLAN — ISO 26262 release-gate review of five ADAS functions (mobility domain)

Planner stage. This plan has not been run. No item has a status yet.
Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/asil_decomposition.json`,
`inputs/fmeda_metrics.json`, `inputs/vv_evidence.json`, `tokn-self/DOMAIN-README.md`,
`tokn-self/introspect-slice.json`.

## Objective

Give each of FN-AEB, FN-LKA, FN-ACC, FN-TJA and FN-APA exactly one status from
{`release_candidate`, `decomposition_invalid`, `hw_metrics_fail`, `vv_incomplete`}. The status comes from three
tool checks run in a fixed order: `asil_decompose_verify`, then `fmea_fta_engine`, then
`safety_validation_report`. Record the result in `result.json` and `RESULT.md` as a DRAFT for safety-manager review.

## Steps

General instructions for the Executor:

- **Call all 15 tools.** That is 3 tools × 5 functions, even after an earlier check has failed. All three tools are T0
  (read-only analysis), and the extra calls make the evidence complete. **Only the first failing check, in the
  order decomposition → HW metrics → V&V, sets the status** (BRIEF rule 1). Results from later checks are evidence
  only.
- **Pass the input fields verbatim.** Copy every value character-for-character from `inputs/`. The only key you
  drop is the `function` label, because no tool takes it as a parameter. Do not add, rename, round or "fix" any field.
- **Save every tool response in full** (raw JSON/text) under `tool_log` in `result.json` (see Acceptance criteria).
- **If a call errors or times out, retry it once with identical input.** If it fails a second time, record the error.
  Rules R1/R2/R3 below say how an error maps to a status.
- **Inspect the output fields on the first call to each tool** (gaps 1 and 7 in CAPABILITIES.md). Record the exact
  field names that carry (a) the verdict and (b) the targets. Read every later call through those same field names.

### Step 1: Decomposition check (Check 1)

Items: FN-AEB, FN-LKA, FN-ACC, FN-TJA, FN-APA
Tool: `asil_decompose_verify`. It is called once per function, with these exact inputs from
`inputs/asil_decomposition.json`:

1a. **FN-AEB**
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
1b. **FN-LKA**
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
1c. **FN-ACC**
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
1d. **FN-TJA**
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
1e. **FN-APA**
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
What changes status: if the tool rejects a function (rule R1), that function becomes `decomposition_invalid`
and no later check can change it. If the tool accepts, the function goes on to Step 2's verdict.

### Step 2: Hardware-metrics check (Check 2)

Items: FN-AEB, FN-LKA, FN-ACC, FN-TJA, FN-APA
Tool: `fmea_fta_engine`. It is called once per function, with these exact inputs from `inputs/fmeda_metrics.json`.
Pass `architecture`, `failure_rates` and `asil_req` as the tool parameters. **Do not pass** `pmhf_fit`,
`spfm_pct` or `lfm_pct` as inputs. Those are the FMEDA values that get *compared* against the targets.

| call | function | `architecture` | `failure_rates` | `asil_req` | FMEDA values to compare (from input file) |
|---|---|---|---|---|---|
| 2a | FN-AEB | `{"elements": ["fusion ECU", "radar monitor", "brake actuator interface"]}` | `{"fusion_ecu_fit": 210, "radar_monitor_fit": 95, "brake_if_fit": 40}` | `"D"` | pmhf_fit 6.2, spfm_pct 99.4, lfm_pct 92.1 |
| 2b | FN-LKA | `{"elements": ["LKA controller", "torque limiter", "torque sensor"]}` | `{"controller_fit": 180, "limiter_fit": 60, "sensor_fit": 35}` | `"D"` | pmhf_fit 3.1, spfm_pct 99.7, lfm_pct 96.0 |
| 2c | FN-ACC | `{"elements": ["ACC controller", "torque monitor"]}` | `{"controller_fit": 150, "monitor_fit": 70}` | `"C"` | pmhf_fit 8.0, spfm_pct 99.0, lfm_pct 90.4 |
| 2d | FN-TJA | `{"elements": ["TJA planner SoC", "safety supervisor", "actuator gateway"]}` | `{"planner_fit": 260, "supervisor_fit": 85, "gateway_fit": 45}` | `"D"` | pmhf_fit 7.5, spfm_pct 98.9, lfm_pct 91.0 |
| 2e | FN-APA | `{"elements": ["parking controller", "brake ECU limiter"]}` | `{"controller_fit": 120, "limiter_fit": 50}` | `"B"` | pmhf_fit 4.0, spfm_pct 99.2, lfm_pct 93.5 |

From each response, extract `pmhf_target` (FIT), `spfm_target` (%) and `lfm_target` (%). Also extract any PMHF/SPFM/LFM
values the tool computes itself, and record them as `tool_computed_*`.

What changes status: a function whose decomposition was accepted becomes `hw_metrics_fail` if any comparison
under rule R2 fails, or if the targets cannot be read. Otherwise it goes on to Step 3.

### Step 3: V&V completion check (Check 3)

Items: FN-AEB, FN-LKA, FN-ACC, FN-TJA, FN-APA
Tool: `safety_validation_report`. It is called once per function, with these exact inputs from `inputs/vv_evidence.json`:

3a. **FN-AEB**
```json
{"all_evidence": ["HIL campaign HIL-AEB-12", "track test TT-AEB-07", "SIL regression SIL-AEB-31"], "safety_case": {"top_goal": "FN-AEB is acceptably safe within its ODD", "open_goals": 0}, "vv_report_path": "evidence/vv/FN-AEB-vv-report.pdf", "requirements_covered_pct": 97.4, "defects_open": 0}
```
3b. **FN-LKA**
```json
{"all_evidence": ["HIL campaign HIL-LKA-09", "proving-ground test PG-LKA-04", "SIL regression SIL-LKA-22"], "safety_case": {"top_goal": "FN-LKA is acceptably safe within its ODD", "open_goals": 0}, "vv_report_path": "evidence/vv/FN-LKA-vv-report.pdf", "requirements_covered_pct": 99.1, "defects_open": 0}
```
3c. **FN-ACC**
```json
{"all_evidence": ["HIL campaign HIL-ACC-15", "road test RT-ACC-11"], "safety_case": {"top_goal": "FN-ACC is acceptably safe within its ODD", "open_goals": 0}, "vv_report_path": "evidence/vv/FN-ACC-vv-report.pdf", "requirements_covered_pct": 95.0, "defects_open": 0}
```
3d. **FN-TJA**
```json
{"all_evidence": ["HIL campaign HIL-TJA-06", "scenario catalogue run SC-TJA-03"], "safety_case": {"top_goal": "FN-TJA is acceptably safe within its ODD", "open_goals": 0}, "vv_report_path": "evidence/vv/FN-TJA-vv-report.pdf", "requirements_covered_pct": 96.8, "defects_open": 0}
```
3e. **FN-APA**
```json
{"all_evidence": ["HIL campaign HIL-APA-05", "parking-lot test PL-APA-02"], "safety_case": {"top_goal": "FN-APA is acceptably safe within its ODD", "open_goals": 1}, "vv_report_path": "evidence/vv/FN-APA-vv-report.pdf", "requirements_covered_pct": 98.0, "defects_open": 1}
```
Pass `requirements_covered_pct` and `defects_open` as numbers, not strings.
What changes status: if both earlier checks passed, the function becomes `vv_incomplete` when the tool rejects it
(rule R3) and `release_candidate` when the tool accepts it.

### Step 4: Assign statuses and write the deliverables

Items: all five. No domain tool is needed. Apply the Decision rules mechanically, then write `result.json` and
`RESULT.md` (Executor stage). `RESULT.md` must use calibrated language: a pass is "evidence supporting a release
decision", never "safe". Every `release_candidate` must be labelled DRAFT.

### Tools deliberately not used

`hara_automate`, `safety_case_build`, `sotif_odd_coverage`, `tara_engine`, and the simulation, V2X, EV/BMS, UAM and
regulatory tools are not used. The brief defines no check for them and `inputs/` has no matching input
(CAPABILITIES.md). Do not call them to "strengthen" a verdict.

## Decision rules

Notation: for function F, D(F), H(F) and V(F) are the outcomes (PASS/FAIL) of Steps 1, 2 and 3.

**R1: Decomposition verdict from `asil_decompose_verify`**
- D(F) = PASS only if the call returns without error **and** the output carries an explicit positive verdict. That
  means a verdict field identified on the first call (for example `valid`/`passed`/`accepted`/`approved` = `true`, or
  `status`/`verdict` equal to a pass/valid/accepted value) **and** no field that indicates rejection.
- D(F) = FAIL in every other case: a tool error (after one retry), an explicit negative verdict, a reported
  coverage/decomposition violation, or a verdict that is missing or ambiguous (fail-closed).
- The tool's verdict governs, even where it disagrees with the Executor's own reading of ISO 26262-9.
  If they disagree, record the disagreement in `discrepancies`. Do not override the verdict.

**R2: Hardware-metrics verdict from `fmea_fta_engine`**
- Targets: `pmhf_target`, `spfm_target` and `lfm_target`, read from the tool output only. Never take them from
  DOMAIN-README.md or from memory (BRIEF rule 5).
- BRIEF says the targets are programme-wide ASIL-D and apply to every function. If calls 2c (asil_req C) or 2e
  (asil_req B) return targets that differ from those returned by ASIL-D calls 2a, 2b and 2d, use the ASIL-D-call
  targets for all five functions and record the difference in `discrepancies`. If 2a, 2b and 2d disagree with
  each other, set H(F) = FAIL for every function whose decomposition passed, and flag the inconsistency.
- Values compared: the FMEDA values in `inputs/fmeda_metrics.json` (`pmhf_fit`, `spfm_pct`, `lfm_pct`), with no
  rounding.
- H(F) = PASS only if all three hold: `pmhf_fit <= pmhf_target` **and** `spfm_pct >= spfm_target`
  **and** `lfm_pct >= lfm_target`. Equality passes.
- H(F) = FAIL if any comparison fails, **or** any of the three targets is absent from the output, **or** the call
  errors after one retry. These last two are fail-closed cases; record the reason as `target_unavailable` or `tool_error`.
- If the tool returns its own PMHF/SPFM/LFM values and they differ from the input values, record both in
  `discrepancies`. The verdict still uses the input values against the tool's targets. If the *tool-computed*
  values would give a different verdict, say so explicitly in RESULT.md.

**R3: V&V verdict from `safety_validation_report`**
- V(F) = PASS only if the call returns without error **and** the output carries an explicit acceptance verdict, with
  no rejection indicator. The same reading applies as in R1.
- V(F) = FAIL on a tool error (after one retry), an explicit rejection, or a missing or ambiguous verdict.
- Cross-check: BRIEF rule 4 says the tool accepts only when `requirements_covered_pct >= 95` and `defects_open == 0`.
  If the tool verdict contradicts that rule for the given input, the tool verdict still governs the status.
  Record the contradiction in `discrepancies`.
- `safety_case.open_goals` > 0 (FN-APA has 1) is not a rule-4 criterion. Report it as an observation. It changes the
  status only if the tool itself rejects on it.

**R4: Status assignment (first failure wins, evaluated in this order)**
1. D(F) = FAIL → `decomposition_invalid`
2. else H(F) = FAIL → `hw_metrics_fail`
3. else V(F) = FAIL → `vv_incomplete`
4. else (all PASS) and all Gates below satisfied → `release_candidate` (DRAFT)

Each function gets exactly one status. No other status string is allowed.

## Gates

Of the six mobility domain gates named in DOMAIN-README.md (HARA, Safety Concept, ASIL Decomposition, PMHF, V&V,
Release), a function may receive `release_candidate` only when all of the following hold:

- **G1, ASIL Decomposition gate:** D(F) = PASS from an actual `asil_decompose_verify` call for F.
- **G2, PMHF/hardware-metrics gate:** H(F) = PASS. PMHF, SPFM and LFM are compared against tool-returned targets.
- **G3, V&V gate:** V(F) = PASS from an actual `safety_validation_report` call for F.
- **G4, Evidence integrity:** all three raw tool responses for F are stored in `tool_log`. Every number reported for
  F traces to a tool response or an input file.
- **G5, Release gate (human):** not passable by this relay. `release_candidate` is always `"draft": true` and
  awaits safety-manager review.

The HARA and Safety Concept gates are **not assessed**. No input or brief check covers them. List them in
`not_assessed`, not as passed. If a check is missing because its tool was never called, the gate is not
satisfied. A missing check is never treated as a pass.

## Acceptance criteria

`result.json` is complete only if it is valid JSON containing:

1. `items`: exactly five entries, keyed or labelled `FN-AEB`, `FN-LKA`, `FN-ACC`, `FN-TJA`, `FN-APA`. Each entry has:
   - `status`: one of the four vocabulary strings;
   - `first_failing_check`: `"decomposition"` | `"hw_metrics"` | `"vv"` | `null`;
   - `draft`: `true` (for every item; mandatory for `release_candidate`);
   - `decomposition`: `{tool: "asil_decompose_verify", parent_asil, child_asils, verdict: PASS|FAIL, verdict_source_field, reason}`;
   - `hw_metrics`: `{tool: "fmea_fta_engine", asil_req, pmhf_fit, spfm_pct, lfm_pct, pmhf_target, spfm_target, lfm_target, pmhf_pass, spfm_pass, lfm_pass, tool_computed: {...}|null, verdict: PASS|FAIL, reason}`;
   - `vv`: `{tool: "safety_validation_report", requirements_covered_pct, defects_open, open_goals, verdict: PASS|FAIL, verdict_source_field, reason}`;
   - `observations`: free-text notes (for example FN-APA `open_goals: 1`, or that independence/DFA claims were taken as stated).
2. `targets`: the `pmhf_target`, `spfm_target` and `lfm_target` used, plus the tool call(s) they came from.
3. `tool_log`: 15 entries (3 tools × 5 functions), each `{call_id (1a…3e), tool, input, raw_output, error|null, retried: bool}`.
4. `discrepancies`: a list, which may be empty. It covers tool vs README thresholds, tool vs input metric values,
   tool verdict vs BRIEF rule 4, target differences across `asil_req`, and tool verdict vs the Executor's ISO 26262-9
   reading.
5. `not_assessed`: at least HARA gate, Safety Concept gate, DFA/independence evidence, SOTIF, cybersecurity, and
   the human Release gate.
6. `summary`: a count of items per status. The counts must sum to 5.
7. `disclaimer`: a statement that the data is synthetic, the statuses are a DRAFT gate review, and passing these
   gates is evidence for a release decision, not proof that a function is safe.

Completeness check before finishing: there are 5 items, 15 tool_log entries, every status is in the vocabulary,
every status agrees with R4 applied to the recorded verdicts, and no target value appears that is not in a
tool_log `raw_output`.
