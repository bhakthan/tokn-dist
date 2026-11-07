# REFLECTION — spacemarine relay: pre-pass go/no-go review for a five-satellite LEO constellation

## What changed between the first and final answer

The statuses did not change: SAT-1 and SAT-2 `go`, SAT-3 `hold`, SAT-4 and SAT-5 `no_go`, in both versions. Every change was to packaging, provenance or calibration:

| Item | v1 → final | Driving finding |
|---|---|---|
| Schema | v1 had only `gates`/`limitations`. Final adds `summary`, `deviations`, `gates_not_assessed`, `caveats`, and per-item `decision_rule`, `reasons`, `informational_only` and structured `orbit`/`link`/`disposal` objects with `raw_output` and nulls for fields the tool did not return | C1 |
| SAT-1 | Rationale now says both TLE checksums fail and the `go` is conditional on confirming TLE integrity. A `tle_check` object was added | C4 |
| SAT-2 | Flagged for zero margin headroom and zero freshness allowance, with a request for a fresh, checksum-valid TLE before any later pass. `go` was kept | C5 |
| SAT-3 | `informational_only: true` and `tle_check` (line 1 true, line 2 false) were added. D1a was kept | C6 |
| SAT-4 | `decision_rule: D2b`, `reasons: ["link_margin_below_3db"]`, and a new deviation: supplied age 20 h against 38 h implied by the epoch | C11, C2 |
| SAT-5 | `decision_rule: D2c`, `reasons: ["disposal_noncompliant"]`, a value-bearing orbit citation, and a deviation: supplied age 40 h against 58 h implied by the epoch | C12, C3 |
| v1 claim "No absolute review timestamp was supplied to cross-check" | Replaced by an inferred review time of 2025-06-10T06:00:00Z, labelled "inferred, not supplied" | C2 |
| Gates | Orbit, Link Budget and Debris changed from `fail` to `mixed` with per-satellite detail. Grounding changed from `pass` to `quote_level_only` | C9, C8 |
| Citations | Field-name quotes were replaced with value-bearing range citations. The grounding output is now saved (`grounding_check.json`: 10 verified, 0 mismatched) | C8 |
| Extra recorded outputs | `fspl_db` for each link, `requires` lists, and `post_mission_perigee_km`/`apogee_km`, with caveats limiting claims to what the tools returned | C10 |
| Confidence | Still `0.9`, but a caveat now limits it to "mechanical application of scenario rules", with operational evidence confidence "low and unquantified". C7 had suggested about 0.6 or a split figure. The reviser chose a written qualification instead of a split field | C7 |
| Debris wording | Now says "echo caller-declared compliant=true", not independent compliance | C7 |
| Checksum count | The critique said 8 of 10 lines fail. The reviser's `tle_omm_fetch` re-run corrected this to 9 of 10 (`critique_response` C7) | C7 (corrected) |
| `critique_response` | Went from `[]` to 12 entries, all `fixed` | all |

## Where TOKN's harness helped

- **The `orbit_propagate` freshness gate:** it blocked SAT-3 with "[SPACEMARINE] [HIGH] TLE epoch age 96.5 hours exceeds maximum 72.0 hours". It accepted SAT-2 at exactly 72 h, which matches the brief's inclusive rule. This settled the only `hold`. `decision.json` stale_tle_cleared = 0.0059 confirms no stale `go`.
- **`link_budget_calc` with `min_margin_db=3`:** it returned `link_closes=false` and the warning "Link margin 2.9 dB below minimum 3.0 dB" for SAT-4, and accepted SAT-2 at exactly 3.0 dB. It labelled every result honestly as `margin_source=supplied_evidence` with `computed=false` and listed `requires`, which kept the result from claiming a computed margin.
- **The `debris_compliance_check` IADC gate:** it blocked SAT-5 with "Disposal plan non-compliant per IADC — debris gate remains blocked until remediation". It also returned `computed=false` and post-mission perigee/apogee equal to the operating altitude, which made clear that compliance was declared by the caller rather than computed (C7, C10).
- **`tle_omm_fetch`:** used only by Critique and Revise. It is the tool that caught the SAT-4 and SAT-5 epoch-age inconsistencies (38 h vs 20 h, 58 h vs 40 h) and the checksum failures, including the correction from 8 to 9 of 10 lines.

## Proposed /teach rule

`/teach In spacemarine TLE reviews, always run tle_omm_fetch on every TLE with start_time set to (reference satellite epoch + its supplied epoch_age_hours), and record checksum failures and any supplied-age vs epoch-age mismatch as deviations before writing result.json.`
