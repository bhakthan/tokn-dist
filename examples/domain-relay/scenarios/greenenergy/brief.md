# Brief — green-finance eligibility screen for five renewable projects

You are the technical adviser to a green-bond committee. Five projects — three electrolysers and two renewable generators — have applied for allocation. The committee funds only projects whose carbon intensity or bankable yield and EU Taxonomy screening hold up under the harness's deterministic checks. Mislabelled hydrogen or an incoherent yield case would undermine the whole bond framework.

The data is synthetic but realistic. Everything you need is in `inputs/`:

| File | Contents |
|---|---|
| `inputs/hydrogen_projects.json` | `GH-1`…`GH-3`: exact `compute_hydrogen_production` payloads |
| `inputs/generation_projects.json` | `GH-4` (solar) and `GH-5` (wind): exact yield-tool payloads with P10/P50/P90 |
| `inputs/taxonomy_screens.json` | One exact `screen_eu_taxonomy` payload per project |

## Items to assess

`GH-1`, `GH-2`, `GH-3`, `GH-4`, `GH-5`

## Status vocabulary (use exactly one per item)

- `eligible`: every tool call for the project completed; hydrogen is classified green (RFNBO carbon intensity at or below the threshold) or the yield case sets both the YieldSimulated and P90Present gates; the Taxonomy screen sets TaxonomyScreened.
- `not_eligible`: every tool call completed, but the hydrogen carbon intensity exceeds the RFNBO threshold (classified grey).
- `rework`: at least one tool call for the project returned an error or was refused by a domain gate (incomplete DNSH screen, incoherent exceedance values, missing yield data source). The applicant must resubmit.

## Rules

1. **Run two tools per project, payloads unchanged:** the hydrogen or yield tool named in its input file, and `screen_eu_taxonomy`.
2. **Precedence:** `rework` > `not_eligible` > `eligible`.
3. The RFNBO carbon-intensity threshold is the one the tool applies (kgCO2e/kgH2); a value exactly equal to it passes.
4. Exceedance values must satisfy P90 < P50 < P10. The Taxonomy screen needs all six DNSH objectives.
5. For each project report the carbon intensity and hydrogen colour or the P50/P90 values, plus the DNSH outcome; quote any tool error.
6. Every number you report must come from a tool call, not mental arithmetic.

## Deliverable

`result.json` and `RESULT.md`, as described in your stage instructions.
