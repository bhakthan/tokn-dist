# REFLECTION — semicon relay: "Tapeout signoff review for six hard macros"

## What changed between the first and final answer

**Statuses: no change.** Both versions give: BLK-CPU `tapeout_ready`, BLK-DSP `tapeout_ready`, BLK-USB `fail_signoff`, BLK-SRAMCTL `ready_with_caveats`, BLK-DMA `fail_signoff`, BLK-PCIE `blocked`.

Item by item:
- **All six items:**
  - Added a `checks` object with `inputs_passed`, `tool_value`, `input_value`, `source`, `warnings`, `discrepancy_note` and `raw_tool_output`. Caused by **C1** (blocking) and **C11** (raw outputs, floorplan `limits`, `computed:false`).
  - Added `rule_applied` (CPU/DSP R4, USB/DMA R2, SRAMCTL R3, PCIE R1). Caused by **C2**.
  - Added `failed_checks`, `caveats` and `blocked_reason`. Caused by **C3**, **C4** and **C5**.
  - Added a `block` field next to `id`. Caused by **C13**.
  - Added a per-item `evidence_gate`.
- **BLK-USB:**
  - The rationale now says that the `lvs_check` blocking error carries L=2, so R2 applies rather than R0's "error = unevaluated" wording. Caused by **C9**.
  - The LVS `source` is now `blocking_error_message`, and the item's evidence_gate is `fail`. Caused by **C7** and **C9**.
- **BLK-SRAMCTL:**
  - The routing-congestion caveat moved into the `caveats` array and is labelled as an inference. Caused by **C4**.
  - The 0.84 limit is now attributed to BRIEF.md ("not explicitly stated in tool output"). Caused by **C14**.
- **BLK-PCIE:**
  - `tool_value: null` for STA, with a `discrepancy_note` saying the input WNS 0.150 must not be trusted.
  - `blocked_reason` now quotes the `[SEMICON] BLOCKING` SDC refusal. Caused by **C5**.
- **Gates:**
  - Evidence gate changed from `pass` to `fail`. Caused by **C7**.
  - DRC gate changed from `pass` to `warn`. Timing and LVS details now say that signoff_* advancement is unverified. Caused by **C8**.
- **Top-level fields:**
  - Added `tool_calls_made: 24` with a `tool_calls_scope` note, `lib_path_not_consumed: true`, `unevaluable_gates` and `assumptions`. Caused by **C6**. The reviser did not adopt the critic's suggested 29; it counted only its own calls.
  - `confidence` changed from 0.93 to a qualitative statement that separates classification confidence from evidence depth. Caused by **C12**.
  - The empty-`timing_arcs` retries are now labelled as deviations from PLAN. Caused by **C10**.
  - `critique_response` changed from `[]` to 14 entries.

## Where TOKN's harness helped

- **`static_timing` + the `[SEMICON] BLOCKING` SDC hook:** for BLK-PCIE's empty `sdc_path` the tool returned "SDC timing constraints file required — synthesis and STA without constraints produces meaningless results" and no WNS. The good-looking 0.150 ns input therefore could not be read as timing closure, which settles CAPABILITIES gap 2 in favour of "refuses". The decider's unconstrained_timing_trusted score was 0.0013.
- **`static_timing` validation warning:** for BLK-DMA it flagged "[HIGH] WNS = -0.003 ns — timing NOT closed (requires WNS ≥ 0.0 ns)", catching a very small negative slack. It gave no warning for BLK-DSP's exact 0, consistent with the brief's ≥ 0 rule.
- **`lvs_check` + the zero-discrepancy hook:** for BLK-USB it returned "[SEMICON] BLOCKING: 2 LVS discrepancies …" with `post_tool_blocked: true`.
- **`floorplan` validation warning:** for BLK-SRAMCTL it reported "Area utilization 82.0% exceeds target 80.0% (within 5.0% margin) — routing congestion likely". It gave no warning for BLK-DSP at exactly 0.8, matching the brief's "strictly above" boundary.
- **`drc_check`:** it returned `violations: 0`, `source: supplied_summary`, `computed: false` for all six blocks. That honest source tag supported the "summary-only evidence" limitation.
- **Independent re-runs:** both the critique and revise stages ran all 24 domain calls again and reproduced every value. That is the strongest evidence the classification is deterministic.
- **The decider's targeted questions:** both substantive-safety probabilities were near zero (0.0076 and 0.0013). They correctly showed that no positive status rested on a failed check.

## Proposed /teach rule

`/teach semicon: pass static_timing only the PLAN's listed arguments (never empty timing_arcs/startpoints/endpoints), treat a [SEMICON] BLOCKING error that states a count as an evaluated failing value, and write result.json in the PLAN's exact per-check schema with raw tool output on the first pass.`
