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
| 0 | Discover | claude-haiku-5.5 | 34.0s | `read_file`×6, `list_directory`×1, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5.5 | 90.5s | `read_file`×6, `list_directory`×1, `write_file`×1, `git_status`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 900.2s | **`static_timing`**×21, **`floorplan`**×6, **`drc_check`**×6, **`lvs_check`**×6, `read_file`×7, `write_file`×3 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 715.3s | **`lvs_check`**×11, **`static_timing`**×7, **`floorplan`**×6, **`drc_check`**×6, `read_file`×10, `write_file`×2 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.3s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 315.7s | **`floorplan`**×6, **`static_timing`**×6, **`drc_check`**×6, **`lvs_check`**×6, `read_file`×10, `run_command`×4 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5.5 | 78.5s | `read_file`×7, `list_directory`×1, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — semicon tapeout signoff review (six hard macros)

Scope: reading only. Items under review: BLK-CPU, BLK-DSP, BLK-USB, BLK-SRAMCTL, BLK-DMA, BLK-PCIE. No item is assessed here.

Evidence base: BRIEF.md; inputs/floorplans.json, inputs/sta_runs.json, inputs/physical_verification.json; tokn-self/introspect-slice.json; tokn-self/DOMAIN-README.md; my live tool list.

## Domain tools that apply

| tool (exact name) | item(s) / input file it applies to | input fields it needs, and whether present in inputs/ |
|---|---|---|
| `floorplan` | Utilization check, all six blocks. Source: inputs/floorplans.json | `netlist_def` (present, path form; tool schema says string, DEF content expected, see Gaps); `lef_path` (present: pdk/sky130hd/sky130_fd_sc_hd.lef); `utilization` (present, fraction); `aspect_ratio` (present). Core dimensions or cell area are NOT present, so the tool relies on the supplied `utilization` summary. |
| `static_timing` | WNS, all six blocks. Source: inputs/sta_runs.json | `netlist` (present); `sdc_path` (present for five blocks; EMPTY for BLK-PCIE, to be passed as given); `spef_path` (present); `wns` (present, supplied ns value). `lib_path` is present in the inputs but has no argument in this tool's schema (see Gaps). |
| `drc_check` | DRC, all six blocks. Source: inputs/physical_verification.json, `drc` array | `gds_path` (present); `drc_rules` (present: sky130A.drc); `violations` (present, supplied count). No `shapes` or `rules` are given, so only the supplied count is evidence. |
| `lvs_check` | LVS, all six blocks. Source: inputs/physical_verification.json, `lvs` array | `gds_path` (present); `cdl_path` (present); `discrepancies` (present, supplied count). No `layout_netlist` is given, so only the supplied count is evidence. |

Tools not used, and why: `route` (needs `cts_def` and `gcell_edges`, absent); `dfm_fill`, `clock_tree`, `place`, `logic_synthesize`, `formal_verify`, `rtl_lint`, `gds_export` (no matching inputs); `preflight_gate` (no destructive EDA action proposed).

## Gates and rules that will constrain the answer
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — semicon tapeout signoff review (six hard macros)

