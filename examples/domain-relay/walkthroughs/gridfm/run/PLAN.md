# PLAN — gridfm trust disposition for PRED-A … PRED-F

Planner stage. Nothing has been executed. Every input value below is copied from `inputs/`. Every number that ends up in `result.json` / `RESULT.md` must come from a tool call (BRIEF rule 6). Do not compute statuses by hand.

## Objective

Independently verify each of the six GridSFM AC-OPF predictions (PRED-A…PRED-F) against power-flow physics, gate the deployment by model tier and OOD, and give each item exactly one of `operational_advisory`, `hold_for_review`, `warm_start_only` or `reject`, using only tool outputs.

## Steps

Run the steps in this order. Steps 1–9 do not depend on each other and can run in parallel. Step 10 depends on the dispositions from Steps 4–9. Step 11 depends on all the earlier steps.

### Step 1 — Confirm verifier checks and tolerances (all items, setup)
- **Items:** all (PRED-A…PRED-F), deployment.
- **Tool:** `list_verification_checks`
- **Input:** `{}` (no fields).
- **Record:** the list of checks and the tolerances (`powerBalancePU`, `thermalSlack`, `consistencyPU`) and the tiers.
- **Status impact:** none directly. If `powerBalancePU` ≠ 0.01 or `thermalSlack` ≠ 0, put a `tolerance_discrepancy` note in `result.json` (the brief's rule 2 says 0.01 pu and no slack). Keep using the tool's verdicts (see Decision rule R6).

### Step 2 — Scale gate (deployment)
- **Items:** deployment (applies to all items).
- **Tool:** `select_model_tier`
- **Input:** `{"bus_count": 3700}` (from `inputs/deployment_context.json` → `full_network_bus_count`).
- **Record:** the tier that is returned, or the refusal.
- **Status impact:** if the tool **refuses** (scale gate), Gate G1 fails, and rule R5 downgrades every positive status. If it returns a tier whose name differs from `"GridSFM-Open"` (the `tier` field in every prediction), record a `tier_mismatch` flag. That flag does not change status.

### Step 3 — OOD / confidence cap (deployment)
- **Items:** deployment (applies to all items).
- **Tool:** `assess_ood`
- **Input:** `{"bus_count": 3700}`. Do **not** pass `independently_verified`. Nothing in `inputs/` supplies it, so leave it unset. It defaults to unverified.
- **Record:** the OOD flag, the confidence cap (`ood_cap`), and the evidence tier it names.
- **Status impact:** none (BRIEF rule 4). The cap only limits how confident the wording in `RESULT.md` may be.

### Steps 4–9 — Independent verification, one call per item
For each item, call **`verify_surrogate_solution`** with `{"prediction": <cases[i].prediction>}`. Pass the object **exactly as given** in `inputs/predictions.json`, including `scenario`, `surrogateFeasibility`, `surrogateConfidence` and `tier`. Do not edit, round or drop any field (BRIEF rule 1). The key values for each item are listed below. Copy the full object from the file, not from this table.

| Step | Item | `cases[i]` | scenario.name | surrogateFeasibility | surrogateConfidence |
|---|---|---|---|---|---|
| 4 | PRED-A | `cases[0].prediction` | feeder-pocket-0700 | feasible | 0.94 |
| 5 | PRED-B | `cases[1].prediction` | feeder-pocket-0800 | infeasible | 0.41 |
| 6 | PRED-C | `cases[2].prediction` | feeder-pocket-0900 | feasible | 0.97 |
| 7 | PRED-D | `cases[3].prediction` | feeder-pocket-1000 | feasible | 0.88 |
| 8 | PRED-E | `cases[4].prediction` | feeder-pocket-1100 | feasible | 0.90 |
| 9 | PRED-F | `cases[5].prediction` | feeder-pocket-1200 | feasible | 0.86 |

Record the following for each item, verbatim from the tool output:
- `disposition` (OPERATIONAL / REVIEW / WARM_START / REJECTED);
- the independent feasibility verdict (for example `independentlyFeasible`);
- every violation, with its kind (voltage_bound, generator_active_limit, generator_reactive_limit, thermal_limit, power_balance, flow_voltage_consistency), the element id, the value and the limit;
- the power-balance residual;
- whether flow_voltage_consistency ran. There is no admittance data in the inputs, so it is expected to be skipped. Record what the tool actually says;
- any per-prediction confidence cap or evidence tier the tool returns (`prediction_cap`). If the tool returns none, record `null`.

**Status impact:** the disposition sets the status through rules R1–R4.

**Boundary cases to watch.** These are qualitative cues. Do not use them to make the decision. Some inputs sit **exactly at** a limit. For example, in PRED-D: B1 `vMagPU` 1.05 = `vMaxPU` 1.05; G2 `pgPU` 1.0 = `pMaxPU` 1.0; L23 `sFlowPU` 0.4 = `ratingPU` 0.4. Under BRIEF rule 2, a value exactly at a limit is **not** a violation. If the verifier flags one of these, apply rule R6.

### Step 10 — Warm-start evaluation (only items whose Step 4–9 disposition is WARM_START)
- **Items:** every item whose disposition is `WARM_START`, and no others (BRIEF rule 3).
- **Tool:** `evaluate_warm_start`
- **Input:** the matching row from `inputs/warm_start_timings.json`:

| Item | scenario | baseline_seconds | warm_seconds |
|---|---|---|---|
| PRED-A | feeder-pocket-0700 | 5.1 | 3.0 |
| PRED-B | feeder-pocket-0800 | 5.0 | 3.1 |
| PRED-C | feeder-pocket-0900 | 4.8 | 2.9 |
| PRED-D | feeder-pocket-1000 | 5.4 | 3.3 |
| PRED-E | feeder-pocket-1100 | 4.2 | 4.6 |
| PRED-F | feeder-pocket-1200 | 6.3 | 3.6 |

  Call it as `{"scenario": "<scenario>", "baseline_seconds": <b>, "warm_seconds": <w>}`.
- **Record:** `speedup` exactly as the tool returns it, plus any anomaly or scrutiny flag (speedup < 1.0, or far above the ~1.5–2× band).
- **Status impact:** speedup ≥ 1.0 → `warm_start_only`. Speedup < 1.0 → `reject` (rule R2). Use the tool's speedup value. Never divide by hand.

### Step 11 — Assemble outputs (no new tool calls)
Apply the Decision rules and Gates to the recorded outputs. Then write `result.json` and `RESULT.md`. Deployment cap = the lower of `ood_cap` (Step 3) and each item's `prediction_cap` (Steps 4–9). If `prediction_cap` is `null`, the deployment cap is `ood_cap`, and you must note that no per-prediction cap came from a tool.

### Not run
- `screen_n1_contingencies`: inputs contain no contingency cases. This is not applicable, and `result.json` must record it as not run, with that reason.

## Decision rules

Apply them in order. The first rule that matches decides the status. Only these inputs are used: the verifier `disposition`, the verifier violation kinds, the `evaluate_warm_start` speedup, and the gate results. `surrogateFeasibility` and `surrogateConfidence` are **never** used to raise a status.

- **R0 (fail-closed):** if `verify_surrogate_solution` errors, returns no disposition, or returns a disposition outside {OPERATIONAL, REVIEW, WARM_START, REJECTED} → `reject`. Record the error.
- **R1:** disposition `REJECTED` → `reject`. This includes any `power_balance` or `flow_voltage_consistency` violation. If the violation list contains either of those kinds and the disposition says otherwise, still assign `reject` and flag the inconsistency.
- **R2:** disposition `WARM_START`:
  - if `evaluate_warm_start` was not run or errored → `reject` (fail-closed: speedup ≥ 1.0 was not shown);
  - speedup (as returned by the tool) ≥ 1.0 → `warm_start_only`;
  - speedup < 1.0 → `reject`.
- **R3:** disposition `REVIEW` → `hold_for_review`.
- **R4:** disposition `OPERATIONAL` → `operational_advisory`. Actuation stays human-approved. Say so in RESULT.md.
- **R5 (gate downgrade):** if any gate in the Gates section fails, an item that would get `operational_advisory` or `warm_start_only` gets `hold_for_review` instead. `reject` stays `reject`.
- **R6 (brief/tool discrepancy):** compare each verifier violation against BRIEF rule 2, using only "strictly outside" vs "exactly at" by reading the input values. No arithmetic.
  - If the verifier flags a value that is exactly at its limit (it is stricter than the brief), keep the tool-derived status, because that is the fail-closed direction, and add a `discrepancy` note.
  - If a bus voltage, generator P/Q or branch |S| in the input is plainly strictly outside its limit and the verifier reports **no** violation for it (a possible false all-clear), the item may **not** be `operational_advisory`. Assign `hold_for_review` and add a `discrepancy` note.
- **R7:** OOD and confidence caps never change status (BRIEF rule 4). They only bound the confidence language.

## Gates

A positive status (`operational_advisory` or `warm_start_only`) may be given only if **all** of the following pass.

- **G1 — Scale gate:** `select_model_tier({"bus_count": 3700})` returns a validated tier and does not refuse. If it fails, apply R5 to all items.
- **G2 — Independent verification ran:** `verify_surrogate_solution` returned a valid disposition for that item. If it fails, apply R0.
- **G3 — Trust gate:** `operational_advisory` needs verifier disposition OPERATIONAL. That means the verifier found no violations **and** the surrogate reported feasible. Surrogate agreement can only lower a status, never raise it.
- **G4 — Warm-start gate:** `warm_start_only` needs `evaluate_warm_start` to have run for that item and to have returned speedup ≥ 1.0.
- **G5 — No false all-clear:** no R6 false-all-clear discrepancy for the item.
- **G6 — Human-in-the-loop:** any `operational_advisory` is advisory only. Actuation stays human-approved (`deployment_context.requested_use`). This gate does not change status but must be stated.
- **Non-blocking but must be reported:** `assess_ood` cap (expected to bind because 3700 is close to the Open ceiling; confirm from the tool, do not assume), flow-voltage consistency not run (no admittance data), and the fact that the 3-bus pocket has not been certified as representative of the 3700-bus model.

## Acceptance criteria

`result.json` is complete only if it contains all of the following.

1. `items`: exactly six entries, `PRED-A`…`PRED-F`, each with:
   - `label`;
   - `status`: exactly one of `operational_advisory | hold_for_review | warm_start_only | reject`;
   - `disposition`: verbatim from `verify_surrogate_solution`;
   - `independently_feasible`: verbatim from the verifier;
   - `violations`: an array of `{kind, element, value, limit}` copied from the verifier (empty array if none), plus `violations_by_kind` counts;
   - `power_balance_residual_pu`: from the verifier;
   - `flow_voltage_consistency`: `run` / `not_run`, as the verifier reports it;
   - `warm_start`: `{scenario, baseline_seconds, warm_seconds, speedup, flags}` from `evaluate_warm_start` if the item was WARM_START, otherwise `null` with `"not_run": "disposition not WARM_START"`;
   - `prediction_cap` (or `null`) and `confidence_cap_applied` (the lower of `ood_cap` and `prediction_cap`);
   - `decision_rule`: the rule ID (R0–R6) that decided the status;
   - `surrogate_self_report`: `{feasibility, confidence}`, labelled as not evidence;
   - `discrepancies`: an array, possibly empty.
2. `deployment`: `bus_count` 3700, the `select_model_tier` result (tier or refusal), the `assess_ood` result (OOD flag, `ood_cap`, evidence tier), and `tier_mismatch` if any.
3. `verification_checks`: the Step 1 output (checks and tolerances), plus any `tolerance_discrepancy`.
4. `tools_not_run`: `screen_n1_contingencies`, with the reason "no contingency cases in inputs".
5. `gates`: pass/fail for G1–G5 per item, and the G6 statement.
6. `tool_calls`: the list of every tool call with its input, so that every number in the file can be traced to one of them. There must be no number that does not come from a tool output or from `inputs/`.
7. `limitations`: no admittance data (consistency check not run); the pocket's representativeness of the full model is not certified; timings are single-sample synthetic data; no hooks or slash commands were available; there is no tool for the per-prediction cap if none was returned.

`RESULT.md` must present the same per-item table (status, disposition, violations by kind, residual, speedup where run). It must use verifier-finding language ("the independent verifier found …"). It must not call any prediction "safe", and it must not cite the surrogate's self-reported feasibility as evidence. Its confidence wording must stay at or below the applied cap.
