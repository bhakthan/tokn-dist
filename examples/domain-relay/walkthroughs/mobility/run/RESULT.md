# DRAFT functional-safety gate report — mobility

**DRAFT — pending safety-manager review. Not a release authorization or proof of safety.**

## Evidence and method

Independent reruns of the applicable domain tools reproduced every original item status. The deciding order is decomposition, hardware metrics, then V&V completion; the first failure sets the item status. Later checks remain informational.

Full corrected live responses or full errors are preserved in `result.json` at `items[].raw_evidence.<tool>.<function>`. Input evidence lists, safety requirements, safety-case goals and element failure rates are recorded in each item's `input_trace`, with complete source records retained in `inputs/`.

All hardware calls returned programme targets **PMHF ≤10 FIT, SPFM ≥99%, LFM ≥90%**. The ASIL-D AEB/LKA/TJA calls supply the applied targets; ACC/APA returned identical programme targets. V&V requires coverage **≥95%** and **0 open defects**. Equality passes under the brief.

## Item outcomes

| Item | Status | Deciding rule | PMHF FIT | SPFM % | LFM % | Coverage % | Open defects |
|---|---|---|---:|---:|---:|---:|---:|
| FN-AEB | `release_candidate` | R1 | 6.2 | 99.4 | 92.1 | 97.4 | 0 |
| FN-LKA | `decomposition_invalid` | D1a | 3.1 | 99.7 | 96.0 | 99.1 | 0 |
| FN-ACC | `release_candidate` | R1 | 8.0 | 99.0 | 90.4 | 95.0 | 0 |
| FN-TJA | `hw_metrics_fail` | H3 | 7.5 | 98.9 | 91.0 | 96.8 | 0 |
| FN-APA | `vv_incomplete` | V1 | 4.0 | 99.2 | 93.5 | 98.0 | 1 |

**Computed status summary:** 2 release candidates, 1 decomposition invalid, 1 hardware failure and 1 V&V incomplete; total 5 items.

### FN-AEB — `release_candidate`

**R1: D2, H5 and V3 all held. DRAFT — pending safety-manager review.** The decomposition verifier accepted the input, reporting child rank sum 5 against parent D rank 4, four independence claims and a DFA reference. Hardware and V&V values passed the programme rules above; V&V returned a DRAFT summary with 3 evidence items.

**Scheme discrepancy:** returned `matched_scheme=C(D)+A(D)` does not correspond to returned children B+C or the input requirements B(D)+C(D). The tool states a rank-sum acceptance method. Its acceptance is not independent verification of a canonical ISO decomposition; safety-manager review is required.

Input safety requirement: **SG-AEB-01**, “Avoid unintended full braking at speeds above 10 km/h”. Input safety-case top goal: “FN-AEB is acceptably safe within its ODD” — an unverified input assertion.

Evidence list: HIL campaign HIL-AEB-12; track test TT-AEB-07; SIL regression SIL-AEB-31. Element rates: fusion ECU 210 FIT, radar monitor 95 FIT, brake interface 40 FIT; tool-returned total **345 FIT**. This total does not re-derive the FMEDA metrics.

### FN-LKA — `decomposition_invalid`

**D1a:** the verifier returned the full error:

> asil_decompose_verify: ASIL decomposition invalid — child ASILs [B A] (sum 3) do not cover parent D (4) per ISO 26262-9 §5

The later hardware and V&V passes are informational only. V&V returned 3 evidence items and DRAFT status. Its snapshot does not override the direct decomposition rejection.

Input safety requirement: **SG-LKA-01**, “Avoid unintended steering torque above 3 Nm”. Input safety-case top goal: “FN-LKA is acceptably safe within its ODD” — an unverified input assertion.

Evidence list: HIL campaign HIL-LKA-09; proving-ground test PG-LKA-04; SIL regression SIL-LKA-22. Element rates: controller 180 FIT, limiter 60 FIT, sensor 35 FIT; tool-returned total **275 FIT**.

### FN-ACC — `release_candidate`

