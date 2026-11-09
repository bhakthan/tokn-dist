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
| BLK-PCIE | `blocked` | D1 | 0.74 | No result; input 0.150 is untrusted | 0 | 0 | Empty sdc_path caused actual refusal on both attempts; missing constraints take precedence. |

USB LVS count 2 is explicitly present in the policy error and the input, not a successful LVS payload. PCIE has no accepted timing WNS; its positive input slack cannot override missing constraints. PCIE secondary findings are utilization 0.74, DRC violations 0 and LVS discrepancies 0; none changes `blocked`. Each block's input `lib_path` is retained as context only, not passed to `static_timing`.

SRAMCTL floorplan warning:

> Warning: Area utilization 82.0% exceeds target 80.0% (within 5.0% margin) — routing congestion likely

DMA timing warning:

> [HIGH] WNS = -0.003 ns — timing NOT closed (requires WNS ≥ 0.0 ns)

## Refusals, retries, and evidence gate

PCIE `static_timing` returned on both unchanged attempts:

> [SEMICON] BLOCKING: SDC timing constraints file required — synthesis and STA without constraints produces meaningless results

USB `lvs_check` returned on both unchanged attempts, with `post_tool_blocked=true`:

> [SEMICON] BLOCKING: 2 LVS discrepancies — zero-discrepancy LVS policy requires all discrepancies resolved before tapeout

These are policy errors, not formatting faults. Each was independently retried once without changing any value.

The literal PLAN.md evidence gate (all four calls successful per block) is **fail**, not pass. All responses are recorded, making classification auditable, but complete records are not equivalent to successful calls. Specific D1 applies to PCIE because constraints are absent; D2 applies to USB because the error explicitly establishes 2 discrepancies. Applying generic D0 to these substantive errors would obscure the brief-defined causes. Retaining D1/D2 is an explicitly disclosed interpretation/exception to a blanket reading of plan D0, and matches the plan expectation table; it is not a claim of literal full plan conformance. No positively classified block has a rejected check.

## Gate outcomes

| Gate | Outcome | Basis |
|---|---|---|
| Timing constraints | Fail | PCIE has empty sdc_path and timing refusal. Five other supplied paths are non-empty and calls were not refused; contents were not independently validated. |
| Timing | Fail | DMA WNS -0.003 ns fails; PCIE has no accepted constrained result; other four summaries are non-negative. |
| DRC | Pass on supplied counts | All six counts zero; no geometry recomputation. |
| LVS | Fail | USB policy errors explicitly carry 2 discrepancies; other five counts zero. |
| Utilization | Pass | All values satisfy hard limit 0.84; SRAMCTL 0.82 retains a separate above-0.80 target caveat. |
| Evidence | Fail | USB LVS and PCIE timing return policy errors on both attempts. Records are complete, not all successful. Specific D2/D1 interpretation versus generic D0 is disclosed above. |
| Synthesis | Unverified / n/a | Lint and formal inputs absent. |
| Placement | Unverified / n/a | Placement inputs absent. |
| Routing congestion | Unmeasured / n/a | route gcell_edges absent. |

## Cross-check and provenance

All six statuses match the plan expectation table. There is no disagreement for returned numerical values. PCIE is excluded from numeric WNS comparison because timing returned no value. USB count 2 is error evidence, not a successful payload. DSP returned utilization 0.8, numerically equal to input 0.80; trailing-zero serialization changes no value. Only SRAMCTL warned on utilization, and DSP at 0.8 did not. The complete raw outputs preserve omitted warning keys; normalized `checks.warnings=[]` denotes no warnings, and `warning_key_present` distinguishes absence from a returned array.

## Summary and confidence

Counts from the six classifications: **tapeout_ready 2; ready_with_caveats 1; fail_signoff 2; blocked 1; total 6.**

CPU and DSP meet supplied-summary tapeout criteria; SRAMCTL is ready with an unmeasured routing-congestion caveat; USB and DMA fail signoff; PCIE is blocked pending constrained STA. The literal all-success evidence gate is not passed.

Assessed confidence: **0.85 in mechanical classification of the supplied synthetic records only**, not independent physical signoff, validated constraint contents, or working silicon.

## Known limitations

- Timing, DRC, and LVS were judged from supplied summaries and policy errors, not recomputed from timing graphs, geometry or extracted/schematic netlists. Successful timing, DRC and LVS calls returned `computed=false`; floorplan used `utilization_source=supplied_summary` and omitted `computed`.
- The 80% target, 84% hard limit and 5% margin are BRIEF.md thresholds, not independently verified PDK limits.
- Synthesis (lint/formal) and Placement gates are unverified; required inputs are absent.
- Routing congestion was not measured; gcell_edges were absent. SRAMCTL has a warning, not measured overflow.
- Paths are illustrative per inputs; upstream artifacts and constraint contents were not independently validated.
- Signoff-clean on these supplied-record checks is **not a guarantee of working silicon**.
- The literal all-success evidence gate fails for two policy errors; negative classifications retain specific D1/D2 rather than generic D0, an explicitly disclosed interpretation.

## Response to critique

- **C1 — fixed:** Added all 24 independently re-run primary tool_calls with exact inputs and full structured raw responses; both unchanged retries are nested in their primary records.
- **C2 — fixed:** Retained legacy item fields and added block, deciding_rule, reasons, caveats, secondary_findings, checks and lib_path. Checks record exact inputs, value, source, warnings, refused and pass. PCIE WNS is null because no value returned; USB count 2 is explicitly from the error.
- **C3 — fixed:** Re-run floorplan returned SRAMCTL utilization 0.82 and its congestion warning. Added required caveats array naming unmeasured routing congestion; timing/DRC/LVS summaries pass.
- **C4 — fixed:** Added summary counts from all six classifications: tapeout_ready 2, ready_with_caveats 1, fail_signoff 2, blocked 1, total 6.
- **C5 — fixed:** Added discrepancies_noted documenting actual PCIE refusal on both attempts, not a warning; no returned-number disagreement, input-only untrusted PCIE slack and serialization equality are explicitly distinguished.
- **C6 — fixed:** Evidence gate downgraded to fail under literal all-success gate 6. Recorded all responses and disclosed specific D1/D2 versus generic D0 interpretation. Errors are not successful calls, and no positive status relies on them.
- **C7 — fixed:** All five successful timing re-runs returned source=supplied_summary and computed=false. Corrected timing provenance everywhere. PCIE returned only refusal, no timing source/value payload.
- **C8 — fixed:** Lowered confidence to 0.85 and scoped it to mechanical classification of supplied synthetic records only. Corrected the overbroad computed=false premise in limitations: floorplan omits computed; rejected calls have no computed payload.
- **C9 — fixed:** All six re-run utilization values satisfy U<=0.84. Utilization gate is pass; SRAMCTL separate above-0.80 target warning remains a caveat.
- **C10 — fixed:** DSP raw utilization is 0.8, numerically equal to input 0.80. Evidence describes omitted warning keys rather than falsely returned empty arrays. Normalized checks warnings arrays include warning_key_present flags; raw outputs preserve omissions.
- **C11 — fixed:** PCIE timing and USB LVS independently retried once unchanged, with identical errors recorded. Specific D1 for empty SDC and D2 for explicit error count 2 remain. Evidence gate fails literally; interpretation against blanket D0 is explicitly disclosed.
- **C12 — fixed:** Final report uses Known limitations heading, retaining limitations and calibrated not-a-guarantee language.
