# Critique — Cluster 7 N-1-1 / grid-forming screen (IR-1 … IR-5)

Critic stage. Scope: `result.json` and `RESULT.md` against `BRIEF.md`, `inputs/n11_study.json`, `inputs/ibr_registry.json` and `PLAN.md`. All ten domain tool calls were re-run with the plan's exact inputs (5 × `powergrid_n1_1_screen`, 5 × `powergrid_ibr_stability_gate`) before any finding was recorded. This critique did not edit `result.json` or `RESULT.md`.

## What was verified and reproduced

Every reported number and severity is correct. In particular:

- **All five screens** returned `computed=true`, `screening_complete=true`, `source=supplied_summary`, `unscreened_pairs=[]`, `n_pairs=6`, `computed_pairs=0`, limits `thermal_limit_pct=115` / `voltage_min_pu=0.85` / `voltage_max_pu=1.1`, standard `NERC TPL-001-4 P6/P7` — exactly as quoted.
- **IR-1** gate: `blocked=false`, `Z-NORTH gfl_penetration_pct=12.5`, `gfl_headroom_mw=100`, `gfm_needed_mw=0`, `over_threshold=false`. Matches.
- **IR-2** screen: one violation, severity **HIGH**, "L-203 at 131.0% > 115% emergency rating after L-201 → L-202", kind=thermal, pair `L-201|L-202`. Matches verbatim. 131.0% < 132.25%, so HIGH (not CRITICAL) is the right classification, and `approve_with_conditions` is the right status.
- **IR-2** gate: `Z-EAST gfl_penetration_pct=17.778`, `gfl_headroom_mw=78.571`, `gfm_needed_mw=0`. Matches.
- **IR-3** gate: returned the error `[BLOCK] zone Z-SOUTH: expansion adds 60 MW GFL with no GFM — post-expansion GFL penetration 34.8% exceeds 30.0% threshold. Add GFM capacity (or synchronous condensers) before approving.` with `result=null` — reproduced character for character. Status `blocked` is correct; the brief's `blocked` definition fits IR-3 exactly.
- **IR-4** screen: `n_violations=0`, `violations=null` — the 115.0% / 0.85 pu / 1.10 pu boundary values returned no violation. Matches, and matches D3.
- **IR-4** gate: `Z-WEST gfl_penetration_pct=30`, `over_threshold=false`, `blocked=false`, `gfl_headroom_mw=0`. Matches; equality with the threshold does not block, per BRIEF Rule 4.
- **IR-5** screen: one violation, severity **CRITICAL**, "loss of synchronism / voltage collapse after outage sequence L-501 → L-502", kind=stability, pair `L-501|L-502`. Matches. Status `reject` is correct.
- **IR-5** gate: `Z-CENTRAL gfl_penetration_pct=16.667`, `gfl_headroom_mw=68.571`, `gfm_needed_mw=0`. Matches.

So all five statuses — approve, approve_with_conditions, blocked, approve, reject — are substantively correct, and the correct one appears for the correct reason. The problems are structural: the deliverable does not conform to the output schema `PLAN.md` itself defines.

## Findings

### C1 — result.json is missing the four required top-level fields (`major`, overall)

`result.json` has no `study`, `standard`, `threshold_pct` or `warnings`. PLAN.md acceptance criterion 1 requires all four: `study` copied from `inputs/n11_study.json`, `standard` = "NERC TPL-001-4 P6/P7", `threshold_pct` = 30, and `warnings` containing "N-1 not checked", "N-0 power flow not run" and "SCR not assessed (no short-circuit data)". The content is present, only the fields are absent — the study string sits in RESULT.md's header and inside `objective`, threshold_pct=30 sits in `objective` and in every gate evidence string, and the three warning phrases sit in `limitations[0]`/`limitations[1]` and in RESULT.md's "Required warnings" blockquote. A consumer reading `warnings` or `standard` as fields finds nothing.

**Fix:** add the four fields: `study` = "Cluster 7 interconnection queue — summer peak 2029, N-1-1 (NERC TPL-001-4 P6/P7)" (verbatim from the inputs), `standard` = "NERC TPL-001-4 P6/P7", `threshold_pct` = 30, `warnings` = ["N-1 not checked", "N-0 power flow not run", "SCR not assessed (no short-circuit data)"]. No new numbers are introduced.

### C2 — item objects do not follow the required structure (`major`, overall)

