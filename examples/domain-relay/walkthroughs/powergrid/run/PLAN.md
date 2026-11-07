# PLAN — Cluster 7 N-1-1 and grid-forming screen (IR-1 … IR-5)

Planner stage. This file says what to run and how to decide. It does not run anything or give any item's status.
Sources: `BRIEF.md`, `CAPABILITIES.md`, `inputs/n11_study.json`, `inputs/ibr_registry.json`.

## Objective

For each of IR-1 to IR-5, run one N-1-1 screen (`powergrid_n1_1_screen`) and one IBR grid-forming gate (`powergrid_ibr_stability_gate`) with that request's own inputs. Then assign exactly one status (approve, approve_with_conditions, reject or blocked) using the rules below, and record it in `result.json`.

## Steps

General instructions for the Executor:

- Make exactly **10 domain tool calls**: 5 to `powergrid_n1_1_screen` and 5 to `powergrid_ibr_stability_gate`. The 10 calls are independent, so you may run them in parallel.
- Copy every input value from the files below **exactly as written**. Do not round, re-key or reorder anything.
- **Do not** pass `network` or `network_path` to `powergrid_n1_1_screen`. The model file `models/synthetic_330bus_summer_peak_2029.raw` is not in the repository, and every pair is already supplied.
- **Do not** pass `zone_short_circuit_mva`, because it is not in `inputs/`.
- **Do not** call `approve_interconnection`, `run_n1_contingency_screen`, `generate_reliability_report`, `run_power_flow` or `inspect_network` (see CAPABILITIES.md for why).
- Save the raw output of each call. Every number in `result.json` and `RESULT.md` must be copied from these outputs (BRIEF Rule 6).

### Shared input: `RESOURCES`

This is the full existing fleet, copied verbatim from `inputs/ibr_registry.json` → `resources`. Pass the whole list in every gate call.

```json
[
  {"id": "GFM-N1", "type": "GFM", "capacity_mw": 200, "zone": "Z-NORTH", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFL-N1", "type": "GFL", "capacity_mw": 50, "zone": "Z-NORTH", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFM-E1", "type": "GFM", "capacity_mw": 250, "zone": "Z-EAST", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFL-E1", "type": "GFL", "capacity_mw": 80, "zone": "Z-EAST", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFM-S1", "type": "GFM", "capacity_mw": 300, "zone": "Z-SOUTH", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFL-S1", "type": "GFL", "capacity_mw": 100, "zone": "Z-SOUTH", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFM-W1", "type": "GFM", "capacity_mw": 350, "zone": "Z-WEST", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFL-W1", "type": "GFL", "capacity_mw": 100, "zone": "Z-WEST", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFM-C1", "type": "GFM", "capacity_mw": 200, "zone": "Z-CENTRAL", "dynamic_response_validated": true, "ieee_2800_compliant": true},
  {"id": "GFL-C1", "type": "GFL", "capacity_mw": 60, "zone": "Z-CENTRAL", "dynamic_response_validated": true, "ieee_2800_compliant": true}
]
```

In every gate call, set `threshold_pct` = `30` (from `inputs/ibr_registry.json` → `threshold_pct`).

---

### Step 1 — IR-1 N-1-1 screen (zone Z-NORTH)

- **Items covered:** IR-1
- **Tool:** `powergrid_n1_1_screen`
- **Inputs:**
  - `first_contingencies`:
    ```json
    [{"id": "L-101", "type": "line", "zone": "Z-NORTH"},
     {"id": "L-102", "type": "line", "zone": "Z-NORTH"},
     {"id": "T-11", "type": "transformer", "zone": "Z-NORTH"}]
    ```
  - `pair_results`:
    ```json
    {"L-101|L-102": {"branch_loading_pct": {"L-103": 98.2}, "bus_voltage_pu": {"B-12": 0.96}},
     "L-101|T-11": {"branch_loading_pct": {"L-103": 104.5}, "bus_voltage_pu": {"B-12": 0.93}},
     "L-102|T-11": {"branch_loading_pct": {"L-104": 88.0}, "bus_voltage_pu": {"B-14": 0.95}}}
    ```
  - Omit `second_contingencies` (it defaults to `first_contingencies`).
- **What changes the status:**
  - Any counted CRITICAL violation → reject.
  - Only counted HIGH (or other non-CRITICAL) violations → approve_with_conditions.
  - No counted violations → this screen allows approve.
  - Incomplete screening or a tool error → blocked (fail-closed; see Gate G1).

