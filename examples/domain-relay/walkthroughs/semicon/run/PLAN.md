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
Items: all six. Tool: `floorplan`. Source: `inputs/floorplans.json`.

| block | netlist_def | lef_path | utilization | aspect_ratio |
|---|---|---|---|---|
| BLK-CPU | `pnr/blk_cpu/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.72 | 1.0 |
| BLK-DSP | `pnr/blk_dsp/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.80 | 1.2 |
| BLK-USB | `pnr/blk_usb/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.65 | 1.0 |
| BLK-SRAMCTL | `pnr/blk_sramctl/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.82 | 0.8 |
| BLK-DMA | `pnr/blk_dma/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.70 | 1.0 |
| BLK-PCIE | `pnr/blk_pcie/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.74 | 1.5 |

Do not pass `cell_area_um2`, core dimensions or macros, because none are given.
Record: the returned `utilization`, `utilization_source`, any warning text, and any limit or target the tool states.
Status effect: the utilization value U puts the block in one of the bands in Decision rules R3: OK, caveat, or fail.

### Step 2 — Timing (`static_timing`), all six blocks
Items: all six. Tool: `static_timing`. Source: `inputs/sta_runs.json`.

| block | netlist | sdc_path | spef_path | wns |
|---|---|---|---|---|
| BLK-CPU | `pnr/blk_cpu/final.v` | `constraints/blk_cpu.sdc` | `pnr/blk_cpu/final.spef` | 0.085 |
| BLK-DSP | `pnr/blk_dsp/final.v` | `constraints/blk_dsp.sdc` | `pnr/blk_dsp/final.spef` | 0.000 |
| BLK-USB | `pnr/blk_usb/final.v` | `constraints/blk_usb.sdc` | `pnr/blk_usb/final.spef` | 0.210 |
| BLK-SRAMCTL | `pnr/blk_sramctl/final.v` | `constraints/blk_sramctl.sdc` | `pnr/blk_sramctl/final.spef` | 0.040 |
| BLK-DMA | `pnr/blk_dma/final.v` | `constraints/blk_dma.sdc` | `pnr/blk_dma/final.spef` | -0.003 |
| BLK-PCIE | `pnr/blk_pcie/final.v` | `""` (empty string, passed literally) | `pnr/blk_pcie/final.spef` | 0.150 |

Do not pass `timing_arcs`, `sdc`, `clock_period_ns` or `lib_path`.
Record: the returned `wns`, `source`, any warning, refusal or error text (especially SDC-related text), and whether the tool refused or accepted the run.
Status effect: an empty SDC means `blocked` (R1). If the SDC is present, WNS < 0 means `fail_signoff` (R2). WNS ≥ 0 means timing is closed.

### Step 3 — DRC (`drc_check`), all six blocks
Items: all six. Tool: `drc_check`. Source: `inputs/physical_verification.json` → `drc`.

| block | gds_path | drc_rules | violations |
|---|---|---|---|
| BLK-CPU | `gds/blk_cpu.gds` | `sky130A.drc` | 0 |
| BLK-DSP | `gds/blk_dsp.gds` | `sky130A.drc` | 0 |
| BLK-USB | `gds/blk_usb.gds` | `sky130A.drc` | 0 |
| BLK-SRAMCTL | `gds/blk_sramctl.gds` | `sky130A.drc` | 0 |
| BLK-DMA | `gds/blk_dma.gds` | `sky130A.drc` | 0 |
| BLK-PCIE | `gds/blk_pcie.gds` | `sky130A.drc` | 0 |

Do not pass `shapes`, `rules` or `enclosure_rules`.
Record: the returned `violations`, `source`, and whether the design advanced to `signoff_drc`.
Status effect: violations > 0 means `fail_signoff` (R2).

### Step 4 — LVS (`lvs_check`), all six blocks
Items: all six. Tool: `lvs_check`. Source: `inputs/physical_verification.json` → `lvs`.

| block | gds_path | cdl_path | discrepancies |
|---|---|---|---|
| BLK-CPU | `gds/blk_cpu.gds` | `netlist/blk_cpu.cdl` | 0 |
| BLK-DSP | `gds/blk_dsp.gds` | `netlist/blk_dsp.cdl` | 0 |
| BLK-USB | `gds/blk_usb.gds` | `netlist/blk_usb.cdl` | 2 |
| BLK-SRAMCTL | `gds/blk_sramctl.gds` | `netlist/blk_sramctl.cdl` | 0 |
| BLK-DMA | `gds/blk_dma.gds` | `netlist/blk_dma.cdl` | 0 |
| BLK-PCIE | `gds/blk_pcie.gds` | `netlist/blk_pcie.cdl` | 0 |

Do not pass `layout_netlist`, `schematic_netlist` or `top_cell`.
Record: the returned `discrepancies`, `source`, and whether the design advanced to `signoff_lvs`.
Status effect: discrepancies > 0 means `fail_signoff` (R2).

### Step 5 — Apply the decision rules (reasoning only, no tool)
Items: all six. Apply R0–R5 below to the recorded outputs, in precedence order. No tool exists for the four-state classification or the precedence order (CAPABILITIES gap 9).

### Step 6 — Cross-check, then write deliverables
For every check, compare each tool-returned value with the input value shown in the tables above. If they differ (for example, the tool reports a worse value because it computed one), **use the tool value**, as the brief requires, and add a `discrepancy_note` to that check. Then write `result.json` and `RESULT.md` as described in Acceptance criteria.

## Decision rules

Notation for each block: U is the utilization returned by `floorplan`. W is the WNS returned by `static_timing`. D is the violations count returned by `drc_check`. L is the discrepancies count returned by `lvs_check`. Compare U after rounding to 4 decimal places, so that floating-point noise cannot move 0.80 across the threshold. Compare W, D and L exactly as returned.