Each item carries only `id`, `status`, `rationale`, `evidence` and `tools_used`. Criterion 2 requires each item to also carry `zone`, a structured `n11` object ({tool, screening_complete, source, pairs_screened, violations: [{pair, element, metric, value, severity_as_returned, counted}], n_critical, n_noncritical}), a structured `ibr_gate` object ({tool, result, zone_gfl_penetration_pct_post_expansion, gfl_headroom_mw, gfm_mw_needed, raw_block_or_violation_messages}), `decision_rule_applied` and `tool_brief_discrepancies`. None of these fields exists in `result.json`; the values appear only as prose in `rationale`/`evidence`, and `decision_rule_applied` appears only in RESULT.md's "Decision rule:" lines. Consequence: criterion 5 ("a reviewer who re-applies D1–D4 to the recorded fields must reach the same status") and criterion 3 (traceability) cannot be evaluated, because the fields the rules would be applied to do not exist.

**Fix:** restructure each item into the criterion-2 schema, populating every field verbatim from the saved tool outputs (IR-2 example: `n11` = {tool, screening_complete: true, source: "supplied_summary", pairs_screened: 3, violations: [{pair: "L-201|L-202", element: "L-203", metric: "branch_loading_pct", value: 131.0, severity_as_returned: "HIGH", counted: true}], n_critical: 0, n_noncritical: 1}; `ibr_gate` = {tool, result: "PASS", zone_gfl_penetration_pct_post_expansion: 17.778, gfl_headroom_mw: 78.571, gfm_mw_needed: 0, raw_block_or_violation_messages: []}; `decision_rule_applied` = "D4.4"; `tool_brief_discrepancies` = []), repeating for IR-1, IR-3, IR-4 and IR-5 with their own outputs.

### C3 — IR-3 has no `blocked_reason` field (`major`, IR-3)

The status is `blocked` but there is no `blocked_reason` field, which criterion 2 requires for any blocked item. The value `ibr_gate_gfl_threshold` appears only inside the `rationale` prose. The gate evidence itself is accurate — my re-run reproduced the quoted block message exactly, with `result=null` and no structured zone_assessment.

**Fix:** add `blocked_reason` to the IR-3 item (value per C5), and put the raw block message into `ibr_gate.raw_block_or_violation_messages` so the 34.8% and 60 MW GFL figures are structured evidence rather than prose.

### C4 — IR-2 has no `conditions` field (`major`, IR-2)

The status is `approve_with_conditions` but there is no `conditions` array, which criterion 2 requires to be non-empty for this status. The corrective action exists only as prose (the rationale's "implement and verify an operating limit or remedial action scheme… then rerun the screen" and RESULT.md's "Required condition" bullet). The violation it responds to is real and correctly quoted, and the status is right; only the structured field is missing.

**Fix:** add a non-empty `conditions` array — one entry per counted violation, naming the element (L-203), the quoted value (131.0%), the outage pair (L-201 → L-202) and the corrective action, ordered by cost and time per D4.4 (operating limit or RAS, then switching, then protection, then FACTS, then reconductoring, then new transmission). Keep the "rerun the screen to verify" requirement.

### C5 — IR-3's recorded decision rule does not match a literal in-order application of D4 (`minor`, IR-3)

