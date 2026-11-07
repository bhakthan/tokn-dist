# CAPABILITIES — Scout stage, energy relay (Q3 2026 board pack)

Scope: capability map only. No item (EN-1 to EN-6) has been assessed or submitted.

Evidence base: `BRIEF.md`; `inputs/analysis_requests.json`; `inputs/release_policy.json`;
`tokn-self/introspect-slice.json`; `tokn-self/DOMAIN-README.md`; my own tool list.
Tool-list check: the 22 `en_` tools named in the README (balance/planning 4, demand 4,
market 4, carbon 4, economics 3, scenario 3) all appear in my tool list. Names agree.

## Domain tools that apply

| Tool (exact name) | Item(s) | Input fields the payload carries (from `inputs/analysis_requests.json`) |
|---|---|---|
| `en_energy_balance` | EN-1 | carriers, period, provenance (metered), meter_id (AMI-HQ-0042), region. Required fields are all present. |
| `en_capacity_expansion` | EN-2 | horizon_years (20), discount_rate (0.0), assumptions. Optional fields candidates, carbon_price and demand_growth are absent. Candidates are only named inside the assumptions text. No provenance field is supplied. |
| `en_ppa_valuate` | EN-3 | contract_type (virtual/cfd), tenor_years (12), strike_price (41.5), discount_rate (0.07), assumptions, disclaimer_acknowledged (true). Required fields are all present. volume_mwh (180000) is present as well. |
| `en_carbon_inventory` | EN-4 | ghg_scope (scope1+2), accounting_method (market-based), reporting_year (2025), organization (operational_control). Required fields are all present. |
| `en_scenario_model` | EN-5 | scenario_name, horizon_years (15), discount_rate (0.06), assumptions, demand_growth (0.021). Required fields are all present. carbon_price is only in the assumptions text (85). |
| `en_demand_forecast` | EN-6 | carrier (electricity), sector (commercial), horizon_years (5), granularity (monthly), provenance (estimated). Required fields are all present. |

Tools not needed for any item: `en_market_settle`, `en_dispatch_simulate`, `en_pathway_model`, etc.

## Gates and rules that will constrain the answer

Domain gates (README, "Domain Gates"; each is a PreToolUse blocking hook):
1. Data provenance: `validate_data_provenance`. Energy data must declare provenance as metered, estimated, modeled or assumed. Metered claims must carry a meter ID.
2. Scenario disclosure: `enforce_scenario_disclosure`. Blocks projections that lack a discount rate, time horizon or key assumptions. Per the brief, a discount rate of 0.0 counts as undisclosed.
3. Carbon boundary: `enforce_carbon_boundary`. Blocks GHG outputs that lack organizational boundary, scope (1/2/3) and accounting method.
4. Market disclaimer: `enforce_market_disclaimer`. Market outputs must state "analysis, not financial advice". The README lists 9 blocked certainty terms, of which it quotes "guaranteed return", "ri[REDACTED]free" and "will definitely".

Confidence caps by data layer (README, "Four-Layer Data Hierarchy"):
- metered 0.95; estimated 0.75; modeled 0.55; assumed 0.35.

Brief status rules (`BRIEF.md`):
- Status vocabulary: exactly one of `release`, `release_with_caveat`, `blocked`.
- Precedence: `blocked` > `release_with_caveat` > `release`.
- `release`: completed, rests on metered or estimated data.
- `release_with_caveat`: completed, rests on modeled or assumed data.
- `blocked`: gate refusal. Quote the gate's reason.
- Submit each payload unchanged. Do not add, remove or correct fields.
- The data layer is the payload's `provenance` if present, otherwise the tool's returned provenance.
- Every reported number must come from a tool call.

Release policy (`inputs/release_policy.json`):
- caveat_layers: ["modeled", "assumed"].
- caveat_wording: "Modeled and assumed results must be labelled as projections with their confidence and key assumptions stated alongside the figure."

Lifecycle gates (README): BALANCE_SIMULATION requires DATA_COLLECTION; REPORTING requires SCENARIO_DESIGN; CARBON_ACCOUNTING requires SCOPE_DEFINITION; MARKET_ANALYSIS requires DEMAND_ANALYSIS.

Pre-run observations (from reading only; not assessments):
- EN-2: discount_rate is 0.0, which the brief defines as undisclosed. Expect a scenario-disclosure block unless the tool treats it differently.
- EN-3: the assumptions text as I received it contains "ri[REDACTED]free rate". The redaction hides the exact term, so I cannot tell whether a blocked term is present. The payload must be submitted as-is.

## Gaps

1. **Hooks, commands and subagents are not visible to me.** The README and introspect slice count 8 hooks (4 blocking), 16 slash commands and 3 subagents. None of these appear in my tool list. Whether the four gates fire is known only from the tool response, not verified in advance.
2. **Redacted blocked term.** The README and the EN-3 payload both show "ri[REDACTED]free". I cannot see the full list of 9 blocked terms. Whether EN-3 trips the certainty-term gate is unknown.
3. **Returned provenance and confidence unknown.** EN-2, EN-4 and EN-5 carry no provenance field in the payload. Their layer must come from the tool's returned output. Any confidence value must be checked against the cap for that layer.
4. **Lifecycle state.** No tool in my list reads or advances the 12-state study lifecycle. `/energy-advance` is a command, not a tool I can call.
5. **Caveat wording.** No tool formats the release_policy caveat. Wording must be produced by reasoning.
6. **Aggregation and arithmetic.** No tool rolls up figures across items for the board pack. Any totals must be tool outputs or be flagged as not produced by a tool.
7. **Result files.** `result.json` and `RESULT.md` are the next stages' deliverables. Writing them is out of scope for the Scout.
8. **Cross-domain handoffs.** None of the six items needs powergrid (grid physics) or greenenergy (project yield). No gap there.
9. **Blocked-item remediation.** Policy says blocked items are fixed next cycle. No tool here proposes corrected payloads, and the brief forbids correcting them in this run.
