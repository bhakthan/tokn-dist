# Spacemarine — final pre-pass review

## Evidence and decision

All mandatory orbit, link and debris calls were independently re-run for every satellite with the supplied numerical records. All five standalone TLE checks were also run. The scenario statuses are unchanged; the evidence-quality qualifications are materially revised. The brief governs: stale orbit state takes precedence, and the link and declared-lifetime thresholds are inclusive.

| Satellite | Orbit call / supplied age | Link tool outcome / supplied margin | Declared disposal lifetime / call outcome | Status and rule |
|---|---|---|---|---|
| SAT-1 | accepted; 18 h | true; 7.4 dB | 6.2 years; accepted | **go / D5** [src:sat1#0-533] |
| SAT-2 | accepted; 72 h | true; 3 dB | 11 years; accepted | **go / D5** [src:sat2#0-532] |
| SAT-3 | refused_stale; 96.5 h | true; 11.2 dB (informational only) | 4.1 years; accepted (informational only) | **hold / D1a** [src:sat3#0-548] |
| SAT-4 | accepted; 20 h | false; 2.9 dB | 9.5 years; accepted | **no_go / D2b** [src:sat4#0-541] |
| SAT-5 | accepted; 40 h | true; 6.1 dB | 25.4 years; blocked | **no_go / D2c** [src:sat5#0-540] |

Every orbit record declares delta-v closure. Every link outcome uses `supplied_evidence` with `computed=false`; “true” predicts closure under the brief, not an independent full-budget verification. Debris acceptance echoes caller-declared compliance derived from the input lifetime; it does not independently establish IADC compliance. Missing output fields remain null in `result.json`.

## Per-satellite conclusions

### SAT-1 — go

D5 under the brief: orbit accepted at supplied 18 h with delta-v closure, supplied 7.4 dB link closes, and declared 6.2-year lifetime passes the input-based rule. Both TLE checksums fail. Operational use of this scenario go remains conditional on TLE integrity confirmation; disposal compliance was not independently computed. [src:sat1#0-533]

### SAT-2 — go

D5 at the inclusive 72 h and 3.0 dB boundaries. The supplied margin has zero headroom above the minimum and the TLE has no remaining freshness allowance. Both checksums fail. Request a fresh, integrity-confirmed TLE before the later pass. Disposal screening accepts the caller-declared 11-year lifetime, not an independent decay calculation. [src:sat2#0-532]

### SAT-3 — hold

D1a: propagation refused at 96.5 h. Request a fresh TLE. Link and disposal records are informational only. Standalone checksums: line 1 true, line 2 false. [src:sat3#0-548]

### SAT-4 — no_go

D2b: supplied 2.9 dB margin yields link_closes=false. Delta-v closes and declared 9.5-year lifetime passes the brief rule, so no other no_go reason applies. Supplied age 20 h differs from cross-check 38 h; both are within 72 h. Both checksums fail. [src:sat4#0-541]

### SAT-5 — no_go

D2c: declared 25.4-year lifetime exceeds 25 years; compliant=false produces a blocked debris call, not a computed lifetime. Orbit accepts supplied 40 h with delta-v closure and supplied 6.1 dB link closes. Cross-check gives 58 h. Both checksums fail. [src:sat5#0-540]

## Epoch provenance and integrity

ASSUMPTION: the common review time is inferred, not provided: SAT-1's epoch plus its supplied age implies `2025-06-10T06:00:00Z`; SAT-2 and approximately SAT-3 corroborate it. Standalone `tle_omm_fetch` at that time reports ages 18, 72, 96.5, 38 and 58 h respectively. SAT-4 and SAT-5 therefore conflict with their supplied ages. This cross-check does not replace the mandatory orbit gate's supplied values. Confirm provenance before planning.

Line-2 checksums fail for every satellite; only SAT-3's line-1 checksum passes. This is nine failing lines, correcting the critique's count of eight. The independent checks are stored per satellite. Scenario `go` is not an operational integrity clearance. SAT-2 must receive a fresh, checksum-valid TLE before a later pass because it has no freshness allowance remaining at the inferred review time.

## Evidence limits and scope

- Synthetic data (NORAD 99001-99005); no real-world operational clearance is issued.
- Link and disposal results are predictions, not guarantees. Link margins cannot be independently computed without receiver G/T (or gain and noise temperature), numerical atmospheric loss, data rate and required Eb/N0. The atmospheric-model label supplies no numerical attenuation; no model-derived attenuation or availability verification was returned. No zero-loss placeholder or retry was used.
- Accepted debris responses have `computed=false`; lifetime, 25-year-rule and contradiction outputs are absent. Area-to-mass and passivation data are required. Post-mission perigee/apogee default to operational altitude, so disposal-method specifics were not demonstrated. SAT-3's labelled perigee lowering was screened at its operational altitude, not a supplied lowered perigee.
- Orbit calls return an epoch state, not a planning-time trajectory. Their at-epoch accuracy estimates must not be presented as demonstrated planning-time accuracy.
- Raw mandatory responses are embedded in `result.json` and saved in `revision_evidence.json`; FSPL, exact requires lists, disposal perigee/apogee and standalone checksum/epoch evidence are retained.

## Gate interpretation and confidence

Gate outcomes are per satellite, not a constellation-wide clearance: orbit accepted for SAT-1, SAT-2, SAT-4 and SAT-5, stale refusal for SAT-3; supplied link threshold satisfied for SAT-1, SAT-2 and SAT-5, failed for SAT-4; caller-declared disposal screening accepted for SAT-1, SAT-2 and SAT-4, blocked for SAT-5. SAT-3's link and debris responses are informational only. Aggregate gates are **mixed**.

ITAR/EAR, IMO and Classification are **not assessed**: no export decision is requested, and the marine gates are outside scope.

Confidence is high in mechanical application of the scenario rules (the retained JSON confidence applies only to that calculation). Confidence in the underlying operational evidence is low and unquantified. No probability of mission success is asserted. Grounding is **quote-level only**: value-bearing ranges cite evidence projections traced to raw calls and input lifetimes; `grounding_check.json` records literal-source verification, not scientific validation. Status/schema verification is recorded in `revision_verification.json`.

## Response to critique

- **C1 — fixed:** Preserved existing result shape and added PLAN acceptance keys and structured per-item evidence; absent tool fields are null. Summary and decisions are derived mechanically.
- **C2 — fixed:** Independent tle_omm_fetch gives SAT-4 epoch 2025-06-08T16:00:00.000288Z and age 38 h at the inferred review time, versus supplied 20 h. Recorded caveat/deviation; mandatory orbit call retains 20 h and no_go remains D2b.
- **C3 — fixed:** Independent tle_omm_fetch gives SAT-5 epoch 2025-06-07T19:59:59.999712Z and age 58 h versus supplied 40 h. Recorded caveat/deviation; D2c unchanged.
- **C4 — fixed:** Both independent SAT-1 checksum flags are false. Added tle_check and qualified orbit acceptance and operational-use caveat. Kept scenario go per D5; the optional PLAN check was optional, not mandatory.
- **C5 — fixed:** Reruns accept SAT-2 at 72 h and margin 3 dB with min_margin_db=3, supplied_evidence and computed=false; both checksums fail. Flagged zero headroom/freshness allowance and request a fresh integrity-confirmed TLE before any later pass. Mechanical go retained; no operational confidence probability asserted.
- **C6 — fixed:** Propagation independently refused at 96.5 h. Structured informational_only=true and tle_check line1=true, line2=false added; D1a retained.
- **C7 — fixed:** Confidence explicitly limited to mechanical rule application, with low unquantified operational evidence confidence. Debris acceptance now identified as an echo of caller-declared compliance, not independent verification. Independent checks show nine failing lines, correcting the critique count of eight.
- **C8 — fixed:** Replaced field-name citations with range citations containing values and outcomes, including SAT-5 orbit/delta-v and input-declared lifetimes. Persisted sources and raw mandatory evidence in revision_evidence.json; quote-level grounding check is saved separately and does not certify scientific validity.
- **C9 — fixed:** Aggregate gates labelled mixed with explicit per-satellite outcomes, not undefined constellation-wide failures. Item status vocabulary remains go/no_go/hold.
- **C10 — fixed:** Independent link reruns confirm FSPL 177.171, 177.961, 176.301, 178.331 and 177.575 dB. Saved fspl_db, exact requires and disposal perigee/apogee fields (null for blocked SAT-5). Label-only atmospheric input and unmodelled disposal-method details are caveats; no stronger internal implementation claim is made.
- **C11 — fixed:** Rerun gives SAT-4 link_closes=false at 2.9 dB, delta-v true, and caller-declared compliant=true. Recorded decision_rule D2b and the sole applicable no_go reason link_margin_below_3db.
- **C12 — fixed:** Independent SAT-5 debris call with compliant=false was blocked; the 25.4-year declared input is the basis, not a computed lifetime. Added D2c, disposal_noncompliant, and value-bearing orbit/delta-v citation.
