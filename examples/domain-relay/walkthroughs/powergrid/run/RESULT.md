# Cluster 7 interconnection screen — IR-1 through IR-5

**Study:** Cluster 7 interconnection queue — summer peak 2029, N-1-1 (NERC TPL-001-4 P6/P7)  
**Governing screen:** NERC TPL-001-4 P6/P7, using the supplied post-contingency pair summaries  
**IBR gate:** IEEE 2800 GFM/GFL penetration screen, `threshold_pct=30`  
**Scope:** Planning-screen dispositions only; not regulatory filings or final interconnection approvals.

> **Required warnings:** **N-1 not checked. N-0 power flow not run. SCR not assessed (no short-circuit data).** The network model was unavailable, so this study does not establish base-case convergence, per-unit consistency, power balance, NERC TPL P1–P5 N-1 compliance, SCR/WSCR, or grid-strength class. No MVA or bus kV base is supplied; per-unit consistency cannot be verified. Voltage values are quoted only as supplied screening limits, not independently solved physical voltages. Physical kV/A conversions are unavailable.

## IR-1 — `approve`

**Item disclosures:** N-1 not checked; N-0 power flow not run; SCR not assessed (no short-circuit data); NERC TPL-001-4 P6/P7 planning screen only; not a regulatory filing or final interconnection approval.

**Decision rule:** D4.5. **G1:** pass. **G2:** pass.

- **N-1-1 evidence:** `powergrid_n1_1_screen` returned `computed=true`, `screening_complete=true`, `source=supplied_summary`, `unscreened_pairs=[]`, `n_violations=0`, and `violations=null`. It returned `n_pairs=6`, listing both directions of the three supplied summary pairs, with `computed_pairs=0`.
- **Returned limits:** `thermal_limit_pct=115`, `voltage_min_pu=0.85`, `voltage_max_pu=1.1`; standard `NERC TPL-001-4 P6/P7`.
- **IBR evidence:** `powergrid_ibr_stability_gate` returned `blocked=false`, `violations=null`, and `expansion_issues=null`. For **Z-NORTH**, post-expansion `gfl_penetration_pct=12.5`, `gfl_headroom_mw=100`, `gfm_needed_mw=0`, and `over_threshold=false`.
- **Disposition:** The clean, complete supplied-summary screen and passing GFM/GFL gate support `approve` at this planning-screen stage. This is not a final interconnection or N-0/N-1 reliability approval.

## IR-2 — `approve_with_conditions`

**Item disclosures:** N-1 not checked; N-0 power flow not run; SCR not assessed (no short-circuit data); NERC TPL-001-4 P6/P7 planning screen only; not a regulatory filing or final interconnection approval.

**Decision rule:** D4.4. **G1:** pass. **G2:** pass.

- **N-1-1 evidence:** The screen returned `computed=true`, `screening_complete=true`, `source=supplied_summary`, `unscreened_pairs=[]`, and `n_violations=1`. Its `n_pairs=6` output lists both directions of the three supplied summary pairs.
- **Violation, severity as returned:** **HIGH** — “L-203 at 131.0% > 115% emergency rating after L-201 → L-202”; `kind=thermal`, pair `L-201|L-202`.
- **IBR evidence:** The gate returned `blocked=false`, `violations=null`, and `expansion_issues=null`. For **Z-EAST**, post-expansion `gfl_penetration_pct=17.778`, `gfl_headroom_mw=78.571`, `gfm_needed_mw=0`, and `over_threshold=false`.
- **Required condition:** Before unconditional approval, implement an operating limit or remedial action scheme (RAS) that keeps **L-203 at or below 115%** for the **L-201 → L-202** sequence, and verify it by rerunning the N-1-1 screen. If that operational measure is not effective, escalation to switching or a topology/reinforcement study is required before approval.

## IR-3 — `blocked`

**Item disclosures:** N-1 not checked; N-0 power flow not run; SCR not assessed (no short-circuit data); NERC TPL-001-4 P6/P7 planning screen only; not a regulatory filing or final interconnection approval.

**Decision rule:** D4.2. **Blocked reason:** `ibr_gate_gfl_threshold`. **G1:** pass. **G2:** fail (explicit domain gate block).

- **IBR evidence:** `powergrid_ibr_stability_gate` returned the following domain block in its error field, with `result=null`:
  > [BLOCK] zone Z-SOUTH: expansion adds 60 MW GFL with no GFM — post-expansion GFL penetration 34.8% exceeds 30.0% threshold. Add GFM capacity (or synchronous condensers) before approving.
