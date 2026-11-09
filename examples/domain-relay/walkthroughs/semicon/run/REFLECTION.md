# REFLECTION — semicon relay: tapeout signoff review for six hard macros

## What changed between the first and final answer

**Statuses: no change.** Both versions give CPU and DSP `tapeout_ready`, SRAMCTL `ready_with_caveats`, USB and DMA `fail_signoff`, and PCIE `blocked`. The decision model's low scores agree: 0.011 for positive_despite_failed_check and 0.006 for unconstrained_timing_trusted. Every change was about structure, provenance or calibration:

| Change (v1 → final) | Caused by |
|---|---|
| No `tool_calls` → 24 records with exact inputs and raw outputs; the PCIE static_timing and USB lvs_check records each include a nested `retry` | C1, C11 |
| Items had `id, status, rationale, evidence, tools_used` → added `block`, `deciding_rule` (D4, D4, D2, D3, D2, D1), `reasons`, `caveats`, `secondary_findings`, `checks` and `lib_path`. Legacy fields were kept. | C2 |
| SRAMCTL caveat existed only as rationale prose → it is now a `caveats` array naming routing congestion as unmeasured | C3 |
| No `summary` → `{tapeout_ready 2, ready_with_caveats 1, fail_signoff 2, blocked 1, total 6}` | C4 |
| No `discrepancies_noted` → 4 entries. One records that PCIE was actually *refused* on both attempts, not merely warned. | C5 |
| Evidence gate `pass` → `fail`, with the D1/D2-over-D0 interpretation disclosed | C6 |
| "no separate source field reported" → `source=supplied_summary`, because the raw outputs do carry `source` | C7 |
| `confidence` 0.97 → 0.85, plus a new `confidence_scope` | C8 |
| Utilization gate `warn` → `pass`; the 0.80-target caveat stays in the detail text | C9 |
| DSP utilization written as 0.80 → noted as 0.8 raw; warning keys that the tool omitted are no longer described as empty arrays | C10 |
| RESULT.md heading renamed to "Known limitations" | C12 |
| A new limitation entry says the literal evidence gate fails | C6, C11 |

## Where TOKN's harness helped

- **`static_timing` SDC gate.** It returned `[SEMICON] BLOCKING: SDC timing constraints file required …` for BLK-PCIE when `sdc_path: ""`, and returned it identically on retry. This settled CAPABILITIES gap 1 (refusal vs warning). It also kept the input WNS of 0.150 ns from being used as evidence: unconstrained_timing_trusted = 0.006.
- **`lvs_check` zero-discrepancy gate.** It returned `BLOCKING: 2 LVS discrepancies …` with `post_tool_blocked=true` for BLK-USB, which decided USB's D2 status.
- **`static_timing` WNS gate.** For BLK-DMA it emitted `[HIGH] WNS = -0.003 ns — timing NOT closed`, catching a negative slack of only 3 ps.
- **`floorplan` utilization warning.** It fired only for SRAMCTL (`82.0% exceeds target 80.0% (within 5.0% margin) — routing congestion likely`) and not for DSP at 0.8. This confirmed the strict-greater-than boundary from brief rule 5.
- **Provenance fields.** `source`/`utilization_source = supplied_summary` and `computed=false` in the raw outputs let the critique show that v1's "no separate source field" claim was false (C7). They also justified lowering confidence (C8).
- **Critique → decide → revise loop.** The independent re-run of all 24 calls by the critic was the evidence behind C1–C12. The relay turned a structurally incomplete v1 into a schema-complete final answer.
- `drc_check` returned 0 violations for all six blocks. That was useful as a recorded gate value, but it caught nothing.

## Proposed /teach rule

semicon: when a domain tool returns a `[SEMICON] BLOCKING:` error, record it as a successful gate verdict (not a tool failure), retry once unchanged, store the raw response in `result.json` → `tool_calls`, and fill every plan-schema field before writing the final answer.
