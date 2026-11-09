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

### Step 1 — Utilization check (all six blocks)
- **Items:** BLK-CPU, BLK-DSP, BLK-USB, BLK-SRAMCTL, BLK-DMA, BLK-PCIE
- **Tool:** `floorplan`
- **Inputs** (from `inputs/floorplans.json`). Pass only these four fields. Do not pass core dimensions or `cell_area_um2`, because none are given.

| block | netlist_def | lef_path | utilization | aspect_ratio |
|---|---|---|---|---|
| BLK-CPU | `pnr/blk_cpu/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.72 | 1.0 |
| BLK-DSP | `pnr/blk_dsp/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.80 | 1.2 |
| BLK-USB | `pnr/blk_usb/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.65 | 1.0 |
| BLK-SRAMCTL | `pnr/blk_sramctl/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.82 | 0.8 |
| BLK-DMA | `pnr/blk_dma/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.70 | 1.0 |
| BLK-PCIE | `pnr/blk_pcie/synth.def` | `pdk/sky130hd/sky130_fd_sc_hd.lef` | 0.74 | 1.5 |

- **Record:** the tool-reported `utilization` (call it **U**), `utilization_source`, and any warning text or flag about utilization or the area limit.
- **What changes status:**
  - U > 0.84 → `fail_signoff` (D2)
  - 0.80 < U ≤ 0.84 → `ready_with_caveats` candidate (D3)
  - U ≤ 0.80 → no utilization issue

  U = 0.80 exactly is **not** above target (brief rule 5).

### Step 2 — Timing check (all six blocks)
- **Items:** all six
- **Tool:** `static_timing`
- **Inputs** (from `inputs/sta_runs.json`). Pass `netlist`, `sdc_path`, `spef_path` and `wns`. `lib_path` is not a `static_timing` input, so do not pass it, but copy it into `result.json` as context. Do **not** pass `sdc`, `clock_period_ns`, `timing_arcs` or `endpoints`, because none are given.

| block | netlist | sdc_path | spef_path | wns (ns) |
|---|---|---|---|---|
| BLK-CPU | `pnr/blk_cpu/final.v` | `constraints/blk_cpu.sdc` | `pnr/blk_cpu/final.spef` | 0.085 |
| BLK-DSP | `pnr/blk_dsp/final.v` | `constraints/blk_dsp.sdc` | `pnr/blk_dsp/final.spef` | 0.000 |
| BLK-USB | `pnr/blk_usb/final.v` | `constraints/blk_usb.sdc` | `pnr/blk_usb/final.spef` | 0.210 |
| BLK-SRAMCTL | `pnr/blk_sramctl/final.v` | `constraints/blk_sramctl.sdc` | `pnr/blk_sramctl/final.spef` | 0.040 |
| BLK-DMA | `pnr/blk_dma/final.v` | `constraints/blk_dma.sdc` | `pnr/blk_dma/final.spef` | -0.003 |
| BLK-PCIE | `pnr/blk_pcie/final.v` | `""` (empty string, **pass as-is**) | `pnr/blk_pcie/final.spef` | 0.150 |

- **Do not** substitute, invent or guess an SDC for BLK-PCIE (brief rule 2).
- **Record:** the tool-reported `wns` (call it **W**), `source`, any SDC warning, and whether the tool refused or rejected the run.
- **What changes status:**
  - The tool refuses or rejects the run for missing SDC, **or** the input `sdc_path` is `""` → `blocked` (D1).
  - Otherwise, W < 0 → `fail_signoff` (D2).
  - W ≥ 0 means timing is closed. W = 0.000 counts as closed (brief rule 4).

### Step 3 — DRC check (all six blocks)
- **Items:** all six
- **Tool:** `drc_check`
- **Inputs** (from `inputs/physical_verification.json` → `drc`). Pass `gds_path`, `drc_rules` and `violations`. Do not pass `shapes`, `rules` or `enclosure_rules`, because none are given.

| block | gds_path | drc_rules | violations |
|---|---|---|---|
| BLK-CPU | `gds/blk_cpu.gds` | `sky130A.drc` | 0 |
| BLK-DSP | `gds/blk_dsp.gds` | `sky130A.drc` | 0 |
| BLK-USB | `gds/blk_usb.gds` | `sky130A.drc` | 0 |
| BLK-SRAMCTL | `gds/blk_sramctl.gds` | `sky130A.drc` | 0 |
| BLK-DMA | `gds/blk_dma.gds` | `sky130A.drc` | 0 |
| BLK-PCIE | `gds/blk_pcie.gds` | `sky130A.drc` | 0 |

- **Record:** the tool-reported `violations` (call it **V**) and `source`.
- **What changes status:** V > 0 → `fail_signoff` (D2). V = 0 means DRC is clean.

### Step 4 — LVS check (all six blocks)
- **Items:** all six
- **Tool:** `lvs_check`
- **Inputs** (from `inputs/physical_verification.json` → `lvs`). Pass `gds_path`, `cdl_path` and `discrepancies`. Do not pass `layout_netlist` or `schematic_netlist`, because none are given.

| block | gds_path | cdl_path | discrepancies |
|---|---|---|---|
| BLK-CPU | `gds/blk_cpu.gds` | `netlist/blk_cpu.cdl` | 0 |
| BLK-DSP | `gds/blk_dsp.gds` | `netlist/blk_dsp.cdl` | 0 |
| BLK-USB | `gds/blk_usb.gds` | `netlist/blk_usb.cdl` | 2 |
| BLK-SRAMCTL | `gds/blk_sramctl.gds` | `netlist/blk_sramctl.cdl` | 0 |
| BLK-DMA | `gds/blk_dma.gds` | `netlist/blk_dma.cdl` | 0 |
| BLK-PCIE | `gds/blk_pcie.gds` | `netlist/blk_pcie.cdl` | 0 |

- **Record:** the tool-reported `discrepancies` (call it **L**) and `source`.
- **What changes status:** L > 0 → `fail_signoff` (D2). L = 0 means LVS is clean.

### Step 5 — Classify and write deliverables
- **Items:** all six
- **Tool:** none. This step applies the decision rules below to the values recorded in Steps 1–4.
- Write `result.json` (schema under Acceptance criteria) and `RESULT.md`. RESULT.md must contain a per-block table, the reason for each status, the gaps listed under Known limitations, and the calibrated-language statement.
- Before finishing, cross-check your statuses against the input-derived expectation table under Decision rules. If any status differs, do not silently change it. Explain which tool output caused the difference.

**Not used:** no other semicon tool has its inputs in `inputs/` (per CAPABILITIES.md). This includes `route`, which would be needed to *measure* congestion. Do not call them. Do not fabricate their inputs.

## Decision rules

Apply the rules in order D0 → D1 → D2 → D3 → D4. The **first** rule that matches gives the status. This follows the brief's precedence: blocked > fail_signoff > ready_with_caveats > tapeout_ready.

Definitions (all values come from tool outputs):
- **U** = utilization reported by `floorplan`. The tool reports the worst of computed and supplied. If it returns no number, use the input value and note that.
- **W** = WNS reported by `static_timing`.
- **V** = violations reported by `drc_check`.
- **L** = discrepancies reported by `lvs_check`.

| rule | condition | status |
|---|---|---|
| **D0** | Any of the four tool calls for this block still errors after one retry, so a required value is missing | `blocked` (reason: `tool_error:<tool>`; say explicitly in RESULT.md that this is "not yet assessable", not the SDC case) |
| **D1** | Input `sdc_path` is `""`, **or** `static_timing` refuses/rejects the run for missing constraints | `blocked` (reason: `unconstrained_sta`). Applies **regardless of W, V, L, U**. A good-looking W must not override it (brief rule 1). |
| **D2** | V > 0, **or** L > 0, **or** W < 0 (any negative value, even −0.001), **or** U > 0.84 | `fail_signoff`. List **every** failing check, not just the first. |
| **D3** | 0.80 < U ≤ 0.84, with V = 0, L = 0 and W ≥ 0 | `ready_with_caveats`. The caveat must name the routing-congestion risk at high utilization, and must say that congestion was **not measured** (`route` had no inputs). |
| **D4** | U ≤ 0.80, V = 0, L = 0, W ≥ 0 | `tapeout_ready` |

Tie-breakers and edge cases (mechanical):
- U = 0.80 → D4, not D3. W = 0.000 → closed.
- **D1 when the tool does not refuse:** `static_timing` may only warn on the empty SDC rather than refuse (CAPABILITIES gap 1). D1 still applies because of the input condition. In that case RESULT.md must state that `blocked` was decided from brief rule 1 and the empty `sdc_path`, not from a tool refusal. Quote the tool's actual warning text.
- **D3 when tool warning and number disagree:** if the `floorplan` warning disagrees with the numeric thresholds (e.g. U = 0.82 but no warning, or a warning at U ≤ 0.80), classify on the number **U** against the brief's 0.80/0.84 thresholds. Record the disagreement in `result.json` → `discrepancies_noted`. The thresholds are brief-specified and not tool-verified (CAPABILITIES gap 5).
- **Tool value differs from the input value** (W, V, L or U): use the **worse** of the two and record the difference in `discrepancies_noted`. The tools themselves report worst-of-computed-and-supplied, so this should not occur.
- **Several D2 conditions at once:** the status is still `fail_signoff`, with all failing reasons listed.
- **Secondary findings for a blocked block:** a `blocked` block may also show failing checks. List them as `secondary_findings`; they do not change the status.

Input-derived expectation (for cross-checking only; **tool outputs govern**):

| block | U | W | V | L | expected status | deciding rule |
|---|---|---|---|---|---|---|
| BLK-CPU | 0.72 | 0.085 | 0 | 0 | tapeout_ready | D4 |
| BLK-DSP | 0.80 | 0.000 | 0 | 0 | tapeout_ready | D4 (boundary: U not > 0.80; W = 0 is closed) |
| BLK-USB | 0.65 | 0.210 | 0 | 2 | fail_signoff | D2 (LVS) |
| BLK-SRAMCTL | 0.82 | 0.040 | 0 | 0 | ready_with_caveats | D3 (routing congestion risk) |
| BLK-DMA | 0.70 | -0.003 | 0 | 0 | fail_signoff | D2 (WNS < 0) |
| BLK-PCIE | 0.74 | 0.150 (untrusted) | 0 | 0 | blocked | D1 (empty sdc_path) |

## Gates

All of the following must pass before a block can receive any positive status (`tapeout_ready` or `ready_with_caveats`):
1. **Timing-constraint gate:** a non-empty `sdc_path`, and `static_timing` did not refuse the run. Failing this gives `blocked`.
2. **Timing gate:** W ≥ 0 from `static_timing` (README tapeout gate: "timing closure (WNS ≥ 0)").
3. **DRC gate:** V == 0 from `drc_check` ("BLOCKS tapeout if violations > 0"; zero tolerance, brief rule 3).
4. **LVS gate:** L == 0 from `lvs_check` ("BLOCKS tapeout if discrepancies > 0"; zero tolerance).
5. **Utilization gate:** U ≤ 0.84 from `floorplan`. U ≤ 0.80 is needed for `tapeout_ready`. 0.80 < U ≤ 0.84 allows at most `ready_with_caveats`.
6. **Evidence gate:** all four tool calls for the block returned successfully. Otherwise D0 applies.

The README's Synthesis gate (lint and formal) and Placement gate cannot be checked from these inputs. They are **not** claimed as passed. List them as unverified in RESULT.md.

## Acceptance criteria

`result.json` is complete only if:
1. It is valid JSON with a top-level `items` array containing **exactly six** entries, one per block ID from BRIEF.md, with no duplicates and none missing.
2. Each entry has:
   - `block`
   - `status`: exactly one of `tapeout_ready`, `ready_with_caveats`, `fail_signoff`, `blocked`
   - `deciding_rule`: one of D0–D4
   - `reasons`: an array that lists every failing or blocking condition
   - `caveats`: an array, required and non-empty for `ready_with_caveats`, and it must mention routing congestion as unmeasured
   - `secondary_findings`: an array, which may be empty
   - `checks`: an object with `floorplan`, `static_timing`, `drc_check` and `lvs_check`. For each tool:
     - `tool` (exact name)
     - `inputs`: the exact values passed, including `sdc_path: ""` for BLK-PCIE
     - `result_value`: U, W, V or L as reported by the tool
     - `source`
     - `warnings`
     - `refused`: boolean, for `static_timing`
     - `pass`: boolean or null
   - `lib_path` (context only)
3. Every number in `result.json` and `RESULT.md` traces to a tool output or an input file (brief rule 6). No invented numbers, including congestion figures.
4. A `tool_calls` array records all 24 calls (6 blocks × 4 tools) with their raw outputs or error text.
5. A `discrepancies_noted` array, which may be empty, records tool-vs-input or warning-vs-threshold disagreements, and records whether `static_timing` actually refused BLK-PCIE or only warned.
6. A `limitations` array states:
   - timing, DRC and LVS were judged from supplied summary counts, not recomputed;
   - the 80%/84% thresholds come from the brief;
   - the Synthesis and Placement gates are unverified;
   - congestion was not measured;
   - signoff-clean is **not** a guarantee of working silicon.
7. A `summary` object counts blocks per status, and the counts add up to 6.
8. `RESULT.md` exists, matches `result.json` exactly, and explains every status that differs from the input-derived expectation table.