**R1: D2, H5 and V3 all held. DRAFT — pending safety-manager review.** The verifier accepted B(C)+A(C), with child rank sum 3 against parent C rank 3, three independence claims and a DFA reference. Hardware passed, including SPFM **99.0% at equality**. V&V accepted coverage **95.0% at equality**, 0 open defects and 2 evidence items.

ASIL-D programme targets were applied to input ASIL C as directed by the brief. Separate tool ISO targets were PMHF **<100 FIT**, SPFM **≥97%**, LFM **≥80%**; they did not determine this status.

Input safety requirement: **SG-ACC-01**, “Avoid unintended acceleration above 2 m/s^2”. Input safety-case top goal: “FN-ACC is acceptably safe within its ODD” — an unverified input assertion.

Evidence list: HIL campaign HIL-ACC-15; road test RT-ACC-11. Element rates: controller 150 FIT, monitor 70 FIT; tool-returned total **220 FIT**.

### FN-TJA — `hw_metrics_fail`

Decomposition was mechanically accepted, reporting child rank sum 5 against parent D rank 4, three independence claims and a DFA reference. **H3:** SPFM **98.9% <99%** fails, although PMHF and LFM pass. The later V&V pass is informational and returned 2 evidence items.

**Scheme discrepancy:** returned `matched_scheme=C(D)+A(D)` does not correspond to returned children C+B or the input requirements C(D)+B(D). The tool states a rank-sum method; this is not independent verification of a canonical ISO split.

Input safety requirement: **SG-TJA-01**, “Avoid unintended lateral or longitudinal motion in traffic-jam assist”. Input safety-case top goal: “FN-TJA is acceptably safe within its ODD” — an unverified input assertion.

Evidence list: HIL campaign HIL-TJA-06; scenario catalogue run SC-TJA-03. Element rates: planner 260 FIT, supervisor 85 FIT, gateway 45 FIT; tool-returned total **390 FIT**.

### FN-APA — `vv_incomplete`

The verifier accepted A(B)+A(B), with child rank sum 2 against parent B rank 2, three independence claims and a DFA reference. Programme hardware metrics passed. **V1:** the fresh V&V call returned:

> safety_validation_report: 1 open defects remain — all safety-critical defects must be resolved before V&V completion

Coverage input is 98.0%; one open defect blocks completion. The historical retry claim has been removed; the recorded error alone supports V1. No later check follows this deciding failure, so `informational_after_failure=false`; the earlier passes are prerequisites, not later informational results. The error returned no evidence tally, so the JSON tool-derived evidence count is null.

ASIL-D programme targets were applied to input ASIL B. Separate tool ISO targets were PMHF **<100 FIT**, SPFM **≥90%**, LFM **≥60%**, not used for the decision. Input `safety_case.open_goals=1` is a review flag, not a deciding field under the brief.

Input safety requirement: **SG-APA-01**, “Avoid unintended vehicle motion above 7 km/h during automated parking”. Input safety-case top goal: “FN-APA is acceptably safe within its ODD” — an unverified input assertion.

Evidence list: HIL campaign HIL-APA-05; parking-lot test PL-APA-02. Element rates: controller 120 FIT, limiter 50 FIT; tool-returned total **170 FIT**.

## Gate roll-ups and overall verdict

These labels are explicit **release-set roll-ups**, not additional per-item rules or blanket failures:

| Gate | Roll-up | Scope |
|---|---|---|
| ASIL Decomposition | Fail: 1 rejected check out of 5 | LKA rejected; four mechanically accepted. |
| Hardware metrics | Fail: 1 failed check out of 5 | TJA SPFM fails; LKA hardware is informational. |
| V&V | Fail: 1 rejected check out of 5 | APA open defect; LKA/TJA passes are informational. |
| HARA | n/a | Not assessed. |
| Safety Concept | n/a | Not assessed; snapshots are not independent reviews. |
| Release | n/a | Not authorized or assessed. |

AEB and ACC remain **DRAFT release candidates pending safety-manager review**. LKA, TJA and APA remain blocked by their first failing gates. These results do not establish vehicle safety or authorize release.

## Confidence, limitations and discrepancies

