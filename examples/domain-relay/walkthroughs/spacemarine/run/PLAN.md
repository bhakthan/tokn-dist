# PLAN — spacemarine pre-pass go/no-go review (SAT-1 … SAT-5)

Planner stage. Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/orbit_states.json`, `inputs/link_budgets.json`, `inputs/disposal_plans.json`, `tokn-self/DOMAIN-README.md`, `tokn-self/introspect-slice.json`. This plan has not been executed. Every input value below was copied from `inputs/`. Where the plan states what a tool is expected to do, that is a prediction. The tool's real output overrides it.

## Objective

For each of SAT-1 … SAT-5, give exactly one status (`go`, `no_go` or `hold`) by applying the BRIEF.md precedence rules to real outputs from `orbit_propagate`, `link_budget_calc` and `debris_compliance_check`. Record the results in `result.json` and `RESULT.md`.

## Steps

General execution rules (these apply to every step):

- **E1.** Make exactly one call per tool per satellite, using the values listed. Do not add, drop, round or "fix" any value. Do not invent values for fields that are missing from `inputs/`, such as `atmospheric_loss_db`, `g_over_t_dbk`, `data_rate_bps`, `required_ebn0_db`, `perigee_alt_km`, `apogee_alt_km` or area-to-mass. The one allowed retry is described in Step 2.
- **E2.** Save the raw output of every call, or the raw error or block message, verbatim. A "blocked" or "refused" call is an outcome, not a failure to retry.
- **E3.** Run Steps 1–3 for **all five** satellites, including any that turn out to be `hold`. For held satellites, the link and disposal results are recorded as `informational_only` and must not affect the status (BRIEF rule 1: "Request a fresh TLE before judging anything else").
- **E4.** Calls for different satellites are independent and may run in parallel.

### Step 0 (optional, informational only): TLE format cross-check
- **Items:** SAT-1 … SAT-5.
- **Tool:** `tle_omm_fetch`.
- **Inputs:** `tle_line1` and `tle_line2` exactly as in Step 1. Pass **no** `start_time`.
- **Effect on status:** **None.** Record `checksum_line1_ok` and `checksum_line2_ok` only. Do **not** use this tool's `fresh` or `epoch_age_hours` for the hold decision. With no `start_time` it measures age against "now", not against the review time. Freshness comes **only** from Step 1 (BRIEF rule 2). If a checksum is false, mention it in `RESULT.md` under caveats.

### Step 1: Orbit freshness and delta-v (covers the `hold` rule and the delta-v part of `no_go`/`go`)
- **Items:** SAT-1, SAT-2, SAT-3, SAT-4, SAT-5.
- **Tool:** `orbit_propagate`.
- **Inputs:** pass exactly these four fields and nothing else (no `start_time`, `end_time` or `step_s`):

| sat | tle_line1 | tle_line2 | epoch_age_hours | delta_v_closes |
|---|---|---|---|---|
| SAT-1 | `1 99001U 25001A   25160.50000000  .00001200  00000-0  65000-4 0  9991` | `2 99001  97.4500 120.1000 0012000  90.0000 270.1000 15.21000000 10001` | 18.0 | true |
| SAT-2 | `1 99002U 25001B   25158.25000000  .00001150  00000-0  62000-4 0  9992` | `2 99002  97.4500 150.2000 0011000  85.0000 275.2000 15.21500000 10002` | 72.0 | true |
| SAT-3 | `1 99003U 25001C   25157.22916667  .00001300  00000-0  70000-4 0  9993` | `2 99003  97.4500 180.3000 0010000  80.0000 280.3000 15.20500000 10003` | 96.5 | true |
| SAT-4 | `1 99004U 25001D   25159.66666667  .00001250  00000-0  68000-4 0  9994` | `2 99004  97.4500 210.4000 0013000  95.0000 265.4000 15.22000000 10004` | 20.0 | true |
| SAT-5 | `1 99005U 25001E   25158.83333333  .00000900  00000-0  48000-4 0  9995` | `2 99005  97.6000 240.5000 0009000 100.0000 260.5000 14.95000000 10005` | 40.0 | true |

(TLE strings keep their internal spacing exactly as in `inputs/orbit_states.json`. Copy them from that file, not from this table, if a renderer has collapsed the spaces.)

- **Record:** `orbit_outcome` takes one of these values:
  - `accepted`: the tool returned ephemeris/elements and no block.
  - `refused_stale`: the call was blocked or returned an error that cites the TLE epoch age or freshness limit.
  - `refused_delta_v`: the call was blocked or failed and cites `delta_v_closes`.
  - `error_other`: any other block or error, such as a parse, checksum or missing-parameter error.
  
  Also record the tool's verbatim message and `accuracy_estimate` if one is present.
- **What changes status:** `refused_stale` → `hold`. `refused_delta_v` → `no_go`. `error_other` → `hold` (D1b). `accepted` → move on to the link and disposal results.
- **Boundary watch:** SAT-2 is at exactly 72.0 h. The brief says that age is accepted. If the tool refuses SAT-2, the tool outcome governs (`hold`, fail-closed), and the conflict with BRIEF rule 2 must be reported in `deviations`. Do not override the tool.

### Step 2: Downlink margin (covers the link part of `no_go`/`go`)
- **Items:** SAT-1, SAT-2, SAT-3, SAT-4, SAT-5.
- **Tool:** `link_budget_calc`.
- **Inputs:** pass each link record exactly as given, every field including `atmospheric_model` and `margin_db` (BRIEF rule 3):

| sat | freq_ghz | eirp_dbw | distance_km | bandwidth_hz | atmospheric_model | margin_db |
|---|---|---|---|---|---|---|
| SAT-1 | 8.2 | 10.5 | 2100 | 150000000 | "ITU-R P.618 99.5% availability" | 7.4 |
| SAT-2 | 8.2 | 9.0 | 2300 | 150000000 | "ITU-R P.618 99.5% availability" | 3.0 |
| SAT-3 | 8.2 | 13.0 | 1900 | 150000000 | "ITU-R P.618 99.5% availability" | 11.2 |
| SAT-4 | 8.2 | 8.5 | 2400 | 150000000 | "ITU-R P.618 99.5% availability" | 2.9 |
| SAT-5 | 8.2 | 10.0 | 2200 | 150000000 | "ITU-R P.618 99.5% availability" | 6.1 |

- **Known gap (CAPABILITIES.md Gap 3):** `atmospheric_loss_db` is required by the tool schema and is not in the inputs. `atmospheric_model` is a text label, not a dB value. The receiver G/T, data rate and required Eb/N0 are also absent, so the tool cannot compute a margin. The best case is `margin_source = supplied_evidence`.
- **Allowed retry (only one):** suppose the first call is rejected *only* because `atmospheric_loss_db` is missing, and returns no `link_closes`. Retry once with the same record plus `atmospheric_loss_db: 0`. Set `retry_atm0: true` and state in `RESULT.md` that the 0 dB value is a **placeholder meaning "losses already included in the supplied `margin_db`"**. It is not a measured atmospheric loss. Make no other retries or additions.
- **Record:** `link_closes` (verbatim), `margin_db` as returned by the tool, `margin_source` (`computed` or `supplied_evidence`), `margin_discrepancy_db` if present, `retry_atm0`, and the verbatim `requires` list if present.
- **What changes status:** `link_closes == false` → `no_go`. `link_closes == true` → the link criterion is satisfied. If no `link_closes` field comes back after the allowed retry → `link_unverified` (D3).
- **Boundary watch:** SAT-2 is at exactly 3.0 dB (the brief says this closes) and SAT-4 is at 2.9 dB (the brief says it does not). If the tool's `link_closes` disagrees with the BRIEF rule-3 threshold (`margin_db >= 3.0`) applied to the input `margin_db`, set `link_discrepancy: true` and apply D3.

### Step 3: Disposal compliance (covers the debris part of `no_go`/`go`)
- **Items:** SAT-1, SAT-2, SAT-3, SAT-4, SAT-5.
- **Tool:** `debris_compliance_check`.
- **Inputs:** `reference_standard: "IADC"`. Set `compliant` to `post_mission_lifetime_years <= 25`, the rule 4 calculation, done mechanically. Pass `orbit` and `disposal_plan` as given:

| sat | orbit | disposal_plan | compliant |
|---|---|---|---|
| SAT-1 | `{"altitude_km": 520, "inclination_deg": 97.45}` | `{"method": "drag-sail assisted natural decay", "post_mission_lifetime_years": 6.2}` | true (6.2 ≤ 25) |
| SAT-2 | `{"altitude_km": 515, "inclination_deg": 97.45}` | `{"method": "natural decay", "post_mission_lifetime_years": 11.0}` | true (11.0 ≤ 25) |
| SAT-3 | `{"altitude_km": 525, "inclination_deg": 97.45}` | `{"method": "propulsive perigee lowering", "post_mission_lifetime_years": 4.1}` | true (4.1 ≤ 25) |
| SAT-4 | `{"altitude_km": 510, "inclination_deg": 97.45}` | `{"method": "natural decay", "post_mission_lifetime_years": 9.5}` | true (9.5 ≤ 25) |
| SAT-5 | `{"altitude_km": 610, "inclination_deg": 97.60}` | `{"method": "natural decay", "post_mission_lifetime_years": 25.4}` | **false** (25.4 > 25) |

- **Known gap (CAPABILITIES.md Gap 4):** `perigee_alt_km`, `apogee_alt_km` and area-to-mass are absent, and must not be invented. The tool may return `computed:false` or `requires`, or a lifetime estimate built on defaults.
- **Record:** call outcome (`accepted` or `blocked`, with the verbatim message), `meets_25_year_rule`, `estimated_lifetime_years`, `evidence_contradiction`, `requires`, and the `compliant` value that was passed.
- **What changes status:** `compliant` passed as false, *or* the call is blocked because of non-compliance, *or* the tool returns `meets_25_year_rule == false` → disposal is non-compliant → `no_go`. If `evidence_contradiction == true` on a satellite passed as `compliant: true` → `disposal_unverified` (D4). A tool lifetime that is `null` or not computed, with no contradiction flagged, does **not** block `go`. The brief makes `post_mission_lifetime_years` the basis (rule 4). Record it as a caveat.

### Step 4: Roll-up (no tool exists; reasoning only, CAPABILITIES.md Gap 7)
- **Items:** all five.
- Apply the Decision rules below in order. Write `result.json` and `RESULT.md`.

### Step 5: Grounding check
- **Items:** all five.
- **Tool:** `grounding_check_citations`. The answer is the `RESULT.md` text. The sources are the verbatim outputs from Steps 1–3, plus the three input files.
- **What changes status:** nothing. Fix every `MISMATCHED` or `UNVERIFIABLE` citation before you finish (BRIEF rule 5).

## Decision rules

Evaluate in this exact order for each satellite. The first rule that matches sets the status, and evaluation stops.

| # | Condition (from recorded outcomes) | Status | reason code |
|---|---|---|---|
| D1a | Step 1 `orbit_outcome == refused_stale` | `hold` | `tle_stale` |
| D1b | Step 1 `orbit_outcome == error_other` | `hold` | `orbit_call_error` (flag as a deviation from the brief's narrow `hold` definition; fail-closed) |
| D2a | Step 1 `orbit_outcome == refused_delta_v`, or input `delta_v_closes == false` | `no_go` | `delta_v_not_closed` |
| D2b | Step 2 `link_closes == false` | `no_go` | `link_margin_below_3db` |
| D2c | Step 3 non-compliant: `compliant` passed false, or blocked for non-compliance, or `meets_25_year_rule == false` | `no_go` | `disposal_noncompliant` |
| D3 | Step 2 produced no `link_closes` (`link_unverified`), or `link_discrepancy == true` | `hold` | `link_unverified` (flag as a deviation; fail-closed, never `go` without the tool's `link_closes`) |
| D4 | Step 3 `evidence_contradiction == true` with `compliant` passed true | `hold` | `disposal_unverified` (flag as a deviation; fail-closed) |
| D5 | `orbit_outcome == accepted` AND `link_closes == true` AND disposal compliant AND `delta_v_closes == true` | `go` | `all_gates_pass` |
| D6 | Anything else | `hold` | `indeterminate` (explain in `RESULT.md`) |

Clarifications:
- Every `no_go` reason that applies (D2a–D2c) is listed in `reasons`, not only the first. The status itself is still `no_go`. Because D2 is checked before D3/D4, a definite `no_go` finding is never hidden by an unverified finding on another criterion.
- For a `hold` from D1, the Step 2–3 results are kept with `informational_only: true` and never cited as the basis for a status.
- Thresholds are inclusive exactly as the brief states: age 72.0 h is accepted, margin 3.0 dB closes, lifetime 25.0 years complies. Where the tool's own output disagrees, the tool output is used with fail-closed handling (D1b, D3, D4), and the disagreement goes into `deviations`.
- Wording: "the link is predicted to close", "the disposal plan is assessed as compliant". Never "will close" or "guaranteed" (BRIEF rule 5).

**Planner's expected outcome.** This is a prediction from the brief's rules applied to the input values. It is not a result and must not be copied. Tool outputs govern. Use it only to spot discrepancies worth reporting.
SAT-1 `go`; SAT-2 `go` (72.0 h and 3.0 dB boundary cases); SAT-3 `hold` (96.5 h); SAT-4 `no_go` (2.9 dB); SAT-5 `no_go` (25.4 years).
If D3 fires because of the link-input gap, SAT-1 and SAT-2 would become `hold`. That is acceptable and must be explained.

## Gates

None of the following can be skipped. A `go` needs all of them to pass:

1. **Orbit gate (TLE freshness + delta-v closure):** `orbit_propagate` accepted the record (not blocked) with the supplied `epoch_age_hours`, and `delta_v_closes == true`.
2. **Link Budget gate (≥ 3.0 dB):** `link_budget_calc` returned `link_closes == true`, with `margin_source` recorded.
3. **Debris gate (IADC 25-year):** `debris_compliance_check` with `reference_standard "IADC"` accepted `compliant: true` with no `evidence_contradiction` and no `meets_25_year_rule == false`.
4. **Grounding:** every number in `RESULT.md` traces to a tool output or an input file (Step 5).

Domain gates not invoked, with reasons:
- **ITAR/EAR:** the brief asks for operational go/no-go, not an export decision. `itar_ear_screen` would need a `cleared` and `justification` that nothing in `inputs/` supports.
- **IMO and Classification:** these are marine-only.

All three are listed as "not assessed" in `result.json` and `RESULT.md`.

## Acceptance criteria

`result.json` must be valid JSON with these top-level keys:

- `domain`: `"spacemarine"`
- `items`: an array of exactly five objects, SAT-1 … SAT-5 in order
- `summary`: an object with arrays `go`, `no_go` and `hold`, each listing satellite ids
- `deviations`: an array of strings (may be empty)
- `gates_not_assessed`: `["ITAR/EAR", "IMO", "Classification"]`
- `caveats`: an array of strings. It must include "synthetic data (NORAD 99001-99005)", "link and disposal results are predictions, not guarantees", and the input gaps found in Steps 2–3.

Each object in `items` must contain:

- `id`: for example `"SAT-1"`
- `status`: exactly one of `go`, `no_go`, `hold`
- `decision_rule`: one of `D1a`, `D1b`, `D2a`, `D2b`, `D2c`, `D3`, `D4`, `D5`, `D6`
- `reasons`: an array of reason codes from the Decision rules
- `informational_only`: true if the item is a D1 hold, else false
- `orbit`: an object with `inputs_passed`, `outcome` (`accepted` | `refused_stale` | `refused_delta_v` | `error_other`), `message` (verbatim, or null) and `accuracy_estimate` (or null)
- `link`: an object with `inputs_passed`, `retry_atm0`, `link_closes`, `margin_db`, `margin_source`, `margin_discrepancy_db`, `requires` and `link_discrepancy`
- `disposal`: an object with `inputs_passed` (including `compliant` and `reference_standard: "IADC"`), `outcome`, `message`, `meets_25_year_rule`, `estimated_lifetime_years`, `evidence_contradiction` and `requires`
- `tle_check`: present only if Step 0 ran, with `checksum_line1_ok` and `checksum_line2_ok`

The result is complete only when:

1. There are exactly five items, each with exactly one valid `status`.
2. Every tool field is copied from the actual output or block message. Fields the tool did not return are `null`. Nothing is fabricated.
3. Each `status` and `decision_rule` follows mechanically from the recorded fields under D1–D6. A second reviewer re-applying the rules gets the same result.
4. `summary` agrees with `items`.
5. `deviations` lists every use of D1b, D3, D4 or D6, any `retry_atm0` use, and any case where the tool contradicts a brief boundary (SAT-2 at 72.0 h or 3.0 dB, or any `evidence_contradiction`).
6. Every number in `result.json` and `RESULT.md` appears in a tool output or an input file. Step 5 reports no `MISMATCHED` or `UNVERIFIABLE` citations.
7. `RESULT.md` gives a per-satellite status table with reasons, uses calibrated language, and lists the gates not assessed and the caveats.
