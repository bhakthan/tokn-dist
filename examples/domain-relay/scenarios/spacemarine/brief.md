# Brief — pre-pass go/no-go review for a five-satellite LEO constellation

You are the flight-dynamics lead for a small Earth-observation constellation in low Earth orbit. Before tomorrow's downlink and station-keeping planning cycle, mission operations wants a go/no-go for each satellite: is its orbit state fresh enough to plan from, does its downlink close with margin, and does its end-of-life disposal plan comply with the IADC 25-year guideline?

The data is synthetic but realistic. Everything you need is in `inputs/`:

| File | Contents |
|---|---|
| `inputs/orbit_states.json` | Per satellite: synthetic two-line element set (`tle_line1`, `tle_line2`), `epoch_age_hours`, and `delta_v_closes` (whether the planned manoeuvre budget closes) |
| `inputs/link_budgets.json` | Per satellite: X-band downlink `freq_ghz`, `eirp_dbw`, `distance_km`, `bandwidth_hz`, `atmospheric_model` and the computed `margin_db` |
| `inputs/disposal_plans.json` | Per satellite: orbit, disposal plan with `post_mission_lifetime_years`, and `reference_standard` |

## Items to assess

`SAT-1`, `SAT-2`, `SAT-3`, `SAT-4`, `SAT-5`

## Status vocabulary (use exactly one per item)

- `go`: orbit propagation accepted, downlink closes (`link_closes` true), disposal plan compliant, and the delta-v budget closes.
- `no_go`: the orbit state is usable, but the link margin is below the 3.0 dB minimum, the disposal plan is non-compliant, or `delta_v_closes` is false.
- `hold`: `orbit_propagate` refuses the TLE because its epoch is older than the 72-hour freshness limit. Request a fresh TLE before judging anything else.

## Rules

1. Precedence is `hold`, then `no_go`, then `go`. A stale TLE means `hold`, however good the link and disposal figures look.
2. Call `orbit_propagate` with each satellite's orbit record exactly as given, including `epoch_age_hours`. A blocked call is a refusal. The limit is strict: an age of exactly 72 hours is accepted.
3. Call `link_budget_calc` with each satellite's link record exactly as given and use the tool's `link_closes` field. A margin of exactly 3.0 dB closes; anything below it does not.
4. Call `debris_compliance_check` with `reference_standard` `"IADC"` and `compliant` set to `post_mission_lifetime_years <= 25`. Exactly 25 years complies; 25.4 does not.
5. Every number you report must come from a tool call or the input files. Use calibrated language: a closing link budget and a compliant plan are predictions, not guarantees.

## Deliverable

`result.json` and `RESULT.md`, as described in your stage instructions.