**Assessed confidence: 0.98, only in reproducibility and ordered mechanical statuses conditional on the supplied synthetic inputs.** This is not a probability that the functions are safe, nor confidence in substantive independence, DFA, FMEDA or V&V evidence quality.

- Inputs are explicitly synthetic teaching-scenario records.
- Independence and DFA completion are input claims. The verifier counts claims and keyword-matches DFA references; it does not verify independence or freedom from interference.
- FMEDA values are supplied summaries, not recomputed. Failure-mode classification and lifetime data needed for re-derivation are absent. Element-rate totals do not validate the supplied metrics.
- V&V content is counted, not verified. Illustrative report paths were not opened or checked for existence. Input safety-case top goals are not conclusions of this review.
- The README's strict PMHF **<10 FIT** differs from the applied programme **≤10 FIT** rule. No supplied PMHF equals that boundary, so no outcome changes. SPFM/LFM README targets agree with programme targets.
- Per-ASIL versus programme target differences for ACC/APA are recorded above. The brief directs ASIL-D targets for all items; safety-manager confirmation remains appropriate.
- Explicit H2 comparisons agree with all tool hardware verdicts. No notation-related errors or accepted-V&V versus brief-rule mismatch occurred. AEB/TJA label-versus-children mismatches remain explicit review flags.
- HARA, Safety Concept and Release are not assessed.

**Relay-owner layout conflict:** readable PLAN.md acceptance criteria request extra top-level `evidence`, `applied_targets`, `discrepancies` and `summary` keys; the reviser instruction requires the same shape as before. This revision preserves existing top-level keys and types. Full raw objects are stored in `items[].raw_evidence.<tool>.<function>`; targets are in the hardware gate, counts in the Release gate, and `limitations` explicitly serves as the discrepancies record. Planned per-item fields are now explicit. This disclosed substitution does not claim exact PLAN.md schema compliance.

Initial reviser decomposition/hardware calls included the function label; corrected calls omitted it per G1. Recorded responses are from corrected calls, with unchanged outcomes. No values were changed to obtain a pass. The original APA retry claim is not asserted.

**Verification gap:** Both files were read back after writing. `review_artifact` reported missing producing code and code–artifact provenance; this report was directly authored from live responses, not generated by recorded executable code. That reproducibility-envelope check did not pass. No automated validation pass is claimed.

## Response to critique

- **C1 — fixed:** Added deciding rules to every item; both positive rationales explicitly name R1 with D2/H5/V3. Verified against readable plan rules and fresh gates.
- **C2 — fixed:** Recorded full corrected live responses/errors for every applicable call in item-level raw evidence and surfaced the plan-versus-required-shape conflict. Raw evidence replaces paraphrase as the auditable basis.
- **C3 — fixed:** Removed unsupported historical APA retry claim. A fresh V&V call independently reproduced the recorded open-defect error; V1 needs no retry assertion.
- **C4 — fixed:** Fresh AEB/TJA calls reproduce the scheme-label mismatch. Added explicit flags and limited the claim to tool rank-sum acceptance, not independent canonical ISO validation.
- **C5 — fixed:** Explicitly designated `limitations` as the discrepancies record. Direct README reading and fresh tools verify the threshold differences and absence of H2/notation/V&V acceptance mismatches.
- **C6 — fixed:** Recorded applied targets with source calls in the hardware gate and computed status counts in the Release gate, preserving top-level shape.
- **C7 — fixed:** Added draft, flags and informational-after-failure fields. LKA/TJA are true; APA is false because no later check follows its V&V failure, contrary to the critic's suggested value and consistent with the plan definition.
- **C8 — fixed:** Recorded all evidence lists, requirement ids/texts, safety-case goals, element rates and independently reproduced hardware totals in the deliverables.
- **C9 — fixed:** Explicitly labelled gate outcomes as release-set roll-ups with the affected-item counts; retained n/a for unassessed gates.
- **C10 — fixed:** Qualified confidence as mechanical-status reproducibility given synthetic inputs, not vehicle safety or unverified evidence quality; removed the historical retry claim.
