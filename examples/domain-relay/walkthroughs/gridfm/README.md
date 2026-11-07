# Trust disposition for grid foundation-model OPF predictions

*Domain mode `gridfm` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Independently verify six GridSFM surrogate AC-OPF predictions and assign each a fail-closed trust disposition before it reaches the operator desk.

Inputs (synthetic, in [`inputs/`](inputs/)): [`deployment_context.json`](inputs/deployment_context.json), [`predictions.json`](inputs/predictions.json), [`warm_start_timings.json`](inputs/warm_start_timings.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `PRED-C` | Highest self-reported confidence (0.97, 'feasible') and every voltage, limit and flow is inside bounds, but generation 1.88 pu vs load 2.00 + losses 0.03 leaves a -0.15 pu power-balance residual — REJECTED. | `reject` |
| `PRED-D` | Boundary item: G2 exactly at Pmax 1.00, B1 exactly at Vmax 1.05, L23 exactly at its 0.40 pu rating and L13 at 0.40 — all limits are strict, so it is OPERATIONAL. | `operational_advisory` |
| `PRED-E` | Disposition is WARM_START (B3 voltage 0.93 < 0.95, L13 1.06 > 1.00), which looks salvageable, but the seeded solve took 4.6 s vs 4.2 s cold (speedup 0.91 < 1.0) — reject. | `reject` |
| `PRED-B` | Physics is identical to PRED-A and passes, but the surrogate self-reports 'infeasible' — REVIEW, not operational. | `hold_for_review` |
| `PRED-F` | Only violation is G2 reactive output 0.62 > Qmax 0.50; speedup 1.75 >= 1.0 — warm_start_only, not operational. | `warm_start_only` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5-5 | 38.6s | **`list_verification_checks`**×1, `read_file`×6, `list_directory`×1, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5-5 | 83.5s | `read_file`×6, `edit_file`×2, `list_directory`×1, `write_file`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 548.6s | **`verify_surrogate_solution`**×6, **`evaluate_warm_start`**×2, **`list_verification_checks`**×1, **`select_model_tier`**×1, **`assess_ood`**×1, `read_file`×9 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 897.7s | **`verify_surrogate_solution`**×6, **`evaluate_warm_start`**×2, **`list_verification_checks`**×1, **`select_model_tier`**×1, **`assess_ood`**×1, `read_file`×16 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.4s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 328.0s | **`verify_surrogate_solution`**×6, **`evaluate_warm_start`**×2, **`list_verification_checks`**×1, **`select_model_tier`**×1, **`assess_ood`**×1, `read_file`×9 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5-5 | 176.5s | `read_file`×9, `list_directory`×2, `run_command`×2, `write_file`×1, `edit_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

Stages that ended without their deliverable were retried once; the retry is recorded in [`TRACE.json`](run/TRACE.json), never hidden.

> **Disclosure:** the execute stage exited with code 1 (a TOKN guard stopped the agent, such as the token-budget breaker). Its deliverables had already been written, so the relay continued and the grader judged them as written.

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — gridfm scout pass

Scope: BRIEF.md, inputs/ (3 files), tokn-self/introspect-slice.json, tokn-self/DOMAIN-README.md, and the live tool list. Items PRED-A..PRED-F are not assessed here.

Evidence sources:
- Live tool list: `verify_surrogate_solution`, `select_model_tier`, `assess_ood`, `evaluate_warm_start`, `list_verification_checks`, `screen_n1_contingencies`.
- `list_verification_checks` output (tool call): checks = voltage_bound, generator_active_limit, generator_reactive_limit, thermal_limit, power_balance, flow_voltage_consistency; tolerances powerBalancePU 0.01, thermalSlack 0, consistencyPU 0.05; tiers GridSFM-Open (≤4000 buses), GridSFM-Premier (≤80000 buses).

## Domain tools that apply

| tool (exact name) | item(s) / input file it applies to | input fields needed and present in inputs/ |
|---|---|---|
| `verify_surrogate_solution` | PRED-A, PRED-B, PRED-C, PRED-D, PRED-E, PRED-F (headline check for every item) | `prediction` = `inputs/predictions.json` `cases[i].prediction`: `scenario` (baseMVA, buses[vMagPU, vAngRad, vMinPU, vMaxPU], generators[pgPU, qgPU, pMin/pMax, qMin/qMax], loads, branches[sFlowPU, ratingPU], lossesPU), `surrogateFeasibility`, `surrogateConfidence`, `tier`. All present. |
| `list_verification_checks` | all items (confirms tolerances used in the gates section) | none. Already called. |
| `evaluate_warm_start` | only items whose verifier disposition is WARM_START (not known until verification runs) | `scenario`, `baseline_seconds`, `warm_seconds` from `inputs/warm_start_timings.json` `timings[i]` (labels A–F). All present. |
| `select_model_tier` | deployment, using full-network size | `bus_count` = 3700 from `inputs/deployment_context.json` `full_network_bus_count`. Present. |
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
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
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# GridFM final trust-disposition report

## Deployment evidence and confidence

Independent reruns selected GridSFM-Open for the full 3700-bus deployment (maxBuses=4000; scaleHeadroom=0.925). assess_ood was called without independently_verified and returned outOfDist=true, confidenceCap=0.3. Every applied confidence cap is 0.3; the cap does not change status. These are reduced-pocket dispositions, not full-network assurance.

list_verification_checks returned voltage_bound, generator_active_limit, generator_reactive_limit, thermal_limit, power_balance and flow_voltage_consistency. Tolerances: powerBalancePU=0.01, thermalSlack=0, consistencyPU=0.05. The stated balance/thermal tolerances match the brief.

## Independent-verifier results

| Item | Status | Disposition | Violations by kind | Residual (pu) | Speedup |
|---|---|---|---|---|---|
| PRED-A | operational_advisory | OPERATIONAL | none listed | 2.498001805406602e-16 | not run |
| PRED-B | hold_for_review | REVIEW | none listed | 2.498001805406602e-16 | not run |
| PRED-C | reject | REJECTED | power_balance: 1 | -0.1500000000000001 | not run |
| PRED-D | operational_advisory | OPERATIONAL | none listed | 2.498001805406602e-16 | not run |
| PRED-E | reject | WARM_START | thermal_limit: 1, voltage_bound: 1 | -1.942890293094024e-16 | 0.9130434782608696 |
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 9 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# CRITIQUE — gridfm trust disposition (PRED-A … PRED-F)

**Critic role.** I re-ran every tool whose output decides a status (`list_verification_checks`, `select_model_tier`, `assess_ood`, all six `verify_surrogate_solution` calls, and both `evaluate_warm_start` calls) and checked every reported number and status against those outputs and against `inputs/`. What follows is every issue found; severity is a label, not a filter.

**What I verified as correct first (grounding for the findings below):** all six statuses, dispositions, residuals, violation records, speedups and confidence caps in `result.json` / `RESULT.md` reproduce my tool re-runs **exactly, verbatim** — PRED-A `OPERATIONAL` / `independentlyFeasible=true` / residual `2.498001805406602e-16`; PRED-B `REVIEW`; PRED-C `REJECTED`, `power_balance` at `system`, margin `0.1400000000000001`; PRED-D `OPERATIONAL` with the three exact-at-limit values correctly not flagged; PRED-E `WARM_START` with `thermal_limit` (L13) and `voltage_bound` (B3), warm-start speedup `0.9130434782608696`; PRED-F `WARM_START` with `generator_reactive_limit` (G2), speedup `1.75`; `select_model_tier`/`assess_ood` at bus count 3700; tolerances 0.01 / 0 / 0.05. **No number, status, disposition or speedup is fabricated, and no status contradicts a tool output or the plan's decision rules.** The problems below are completeness and framing, not calculation.

---

## Findings

### C1 — `overall` — major
**result.json omits four top-level sections the plan's acceptance criteria require:** `deployment` (criterion 2), `verification_checks` (criterion 3), `tools_not_run` with the `screen_n1_contingencies` reason (criterion 4), and `tool_calls` with every call's input (criterion 6). The facts are right — my re-runs reproduce `select_model_tier` → GridSFM-Open / maxBuses 4000 / scaleHeadroom 0.925 / no refusal, `assess_ood` → `outOfDist=true` / cap 0.3, `list_verification_checks` → powerBalancePU 0.01, thermalSlack 0, consistencyPU 0.05 — but they appear only inside per-item `evidence` prose and the `gates` array. Because `tool_calls` is absent, result.json records **no tool inputs at all** and cannot show that `assess_ood` was called without `independently_verified` (PLAN Step 3) or that each prediction was passed to the verifier exactly as given (BRIEF rule 1).
**Fix:** add the four sections verbatim from tool outputs (bus_count 3700; tier GridSFM-Open with maxBuses 4000 and scaleHeadroom 0.925; OOD flag true, ood_cap 0.3, evidence tier GridSFM-Open; no tier mismatch; the six checks and three tolerances; `screen_n1_contingencies` not run, reason "no contingency cases in inputs"), plus a `tool_calls` list of all 11 calls with their exact inputs.

### C2 — `overall` — major
**The six item entries carry none of the structured fields acceptance criterion 1 enumerates** — `label`, `disposition`, `independently_feasible`, `violations` as `{kind, element, value, limit}` plus `violations_by_kind` counts, `power_balance_residual_pu`, `warm_start`, `prediction_cap`, `confidence_cap_applied`, `decision_rule`, `discrepancies`. Every value is present and accurate, but only as prose inside `rationale`/`evidence`, and the plan's "empty array if none" is not followed (the verifier's `violations=null` is repeated as-is for PRED-A/B/D, which limitation 4 does disclose).
**Fix:** restructure each item as data: `violations: []` and `violations_by_kind: {}` for PRED-A/B/D; PRED-C `[{power_balance, system, detail, margin 0.1400000000000001}]`; PRED-E the `thermal_limit`/`voltage_bound` pair; PRED-F `generator_reactive_limit`; per-item `power_balance_residual_pu`; `warm_start` objects for PRED-E (speedup 0.9130434782608696) and PRED-F (speedup 1.75), `null` + not_run reason for the rest; `prediction_cap` 0.9/0.9/0.5/0.9/0.5/0.5; `confidence_cap_applied` 0.3; `decision_rule` R4/R3/R1/R4/R2/R2; `discrepancies: []`. Note per item that the verifier supplies `detail`/`margin`, not separate `value`/`limit` fields.

### C3 — `overall` — major
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.060 |
| Does any prediction receive operational_advisory or warm_start_only because of the surrogate's own feasibility flag or confidence rather than the independent verifier's result? | 0.026 |
| Does the result describe any prediction with confidence above the 0.30 out-of-distribution cap implied by the 3,700-bus full network on the GridSFM-Open tier? | 0.798 |

Routing: **light-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 9 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | major | result.json omits four top-level sections that PLAN.md's acceptance criteria require: 'deployment' (criterion 2: bus_count 3700, the select_model_tier result, the assess_ood result, tier_mismatch), 'verification_checks' … | **fixed**: Independently reran deployment and tolerance tools: GridSFM-Open, scaleHeadroom=0.925, OOD cap=0.3, powerBalancePU=0.01, thermalSlack=0, consistencyPU=0.05 repr… |
| C2 | major | None of the six item entries carries the structured fields PLAN acceptance criterion 1 enumerates: 'label' (the file uses 'id'), 'disposition', 'independently_feasible', 'violations' as an array of {kind, element, value,… | **fixed**: All exact-object verifier reruns reproduce dispositions, residuals, caps and violation detail/margin. Added structured item fields and counts; normalized null t… |
| C3 | major | PLAN acceptance criterion 1 requires a per-item 'surrogate_self_report' {feasibility, confidence} labelled as not evidence. It is missing from all six items, and the surrogateConfidence values in inputs/predictions.json … | **fixed**: Read all input self-reports and recorded feasibility/confidence with evidence=false. Exact-object rerun rejects PRED-C despite feasible/0.97 self-report. |
| C4 | major | PLAN acceptance criterion 1 and Steps 4-9 require a per-item 'flow_voltage_consistency' field set to run/not_run 'as the verifier reports it', with the instruction to 'record what the tool actually says'. My re-run confi… | **fixed**: All reruns omit consistency execution metadata. Added not_reported_by_verifier per item. Did not adopt unsupported suggested assertion that consistencyPU=0.05 w… |
| C5 | minor | The PRED-B verifier output pairs disposition='REVIEW' with phase='WARM_START' - an internal inconsistency in the tool result that neither result.json nor RESULT.md records or explains. The reported status (hold_for_revie… | **fixed**: Independent B rerun confirms disposition=REVIEW, phase=WARM_START. Recorded every phase and B mismatch; R3/Step 10 use disposition, preserving hold_for_review a… |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. Opus reads the full trace, which tools mattered, where the run stalled, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

In gridfm, the Executor must write result.json directly in PLAN.md's acceptance-criteria schema (structured per-item fields incl. disposition, phase, surrogate_self_report with evidence:false, violations as [] not null, plus deployment, verification_checks, tools_not_run and a tool_calls input ledger) and must copy every number from a stored tool output, never from a hard-coded script literal.
```

## The answer

| Item | First answer (Kimi) | Final (after critique) | Expected |
|---|---|---|---|
| `PRED-A` | `operational_advisory` | `operational_advisory` ✅ | `operational_advisory` |
| `PRED-B` | `hold_for_review` | `hold_for_review` ✅ | `hold_for_review` |
| `PRED-C` | `reject` | `reject` ✅ | `reject` |
| `PRED-D` | `operational_advisory` | `operational_advisory` ✅ | `operational_advisory` |
| `PRED-E` | `reject` | `reject` ✅ | `reject` |
| `PRED-F` | `warm_start_only` | `warm_start_only` ✅ | `warm_start_only` |

Accuracy: first answer 1.0, final 1.0.

## How it was graded

No model grades itself. [`verify.py`](../../verify.py) checks the files and the run log:

| Check | Result | Detail |
|---|---|---|
| artifacts_present | ✅ | all 10 present |
| result_json_valid | ✅ | final result.json parses with an items list |
| status_vocabulary | ✅ | all statuses in vocabulary |
| all_items_assessed | ✅ | 6 items |
| ground_truth | ✅ | final 1.0 (v1 1.0) |
| must_mention | ✅ | all present |
| forbidden_phrases | ✅ | none found |
| critique_has_findings | ✅ | 9 findings |
| every_finding_answered | ✅ | 9 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['assess_ood', 'evaluate_warm_start', 'list_verification_checks', 'select_model_tier', 'verify_surrogate_solution'] of expected ['assess_ood', 'evaluate_warm_start', 'list_verification_checks', 'select_model_tier', 'verify_surrogate_solution'] |
| critic_reran_tools | ✅ | critic used ['assess_ood', 'evaluate_warm_start', 'list_verification_checks', 'select_model_tier', 'verify_surrogate_solution'] |
| reflection_grounded | ✅ | names traced tools ['assess_ood', 'evaluate_warm_start', 'list_verification_checks', 'select_model_tier', 'verify_surrogate_solution']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Would it have prevented the stall recorded in [`TRACE.json`](run/TRACE.json)?

## Run it yourself

```powershell
python run.py --domains gridfm --out C:\tmp\relay-gridfm
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
