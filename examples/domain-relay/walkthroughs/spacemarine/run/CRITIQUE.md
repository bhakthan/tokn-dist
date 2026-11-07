# CRITIQUE — spacemarine pre-pass go/no-go review

Critic stage. I re-ran every tool whose output decides a status:

- `orbit_propagate` for all five satellites, using the exact input records.
- `link_budget_calc` for all five, using the exact input records.
- `debris_compliance_check` for all five, with `IADC` and `compliant = lifetime <= 25`.
- `tle_omm_fetch` for all five, with `start_time = 2025-06-10T06:00:00Z`. I derived that time from SAT-1's epoch (2025-06-09T12:00Z) plus its supplied 18 h age.

**Re-run outcomes.**

| Sat | orbit_propagate | link_closes / margin | debris | Correct status | Result's status |
|---|---|---|---|---|---|
| SAT-1 | accepted, checksums false/false | true / 7.4 (supplied_evidence) | compliant=true, computed=false | go (D5) | go ✔ |
| SAT-2 | accepted at 72 h, checksums false/false | true / 3 (supplied_evidence) | compliant=true, computed=false | go (D5) | go ✔ |
| SAT-3 | **blocked**: "TLE epoch age 96.5 hours exceeds maximum 72.0 hours" | true / 11.2 (info only) | compliant=true (info only) | hold (D1a) | hold ✔ |
| SAT-4 | accepted, checksums false/false | **false** / 2.9 | compliant=true, computed=false | no_go (D2b) | no_go ✔ |
| SAT-5 | accepted, checksums false/false | true / 6.1 | **blocked**: non-compliant per IADC | no_go (D2c) | no_go ✔ |

All five statuses and every reported number match my re-runs. The findings below are about schema, missing inputs or outputs, and overconfidence.

## Findings

**C1 — overall — major.** result.json does not follow the PLAN.md acceptance schema.
- Missing top-level keys: `summary`, `deviations`, `gates_not_assessed`, `caveats`.
- Missing on every item: `decision_rule`, `reasons`, `informational_only`, and the structured `orbit`/`link`/`disposal` objects.

Without these, a second reviewer cannot re-apply D1–D6 from result.json.
*Fix:* re-emit result.json in the plan's schema, including the two mandated caveat strings, the summary arrays, and null for fields the tool did not return.

**C2 — SAT-4 — major.** The input epoch age does not match the TLE epoch. `tle_omm_fetch` with the derived review time (2025-06-10T06:00Z) gives `epoch_age_hours=38`; the input says 20.0. The same review time reproduces SAT-1, SAT-2 and SAT-3 exactly (18, 72, 96.5). The status is unchanged because 38 h is still under 72 h. But RESULT.md says no cross-check was possible, and that is false.
*Fix:* add a caveat and a deviation, and request confirmation of the orbit-state provenance.

**C3 — SAT-5 — major.** Same problem as C2. The TLE epoch implies `epoch_age_hours=58`; the input says 40.0. The status is unchanged.
*Fix:* report it together with C2.

**C4 — SAT-1 — major.** SAT-1 is `go` while both TLE lines fail checksum (`checksum_line1_ok=false`, `checksum_line2_ok=false` in both `orbit_propagate` and `tle_omm_fetch`). The orbit gate is reported as a plain "pass", the rationale does not mention the checksums, and the Step 0 check was skipped.
*Fix:* make the `go` conditional on confirming TLE integrity, add `tle_check`, and add a deviation.

**C5 — SAT-2 — major.** SAT-2 sits at every boundary at once:
- margin exactly 3.0 dB (`margin_db=3`, `min_margin_db=3`, supplied_evidence, computed=false), so no headroom;
- TLE age exactly 72 h, so no freshness left;
- both TLE checksums false.

The result still reports it at the same 0.9 confidence. By tomorrow's pass the TLE will be stale.
*Fix:* keep `go`, flag it as boundary-only, and recommend a fresh TLE before the pass.