### Step 2 — IR-1 IBR gate

- **Items covered:** IR-1
- **Tool:** `powergrid_ibr_stability_gate`
- **Inputs:**
  - `resources` = RESOURCES
  - `threshold_pct` = `30`
  - `additions`:
    ```json
    [{"id": "IR-1-BESS", "type": "GFM", "capacity_mw": 150, "zone": "Z-NORTH", "dynamic_response_validated": true, "ieee_2800_compliant": true}]
    ```
- **What changes the status:** a gate BLOCK (or a threshold violation or expansion issue) attributed to zone Z-NORTH or to IR-1-BESS → blocked. Otherwise the gate passes.

### Step 3 — IR-2 N-1-1 screen (zone Z-EAST)

- **Items covered:** IR-2
- **Tool:** `powergrid_n1_1_screen`
- **Inputs:**
  - `first_contingencies`:
    ```json
    [{"id": "L-201", "type": "line", "zone": "Z-EAST"},
     {"id": "L-202", "type": "line", "zone": "Z-EAST"},
     {"id": "G-21", "type": "generator", "zone": "Z-EAST"}]
    ```
  - `pair_results`:
    ```json
    {"L-201|L-202": {"branch_loading_pct": {"L-203": 131.0}, "bus_voltage_pu": {"B-22": 0.91}},
     "L-201|G-21": {"branch_loading_pct": {"L-203": 109.0}, "bus_voltage_pu": {"B-22": 0.88}},
     "L-202|G-21": {"branch_loading_pct": {"L-204": 97.0}, "bus_voltage_pu": {"B-24": 0.97}}}
    ```
- **What changes the status:** same rule as Step 1. L-203 at 131.0% lies between 115% and 132.25%. Check what severity the tool gives it, and quote that severity.

### Step 4 — IR-2 IBR gate

- **Items covered:** IR-2
- **Tool:** `powergrid_ibr_stability_gate`
- **Inputs:**
  - `resources` = RESOURCES
  - `threshold_pct` = `30`
  - `additions`:
    ```json
    [{"id": "IR-2-BESS", "type": "GFM", "capacity_mw": 120, "zone": "Z-EAST", "dynamic_response_validated": true, "ieee_2800_compliant": true}]
    ```
- **What changes the status:** a BLOCK attributed to Z-EAST or IR-2-BESS → blocked.

### Step 5 — IR-3 N-1-1 screen (zone Z-SOUTH)

- **Items covered:** IR-3
- **Tool:** `powergrid_n1_1_screen`
- **Inputs:**
  - `first_contingencies`:
    ```json
    [{"id": "L-301", "type": "line", "zone": "Z-SOUTH"},
     {"id": "L-302", "type": "line", "zone": "Z-SOUTH"},
     {"id": "T-31", "type": "transformer", "zone": "Z-SOUTH"}]
    ```
  - `pair_results`:
    ```json
    {"L-301|L-302": {"branch_loading_pct": {"L-303": 101.0}, "bus_voltage_pu": {"B-32": 0.94}},
     "L-301|T-31": {"branch_loading_pct": {"L-303": 99.5}, "bus_voltage_pu": {"B-32": 0.92}},
     "L-302|T-31": {"branch_loading_pct": {"L-304": 92.0}, "bus_voltage_pu": {"B-34": 0.96}}}
    ```
- **What changes the status:** same rule as Step 1.

### Step 6 — IR-3 IBR gate

- **Items covered:** IR-3
- **Tool:** `powergrid_ibr_stability_gate`
- **Inputs:**
  - `resources` = RESOURCES
  - `threshold_pct` = `30`
  - `additions`:
    ```json
    [{"id": "IR-3-PV", "type": "GFL", "capacity_mw": 60, "zone": "Z-SOUTH", "dynamic_response_validated": true, "ieee_2800_compliant": true}]
    ```
- **What changes the status:** this addition is GFL-only with no GFM. If the gate BLOCKS and its returned Z-SOUTH GFL penetration is strictly above 30 → blocked.

### Step 7 — IR-4 N-1-1 screen (zone Z-WEST)

