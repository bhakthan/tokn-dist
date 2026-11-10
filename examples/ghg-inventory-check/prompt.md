# Brief: reporting-year 2025 GHG inventory and disclosure review

You are the group sustainability controller for a mid-sized manufacturing group that reports under CSRD (ESRS E1). Reporting year 2025 is closing. Before the sustainability statement goes to internal review and then to the limited-assurance provider, the CFO needs a defensible status for six items: four entity inventories, one Scope 3 calculation and one line of draft disclosure wording. For each item, can it go forward as is, go forward with a caveat, does it fail a check, or can it not yet be assessed?

The data is synthetic: the entities, grids, factors and certificates are illustrative. The inventory uses IPCC AR6 GWP100 values throughout. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/scope1_scope2.json` | Per entity: a complete `esg_scope1_calculate` input (`scope1`, ENT-A only) and a complete `esg_scope2_dual_report` input (`scope2`). Each `scope2` block holds the sites (market, consumption, `location_factor`, `residual_mix_factor`) and the contractual instruments (type, MWh, `vintage_year`, `market`, `site`, `retired`). |
| `demo-input/factor_register.json` | Per entity: a complete `esg_factor_provenance_check` input. Each factor carries value, unit, source, year, region and GWP set, plus the activity and the `reported_tco2e` from the entity's spreadsheet. |
| `demo-input/scope3.json` | `SC3-CAT3`: a `screen` input (all 15 categories) and a `calculate` input for ENT-A's Scope 3. |
| `demo-input/claims.json` | `CLAIM-1`: the draft disclosure text and the evidence behind it. |

## Items to assess

| Item | Tool calls |
|---|---|
| `ENT-A` | `esg_scope1_calculate`, `esg_scope2_dual_report`, `esg_factor_provenance_check` |
| `ENT-B` | `esg_scope2_dual_report` |
| `ENT-C` | `esg_scope2_dual_report` |
| `ENT-D` | `esg_factor_provenance_check` |
| `SC3-CAT3` | `esg_scope3_screen`, then `esg_scope3_calculate` |
| `CLAIM-1` | `esg_claim_language_check` |

## Status vocabulary (use exactly one per item)

- `pass`: every tool call for the item succeeds, and no blocking or advisory gate fires.
- `pass_with_caveats`: every call succeeds and no blocking gate fires, but an advisory gate warns (e.g. a stale emission factor). Name the caveat.
- `fail`: a tool ran but a blocking PostToolUse gate rejected its result. Examples:
  - instrument issues (vintage, market, retirement, double claim)
  - a factor unit mismatch or missing provenance
  - a double count
  - an unjustified Scope 3 exclusion
  - a blocked claim
- `blocked`: a PreToolUse gate refused the call, or the tool could not compute, so the item cannot be assessed until its inputs are fixed.

## Rules

1. Precedence is `blocked`, then `fail`, then `pass_with_caveats`, then `pass`. The worst result across an item's tool calls decides its status.
2. Pass every record to the tools exactly as given. Do not add a missing location factor, re-date an instrument or correct a reported figure.
3. Scope 2 needs both a location-based (grid-average) and a market-based total. Contractual instruments reduce the market-based figure only when:
   - they are retired;
   - their vintage matches the reporting year;
   - their market matches the consuming site;
   - they are claimed once.
4. For `SC3-CAT3`, set `scope2_includes_td_losses` from the `location_factors_include_td_losses` field of ENT-A's `esg_scope2_dual_report` output before you call `esg_scope3_calculate`.
5. Every number you report must come from a tool call or the input files. Report location-based and market-based Scope 2 side by side.
6. Use calibrated language. A passing inventory is "ready for internal review", not "compliant" or "assured". Carbon credits are disclosed separately from gross emissions and are never described as reductions.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"ENT-A": "<status>"}`.