**R0 — Tool failure (evaluate first, then fall through).** A check counts as *unevaluated* if its tool returned an error, or returned no value for U, W, D or L.
- If any other evaluated check meets an R2 fail condition, apply R2: `fail_signoff`.
- Otherwise the status is `blocked`, with `blocked_reason: "tool_unevaluated:<tool>"`.

An unevaluated check can never support a positive status. This extends the brief's "not yet assessable" meaning, and it must be flagged in RESULT.md if it happens.

Exception: an unevaluated `static_timing` call on a block whose `sdc_path` is `""` falls under R1, not R0.

**R1 — `blocked` (highest precedence).** The block is `blocked` if its STA record has `sdc_path == ""`. Today that is true only for BLK-PCIE.
- This applies whatever `static_timing` returns, and however good W looks (Brief rule 1).
- Record the tool's actual response to the empty SDC (refusal, warning, or acceptance) verbatim. CAPABILITIES gap 2 notes that the brief says "refuses" while the schema says "warns". Either response leads to `blocked`.
- If the tool *accepted* the run silently, still mark the block `blocked`, and add a note that the tool did not enforce the SDC requirement.
- A warning that a **non-empty** sdc_path is unreadable does **not** trigger R1. Record it as a note only, because the paths are illustrative.
- The other checks for a blocked block are still run and reported.

**R2 — `fail_signoff`.** Applies only if R1 does not. The block fails if any of these holds:
- W < 0 (any negative value, for example -0.003)
- D > 0
- L > 0
- U > 0.84

List every failing check in `failed_checks`.

**R3 — `ready_with_caveats`.** Applies only if neither R1 nor R2 does. All of these must hold: W ≥ 0, D == 0, L == 0, and 0.80 < U ≤ 0.84.
- The `floorplan` warning is expected here. If the tool does not warn even though U is in this band, use the U value anyway and note that the warning is missing.
- The caveat must name the **routing-congestion risk**. Label it as an inference from utilization alone, because `route` was not run and `gcell_edges` were not supplied (CAPABILITIES gap 1).

**R4 — `tapeout_ready`.** Applies only if none of R1–R3 does. All of these must hold: W ≥ 0 (exactly 0.000 counts as closed), D == 0, L == 0, and U ≤ 0.80 (exactly 0.80 does **not** trigger the warning, per Brief rule 5).

**R5 — Language.** Even for `tapeout_ready`, the wording must say "signoff-clean on the supplied records". Never say "will work in silicon". DRC and LVS evidence is summary-count only (CAPABILITIES gap 6). The STA library corner was not passed to the tool (gap 3).

## Gates

Before any positive status (`tapeout_ready` or `ready_with_caveats`), all of these must hold, and each must be evidenced by a tool output:

1. **SDC gate.** The STA run had a non-empty `sdc_path`, and `static_timing` did not refuse it.
2. **Timing gate** (DOMAIN-README Tapeout gate). The `static_timing` WNS is ≥ 0 ns, and the run reached `signoff_timing` if the tool reports state.
3. **DRC gate** (zero violations). `drc_check` violations == 0, and the run advanced to `signoff_drc`.
4. **LVS gate** (zero discrepancies). `lvs_check` discrepancies == 0, and the run advanced to `signoff_lvs`.
5. **Utilization gate.** `floorplan` utilization is ≤ 0.84. A value ≤ 0.80 gives `tapeout_ready`. A value in (0.80, 0.84] gives `ready_with_caveats`.
6. **Evidence gate.** All four tool calls for the block returned a value (see R0).

The Synthesis and Placement gates and the ITAR/EAR and PDK-NDA checks cannot be evaluated from these inputs (CAPABILITIES gaps 7–8). State this in RESULT.md. Do not claim they passed.

## Acceptance criteria

`result.json` is complete only if all of the following are true.

1. It contains a top-level `items` array with **exactly six** entries, one each for BLK-CPU, BLK-DSP, BLK-USB, BLK-SRAMCTL, BLK-DMA and BLK-PCIE. There are no other entries.
2. Each entry has these fields:
   - `block`
   - `status`: exactly one of `tapeout_ready`, `ready_with_caveats`, `fail_signoff` or `blocked`
   - `rule_applied`: one of R0, R1, R2, R3 or R4
   - `failed_checks`: an array, empty if there are none
   - `caveats`: an array. For `ready_with_caveats` it must include routing-congestion risk, labelled as inference.
   - `blocked_reason`: a string or null
   - `checks`: an object with keys `floorplan`, `static_timing`, `drc_check` and `lvs_check`. Each key holds:
     - `inputs_passed`: the exact arguments sent
     - `tool_value`: U, W, D or L as returned
     - `input_value`: the value from `inputs/`
     - `source`: the computed or supplied tag as returned
     - `warnings`: the tool's warnings or errors, verbatim
     - `discrepancy_note`: present if the tool value differs from the input value
3. Every number in the file appears either in a tool output or in `inputs/`. No numbers are invented. No SDC file is substituted.
4. Top-level metadata:
   - `tool_calls_made`: should be 24, plus the count of any errored calls
   - `lib_path_not_consumed: true`
   - `unevaluable_gates`: Synthesis, Placement, ITAR/EAR and PDK-NDA
   - `assumptions`: the 4-decimal rounding of U, and the R0 handling of tool failure
5. The statuses follow the precedence blocked > fail_signoff > ready_with_caveats > tapeout_ready. If a reviewer applies R0–R4 to the recorded `tool_value`s, they must reproduce every status.
6. `RESULT.md` gives the same six statuses with a one-line justification each. It uses calibrated language (R5) and lists the gaps from CAPABILITIES that limit confidence.