**C6 — SAT-3 — minor.** The `hold` is confirmed. However, `tle_omm_fetch` shows `checksum_line1_ok=true` and `checksum_line2_ok=false`, which the result does not report. The structured `informational_only=true` field is also missing.
*Fix:* add both.

**C7 — overall — major.** Confidence 0.9 overstates the evidence:
- Every link margin is supplied evidence (computed=false; G/T, atmospheric loss, data rate and Eb/N0 are missing).
- No disposal lifetime was computed.
- 8 of the 10 TLE lines fail checksum.
- Two epoch ages are inconsistent (C2, C3).

The debris "pass" is also circular: the tool just echoes the `compliant=true` that the caller passed in.
*Fix:* split confidence into high confidence in rule application and low confidence in the gate evidence, and reword the debris evidence.

**C8 — overall — major.** The Grounding gate is "pass" without enough evidence. No grounding output is saved, and many citations quote field names rather than the values they are meant to support:
- `"supplied_epoch_age_hours"` is cited for the 72 h and 20 h ages;
- `"supplied_evidence"` is cited for the dB values;
- `"LEO (IADC region A…)"` is cited for compliance.

The SAT-5 orbit claims have no citation at all.
*Fix:* re-cite with value-bearing quotes, save the grounding check output, and qualify the gate status until then.

**C9 — overall — minor.** The aggregate Orbit, Link and Debris gates are marked "fail", which contradicts the two `go` items that pass all of them. The PLAN defines gates per satellite.
*Fix:* report the gates per satellite, or label the aggregate "mixed".

**C10 — overall — minor.** Some tool outputs and one input caveat are missing from the result:
- `fspl_db` values (177.171, 177.961, 176.301, 178.331, 177.575 dB);
- the `requires` lists;
- `post_mission_perigee_km` and `post_mission_apogee_km`, which equal the operational altitude, so no disposal manoeuvre was modelled (for example, SAT-3's perigee lowering was assessed at 525 km);
- a note that `atmospheric_model` is a label the tool does not use.

*Fix:* record these outputs and add the caveats.

**C11 — SAT-4 — minor.** The `no_go` is confirmed (`link_closes=false`, "[HIGH] Link margin 2.9 dB below minimum 3.0 dB — link may not close"). result.json has no `reasons` or `decision_rule` showing that D2a and D2c were checked and do not apply.
*Fix:* add `reasons:["link_margin_below_3db"]` and `decision_rule:"D2b"`.

**C12 — SAT-5 — minor.** The `no_go` is confirmed (blocked: "Disposal plan non-compliant per IADC — debris gate remains blocked until remediation"). The structured reasons are missing, and the orbit paragraph has no citation.
*Fix:* add `reasons:["disposal_noncompliant"]` and `decision_rule:"D2c"`, and cite the orbit-sat5 output.

## Overall assessment

The statuses are correct. My independent re-runs reproduce go/go/hold/no_go/no_go, and every reported number matches the tool outputs. The weaknesses are in how the result is packaged and how confident it sounds:

- **Schema.** result.json ignores the PLAN's acceptance schema (no summary, deviations, decision_rule or structured tool objects), so it cannot be audited mechanically.
- **Unreported inconsistencies.** The result says the epoch ages could not be cross-checked. A cross-check derived from the TLE epochs shows SAT-4 and SAT-5 are inconsistent with their own TLEs (38 h vs 20 h and 58 h vs 40 h).
- **Weak evidence behind the two `go` items.** They rest on TLEs that fail checksum, on supplied rather than computed link margins (SAT-2 has exactly 0 dB headroom and 0 h of freshness left), and on a debris check that only echoes the caller's compliant flag.
- **Overstated assurance.** The 0.9 confidence and the "verified" grounding gate claim more than the evidence supports.

The result is usable for its status calls once those calls are labelled as mechanically valid but conditional. Before planning from them, operations should get a fresh, checksum-valid TLE (at least for SAT-2), check where the SAT-4 and SAT-5 orbit states came from, and complete the result.json schema.
