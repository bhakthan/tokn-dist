# N-1-1 and grid-forming screen for an interconnection cluster

*Domain mode `grideng` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Dispose five interconnection requests using the N-1-1 cascading-outage screen and the IEEE 2800 IBR stability gate.

Inputs (synthetic, in [`inputs/`](inputs/)): [`ibr_registry.json`](inputs/ibr_registry.json), [`n11_study.json`](inputs/n11_study.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `IR-3` | Cleanest N-1-1 screen in the batch (max 101% loading, all voltages >= 0.92 pu), but it adds 60 MW grid-following with no grid-forming capacity, pushing Z-SOUTH GFL penetration to 34.8% > 30% — the IBR gate blocks it. | `blocked` |
| `IR-4` | Boundary item: L-403 at exactly 115.0%, B-42 at exactly 0.85 pu, B-44 at exactly 1.10 pu, and post-expansion GFL penetration exactly 30.0% — none exceeds its strict limit, so it is a clean approve. | `approve` |
| `IR-2` | L-203 at 131.0% looks severe and exceeds the 100% N-1 criterion the baseline screen tool prints, but N-1-1 CRITICAL needs > 132.25% (115% x 1.15); it is HIGH only, so approve_with_conditions, not reject. | `approve_with_conditions` |
| `IR-5` | Every loading and voltage is inside limits; the only signal is stability_loss on the L-501|L-502 pair, which is CRITICAL. | `reject` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5.5 | 39.1s | `read_file`×5, `list_directory`×1, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5.5 | 149.3s | `read_file`×4, `list_directory`×1, `write_file`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 80.7s | **`powergrid_n1_1_screen`**×5, **`powergrid_ibr_stability_gate`**×5, `read_file`×5, `write_file`×2, `list_directory`×1, `run_command`×1 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 705.1s | **`powergrid_ibr_stability_gate`**×6, **`powergrid_n1_1_screen`**×5, `read_file`×6, `grep_search`×3, `write_file`×3, `edit_file`×3 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.9s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 134.1s | **`powergrid_n1_1_screen`**×5, **`powergrid_ibr_stability_gate`**×5, `read_file`×8, `list_directory`×1, `write_file`×1, `run_command`×1 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5.5 | 83.4s | `read_file`×7, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — Cluster 7 N-1-1 and GFM screen (items IR-1 to IR-5)

Scope: this file records what tools and rules apply. It does not assess any item.
Ground truth for tool names is the live tool list. Where the README disagrees, the
disagreement is recorded under Gaps.

## Domain tools that apply

| tool (exact name) | Items / input file it applies to | Input fields needed and whether present in `inputs/` |
|---|---|---|
| `powergrid_n1_1_screen` | IR-1, IR-2, IR-3, IR-4, IR-5. Source: `inputs/n11_study.json` | `first_contingencies`: present per request (3 elements each). `pair_results`: present per request, keyed `firstID\|secondID` (3 pairs each, which covers all 3 pairs of the 3 first contingencies). Use supplied summary only; `network` / `network_path` not needed because no pairs are missing. `stability_loss` flag present on IR-5 pair `L-501\|L-502` only. |
| `powergrid_ibr_stability_gate` | IR-1, IR-2, IR-3, IR-4, IR-5. Sources: `inputs/ibr_registry.json` (`resources`, `additions[IR-x]`, `threshold_pct`) | `resources`: present (10 existing units, GFM and GFL). `additions`: present per request, one unit each. `threshold_pct`: present (30). `zone_short_circuit_mva`: **absent** (SCR and grid-strength class will not be returned). Pass only the one request's additions per call. |
| `run_n1_contingency_screen` | Not applied to the brief | Needs `network` or `network_path` or `contingency_results`. Only N-1 pair data is supplied, not single-outage N-1 results for the model. Not used. |
| `approve_interconnection` | Not applied to the brief | Needs `thevenin_r_pu`, `thevenin_x_pu`, `base_mva`, `short_circuit_mva`, `capacity_mw`, `power_factor`, etc. None are in `inputs/`. It is a CRITICAL-risk approval tool. It must not be used to produce the disposition. |
| `generate_reliability_report` | Not applied to the brief | Requires `studies/power_flow/latest/n1_summary.json` showing N-1 compliance. Not present. The brief does not ask for a report. |
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
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
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# Cluster 7 interconnection screen — IR-1 through IR-5

**Study:** Cluster 7 interconnection queue — summer peak 2029, N-1-1 (NERC TPL-001-4 P6/P7)  
**Governing screen:** NERC TPL-001-4 P6/P7, using the supplied post-contingency pair summaries  
**IBR gate:** IEEE 2800 GFM/GFL penetration screen, `threshold_pct=30`  
**Scope:** Planning-screen dispositions only; not regulatory filings or final interconnection approvals.

> **Required warnings:** **N-1 not checked. N-0 power flow not run. SCR not assessed (no short-circuit data).** The network model was unavailable, so this study does not establish base-case convergence, per-unit consistency, power balance, NERC TPL P1–P5 N-1 compliance, SCR/WSCR, or grid-strength class. No MVA or bus kV base is supplied; per-unit consistency cannot be verified. Voltage values are quoted only as supplied screening limits, not independently solved physical voltages. Physical kV/A conversions are unavailable.

## IR-1 — `approve`

**Item disclosures:** N-1 not checked; N-0 power flow not run; SCR not assessed (no short-circuit data); NERC TPL-001-4 P6/P7 planning screen only; not a regulatory filing or final interconnection approval.

**Decision rule:** D4.5. **G1:** pass. **G2:** pass.

- **N-1-1 evidence:** `powergrid_n1_1_screen` returned `computed=true`, `screening_complete=true`, `source=supplied_summary`, `unscreened_pairs=[]`, `n_violations=0`, and `violations=null`. It returned `n_pairs=6`, listing both directions of the three supplied summary pairs, with `computed_pairs=0`.
- **Returned limits:** `thermal_limit_pct=115`, `voltage_min_pu=0.85`, `voltage_max_pu=1.1`; standard `NERC TPL-001-4 P6/P7`.
- **IBR evidence:** `powergrid_ibr_stability_gate` returned `blocked=false`, `violations=null`, and `expansion_issues=null`. For **Z-NORTH**, post-expansion `gfl_penetration_pct=12.5`, `gfl_headroom_mw=100`, `gfm_needed_mw=0`, and `over_threshold=false`.
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 9 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# Critique — Cluster 7 N-1-1 / grid-forming screen (IR-1 … IR-5)

Critic stage. Scope: `result.json` and `RESULT.md` against `BRIEF.md`, `inputs/n11_study.json`, `inputs/ibr_registry.json` and `PLAN.md`. All ten domain tool calls were re-run with the plan's exact inputs (5 × `powergrid_n1_1_screen`, 5 × `powergrid_ibr_stability_gate`) before any finding was recorded. This critique did not edit `result.json` or `RESULT.md`.

## What was verified and reproduced

Every reported number and severity is correct. In particular:

- **All five screens** returned `computed=true`, `screening_complete=true`, `source=supplied_summary`, `unscreened_pairs=[]`, `n_pairs=6`, `computed_pairs=0`, limits `thermal_limit_pct=115` / `voltage_min_pu=0.85` / `voltage_max_pu=1.1`, standard `NERC TPL-001-4 P6/P7` — exactly as quoted.
- **IR-1** gate: `blocked=false`, `Z-NORTH gfl_penetration_pct=12.5`, `gfl_headroom_mw=100`, `gfm_needed_mw=0`, `over_threshold=false`. Matches.
- **IR-2** screen: one violation, severity **HIGH**, "L-203 at 131.0% > 115% emergency rating after L-201 → L-202", kind=thermal, pair `L-201|L-202`. Matches verbatim. 131.0% < 132.25%, so HIGH (not CRITICAL) is the right classification, and `approve_with_conditions` is the right status.
- **IR-2** gate: `Z-EAST gfl_penetration_pct=17.778`, `gfl_headroom_mw=78.571`, `gfm_needed_mw=0`. Matches.
- **IR-3** gate: returned the error `[BLOCK] zone Z-SOUTH: expansion adds 60 MW GFL with no GFM — post-expansion GFL penetration 34.8% exceeds 30.0% threshold. Add GFM capacity (or synchronous condensers) before approving.` with `result=null` — reproduced character for character. Status `blocked` is correct; the brief's `blocked` definition fits IR-3 exactly.
- **IR-4** screen: `n_violations=0`, `violations=null` — the 115.0% / 0.85 pu / 1.10 pu boundary values returned no violation. Matches, and matches D3.
- **IR-4** gate: `Z-WEST gfl_penetration_pct=30`, `over_threshold=false`, `blocked=false`, `gfl_headroom_mw=0`. Matches; equality with the threshold does not block, per BRIEF Rule 4.
- **IR-5** screen: one violation, severity **CRITICAL**, "loss of synchronism / voltage collapse after outage sequence L-501 → L-502", kind=stability, pair `L-501|L-502`. Matches. Status `reject` is correct.
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.029 |
| Does any request whose expansion the IBR stability gate blocks still receive approve or approve_with_conditions? | 0.002 |
| Is any value sitting exactly at an N-1-1 limit (115.0% loading, 0.85 pu, 1.10 pu) or exactly at the 30.0% GFL threshold treated as a violation? | 0.004 |

Routing: **light-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 9 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | major | result.json has no top-level `study`, `standard`, `threshold_pct` or `warnings` fields, all four of which PLAN.md acceptance criterion 1 requires (`study` copied from inputs/n11_study.json; `standard` = "NERC TPL-001-4 P… | **fixed**: Added study, standard, threshold_pct and warnings after checking both input files and the reproduced tool standard/threshold. |
| C2 | major | Every item object in result.json carries only `id`, `status`, `rationale`, `evidence` and `tools_used`. Acceptance criterion 2 requires each item to also carry `zone`, a structured `n11` object ({tool, screening_complete… | **fixed**: Added zone, structured n11 and ibr_gate evidence, decision_rule_applied, conditions and discrepancy lists to every item without removing the original fields. Al… |
| C3 | major | IR-3's status is `blocked` but the item object has no `blocked_reason` field. Acceptance criterion 2 requires `blocked_reason` whenever the status is blocked. The value `ibr_gate_gfl_threshold` appears only inside the `r… | **fixed**: Added IR-3 blocked_reason=ibr_gate_gfl_threshold and the complete raw block message. The rerun returned result=null and Z-SOUTH 34.8% with 60 MW added GFL; unav… |
| C4 | major | IR-2's status is `approve_with_conditions` but the item object has no `conditions` field. Acceptance criterion 2 requires `conditions` to be a non-empty list for approve_with_conditions items. The corrective action exist… | **fixed**: The IR-2 rerun returned one HIGH L-203 thermal violation at 131.0%. Added a non-empty conditions array requiring an operating limit or validated RAS and a verif… |
| C5 | minor | The recorded decision rule for IR-3 (D4.2, blocked_reason=ibr_gate_gfl_threshold) is not what a literal in-order application of PLAN.md D4 yields. D4 says "apply in order and stop at the first match", and D4.1 fires when… | **fixed**: Retained D4.2 and the physical threshold cause, explicitly stating the limited waiver of G2 error-return validity for cause attribution. The gate remains failed… |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. The reflector reads the full trace, names which tools mattered, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

/teach powergrid: when powergrid_ibr_stability_gate returns result=null with an error containing "[BLOCK] zone <Z>", treat it as a valid gate BLOCK (status blocked, blocked_reason ibr_gate_gfl_threshold, copy the zone and penetration % verbatim from the message), not as a tool failure.
```

## The answer

| Item | First answer (Kimi-K3.1-Pro) | Final (after critique) | Expected |
|---|---|---|---|
| `IR-1` | `approve` | `approve` ✅ | `approve` |
| `IR-2` | `approve_with_conditions` | `approve_with_conditions` ✅ | `approve_with_conditions` |
| `IR-3` | `blocked` | `blocked` ✅ | `blocked` |
| `IR-4` | `approve` | `approve` ✅ | `approve` |
| `IR-5` | `reject` | `reject` ✅ | `reject` |

Accuracy: first answer 1.0, final 1.0.

## How it was graded

No model grades itself. [`verify.py`](../../verify.py) checks the files and the run log:

| Check | Result | Detail |
|---|---|---|
| artifacts_present | ✅ | all 10 present |
| result_json_valid | ✅ | final result.json parses with an items list |
| status_vocabulary | ✅ | all statuses in vocabulary |
| all_items_assessed | ✅ | 5 items |
| ground_truth | ✅ | final 1.0 (v1 1.0) |
| must_mention | ✅ | all present |
| forbidden_phrases | ✅ | none found |
| critique_has_findings | ✅ | 9 findings |
| every_finding_answered | ✅ | 9 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['powergrid_ibr_stability_gate', 'powergrid_n1_1_screen'] of expected ['powergrid_ibr_stability_gate', 'powergrid_n1_1_screen', 'run_n1_contingency_screen'] |
| critic_reran_tools | ✅ | critic used ['powergrid_ibr_stability_gate', 'powergrid_n1_1_screen'] |
| reflection_grounded | ✅ | names traced tools ['powergrid_ibr_stability_gate', 'powergrid_n1_1_screen']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Is it specific enough to change how the next run uses the domain tools?

## Run it yourself

```powershell
python run.py --domains powergrid --out C:\tmp\relay-powergrid
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