- **N-1-1 evidence:** The screen returned `computed=true`, `screening_complete=true`, `source=supplied_summary`, `unscreened_pairs=[]`, `n_violations=0`, and `violations=null`. Its `n_pairs=6` output lists both directions of the three supplied summary pairs.
- **Plan interpretation:** PLAN D4.1/G2 is internally tense with D4.2: G2 requires an error-free PASS, while this domain tool returns an explicit BLOCK in the error field with result=null. For disposition and cause attribution, this BLOCK message is treated as valid domain evidence returning 34.8% post-expansion GFL and 60 MW added GFL; G2’s error-return condition is waived for that purpose only. G2 remains failed for approval. D4.2 and ibr_gate_gfl_threshold are retained to reflect BRIEF precedence and the actual cause. A literal D4.1 interpretation would also leave the request blocked.
- **Disposition:** The gate block overrides the clean N-1-1 screen under the brief's precedence rule. The request remains `blocked` until a revised resource proposal passes the gate. The tool mentions synchronous condensers, but their equivalence to GFM capacity in this share-based gate is not established and requires separate validated strength/stability evidence; the error-form return supplied no structured Z-SOUTH headroom or GFM-needed assessment.

## IR-4 — `approve`

**Item disclosures:** N-1 not checked; N-0 power flow not run; SCR not assessed (no short-circuit data); NERC TPL-001-4 P6/P7 planning screen only; not a regulatory filing or final interconnection approval.

**Decision rule:** D4.5, with D3 boundary treatment. **G1:** pass. **G2:** pass.

- **N-1-1 evidence:** The screen returned `computed=true`, `screening_complete=true`, `source=supplied_summary`, `unscreened_pairs=[]`, `n_violations=0`, and `violations=null`. Its `n_pairs=6` output lists both directions of the three supplied summary pairs.
- **Boundary evidence:** The returned limits were `thermal_limit_pct=115`, `voltage_min_pu=0.85`, and `voltage_max_pu=1.1`. The supplied **115.0%**, **0.85 pu**, and **1.10 pu** boundary values produced no returned violations, consistent with D3: equality at a limit is not a violation.
- **IBR evidence:** The gate returned `blocked=false`, `violations=null`, and `expansion_issues=null`. For **Z-WEST**, post-expansion `gfl_penetration_pct=30`, exactly the `threshold_pct=30`, with `over_threshold=false`, `gfl_headroom_mw=0`, and `gfm_needed_mw=0`.
- **Disposition:** Exactly 30% GFL penetration does not exceed the threshold, so no gate block applies. The planning-screen disposition is `approve`; the returned zero headroom means this result should not be represented as leaving room for additional GFL capacity.

## IR-5 — `reject`

**Item disclosures:** N-1 not checked; N-0 power flow not run; SCR not assessed (no short-circuit data); NERC TPL-001-4 P6/P7 planning screen only; not a regulatory filing or final interconnection approval.

**Decision rule:** D4.3. **G1:** pass. **G2:** pass.

- **N-1-1 evidence:** The screen returned `computed=true`, `screening_complete=true`, `source=supplied_summary`, `unscreened_pairs=[]`, and `n_violations=1`. Its `n_pairs=6` output lists both directions of the three supplied summary pairs.
- **Violation, severity as returned:** **CRITICAL** — “loss of synchronism / voltage collapse after outage sequence L-501 → L-502”; `kind=stability`, pair `L-501|L-502`.
- **IBR evidence:** The gate returned `blocked=false`, `violations=null`, and `expansion_issues=null`. For **Z-CENTRAL**, post-expansion `gfl_penetration_pct=16.667`, `gfl_headroom_mw=68.571`, `gfm_needed_mw=0`, and `over_threshold=false`.
- **Disposition:** The CRITICAL stability violation requires `reject`; the passing resource-mix gate does not override it. Resubmission should include a validated stability restudy and a corrective operating, RAS, or topology solution demonstrating no loss of synchronism for **L-501 → L-502**. The supplied flag is screening evidence, not a time-domain stability demonstration.

## Gate outcomes

| Gate | Outcome | Evidence-based meaning |
|---|---|---|
| G1 — N-1-1 screen validity | **PASS** | All item calls returned `screening_complete=true`, `source=supplied_summary`, and no unscreened pairs. Each `n_pairs=6` result enumerates both directions of the three supplied pair keys; no network-calculated pairs were substituted (`computed_pairs=0`). |
| G2 — IR-1 IBR gate | **PASS** | Z-NORTH 12.5%; `over_threshold=false`, `blocked=false`. |
| G2 — IR-2 IBR gate | **PASS** | Z-EAST 17.778%; `over_threshold=false`, `blocked=false`. |
| G2 — IR-3 IBR gate | **FAIL** | Explicit Z-SOUTH block at 34.8% against the 30.0% threshold; returned as a tool error with `result=null`. |
| G2 — IR-4 IBR gate | **PASS** | Z-WEST exactly 30%; `over_threshold=false`, `blocked=false`. |
| G2 — IR-5 IBR gate | **PASS** | Z-CENTRAL 16.667%; `over_threshold=false`, `blocked=false`. |
| G3 — Domain disclosures | **WARN** | N-1 not checked; N-0 power flow not run; SCR not assessed (no short-circuit data). NERC TPL-001-4 P6/P7 planning screens only. |

