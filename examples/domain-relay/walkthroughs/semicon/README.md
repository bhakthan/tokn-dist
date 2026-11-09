# Tapeout signoff review for six hard macros

*Domain mode `semicon` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

![Tapeout signoff review for six hard macros](infographic.webp)
*The run at a glance: why it matters, who did the work, what each item was checked for, and what it found. Click to open the full 4K image.*

## The problem

Assign a signoff status to six place-and-routed macros from utilization, constrained static timing, DRC and LVS before integration freeze.

Inputs (synthetic, in [`inputs/`](inputs/)): [`floorplans.json`](inputs/floorplans.json), [`physical_verification.json`](inputs/physical_verification.json), [`sta_runs.json`](inputs/sta_runs.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `BLK-PCIE` | Recorded WNS +0.150 ns with clean DRC and LVS looks ready, but sdc_path is empty, so the enforce_constraints_present hook blocks static_timing: the slack is unconstrained and meaningless. | `blocked` |
| `BLK-USB` | Best timing in the batch (WNS +0.210 ns) and lowest utilization, but 2 LVS discrepancies fail the zero-discrepancy policy. | `fail_signoff` |
| `BLK-DSP` | Sits exactly on two boundaries: WNS 0.000 ns is closed (WNS >= 0) and utilization 0.80 is not above the 80% target, so floorplan emits no warning. A careless run downgrades it. | `tapeout_ready` |
| `BLK-DMA` | WNS -0.003 ns is only 3 ps negative; rounding to 0.00 gives tapeout_ready, but timing is not closed. | `fail_signoff` |
| `BLK-SRAMCTL` | Utilization 0.82 triggers floorplan's within-margin warning (limit 84%), not a failure; calling it fail_signoff is too harsh. | `ready_with_caveats` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5.5 | 33.7s | `read_file`×6, `list_directory`×1, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5.5 | 78.2s | `read_file`×5, `list_directory`×1, `write_file`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 547.9s | **`floorplan`**×6, **`static_timing`**×6, **`drc_check`**×6, **`lvs_check`**×6, `edit_file`×13, `read_file`×9 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 367.4s | **`static_timing`**×6, **`lvs_check`**×6, **`floorplan`**×6, **`drc_check`**×6, `read_file`×8, `write_file`×4 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.8s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 350.7s | **`static_timing`**×7, **`lvs_check`**×7, **`floorplan`**×6, **`drc_check`**×6, `read_file`×9, `run_command`×3 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5.5 | 65.5s | `read_file`×6, `run_command`×2, `list_directory`×1, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — semicon scout pass (tapeout signoff review, six hard macros)

Evidence base: BRIEF.md; inputs/floorplans.json, inputs/sta_runs.json, inputs/physical_verification.json; tokn-self/introspect-slice.json; tokn-self/DOMAIN-README.md; the live semicon tool list (20 tools). Items: BLK-CPU, BLK-DSP, BLK-USB, BLK-SRAMCTL, BLK-DMA, BLK-PCIE.

## Domain tools that apply

| tool (exact name) | item(s) / input file it applies to | input fields needed and present in inputs/ |
|---|---|---|
| `floorplan` | all six blocks; inputs/floorplans.json | `utilization` (fraction) — present for all six. `netlist_def`, `lef_path`, `aspect_ratio` — present. Core dimensions and `cell_area_um2` are absent; not needed if the supplied `utilization` is used. Tool reports the worse of computed and supplied utilization. |
| `static_timing` | all six blocks; inputs/sta_runs.json | `wns` (supplied summary) — present for all six. `netlist`, `spef_path` — present. `sdc_path` — present for five blocks; **empty for BLK-PCIE** (passed through unchanged per brief rule 2). No `timing_arcs`, `endpoints`, or `clock_period_ns` are present, so only the supplied WNS can drive the result. `lib_path` is present in the record but is not a `static_timing` input field. |
| `drc_check` | all six blocks; inputs/physical_verification.json (`drc`) | `violations` (supplied count) — present for all six. `gds_path` — present. `drc_rules` — present as a rule-deck name string ("sky130A.drc"). No `shapes` or `rules` geometry are present, so the check runs on the supplied count only. |
| `lvs_check` | all six blocks; inputs/physical_verification.json (`lvs`) | `discrepancies` (supplied count) — present for all six. `gds_path`, `cdl_path` — present. No `layout_netlist` or `schematic_netlist` is present, so the check runs on the supplied count only. |

No other semicon tool has its inputs in `inputs/`. `power_analysis`, `route`, `place`, `clock_tree`, `dfm_fill`, `gds_export`, `metrics_extract` and the others need data that is not provided (logs, grids, cell lists, GDS, or routing congestion). They are not used for this brief.

## Gates and rules that will constrain the answer

Quoted from the brief (BRIEF.md, Status vocabulary and Rules):
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — semicon tapeout signoff review, six hard macros

Planner stage. Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/floorplans.json`, `inputs/sta_runs.json`, `inputs/physical_verification.json`. Do not execute anything except the tool calls listed below. Do not edit any file in `inputs/`.

## Objective
For each of BLK-CPU, BLK-DSP, BLK-USB, BLK-SRAMCTL, BLK-DMA and BLK-PCIE, run `floorplan`, `static_timing`, `drc_check` and `lvs_check` on the records exactly as given in `inputs/`. Then assign one status per block (`tapeout_ready` | `ready_with_caveats` | `fail_signoff` | `blocked`) using the mechanical rules below, and write `result.json` and `RESULT.md`.

## Steps

General instructions for every step:
- Call the tool **once per block**. Never batch two blocks into one call.
- Copy values exactly as they appear in the input files. Do not round, convert units, or change paths. Pass the empty string `""` where the input has one.
- Run all four checks for **every** block, even when an earlier check already decides the status. The full evidence must be recorded.
- Some tools say they "advance the design" to a stage, and `static_timing` says it records the worst WNS "for the timing gate". That state may be shared across calls. **Read each block's result only from that call's own output.** Never read it from accumulated or session-level gate state.
- Save the raw output of every call (24 calls in total) for `result.json` → `tool_calls`.
- If a call errors, analyse the error, fix only the call formatting (never the values), and retry **once**. If it still fails, record the error and apply decision rule D0.
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# Semicon tapeout signoff review

## Evidence and decision basis

All six blocks were independently re-checked with `floorplan`, `static_timing`, `drc_check`, and `lvs_check`, using the supplied values unchanged. `result.json` records all 24 primary responses and one unchanged retry for each policy error. No constraints file was substituted. Five successful timing calls returned `source=supplied_summary` and `computed=false`; DRC and successful LVS calls likewise used supplied summaries. Floorplan returned `utilization_source=supplied_summary` and omitted the `computed` field.

The brief precedence is `blocked`, then `fail_signoff`, then `ready_with_caveats`, then `tapeout_ready`. The hard utilization limit is 0.84; the separate 0.80 target determines the utilization caveat. WNS exactly 0 ns is closed; any negative WNS fails. DRC and LVS have zero tolerance.

## Per-block assessment

| Block | Status | Rule | Utilization | WNS (ns) | DRC violations | LVS discrepancies | Reason |
|---|---|---|---:|---|---:|---|---|
| BLK-CPU | `tapeout_ready` | D4 | 0.72 | 0.085 | 0 | 0 | Within target, non-negative constrained-record WNS, zero DRC/LVS counts; no call rejected. |
| BLK-DSP | `tapeout_ready` | D4 | 0.8 | 0 | 0 | 0 | Utilization equals target, not above it; WNS exactly zero is closed. |
| BLK-USB | `fail_signoff` | D2 | 0.65 | 0.21 | 0 | 2, explicitly in policy error | Zero-tolerance LVS failure, unchanged on retry; passing other checks cannot override it. |
| BLK-SRAMCTL | `ready_with_caveats` | D3 | 0.82 | 0.04 | 0 | 0 | Above 0.80 target but within 0.84 hard limit; routing-congestion risk. Congestion was not measured because route gcell_edges inputs were absent. |
| BLK-DMA | `fail_signoff` | D2 | 0.7 | -0.003 | 0 | 0 | Negative WNS fails timing regardless of other passing summaries. |
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 12 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# Critique — semicon tapeout signoff review

**Method.** I read `BRIEF.md`, `PLAN.md`, `CAPABILITIES.md`, everything in `inputs/`, `result.json` and `RESULT.md`, then re-ran all 24 domain tool calls myself (`floorplan`, `static_timing`, `drc_check` and `lvs_check` for each of the six blocks, passing the input values exactly as the plan specifies, including `sdc_path: ""` for BLK-PCIE). Every quoted tool output below is from my own re-run.

**What checks out.** The classification layer is correct. All six statuses and deciding rules match both the plan's input-derived expectation table and my independent tool runs: BLK-PCIE's `static_timing` call does *refuse* the empty SDC with exactly the quoted blocking text (not merely a warning); BLK-USB's `lvs_check` returns the 2-discrepancy policy block with `post_tool_blocked=true`; BLK-DMA's WNS is −0.003 ns with the `[HIGH] ... timing NOT closed` warning; BLK-SRAMCTL's `floorplan` warns at 0.82 while BLK-DSP's 0.80 returns no warning; all DRC counts are 0. No status contradicts a tool output, no gate was skipped, and no number is invented.

**What does not.** The defects are structural and evidentiary, not classificatory.

---

## Findings

### C1 — blocking — overall
**`tool_calls` is missing entirely.** The plan's step instructions require "Save the raw output of every call (24 calls in total) for `result.json` → `tool_calls`", and acceptance criterion 4 requires "A `tool_calls` array records all 24 calls … with their raw outputs or error text." result.json has no such array — its only top-level arrays are `items`, `gates`, `limitations` and an empty `critique_response`. The reported values therefore cannot be audited from the artifact itself, and the retry protocol for the two erroring calls is unverifiable.
**Fix:** add a 24-entry `tool_calls` array with the exact inputs and raw outputs/errors. The two error outputs, confirmed by re-run, are `[SEMICON] BLOCKING: SDC timing constraints file required — synthesis and STA without constraints produces meaningless results` (BLK-PCIE static_timing) and `[SEMICON] BLOCKING: 2 LVS discrepancies — zero-discrepancy LVS policy requires all discrepancies resolved before tapeout` (BLK-USB lvs_check, `post_tool_blocked=true`).

### C2 — blocking — overall
**The per-item entries do not implement the plan's schema.** Acceptance criterion 2 requires `block`, `deciding_rule`, `reasons`, `caveats`, `secondary_findings`, `checks` (with `tool`, `inputs`, `result_value`, `source`, `warnings`, `refused`, `pass` per tool) and `lib_path`. The entries carry only `id`, `status`, `rationale`, `evidence`, `tools_used`. `deciding_rule` appears nowhere in result.json (only in RESULT.md's table). Because `checks.inputs` is absent, the exact values passed are unrecorded: `netlist_def`, `lef_path`, `aspect_ratio`, `spef_path`, `drc_rules`, `cdl_path` and `lib_path` from `inputs/` appear nowhere in the deliverable, and brief-rule-2 compliance (`sdc_path: ""` passed as-is for BLK-PCIE) cannot be demonstrated from the artifact.
**Fix:** restructure each item to the plan's schema — `block` (not `id`), `deciding_rule` (D4, D4, D2, D3, D2, D1 for CPU, DSP, USB, SRAMCTL, DMA, PCIE), `reasons` arrays listing every failing/blocking condition, `secondary_findings` (empty except BLK-PCIE: U=0.74, V=0, L=0), a `checks` object with the four tools' exact inputs/result_value/source/warnings/refused/pass, and `lib_path` (`pdk/sky130hd/sky130_fd_sc_hd__ss_100C_1v60.lib`) as context.
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.407 |
| Does any block with a DRC violation, an LVS discrepancy or a negative WNS receive tapeout_ready or ready_with_caveats? | 0.011 |
| Does the result treat BLK-PCIE's recorded WNS as evidence of timing closure even though its STA run had no SDC constraints? | 0.006 |

Routing: **full-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 12 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | blocking | result.json contains no `tool_calls` array. PLAN.md's general step instructions require 'Save the raw output of every call (24 calls in total) for result.json -> tool_calls', and acceptance criterion 4 requires 'A tool_c… | **fixed**: Added all 24 independently re-run primary tool_calls with exact inputs and full structured raw responses; both unchanged retries are nested in their primary rec… |
| C2 | blocking | The per-item entries do not implement the schema the plan defines. Acceptance criterion 2 requires each entry to have `block`, `deciding_rule`, `reasons`, `caveats`, `secondary_findings`, `checks` (with per-tool `tool`, … | **fixed**: Retained legacy item fields and added block, deciding_rule, reasons, caveats, secondary_findings, checks and lib_path. Checks record exact inputs, value, source… |
| C3 | major | The `caveats` array is missing. Acceptance criterion 2 makes `caveats` 'required and non-empty for ready_with_caveats', and it must mention routing congestion as unmeasured. BLK-SRAMCTL is the only ready_with_caveats blo… | **fixed**: Re-run floorplan returned SRAMCTL utilization 0.82 and its congestion warning. Added required caveats array naming unmeasured routing congestion; timing/DRC/LVS… |
| C4 | major | The `summary` object is missing. Acceptance criterion 7 requires 'A summary object counts blocks per status, and the counts add up to 6'. result.json has only a prose `overall_verdict` string; no per-status counts are gi… | **fixed**: Added summary counts from all six classifications: tapeout_ready 2, ready_with_caveats 1, fail_signoff 2, blocked 1, total 6. |
| C5 | major | The `discrepancies_noted` array is missing. Acceptance criterion 5 requires it (it may be empty) and specifically requires recording 'whether static_timing actually refused BLK-PCIE or only warned', because CAPABILITIES … | **fixed**: Added discrepancies_noted documenting actual PCIE refusal on both attempts, not a warning; no returned-number disagreement, input-only untrusted PCIE slack and … |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. The reflector reads the full trace, names which tools mattered, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

semicon: when a domain tool returns a `[SEMICON] BLOCKING:` error, record it as a successful gate verdict (not a tool failure), retry once unchanged, store the raw response in `result.json` → `tool_calls`, and fill every plan-schema field before writing the final answer.
```

## The answer

| Item | First answer (Kimi-K3.1-Pro) | Final (after critique) | Expected |
|---|---|---|---|
| `BLK-CPU` | `tapeout_ready` | `tapeout_ready` ✅ | `tapeout_ready` |
| `BLK-DMA` | `fail_signoff` | `fail_signoff` ✅ | `fail_signoff` |
| `BLK-DSP` | `tapeout_ready` | `tapeout_ready` ✅ | `tapeout_ready` |
| `BLK-PCIE` | `blocked` | `blocked` ✅ | `blocked` |
| `BLK-SRAMCTL` | `ready_with_caveats` | `ready_with_caveats` ✅ | `ready_with_caveats` |
| `BLK-USB` | `fail_signoff` | `fail_signoff` ✅ | `fail_signoff` |

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
| critique_has_findings | ✅ | 12 findings |
| every_finding_answered | ✅ | 12 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['drc_check', 'floorplan', 'lvs_check', 'static_timing'] of expected ['drc_check', 'floorplan', 'lvs_check', 'static_timing'] |
| critic_reran_tools | ✅ | critic used ['drc_check', 'floorplan', 'lvs_check', 'static_timing'] |
| reflection_grounded | ✅ | names traced tools ['drc_check', 'floorplan', 'lvs_check', 'static_timing']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Is it specific enough to change how the next run uses the domain tools?

## Run it yourself

```powershell
python run.py --domains semicon --out C:\tmp\relay-semicon
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
