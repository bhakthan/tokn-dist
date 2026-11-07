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
| BLK-PCIE | `blocked` | 0.74 | not returned | 0 | 0 | R1 |

### BLK-CPU — `tapeout_ready`

Signoff-clean on supplied records: utilization 0.72, WNS 0.085 ns, zero DRC violations and zero LVS discrepancies. Its non-empty SDC path appears unchanged in the successful tool result. Tool acceptance is not independent verification of the illustrative file’s contents.

### BLK-DSP — `tapeout_ready`

Signoff-clean on supplied records: utilization 0.80 exactly meets the target with no warning, WNS 0.000 ns is closed, and both physical-verification counts are zero. No strictly-above-target caveat applies.

### BLK-USB — `fail_signoff`

The independent LVS rerun returned:

> [SEMICON] BLOCKING: 2 LVS discrepancies — zero-discrepancy LVS policy requires all discrepancies resolved before tapeout

The error includes `post_tool_blocked=true` and confirms L=2, matching the input. This known failure invokes BRIEF.md’s any-discrepancy rule (R2), despite utilization 0.65, WNS 0.210 ns and zero DRC violations.

PLAN R0 literally calls an error unevaluated. That ambiguity is resolved explicitly in favor of the controlling brief’s confirmed-failure rule: the error message establishes failure, not a positive result. It is not a successful discrepancies result object and does **not** satisfy the Evidence gate.

### BLK-SRAMCTL — `ready_with_caveats`

WNS 0.040 ns and zero DRC/LVS counts are signoff-clean on supplied records. Utilization 0.82 triggered:

> Warning: Area utilization 82.0% exceeds target 80.0% (within 5.0% margin) — routing congestion likely

**Routing-congestion risk is an inference from utilization alone**, not a measured routing result. No `route` run or `gcell_edges` demand/capacity evidence is available.

The **0.84 hard limit comes from BRIEF.md**, not a numeric limit explicitly returned by floorplan. The live warning reports the 80.0% target and 5.0% margin only. SRAMCTL remains within the brief’s limit and requires the congestion caveat.

### BLK-DMA — `fail_signoff`

WNS -0.003 ns is negative and fails timing closure regardless of its small magnitude. Utilization 0.70 and zero DRC/LVS counts cannot override it. Live warning:

> [HIGH] WNS = -0.003 ns — timing NOT closed (requires WNS ≥ 0.0 ns)

### BLK-PCIE — `blocked`

The empty SDC path was passed literally and the tool refused it:

> [SEMICON] BLOCKING: SDC timing constraints file required — synthesis and STA without constraints produces meaningless results

No WNS was returned. The input’s 0.150 ns is **not accepted timing-closure evidence**. Utilization 0.74 and zero DRC/LVS counts do not override blocked precedence. Supply actual SDC constraints and rerun STA before judging readiness.

## Gates and verification gaps

- **SDC:** fails for PCIE. Other non-empty paths appear unchanged in successful outputs; tool acceptance does not independently verify file contents.
- **Timing:** the WNS condition fails for DMA; PCIE is unassessable. The other four WNS values pass the numeric condition.
- **DRC:** the zero-count condition passes for all blocks. The full PLAN lifecycle gate is unverified, rather than unconditionally passed.
- **LVS:** fails for USB; the zero-count condition passes for the other blocks.
- **Lifecycle:** no returned object exposes `signoff_timing`, `signoff_drc` or `signoff_lvs` advancement. No transition is claimed or inferred as completed. Count/WNS passes are record-level only; full lifecycle authorization remains unverified.
- **Evidence:** incomplete overall because PCIE STA and USB LVS returned errors instead of successful value objects. All other blocks, including all positive-status blocks, returned all four values. Calling every tool is not equivalent to passing this gate.
- **Utilization:** SRAMCTL warns; no supplied utilization exceeds the 0.84 hard limit specified by **BRIEF.md**, not explicitly reported by a tool. DSP at exactly 0.80 does not warn.
- **Synthesis, Placement, ITAR/EAR and PDK-NDA:** not evaluable from inputs; no pass is claimed.
- **Evidence depth:** no geometry, parasitic or extracted-netlist recomputation. Floorplan limits also state that IO placement, tracks and power grid are not generated.
- **Library:** `lib_path` has no `static_timing` argument and was not consumed; actual application of the input slow-corner library is unverified.

## Execution deviations and confidence

The prior deliverables disclose deviations from PLAN Step 2 (empty optional timing arrays supplied) and from its no-altered-retry instruction (arrays omitted on retries). This is historical disclosure, not an independently audited call log. Current exact-argument reruns independently reproduce every previously reported accepted WNS value without those arrays; no classification change is found. `tool_calls_made` counts this revision only, including blocking responses once rather than adding them again.

**Confidence:** high for deterministic classification of supplied records, based on all required reruns and explicit boundary handling. This is not a numeric probability of working silicon; evidence remains supplied-summary only. The prior unsupported numeric confidence has been replaced.

## Response to critique

- **C1 — fixed:** Confirmed missing check structure. Added every check’s exact arguments, independently rerun values, sources, warnings, discrepancy notes and full raw response.
- **C2 — fixed:** Added verified `rule_applied`: CPU/DSP R4, USB/DMA R2, SRAMCTL R3, PCIE R1.
- **C3 — fixed:** Added `failed_checks`: USB LVS, DMA timing, empty for all other blocks after rerunning every check.
- **C4 — fixed:** Added `caveats` arrays; SRAMCTL carries utilization-backed routing-congestion risk explicitly labelled as inference.
- **C5 — fixed:** Added PCIE `blocked_reason` with the independently reproduced empty-SDC refusal; null for other blocks.
- **C6 — fixed:** Added call count scoped to this revision, `lib_path_not_consumed`, `unevaluable_gates` and policy assumptions. The suggested historical count is not asserted as independently audited.
- **C7 — fixed:** Evidence gate is now incomplete overall, with per-item results. Error-only returns do not pass; all positive-status blocks returned all required values.
- **C8 — fixed:** Reruns confirm absent lifecycle fields. Qualified count/WNS outcomes and left advancement conjuncts unverified; no completed transition is claimed.
- **C9 — fixed:** Live USB error confirms 2 discrepancies. Explained the brief’s confirmed-failure R2 rule and the explicit PLAN R0 ambiguity; the error does not pass the Evidence gate.
- **C10 — fixed:** Labelled prior disclosed empty-array attempts and altered retries as PLAN deviations, distinguishing historical disclosure from observed revision calls. Exact-argument reruns reproduce all accepted WNS values without those arrays.
- **C11 — fixed:** Stored full raw response envelopes, including floorplan limits/method, `computed=false`, unchanged SDC paths, warnings and blocking errors. No invented SDC acceptance quote is used.
- **C12 — fixed:** Replaced unsupported numeric confidence with qualitative classification confidence and supplied-summary evidence-depth limitations.
- **C13 — fixed:** Added `block` alongside retained `id` for every item, preserving the original shape while satisfying PLAN field naming.
- **C14 — fixed:** Attributed 0.84 to BRIEF.md in both files; live floorplan outputs do not explicitly state that numeric hard limit.