## Overall verdict

IR-1 and IR-4 receive planning-screen `approve` dispositions; IR-2 receives `approve_with_conditions` subject to the stated L-203 operating/RAS corrective action; IR-3 is `blocked` by the Z-SOUTH GFL threshold; and IR-5 is `reject` because of the CRITICAL L-501|L-502 stability violation. These outcomes do **not** establish N-0, N-1, SCR, or time-domain stability compliance.

## Limitations

1. **N-1 not checked; N-0 power flow not run.** The network model was unavailable, preventing independent base-case convergence, per-unit, power-balance, and NERC TPL P1–P5 N-1 checks.
2. **SCR not assessed (no short-circuit data).** `zone_short_circuit_mva` was absent; structured gate outputs reported `grid_strength_assessed=false`. No SCR, WSCR, or grid-strength class is claimed.
3. The N-1-1 analysis uses supplied post-contingency summaries rather than an independently solved network. The IR-5 stability finding uses a supplied `stability_loss` flag, not a time-domain simulation of IBR response.
4. The IR-3 gate returned its block in the error field with `result=null`; no structured zone assessment, GFL headroom, or GFM-needed result was available for that call.
5. Per-unit voltage values cannot be converted to physical kV/A or contingency flows to MW/MVAr without the unavailable network base and branch data.
6. These are planning-screen dispositions under the brief's NERC TPL-001-4 P6/P7 rules, not regulatory filings or final interconnection approvals.

## Evidence and conformance

G1 counts the supplied pair-summary keys, not ordered outage entries. The rerun returned n_pairs=6, computed_pairs=0, screening_complete=true, source=supplied_summary and unscreened_pairs=[]. The three input summaries cover the six enumerated entries by reverse-key reuse. This is a documented interpretation of PLAN G1, not independent proof of sequence-specific equivalence.

The full semantic inputs and transcribed raw outputs of the ten reviser rechecks are in `result.json` → `calls` and `reviser_tool_outputs.json`. No unavailable network or short-circuit data was substituted. Original fields are retained with structured evidence added. The required top-level and item fields, per-item disclosures, conditions, blocked reason and ten input/output recheck records are now present. G1 pair-count normalization and IR-3 D4.2/G2 interpretation are explicitly documented; literal unqualified PLAN conformance is not claimed for these internal tensions. Counts are derived from recorded lists. All reported physical assessments reproduce the reviser domain reruns. The record contains ten reviser rechecks, not a claim that the entire multi-stage relay made only ten calls.

The retained confidence value is an inherited, subjective estimate for the five planning-screen dispositions only, not a calibrated probability or a measure of deliverable completeness, physical reliability, or regulatory compliance.

## Response to critique

- **C1 — fixed:** Added study, standard, threshold_pct and warnings after checking both input files and the reproduced tool standard/threshold.
- **C2 — fixed:** Added zone, structured n11 and ibr_gate evidence, decision_rule_applied, conditions and discrepancy lists to every item without removing the original fields. All request screens and gates were rerun independently; statuses and returned severities reproduced.
- **C3 — fixed:** Added IR-3 blocked_reason=ibr_gate_gfl_threshold and the complete raw block message. The rerun returned result=null and Z-SOUTH 34.8% with 60 MW added GFL; unavailable headroom and GFM-needed fields are null, not invented.
- **C4 — fixed:** The IR-2 rerun returned one HIGH L-203 thermal violation at 131.0%. Added a non-empty conditions array requiring an operating limit or validated RAS and a verification restudy.
- **C5 — fixed:** Retained D4.2 and the physical threshold cause, explicitly stating the limited waiver of G2 error-return validity for cause attribution. The gate remains failed for approval; literal D4.1 also gives blocked. No status changed.
- **C6 — fixed:** Each rerun returned six ordered entries, zero computed pairs, complete supplied_summary coverage and no unscreened pairs. Recorded pairs_screened as the count of supplied keys, with the ordered count and an explicit G1 interpretation note; reverse-key reuse does not independently validate outage-order equivalence.
- **C7 — fixed:** Added the required N-1, N-0, SCR and planning-only disclosures to every JSON item and every report item section.
- **C8 — fixed:** Recorded ten reviser domain rechecks with complete actual semantic inputs and transcribed raw output envelopes in result.json calls; the same records are saved in reviser_tool_outputs.json. Full existing resources plus only each request’s additions were used. This is a reviser-stage call count, not a relay-wide count.
- **C9 — fixed:** Qualified the inherited confidence as a subjective disposition-only estimate and added a conformance note documenting repaired fields and the remaining explicit PLAN interpretations, rather than claiming literal unconditional conformance.
