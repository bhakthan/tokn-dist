# Critique — semicon tapeout signoff review

**Method.** I read `BRIEF.md`, `PLAN.md`, `CAPABILITIES.md`, everything in `inputs/`, `result.json` and `RESULT.md`, then re-ran all 24 domain tool calls myself (`floorplan`, `static_timing`, `drc_check` and `lvs_check` for each of the six blocks, passing the input values exactly as the plan specifies, including `sdc_path: ""` for BLK-PCIE). Every quoted tool output below is from my own re-run.

**What checks out.** The classification layer is correct. All six statuses and deciding rules match both the plan's input-derived expectation table and my independent tool runs: BLK-PCIE's `static_timing` call does *refuse* the empty SDC with exactly the quoted blocking text (not merely a warning); BLK-USB's `lvs_check` returns the 2-discrepancy policy block with `post_tool_blocked=true`; BLK-DMA's WNS is −0.003 ns with the `[HIGH] ... timing NOT closed` warning; BLK-SRAMCTL's `floorplan` warns at 0.82 while BLK-DSP's 0.80 returns no warning; all DRC counts are 0. No status contradicts a tool output, no gate was skipped, and no number is invented.

**What does not.** The defects are structural and evidentiary, not classificatory.

---

## Findings

### C1 — blocking — overall
**`tool_calls` is missing entirely.** The plan's step instructions require "Save the raw output of every call (24 calls in total) for `result.json` → `tool_calls`", and acceptance criterion 4 requires "A `tool_calls` array records all 24 calls … with their raw outputs or error text." result.json has no such array — its only top-level arrays are `items`, `gates`, `limitations` and an empty `critique_response`. The reported values therefore cannot be audited from the artifact itself, and the retry protocol for the two erroring calls is unverifiable.
**Fix:** add a 24-entry `tool_calls` array with the exact inputs and raw outputs/errors. The two error outputs, confirmed by re-run, are `[SEMICON] BLOCKING: SDC timing constraints file required — synthesis and STA without constraints produces meaningless results` (BLK-PCIE static_timing) and `[SEMICON] BLOCKING: 2 LVS discrepancies — zero-discrepancy LVS policy requires all discrepancies resolved before tapeout` (BLK-USB lvs_check, `post_tool_blocked=true`).

### C2 — blocking — overall
**The per-item entries do not implement the plan's schema.** Acceptance criterion 2 requires `block`, `deciding_rule`, `reasons`, `caveats`, `secondary_findings`, `checks` (with `tool`, `inputs`, `result_value`, `source`, `warnings`, `refused`, `pass` per tool) and `lib_path`. The entries carry only `id`, `status`, `rationale`, `evidence`, `tools_used`. `deciding_rule` appears nowhere in result.json (only in RESULT.md's table). Because `checks.inputs` is absent, the exact values passed are unrecorded: `netlist_def`, `lef_path`, `aspect_ratio`, `spef_path`, `drc_rules`, `cdl_path` and `lib_path` from `inputs/` appear nowhere in the deliverable, and brief-rule-2 compliance (`sdc_path: ""` passed as-is for BLK-PCIE) cannot be demonstrated from the artifact.
**Fix:** restructure each item to the plan's schema — `block` (not `id`), `deciding_rule` (D4, D4, D2, D3, D2, D1 for CPU, DSP, USB, SRAMCTL, DMA, PCIE), `reasons` arrays listing every failing/blocking condition, `secondary_findings` (empty except BLK-PCIE: U=0.74, V=0, L=0), a `checks` object with the four tools' exact inputs/result_value/source/warnings/refused/pass, and `lib_path` (`pdk/sky130hd/sky130_fd_sc_hd__ss_100C_1v60.lib`) as context.

### C3 — major — BLK-SRAMCTL
**The required `caveats` array is missing.** Criterion 2 makes `caveats` "required and non-empty for `ready_with_caveats`", and it must mention routing congestion as unmeasured. BLK-SRAMCTL is the only caveated block and its caveat lives only inside the `rationale` prose.
**Fix:** add e.g. `caveats: ["High utilization (0.82, above the 0.80 target, within the 0.84 limit) creates a routing-congestion risk, as flagged by the floorplan warning; congestion was NOT measured because route had no gcell_edges inputs."]`

### C4 — major — overall
**The `summary` object is missing.** Criterion 7 requires per-status counts that add up to 6; result.json offers only a prose `overall_verdict`.
**Fix:** add `{"tapeout_ready": 2, "ready_with_caveats": 1, "fail_signoff": 2, "blocked": 1, "total": 6}`.

### C5 — major — overall
**The `discrepancies_noted` array is missing.** Criterion 5 requires it (even if empty) and specifically requires recording whether `static_timing` actually *refused* BLK-PCIE or only warned — the open question CAPABILITIES gap 1 flagged. My re-run confirms a genuine refusal, but that fact sits only in the BLK-PCIE rationale, and the "no tool-vs-input disagreements" claim in RESULT.md is likewise not recorded where required.
**Fix:** add the array, recording the confirmed refusal text and the serialization-only value differences (0.80→0.8, 0.000→0, 0.210→0.21, 0.040→0.04, 0.70→0.7).