Planner stage output. Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/floorplans.json`, `inputs/sta_runs.json`, `inputs/physical_verification.json`, `tokn-self/DOMAIN-README.md`. Nothing has been executed. No status below is pre-decided. Every status must come from the tool outputs, using the Decision rules.

## Objective

Give each of BLK-CPU, BLK-DSP, BLK-USB, BLK-SRAMCTL, BLK-DMA and BLK-PCIE exactly one status (`tapeout_ready`, `ready_with_caveats`, `fail_signoff` or `blocked`). Base each status on four tool-backed checks per block: `floorplan`, `static_timing`, `drc_check` and `lvs_check`. Record the results in `result.json` and `RESULT.md`.

## Steps

General instructions for the Executor:
- Make all 24 tool calls: 4 tools × 6 blocks. Run every check for every block, including a block that is already known to be `blocked` or failing. The report must show every check.
- Pass each value **exactly as written in `inputs/`**. Do not change paths, round numbers, fill in an empty string, or add arguments that are not listed here (Brief rule 2).
- Copy the **raw tool output** for each call into `evidence/` (for example `evidence/<block>_<tool>.json`) or straight into `result.json`. If a tool returns an error, record the error text verbatim. Do not retry with altered inputs.
- `lib_path` from `sta_runs.json` has **no argument** in `static_timing`, so do not pass it. Record it in `result.json` as `"lib_path_not_consumed": true` (CAPABILITIES gap 3).
- Calls for different blocks do not depend on each other and may run in parallel.

### Step 1 — Utilization (`floorplan`), all six blocks
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# Semicon tapeout signoff review

## Evidence and method

All required checks were independently rerun for every block: `floorplan`, `static_timing`, `drc_check`, and `lvs_check`. This revision issued **24 domain calls**, each once, including the two blocking responses. Exact supplied arguments and complete raw response envelopes are recorded in `result.json`. No SDC was invented or substituted.

Status precedence follows **BRIEF.md**: blocked → fail_signoff → ready_with_caveats → tapeout_ready. These are record-level classifications, not full lifecycle authorization or guarantees of working silicon. Successful timing, DRC and LVS outputs report `source=supplied_summary` and `computed=false`; floorplan reports `utilization_source=supplied_summary`.

## Verified results

| Block | Status | Utilization | WNS (ns) | DRC violations | LVS discrepancies | Rule |
|---|---|---:|---:|---:|---:|---|
| BLK-CPU | `tapeout_ready` | 0.72 | 0.085 | 0 | 0 | R4 |
| BLK-DSP | `tapeout_ready` | 0.80 | 0.000 | 0 | 0 | R4 |
| BLK-USB | `fail_signoff` | 0.65 | 0.210 | 0 | 2 (error message) | R2 |
| BLK-SRAMCTL | `ready_with_caveats` | 0.82 | 0.040 | 0 | 0 | R3 |
| BLK-DMA | `fail_signoff` | 0.70 | -0.003 | 0 | 0 | R2 |
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 14 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# Critique — semicon tapeout signoff review

**Critic role:** independent re-verification. I re-ran every domain tool whose output decides a status — all 6 `floorplan`, all 6 `static_timing`, all 6 `drc_check` and all 6 `lvs_check` calls (24 calls), plus 6 follow-up `lvs_check` probes to establish how that tool behaves. Every number reported in `result.json` and `RESULT.md` reproduces exactly. The six statuses are all correct. The defects are structural and presentational, not substantive.

## What reproduces

For the record, my re-run values, all of which match the executor's:

| block | `floorplan` U | `static_timing` W | `drc_check` D | `lvs_check` L | status |
|---|---|---|---|---|---|
| BLK-CPU | 0.72, `supplied_summary`, no warning | 0.085 ns, `supplied_summary` | 0, `supplied_summary`, `computed=false` | 0, `supplied_summary`, `computed=false` | `tapeout_ready` (R4) ✓ |
| BLK-DSP | 0.8, `supplied_summary`, no warning | 0 ns, `supplied_summary` | 0 | 0 | `tapeout_ready` (R4) ✓ |
| BLK-USB | 0.65, `supplied_summary` | 0.21 ns, `supplied_summary` | 0 | **error: "[SEMICON] BLOCKING: 2 LVS discrepancies — zero-discrepancy LVS policy requires all discrepancies resolved before tapeout"**, `post_tool_blocked=true` | `fail_signoff` (R2) ✓ |
| BLK-SRAMCTL | 0.82, `supplied_summary`, warning "Area utilization 82.0% exceeds target 80.0% (within 5.0% margin) — routing congestion likely" | 0.04 ns, `supplied_summary` | 0 | 0 | `ready_with_caveats` (R3) ✓ |
| BLK-DMA | 0.70, `supplied_summary` | **-0.003 ns**, `supplied_summary`, warning "[HIGH] WNS = -0.003 ns — timing NOT closed (requires WNS ≥ 0.0 ns)" | 0 | 0 | `fail_signoff` (R2) ✓ |
| BLK-PCIE | 0.74, `supplied_summary` | **error: "[SEMICON] BLOCKING: SDC timing constraints file required — synthesis and STA without constraints produces meaningless results"** | 0 | 0 | `blocked` (R1) ✓ |
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.500 |
| Does any block with a DRC violation, an LVS discrepancy or a negative WNS receive tapeout_ready or ready_with_caveats? | 0.008 |
| Does the result treat BLK-PCIE's recorded WNS as evidence of timing closure even though its STA run had no SDC constraints? | 0.001 |

Routing: **full-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 14 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | blocking | result.json contains no per-check `checks` object. PLAN acceptance criterion 2 requires each entry to carry `checks` with keys `floorplan`, `static_timing`, `drc_check` and `lvs_check`, each holding `inputs_passed`, `too… | **fixed**: Confirmed absent checks in original file. Added every required check with exact arguments, independently rerun values, sources, warnings, discrepancy notes and … |
| C2 | major | `rule_applied` is absent from all six entries. PLAN acceptance criterion 2 lists it as a required field (one of R0, R1, R2, R3, R4), and criterion 5 requires that a reviewer be able to see which rule produced each status… | **fixed**: Added rule_applied from independently verified values: CPU/DSP R4, USB/DMA R2, SRAMCTL R3, PCIE R1. |
| C3 | major | `failed_checks` is absent from all six entries. PLAN acceptance criterion 2 requires the array (empty if none), and decision rule R2 says 'List every failing check in `failed_checks`'. BLK-USB and BLK-DMA are fail_signof… | **fixed**: Added failed_checks arrays: USB lvs_check and DMA static_timing; all others empty, following all-check reruns. |
| C4 | major | The `caveats` array required by PLAN acceptance criterion 2 is missing, and R3 requires that the routing-congestion risk be carried in it, labelled as an inference. The caveat text exists only inside the `rationale` stri… | **fixed**: Added caveats arrays; SRAMCTL carries inferred routing-congestion risk backed by the live utilization 0.82 warning, not a congestion measurement. |
| C5 | major | `blocked_reason` is absent. PLAN acceptance criterion 2 requires it on every entry as 'a string or null', and R0 defines the recorded format. BLK-PCIE is the one blocked block, so the field carries the audit trail for th… | **fixed**: Added PCIE blocked_reason with independently reproduced empty-SDC refusal; null for other blocks. |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. The reflector reads the full trace, names which tools mattered, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

`/teach semicon: pass static_timing only the PLAN's listed arguments (never empty timing_arcs/startpoints/endpoints), treat a [SEMICON] BLOCKING error that states a count as an evaluated failing value, and write result.json in the PLAN's exact per-check schema with raw tool output on the first pass.`
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
| critique_has_findings | ✅ | 14 findings |
| every_finding_answered | ✅ | 14 responses |
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
