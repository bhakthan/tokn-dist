# CAPABILITIES — spacemarine scout pass

Scope: SAT-1 … SAT-5 go/no-go per `BRIEF.md`. Scout pass only; no items assessed here.

Sources read: `BRIEF.md`; `inputs/orbit_states.json`, `inputs/link_budgets.json`, `inputs/disposal_plans.json`; `tokn-self/introspect-slice.json` (version 0.3.0, contract 1.0); `tokn-self/DOMAIN-README.md` (domain 0.1.0). Tool list checked against both.

## Domain tools that apply

| tool (exact name) | applies to | input fields needed and present in `inputs/` |
|---|---|---|
| `orbit_propagate` | Orbit freshness gate (`hold` rule) and delta-v gate, all five satellites | `tle_line1`, `tle_line2` (present in `orbit_states.json`); `epoch_age_hours` (present); `delta_v_closes` (present, boolean per satellite). Brief rule 2: pass the orbit record as given. |
| `link_budget_calc` | Downlink margin gate (3.0 dB), all five satellites | Present in `link_budgets.json`: `freq_ghz`, `eirp_dbw`, `distance_km`, `bandwidth_hz`. **Missing (required or needed):** `atmospheric_loss_db` (required by the schema; `atmospheric_model` is a text label, not a dB value), `g_over_t_dbk` or antenna gain plus system noise temperature, `data_rate_bps`, `required_ebn0_db`. See Gaps. |
| `debris_compliance_check` | IADC 25-year disposal gate, all five satellites | `orbit.altitude_km` (present); `disposal_plan` with `post_mission_lifetime_years` (present, used to set `compliant`). **Missing:** `perigee_alt_km`, `apogee_alt_km`, `area_to_mass_m2_per_kg` or `area_m2`+`mass_kg`. `reference_standard` = `"IADC"` (present). |
| `tle_omm_fetch` | Optional cross-check of TLE format and checksums before `orbit_propagate` (not required by the brief) | `tle_line1`, `tle_line2` (present); `start_time` optional. Offline; returns `checksum_line1_ok`, `checksum_line2_ok`, `epoch_age_hours`, `fresh`. |

Tools checked and judged not applicable to this brief: `conjunction_screen`, `constellation_design`, `earth_observation_plan`, `pass_predict`, `launch_window_calc`, `radiation_assess`, `thermal_node_model`, `link_budget_marine_comms`, `itar_ear_screen`, and all marine tools (`hull_resistance_estimate`, `stability_check`, `cii_eexi_calculate`, `marpol_compliance_check`, `maritime_reg_qa`, `ais_decode_analyze`, `oceanographic_forecast`, `seakeeping_bem`, `cfd_case_setup`). The brief asks nothing about them.

## Gates and rules that will constrain the answer

From `BRIEF.md` (the brief is the operative rule set for this run):

- **Status vocabulary (one per item):** `go`, `no_go`, `hold`.
- **Precedence (rule 1):** "Precedence is `hold`, then `no_go`, then `go`. A stale TLE means `hold`, however good the link and disposal figures look."
- **Freshness (rule 2):** `orbit_propagate` refuses when the epoch is older than the 72-hour limit. "The limit is strict: an age of exactly 72 hours is accepted." SAT-2 is at exactly 72.0 h and SAT-3 at 96.5 h in the input.
- **Link (rule 3):** "A margin of exactly 3.0 dB closes; anything below it does not." Use the tool's `link_closes` field.
- **Disposal (rule 4):** `compliant` = `post_mission_lifetime_years <= 25`. "Exactly 25 years complies; 25.4 does not." Reference standard `"IADC"`.
- **Calibrated language (rule 5):** "a closing link budget and a compliant plan are predictions, not guarantees." Every number must come from a tool call or an input file.

From `DOMAIN-README.md` (domain-level, not overriding the brief):

- "TLE epoch staleness validation (72h default threshold)."
- Six domain gates named: Orbit (delta-V budget closure), Link Budget (≥3 dB margin), ITAR/EAR, Debris (IADC/ISO 24113), IMO, Classification. Only the first four touch this brief.
- "ITAR/EAR export control enforcement" and the IADC/ISO 24113 debris rules apply to the disposal figures.

Harness-level rules (from the introspection slice): the `tool_selection_policy` and grounding rules in the system prompt. Tool outputs are the only acceptable source of numbers.

## Gaps

1. **README vs tool list disagreement (record, do not resolve here).** The README says "22 LLM tools: 12 space + 10 marine". My tool list shows 22 tools that fit the domain: 13 space-side (`orbit_propagate`, `tle_omm_fetch`, `link_budget_calc`, `link_budget_marine_comms`, `debris_compliance_check`, `conjunction_screen`, `constellation_design`, `earth_observation_plan`, `pass_predict`, `launch_window_calc`, `radiation_assess`, `thermal_node_model`, `itar_ear_screen`) and 9 marine-side (`ais_decode_analyze`, `cfd_case_setup`, `cii_eexi_calculate`, `hull_resistance_estimate`, `marpol_compliance_check`, `maritime_reg_qa`, `oceanographic_forecast`, `seakeeping_bem`, `stability_check`). The total agrees; the split is 13/9, not 12/10. The README also describes 8 hooks, 16 slash commands, 3 subagents (orbital-analyst, marine-architect, compliance-officer) and a 12-state lifecycle. None of these appear in my tool list, and I have no tool that exposes them. I treat them as unverified.
2. **No tool carries a `spacemarine` label.** Domain tools are identified by function only. Name-level membership in the domain is inferred, not confirmed.
3. **`link_budget_calc` inputs are incomplete.** The link records lack a receiver figure of merit (`g_over_t_dbk` or antenna gain plus system noise temperature), `data_rate_bps` and `required_ebn0_db`. The tool cannot compute a margin from these alone. `atmospheric_model` is a label ("ITU-R P.618 99.5% availability"), not a `atmospheric_loss_db` value. The input `margin_db` values are precomputed. The tool accepts `margin_db` only as `supplied_evidence` when the margin cannot be computed, so supplying it would not produce a computed margin. The answer must say which path produced the margin.
4. **`debris_compliance_check` inputs are incomplete.** `perigee_alt_km`, `apogee_alt_km` and area-to-mass are absent. The tool's computed lifetime may not match the input `post_mission_lifetime_years`. Per the tool's `evidence_contradiction` field, a mismatch with the supplied `compliant` flag will be reported. The brief fixes `compliant` by rule 4, so any contradiction must be reported, not hidden.
5. **Freshness boundary is a tool setting, not verified.** The brief's strict 72 h rule is the spec. The tool's threshold is described as "configured" and "72h default". Whether it accepts exactly 72.0 h must be confirmed by the call, not assumed. SAT-2 sits on that boundary.
6. **Epoch vs age consistency not checkable.** Each TLE epoch (for example `25158.25000000` for SAT-2) is given without a reference time, while `epoch_age_hours` is "hours since the TLE epoch at review time". No review timestamp is supplied, so the two cannot be cross-checked from the inputs.
7. **No tool implements the status logic.** The `hold`/`no_go`/`go` precedence and the per-item rollup are reasoning-only.
8. **No tool implements calibrated-language review.** Rule 5 is a reasoning and wording constraint.
9. **Classification-society and IMO gates have no tool here.** Not in scope for this brief; listed to be explicit.
10. **Fictional data.** Inputs are declared synthetic (NORAD IDs 99001–99005). Results are teaching-scenario outputs, not operational.
