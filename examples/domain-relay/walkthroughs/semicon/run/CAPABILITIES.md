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
- Precedence: `blocked`, then `fail_signoff`, then `ready_with_caveats`, then `tapeout_ready`.
- `blocked`: "the STA run had no SDC constraints, so `static_timing` refuses it." Rule 1: "A block whose timing was never constrained is `blocked`, however good its recorded WNS looks."
- `fail_signoff`: "any DRC violation, any LVS discrepancy, WNS < 0 ns, or utilization above the 84% hard limit."
- `ready_with_caveats`: utilization "above the 80% target while still within the 5% margin (limit 84%)". Rule 5: "The utilization warning fires only when utilization is strictly above the 80% target."
- `tapeout_ready`: "WNS ≥ 0 ns, DRC clean, LVS clean, and utilization at or below the 80% target."
- Rule 4: "A WNS of exactly 0.000 ns is closed; any negative WNS, however small, is not."
- Rule 2: "Pass every record to the tools exactly as given, including an empty `sdc_path`. Do not invent or substitute a constraints file."
- Rule 3: signoff policy is zero tolerance for DRC and LVS.
- Rule 6: every number must come from a tool call or the input files. Calibrated language: "signoff-clean is not a guarantee of working silicon."

Quoted from tool and README descriptions:
- `drc_check`: "BLOCKS tapeout if violations > 0" (README: "DRC: blocks tapeout when violations > 0").
- `lvs_check`: "BLOCKS tapeout if discrepancies > 0" (README: "LVS: blocks tapeout when discrepancies > 0").
- `static_timing`: "Worst of computed and supplied WNS is recorded for the timing gate."
- README Tapeout gate: "requires DRC and LVS closure and timing closure (WNS ≥ 0)."
- README: "Preflight (PreToolUse): destructive or non-allowlisted EDA commands are refused." (Not triggered by this read-only review.)

Threshold provenance: the 80% target, 84% hard limit and 5% margin come from BRIEF.md only. The `floorplan` tool description says only "checked against the area limit" and does not quote the value. Treat the 80/84 values as brief-specified, not tool-verified.

## Gaps

1. **Empty-SDC refusal is not confirmed.** The brief's `blocked` status assumes `static_timing` refuses a run with no SDC. The tool description says only that an empty `sdc_path` "triggers the SDC warning," with no refusal. The README does not mention refusal either. Handling for BLK-PCIE: call `static_timing` with the record as given and read the returned output. If the tool warns but does not refuse, the `blocked` status must be decided by reasoning from the brief's rule 1, and the answer must say so. The recorded WNS of 0.150 must not be used to override `blocked`.
2. **README vs tool list disagreement.** The README (and introspect slice) says 8 hooks and 16 commands. Neither is in my tool list, so I cannot verify them. The 20 semicon tools in my list match the README's tool count and names. The README's "Synthesis" gate (lint-clean and formal-proven) and "Placement" gate are not checkable from these inputs.
3. **Timing is supplied, not computed.** `static_timing` gets only the supplied `wns`. No timing arcs, endpoints or clock period are given, so the WNS values, including BLK-DMA at -0.003 ns, cannot be recomputed here. The `lib_path` (ss corner) cannot be consumed by `static_timing`. Stated as a limitation, not a defect.
4. **DRC and LVS are count-only.** `drc_check` and `lvs_check` will run on the supplied violation and discrepancy counts. No geometry, DRC rule deck contents, or netlist comparison is available. The rule-deck name "sky130A.drc" cannot be expanded by any tool here. Zero-count results are only as good as the upstream runs.
5. **Utilization threshold values not tool-verified.** See the threshold provenance note above. The "5% margin" and the 84% limit exist only in the brief.
6. **Out of scope for available tools:** routing congestion risk (named by `ready_with_caveats`) — `route` requires `gcell_edges` demand/capacity, which are not in `inputs/`. So the routing-congestion risk for any caveated block must be stated by reasoning, not measured.
7. **Calibrated-language claims** (e.g., "not a guarantee of working silicon") are a reasoning obligation; no tool checks them.