- **Items covered:** IR-4
- **Tool:** `powergrid_n1_1_screen`
- **Inputs:**
  - `first_contingencies`:
    ```json
    [{"id": "L-401", "type": "line", "zone": "Z-WEST"},
     {"id": "L-402", "type": "line", "zone": "Z-WEST"},
     {"id": "T-41", "type": "transformer", "zone": "Z-WEST"}]
    ```
  - `pair_results`:
    ```json
    {"L-401|L-402": {"branch_loading_pct": {"L-403": 115.0}, "bus_voltage_pu": {"B-42": 0.85}},
     "L-401|T-41": {"branch_loading_pct": {"L-403": 112.0}, "bus_voltage_pu": {"B-42": 0.89}},
     "L-402|T-41": {"branch_loading_pct": {"L-404": 108.0}, "bus_voltage_pu": {"B-44": 1.10}}}
    ```
- **What changes the status:** same rule as Step 1. This request is a boundary case: 115.0%, 0.85 pu and 1.10 pu are each **exactly at** a limit, so apply Decision rule D3 (the boundary rule).

### Step 8 — IR-4 IBR gate

- **Items covered:** IR-4
- **Tool:** `powergrid_ibr_stability_gate`
- **Inputs:**
  - `resources` = RESOURCES
  - `threshold_pct` = `30`
  - `additions`:
    ```json
    [{"id": "IR-4-WIND", "type": "GFL", "capacity_mw": 50, "zone": "Z-WEST", "dynamic_response_validated": true, "ieee_2800_compliant": true}]
    ```
- **What changes the status:** this addition is GFL-only. If the gate BLOCKS and its returned Z-WEST penetration is strictly above 30 → blocked. A returned value exactly equal to 30.0 → not blocked (BRIEF Rule 4; apply D3).

### Step 9 — IR-5 N-1-1 screen (zone Z-CENTRAL)

- **Items covered:** IR-5
- **Tool:** `powergrid_n1_1_screen`
- **Inputs:**
  - `first_contingencies`:
    ```json
    [{"id": "L-501", "type": "line", "zone": "Z-CENTRAL"},
     {"id": "L-502", "type": "line", "zone": "Z-CENTRAL"},
     {"id": "G-51", "type": "generator", "zone": "Z-CENTRAL"}]
    ```
  - `pair_results`:
    ```json
    {"L-501|L-502": {"branch_loading_pct": {"L-503": 96.0}, "bus_voltage_pu": {"B-52": 0.90}, "stability_loss": true},
     "L-501|G-51": {"branch_loading_pct": {"L-503": 102.0}, "bus_voltage_pu": {"B-52": 0.93}},
     "L-502|G-51": {"branch_loading_pct": {"L-504": 94.0}, "bus_voltage_pu": {"B-54": 0.95}}}
    ```
- **What changes the status:** the `stability_loss: true` flag on `L-501|L-502` should come back as a CRITICAL violation, which means reject. Confirm this from the tool output; do not assume it.

### Step 10 — IR-5 IBR gate

- **Items covered:** IR-5
- **Tool:** `powergrid_ibr_stability_gate`
- **Inputs:**
  - `resources` = RESOURCES
  - `threshold_pct` = `30`
  - `additions`:
    ```json
    [{"id": "IR-5-BESS", "type": "GFM", "capacity_mw": 100, "zone": "Z-CENTRAL", "dynamic_response_validated": true, "ieee_2800_compliant": true}]
    ```
- **What changes the status:** a BLOCK attributed to Z-CENTRAL or IR-5-BESS → blocked.

### Step 11 — Assemble outputs (no domain tool)

- Apply the decision rules below to the saved outputs of Steps 1–10.
- Write `result.json` and `RESULT.md` (later stage).
- No new numbers may be introduced at this step.

## Decision rules

Apply these rules to each item separately, using only that item's two tool outputs.

**D1 — Counting N-1-1 violations.** Start from the `violations` list returned by `powergrid_n1_1_screen` for the item.

- Count a violation only if it survives the boundary rule in D3.
- Severity is the severity **the tool returned**. Quote it verbatim.
- `n_critical` = the number of counted violations with severity `CRITICAL`.
- `n_noncritical` = all other counted violations. These are normally `HIGH`. Any `MEDIUM` or other non-CRITICAL label is also counted here.

**D2 — Gate outcome.** The gate result for item IR-x is **BLOCK** if both of these hold:

- (a) the tool reports a block, or a violation or expansion issue, for IR-x's zone or IR-x's addition id; and
- (b) the zone's post-expansion GFL penetration, as returned by the tool, is strictly greater than 30.

Otherwise the gate result is **PASS**. Ignore issues that the tool raises only for other zones. Existing zones are not part of this request (BRIEF Rule 2). Record them as notes.

**D3 — Boundary rule (BRIEF Rules 3 and 4).**

