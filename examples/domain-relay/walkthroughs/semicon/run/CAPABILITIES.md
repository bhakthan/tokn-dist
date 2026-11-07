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

Brief rules (quoted):
- Status precedence: "blocked, then fail_signoff, then ready_with_caveats, then tapeout_ready." Rule 1: a block with unconstrained timing is `blocked` "however good its recorded WNS looks."
- Timing: "Timing closure means WNS ≥ 0 ns. A WNS of exactly 0.000 ns is closed; any negative WNS, however small, is not."
- Utilization: target "80% target"; warning fires only when "strictly above the 80% target", with a margin "limit 84%". `fail_signoff` if "utilization above the 84% hard limit."
- DRC: "any DRC violation" → `fail_signoff`. Policy "zero tolerance for DRC and LVS."
- LVS: "any LVS discrepancy" → `fail_signoff`.
- Input handling: "Pass every record to the tools exactly as given, including an empty `sdc_path`. Do not invent or substitute a constraints file."
- Tool choice: `floorplan` for utilization, `static_timing` for WNS, `drc_check` for DRC, `lvs_check` for LVS.
- Language: "Use calibrated language: signoff-clean is not a guarantee of working silicon."

Tool-level gates (from tool descriptions):
- `drc_check`: "advances to signoff_drc only when violations == 0."
- `lvs_check`: "Advances to signoff_LVS only when discrepancies == 0." (BLOCKS tapeout if discrepancies > 0.)
- `static_timing`: "Worst of computed and supplied WNS is recorded for the timing gate." Empty `sdc_path` "triggers the SDC warning" (per schema).
- `floorplan`: utilization is "checked against the area limit" (numeric limit not stated in tool text).

Domain README gates (tokn-self/DOMAIN-README.md): Tapeout gate = "DRC+LVS+timing closure WNS≥0"; DRC gate = "zero violations"; LVS gate = "zero discrepancies". Synthesis and Placement gates cannot be evaluated from these inputs.

Lifecycle caution: README lists a 14-state lifecycle (INIT → … → TAPEOUT_READY → ARCHIVED). Inputs record no per-block lifecycle state, so transition gating cannot be checked here.

## Gaps

1. **Routing-congestion risk for `ready_with_caveats`.** The brief requires naming it. `route` needs `cts_def` and `gcell_edges` (demand/capacity), which are not in inputs. Any congestion statement must be reasoned from the utilization figure alone and labelled as inference, not measurement.
2. **Blocked status depends on a tool behaviour that conflicts across sources.** The brief says `static_timing` "refuses" an empty SDC. The tool schema says an empty `sdc_path` "triggers the SDC warning." The actual call output must be recorded and used; neither source should be assumed.
3. **`lib_path` not consumed.** `sta_runs.json` carries `lib_path` per block, but `static_timing` has no lib argument. Whether the slow-corner library is used is unknown; it must not be claimed as applied.
4. **Floorplan limit.** The 84% hard limit is in the brief only. The tool text says "checked against the area limit" without a number. The tool's own output must confirm the limit before it is quoted.
5. **Floorplan input form.** `netlist_def` is a required string; inputs give file paths (`pnr/.../synth.def`), and the README says paths are "illustrative only." Whether the tool can open them is unknown until it runs.
6. **Summary-only DRC/LVS.** Only supplied counts exist. No geometry is available for computed checks, so the signoff counts rest on the input records.
7. **Domain self-description versus tool list.** The README and introspect slice claim 20 LLM tools, 8 hooks, 16 commands, 3 subagents. My tool list shows no `semicon`-prefixed tool and does not enumerate hooks, commands or subagents. The 20-tool count and hook/gate enforcement are unverified. Ground truth used: the tool list.
8. **Export-control and PDK-NDA records.** README claims ITAR/EAR and PDK NDA enforcement. Inputs contain no export-control classification or NDA field, so these checks cannot be evidenced here.
9. **Reasoning-only items.** The four-state vocabulary, precedence ordering, and the "signoff-clean is not working silicon" caveat have no tool; they are applied by reasoning against the brief.
