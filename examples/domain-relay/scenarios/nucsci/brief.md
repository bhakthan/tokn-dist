# Brief — criticality-safety QA review of spent-fuel pool storage packages

You are a nuclear criticality safety reviewer at a commercial power plant. Six calculation packages support the storage of low-enriched commercial fuel in the spent-fuel pool, the cask loading pit and the new fuel vault. Before any package goes into a Safety Analysis Report (SAR) chapter, QA wants a defensible review of each one.

The data is synthetic. Everything you need is in `inputs/`:

| File | Contents |
|---|---|
| `inputs/packages.json` | Six packages: `keff_mean`, `keff_sigma`, `max_burnup_gwd_thm`, `has_decay_heat_analysis`, `has_shielding_analysis`, `nuclear_data`, and a `sar_request` |
| `inputs/benchmark_validation.json` | The code-validation report for each package: `n_cases` and `mean_bias` (delta-k) |
| `inputs/acceptance_criteria.json` | The review thresholds, restated from the rules below |

## Items to assess

`PKG-A`, `PKG-B`, `PKG-C`, `PKG-D`, `PKG-E`, `PKG-F`

## Status vocabulary (use exactly one per item)

- `acceptable`: every gate passes and keff + 2σ is below 0.90.
- `engineer_review`: every gate passes, but keff + 2σ is at least 0.90 and below the USL of 0.95, or burnup is at least 40 and below 45 GWd/tHM.
- `revalidate`: the criticality gates pass, but the benchmark validation is inadequate: fewer than 20 cases, or |mean_bias| above 0.01.
- `blocked`: a hard gate fails. Either keff + 2σ is at or above the USL of 0.95, or burnup is at or above 45 GWd/tHM without both a decay-heat and a shielding analysis, or `generate_sar_section` refuses the draft for a missing benchmark reference.

## Rules

1. Precedence is `blocked` > `revalidate` > `engineer_review` > `acceptable`.
2. Gate on the upper bound keff + 2σ, never on the mean. Show the arithmetic for each package. "At or above" includes equality.
3. A benchmark bias exactly at ±0.01 is within the limit. Exactly 20 cases meets the minimum.
4. Call `generate_sar_section` once per package with its `sar_request` fields exactly as written (`section_type`, `topic`, `benchmark_ref`) and `output` set to `sar/<id>.md`. Do not invent or fill in a missing `benchmark_ref`. A refusal is evidence, not a tool failure to work around.
5. Call `query_icsbep` with `query` `LEU-COMP-THERM` and `fissile` `LEU`, and report how many cases it returned. In this build, the case list is a stub, so benchmark adequacy comes from `inputs/benchmark_validation.json`.
6. Call `process_nuclear_data` with each distinct `nuclear_data` `material` and `temperature_k`, and `output_dir` `nuclear_data/ace`. Report `sab_included`: the pool is water-moderated, so thermal-scattering data must be present.
7. Every SAR section produced here is a DRAFT for a qualified engineer. Use calibrated language: subcritical with margin to the USL, not "safe".

## Deliverable

`result.json` and `RESULT.md`, as described in your stage instructions.
