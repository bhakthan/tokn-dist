# CAPABILITIES — Cluster 7 N-1-1 and GFM screen (items IR-1 to IR-5)

Scope: this file records what tools and rules apply. It does not assess any item.
Ground truth for tool names is the live tool list. Where the README disagrees, the
disagreement is recorded under Gaps.

## Domain tools that apply

| tool (exact name) | Items / input file it applies to | Input fields needed and whether present in `inputs/` |
|---|---|---|
| `powergrid_n1_1_screen` | IR-1, IR-2, IR-3, IR-4, IR-5. Source: `inputs/n11_study.json` | `first_contingencies`: present per request (3 elements each). `pair_results`: present per request, keyed `firstID\|secondID` (3 pairs each, which covers all 3 pairs of the 3 first contingencies). Use supplied summary only; `network` / `network_path` not needed because no pairs are missing. `stability_loss` flag present on IR-5 pair `L-501\|L-502` only. |
| `powergrid_ibr_stability_gate` | IR-1, IR-2, IR-3, IR-4, IR-5. Sources: `inputs/ibr_registry.json` (`resources`, `additions[IR-x]`, `threshold_pct`) | `resources`: present (10 existing units, GFM and GFL). `additions`: present per request, one unit each. `threshold_pct`: present (30). `zone_short_circuit_mva`: **absent** (SCR and grid-strength class will not be returned). Pass only the one request's additions per call. |
| `run_n1_contingency_screen` | Not applied to the brief | Needs `network` or `network_path` or `contingency_results`. Only N-1 pair data is supplied, not single-outage N-1 results for the model. Not used. |
| `approve_interconnection` | Not applied to the brief | Needs `thevenin_r_pu`, `thevenin_x_pu`, `base_mva`, `short_circuit_mva`, `capacity_mw`, `power_factor`, etc. None are in `inputs/`. It is a CRITICAL-risk approval tool. It must not be used to produce the disposition. |
| `generate_reliability_report` | Not applied to the brief | Requires `studies/power_flow/latest/n1_summary.json` showing N-1 compliance. Not present. The brief does not ask for a report. |
| `inspect_network` / `run_power_flow` | Not applicable | `network_path` points to `models/synthetic_330bus_summer_peak_2029.raw` (PSS/E). The raw file is not in `inputs/`. PSS/E `.raw` returns `computed=false`. |

## Gates and rules that will constrain the answer

Sources: `BRIEF.md` (Rules 1–6, status vocabulary) and tool descriptions as shown in the tool list.

- **Status precedence (BRIEF Rule 1):** `blocked` > `reject` > `approve_with_conditions` > `approve`. A gate block overrides a clean N-1-1 screen.
- **Screen each request on its own (BRIEF Rule 2):** one `powergrid_n1_1_screen` call per request, and one `powergrid_ibr_stability_gate` call with the full existing `resources` plus only that request's `additions`.
- **Bus voltage limits (BRIEF Rule 3):** 0.85–1.10 pu. Values exactly at a limit are not violations.
- **Thermal (tool description and BRIEF Rule 3):** "> 115% HIGH" (emergency rating). "> 132.25% CRITICAL". The brief says CRITICAL only above 115% × 1.15. Loading at or below 115% is not a violation.
- **Voltage severity (tool description):** "V < 0.85 HIGH", "< 0.80 CRITICAL".
- **Stability (tool description and BRIEF Rule 3):** any loss of synchronism is CRITICAL.
- **Overvoltage above 1.10 pu:** the brief sets 1.10 as a limit but no severity is given for it by the tool description. See Gaps.
- **GFL penetration (BRIEF Rule 4, gate `threshold_pct` 30):** threshold is 30% of zonal IBR capacity. Exactly 30.0% does not exceed it.
- **Reporting (BRIEF Rule 5):** report post-expansion zonal GFL penetration as the gate returns it. Quote the violation severities the N-1-1 screen returns.
- **Numbers (BRIEF Rule 6):** every number reported must come from a tool call, not mental arithmetic.
- **Vocabulary:** exactly one of `approve`, `approve_with_conditions`, `reject`, `blocked` per item.
- **N-1 reporting rule (system prompt):** N-1 must be shown before any reliability report. A warning is required when N-1 is not checked. No N-0 power flow was run here, so N-0 and N-1 status is not established by this study. Say so.
- **Calibrated language:** the README has no domain calibrated-language rule. Keep claims to what the tools return and what the brief states.

## Gaps

1. **README vs tool list (tool names):** the README (`tokn-self/DOMAIN-README.md`) does not mention `powergrid_n1_1_screen` or `powergrid_ibr_stability_gate`. Both are in the live tool list, so the tool list is trusted. The README also does not list a state-machine tool or a validator tool.
2. **README vs brief (standard):** the README and its config example name NERC TPL-001-5. The brief names NERC TPL-001-4 P6/P7 for N-1-1. Use the brief for this study.
3. **README vs brief (limits):** the README's N-1 config uses voltage 0.90–1.10 pu and thermal 100%. The brief's N-1-1 limits are 0.85–1.10 pu and 115%. Per BRIEF Rule 3, the brief's N-1-1 limits govern.
4. **Mode naming:** `tokn-self/introspect-slice.json` names the mode `grideng`. The brief and the README use `powergrid`. The introspect slice lists no tools, so it cannot confirm tool availability.
5. **Short-circuit / SCR:** no `zone_short_circuit_mva` or short-circuit data is in `inputs/`. The gate cannot return SCR, WSCR or grid-strength class. Any stability statement about strength must be reasoned, not tool-backed.
6. **Overvoltage severity:** the N-1-1 screen tool description gives severities for thermal and undervoltage only. Pair results can include bus voltages up to 1.10 (e.g. IR-4 `B-44` at 1.10). Severity for V > 1.10 is not defined by the tool. Reason from BRIEF Rule 3 and say so.
7. **Network model not available:** `models/synthetic_330bus_summer_peak_2029.raw` is not in `inputs/`. No base-case N-0 power flow, N-1 screen, or per-unit check can be run on the network. Results rely on the supplied pair summaries.
8. **Brief status `blocked`:** the tool returns a gate BLOCK or pass with violations. It does not use the word `blocked`. Map it to the brief's definition: the gate blocks expansion that adds GFL with no GFM and pushes zonal GFL past the threshold.
9. **Stability detail:** the screen takes a supplied `stability_loss` flag only. Stability analysis of IBR response (transient, voltage, frequency) is not covered by any available tool for these requests.
10. **Deliverables:** `result.json` and `RESULT.md` are for the later stages. No tool in the list writes the planning-committee package.