- These values are **not** violations when they exactly equal the limit:
  - loading = 115.0%
  - voltage = 0.85 pu
  - voltage = 1.10 pu
  - GFL penetration = 30.0%
- A CRITICAL classification needs one of these:
  - loading strictly above 132.25% (= 115 × 1.15)
  - voltage strictly below 0.80 pu
  - `stability_loss` = true
- If the tool flags a value that is exactly at a limit, do not count it. Record it in `tool_brief_discrepancies` with these fields: element, value, the tool's severity, and the reason ("exactly at limit, BRIEF Rule 3/4").
- If the tool's severity disagrees with these thresholds for a value strictly past a limit, use the brief's classification and record the discrepancy the same way.
- Voltage strictly above 1.10 pu is not given a severity by the tool. Classify it as non-CRITICAL (counts toward approve_with_conditions) and record it as a discrepancy.

**D4 — Status (apply in order and stop at the first match; this is the precedence in BRIEF Rule 1):**

1. If Gate G1 or G2 fails for the item → `blocked`, with `blocked_reason` = `"tool_failure_or_incomplete_screen"`. This is a fail-closed rule: without valid evidence, no positive status can be given.
2. If the gate result is BLOCK → `blocked`, with `blocked_reason` = `"ibr_gate_gfl_threshold"`.
3. If `n_critical` ≥ 1 → `reject`.
4. If `n_noncritical` ≥ 1 → `approve_with_conditions`. List one required corrective action per counted violation, naming the element and the value that was quoted. Order the actions by cost and time: operating limits or RAS, then switching, then protection, then FACTS, then reconductoring, then new transmission.
5. Otherwise → `approve`.

## Gates

Both of these must pass for an item before it can receive `approve` or `approve_with_conditions`.

- **G1 — N-1-1 screen validity:**
  - the call returned without error;
  - `screening_complete` = true;
  - `unscreened_pairs` is empty;
  - `source` = `supplied_summary`;
  - the number of screened pairs = 3.
- **G2 — IBR gate validity:**
  - the call returned without error;
  - a GFL penetration value is returned for the item's zone;
  - the gate result is PASS under D2.
- **G3 — Domain disclosures (required for every item, and required in the outputs):**
  - No N-0 power flow and no N-1 (TPL P1–P5) screen was run, because the network model is unavailable. Include the warning "N-1 not checked".
  - SCR/WSCR was not assessed, because `zone_short_circuit_mva` is absent.
  - The standard used is NERC TPL-001-4 P6/P7, as the brief specifies.
  - These are planning-screen dispositions, not regulatory filings. Do not call `file_regulatory_document` or `approve_interconnection`.

## Acceptance criteria

`result.json` is complete only if all of the following hold:

1. **Top-level fields:**
   - `study` (copied from `inputs/n11_study.json` → `study`)
   - `standard`: `"NERC TPL-001-4 P6/P7"`
   - `threshold_pct`: 30
   - `items`: an array of exactly 5 objects, IR-1 … IR-5
   - `warnings`, which must include "N-1 not checked", "N-0 power flow not run" and "SCR not assessed (no short-circuit data)"
2. **Each item object** contains:
   - `id`
   - `zone`
   - `status`: exactly one of `approve` | `approve_with_conditions` | `reject` | `blocked`
   - `blocked_reason`, if the status is blocked
   - `n11`: `{ tool: "powergrid_n1_1_screen", screening_complete, source, pairs_screened, violations: [ {pair, element, metric, value, severity_as_returned, counted} ], n_critical, n_noncritical }`
   - `ibr_gate`: `{ tool: "powergrid_ibr_stability_gate", result: "PASS"|"BLOCK", zone_gfl_penetration_pct_post_expansion, gfl_headroom_mw, gfm_mw_needed, raw_block_or_violation_messages }`. Include `gfl_headroom_mw` and `gfm_mw_needed` if the tool returned them.
   - `decision_rule_applied`: e.g. `"D4.3"`
   - `conditions`: a non-empty list if the status is approve_with_conditions; otherwise an empty list
   - `tool_brief_discrepancies`: a list, which may be empty
3. **Traceability:** every numeric value appears verbatim in a saved Step 1–10 tool output. There must be no hand-computed percentages (BRIEF Rule 6).
4. **Call count:** exactly 10 domain tool calls are recorded (5 screen + 5 gate), each called with the item's own inputs as listed above.
5. **Status consistency:** each status follows from D4 applied to the recorded `n11` and `ibr_gate` fields. A reviewer who re-applies D1–D4 to the recorded fields must reach the same status.
