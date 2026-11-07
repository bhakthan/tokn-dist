# Brief — tapeout signoff review for six hard macros

You are the physical-design signoff lead for a mixed-signal SoC on an open 130 nm PDK. Six hard macros have come back from place-and-route. Before the top-level integration freeze, the programme manager needs a defensible signoff status for each block: is it ready to hand to tapeout, ready with a caveat, failing signoff, or not yet assessable?

The data is synthetic but realistic. Everything you need is in `inputs/`:

| File | Contents |
|---|---|
| `inputs/floorplans.json` | Per block: `netlist_def`, `lef_path`, `utilization` (fraction of core area) and `aspect_ratio` |
| `inputs/sta_runs.json` | Per block: the static-timing run record: `netlist`, `sdc_path`, `spef_path`, `lib_path` and worst negative slack `wns` (ns) |
| `inputs/physical_verification.json` | Per block: the DRC record (`gds_path`, `drc_rules`, `violations`) and the LVS record (`gds_path`, `cdl_path`, `discrepancies`) |

## Items to assess

`BLK-CPU`, `BLK-DSP`, `BLK-USB`, `BLK-SRAMCTL`, `BLK-DMA`, `BLK-PCIE`

## Status vocabulary (use exactly one per item)

- `tapeout_ready`: timing closed (WNS ≥ 0 ns), DRC clean, LVS clean, and utilization at or below the 80% target.
- `ready_with_caveats`: as `tapeout_ready`, but `floorplan` warns that utilization is above the 80% target while still within the 5% margin (limit 84%). Name the routing-congestion risk.
- `fail_signoff`: at least one signoff check fails: any DRC violation, any LVS discrepancy, WNS < 0 ns, or utilization above the 84% hard limit.
- `blocked`: the timing result cannot be trusted because the STA run had no SDC constraints, so `static_timing` refuses it. Fix the run before judging the block.

## Rules

1. Precedence is `blocked`, then `fail_signoff`, then `ready_with_caveats`, then `tapeout_ready`. A block whose timing was never constrained is `blocked`, however good its recorded WNS looks.
2. Pass every record to the tools exactly as given, including an empty `sdc_path`. Do not invent or substitute a constraints file.
3. Use `floorplan` for the utilization check, `static_timing` for WNS, `drc_check` for DRC and `lvs_check` for LVS. Signoff policy is zero tolerance for DRC and LVS.
4. Timing closure means WNS ≥ 0 ns. A WNS of exactly 0.000 ns is closed; any negative WNS, however small, is not.
5. The utilization warning fires only when utilization is strictly above the 80% target.
6. Every number you report must come from a tool call or the input files. Use calibrated language: signoff-clean is not a guarantee of working silicon.

## Deliverable

`result.json` and `RESULT.md`, as described in your stage instructions.