### C6 — major — overall
**A gate marked pass without evidence.** The `evidence` gate is "pass" with the detail "Each block has one call-output record for every required tool" — but the artifact contains no call-output records at all (no `tool_calls`, no `checks`), only paraphrased prose. PLAN.md gate 6 defines the evidence gate as "all four tool calls for the block returned successfully. Otherwise D0 applies"; two of 24 calls returned blocking errors and BLK-PCIE's timing call yielded no WNS value. RESULT.md repeats the same "Pass for classification" claim.
**Fix:** either downgrade the gate to partial/fail-with-explanation, or keep "pass" with an explicit justification against gate 6's wording *and* add the `tool_calls` records the claim currently has nothing to point to.

### C7 — major — overall
**A repeated factual error about the tool output.** Every non-refused `static_timing` call I re-ran returns `"source": "supplied_summary"` (verified for all five constrained blocks; e.g. the BLK-DMA re-run returned `{"wns": -0.003, "computed": false, "source": "supplied_summary", …}`). result.json asserts "no separate source field reported" in all six items, and RESULT.md repeats it. The claim is false; it also fails PLAN.md step 2, which requires recording `source`. No status changes as a result, but the provenance of the timing evidence is misdescribed.
**Fix:** correct to `source=supplied_summary` in the evidence strings, RESULT.md, and the `checks.static_timing.source` field.

### C8 — minor — overall
**`confidence: 0.97` is more confident than the evidence supports.** Every call returned `computed=false` / `supplied_summary` — nothing was recomputed — and the deliverable is missing six of the eight elements the acceptance criteria require (C1–C5).
**Fix:** lower it (≈0.8–0.85 for the mechanical classification) or qualify it as confidence in the status assignments only, not the physical signoff outcome.

### C9 — minor — overall
**The `utilization` gate is labeled "warn" against the plan's own definition.** Gate 5 is "U ≤ 0.84 from floorplan", which all six blocks satisfy (max 0.82, per my re-run). The "warn" reflects the brief's separate 0.80 target, not the gate criterion.
**Fix:** label the gate "pass" and keep the 0.80-target caveat in the detail text, or state explicitly that "warn" refers to the target rather than the gate.

### C10 — minor — BLK-DSP
**result.json states a tool-reported value in a form the tool did not produce.** Its evidence says "utilization=0.80"; the floorplan output serializes `0.8` (numerically equal, and RESULT.md discloses it, but result.json alone does not). The same items write `validation_warnings=[]` for calls where the tool omits the key entirely.
**Fix:** quote 0.8 (noting equality with the input 0.80) or add the serialization note; say "no validation_warnings returned" rather than `[]`.

### C11 — minor — overall
**The retry-once error protocol is not evidenced.** The plan requires a single retry, formatting-only, for any erroring call. BLK-PCIE's static_timing and BLK-USB's lvs_check both errored, but no retry is documented and no `tool_calls` record exists to show one. The statuses are unaffected — I re-ran both and they deterministically return the same blocking errors — and D1/D2 over D0 is defensible (the error text carries the deciding values; D1 is the plan's specific rule for the empty `sdc_path`, matching its own expectation table) — but the protocol step is undocumented.
**Fix:** record the retry and the reason D0 does not apply, in `tool_calls` or a note.

### C12 — minor — overall
**RESULT.md's gaps are listed under the wrong heading.** PLAN.md step 5 requires "the gaps listed under **Known limitations**"; RESULT.md uses "## Limitations". The content is present and satisfies all six required limitation items from acceptance criterion 6, so this is a heading-name deviation only — but a reader or checker looking for the named section will not find it.
**Fix:** rename the heading to "## Known limitations" (keeping the existing six bullets).

---

## Overall assessment

The thinking in this deliverable is sound and its conclusions are right: all six statuses and deciding rules match both the plan's expectation table and my independent re-run of all 24 tool calls, the two blocking tool responses are quoted verbatim and accurately, no gate was skipped, no input value was misread, and no number was invented. What fails is the form of the deliverable, and it fails badly against the plan's own acceptance criteria: `result.json` omits `tool_calls`, `summary`, `discrepancies_noted` and the per-item `deciding_rule`/`reasons`/`caveats`/`secondary_findings`/`checks`/`lib_path` fields, so six of the eight completeness criteria are unmet and a downstream consumer working to the plan's schema cannot read it; the `evidence` gate is marked pass with no records to substantiate it and against gate 6's literal wording; and a false claim ("no separate source field") about the `static_timing` output is repeated through both files. Because the defects are structural rather than classificatory, the correction is mechanical — re-emit `result.json` to the plan's schema using the already-correct values — but until that is done the deliverable should not be accepted as the signoff record, even though every status in it is one I can independently confirm.