The deliverable records D4.2 / `ibr_gate_gfl_threshold`. But D4 says "apply in order and stop at the first match", and D4.1 fires whenever G1 or G2 fails. G2's conditions are: the call returned without error; a GFL penetration value is returned for the item's zone; the gate result is PASS under D2. For IR-3 the call returned an error, no structured zone_assessment was returned, and D2's result is BLOCK — so G2 fails on the first and third conditions and D4.1 gives `blocked_reason` = "tool_failure_or_incomplete_screen". The executor's choice is defensible (the brief's own `blocked` definition describes IR-3 exactly, and the error text does carry the 34.8% figure), and the status is `blocked` either way — but on the literal reading D4.2 can never fire with this tool, since every gate BLOCK arrives as an error with `result=null`. The plan is internally tense here and the deliverable does not say which reading was used or why.

**Fix:** either record `decision_rule_applied` = "D4.1" with `blocked_reason` = "tool_failure_or_incomplete_screen", or keep D4.2 / "ibr_gate_gfl_threshold" and add one sentence stating that the gate's BLOCK message is treated as valid domain evidence (it returns the post-expansion penetration and the GFL MW figure), waiving G2's error-return condition and noting the plan tension. Do not change the status.

### C6 — G1's "screened pairs = 3" condition is reconciled but not recorded (`minor`, overall)

G1 is marked "pass" with the detail "Each returned n_pairs=6 because both directions are listed for the three supplied outage-pair keys", but G1 as written requires "the number of screened pairs = 3". The tool returns `n_pairs=6`; my re-runs confirm the six ordered entries cover exactly the three supplied pair keys in both directions, with `computed_pairs=0`, `unscreened_pairs=[]`, `screening_complete=true` and `source=supplied_summary`. The reconciliation is sound — but the 3-vs-6 mismatch is recorded nowhere, and the `pairs_screened` field that would make it visible to a reviewer does not exist in `result.json`.

**Fix:** record `pairs_screened` = 3 (the supplied pair summaries screened) in each item's `n11`, note that the tool enumerates them as 6 ordered entries (`n_pairs=6`, `computed_pairs=0`, `unscreened_pairs=[]`), and add a `tool_brief_discrepancies` entry (or explicit note) documenting the difference so G1's pass is auditable rather than asserted.

### C7 — G3 disclosures are not carried per item (`minor`, overall)

G3 states the disclosures are "required for every item, and required in the outputs". The three warnings appear globally (RESULT.md's "Required warnings" blockquote, `limitations[0]`/`limitations[1]`) but are not carried in any item record. Only IR-1 and IR-5 carry item-level caveats; IR-2, IR-3 and IR-4 carry none.

**Fix:** repeat the disclosure line ("N-1 not checked; N-0 power flow not run; SCR not assessed (no short-circuit data); NERC TPL-001-4 P6/P7 planning screen only") in each item object (e.g. a `disclosures` field, or a reference to the global `warnings` array) and in each RESULT.md item section.

### C8 — the required 10-call record is not in the deliverable (`minor`, overall)

Criterion 4 requires "exactly 10 domain tool calls are recorded (5 screen + 5 gate), each called with the item's own inputs". `result.json` records only per-item `tools_used` name lists — no call record, no input echo, no saved raw output — so the "each called with the item's own inputs" half cannot be audited from `result.json` alone. I re-ran all ten calls with the plan's exact inputs and reproduced every reported number and severity, so the work was done correctly; the gap is the missing record, not missing analysis. The `evidence` strings, which quote the tool outputs, partially compensate.

**Fix:** add a `calls` array of 10 entries (item id, tool, and the key inputs actually passed: contingency ids, the three pair keys, the addition's id/type/capacity_mw/zone, `threshold_pct=30`), or embed the same information in each item's `n11` and `ibr_gate` blocks, and retain the saved raw tool outputs alongside `result.json` so traceability is checkable.

### C9 — the unqualified 0.95 confidence reads as endorsement of an unconformant file (`minor`, overall)

`result.json` carries `"confidence": 0.95` with no qualifier, and neither `result.json` nor `RESULT.md` says anything about conformance to the plan's acceptance criteria. The five dispositions do deserve high confidence — I re-ran all ten calls and every number and severity reproduced — but the deliverable is not conformant to its own schema (C1–C4), so a reader taking `confidence` at face value would read the file as complete when acceptance criteria 1, 2, 3 and 5 are unmet. The confidence claim covers the dispositions but is presented as covering the deliverable. Relatedly, `overall_verdict` asserts "none of these dispositions establishes N-0, N-1, SCR, or time-domain stability compliance", which is appropriately hedged; the schema-level omissions are hedged nowhere.

**Fix:** qualify the confidence field (e.g. "confidence in the five dispositions: 0.95; schema conformance to PLAN.md acceptance criteria: unmet, see critique findings C1–C4") or add a short conformance note to `result.json` and `RESULT.md` stating which acceptance criteria are satisfied and which are not, so the 0.95 is not read as an endorsement of the file's completeness.

## Overall assessment

The engineering substance of this deliverable is sound and I could not break any of its numbers: re-running all ten domain calls with the plan's exact inputs reproduced every quoted value, severity label and limit — the IR-2 HIGH thermal finding at 131.0%, the IR-3 Z-SOUTH block at 34.8%, the IR-4 boundary case returning exactly 30% with zero violations, and the IR-5 CRITICAL stability loss — and each of the five statuses follows correctly from the evidence under the brief's precedence rules. That is the part that matters most, and it is right. What the deliverable fails is its own contract rather than the physics: `result.json` is a prose-and-evidence document where PLAN.md's acceptance criteria specify a structured, machine-checkable schema, so four required top-level fields and six per-item fields are absent (C1, C2), the two items whose statuses require mandatory companion fields — IR-3's `blocked_reason` and IR-2's `conditions` — carry those only as narrative (C3, C4), and four smaller conformance gaps remain unrecorded (C5's decision-rule ambiguity on IR-3, C6's 3-vs-6 pair reconciliation, C7's per-item disclosures, C8's missing 10-call record), with C9 the unqualified 0.95 confidence reading as endorsement of an unconformant file. None of these findings changes a status, so the planning committee's per-request dispositions stand; but the deliverable is not yet in the shape that a downstream reviewer can re-apply D1–D4 to, and criterion 5 is therefore unmet until the schema gaps are closed. Because the fixes are reshuffles of values already present and verified, they carry no risk of introducing hand-computed numbers (BRIEF Rule 6 remains satisfied).

— Critic, TOKN relay stage 6/7, `powergrid` domain.
