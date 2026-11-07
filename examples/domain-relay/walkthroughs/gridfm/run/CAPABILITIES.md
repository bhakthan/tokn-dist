# CAPABILITIES — gridfm scout pass

Scope: BRIEF.md, inputs/ (3 files), tokn-self/introspect-slice.json, tokn-self/DOMAIN-README.md, and the live tool list. Items PRED-A..PRED-F are not assessed here.

Evidence sources:
- Live tool list: `verify_surrogate_solution`, `select_model_tier`, `assess_ood`, `evaluate_warm_start`, `list_verification_checks`, `screen_n1_contingencies`.
- `list_verification_checks` output (tool call): checks = voltage_bound, generator_active_limit, generator_reactive_limit, thermal_limit, power_balance, flow_voltage_consistency; tolerances powerBalancePU 0.01, thermalSlack 0, consistencyPU 0.05; tiers GridSFM-Open (≤4000 buses), GridSFM-Premier (≤80000 buses).

## Domain tools that apply

| tool (exact name) | item(s) / input file it applies to | input fields needed and present in inputs/ |
|---|---|---|
| `verify_surrogate_solution` | PRED-A, PRED-B, PRED-C, PRED-D, PRED-E, PRED-F (headline check for every item) | `prediction` = `inputs/predictions.json` `cases[i].prediction`: `scenario` (baseMVA, buses[vMagPU, vAngRad, vMinPU, vMaxPU], generators[pgPU, qgPU, pMin/pMax, qMin/qMax], loads, branches[sFlowPU, ratingPU], lossesPU), `surrogateFeasibility`, `surrogateConfidence`, `tier`. All present. |
| `list_verification_checks` | all items (confirms tolerances used in the gates section) | none. Already called. |
| `evaluate_warm_start` | only items whose verifier disposition is WARM_START (not known until verification runs) | `scenario`, `baseline_seconds`, `warm_seconds` from `inputs/warm_start_timings.json` `timings[i]` (labels A–F). All present. |
| `select_model_tier` | deployment, using full-network size | `bus_count` = 3700 from `inputs/deployment_context.json` `full_network_bus_count`. Present. |
| `assess_ood` | deployment, OOD cap | `bus_count` = 3700 (present). Optional `independently_verified`: not in inputs; ASSUMPTION: leave unset, which defaults to unverified. |
| `screen_n1_contingencies` | NOT APPLICABLE to this brief | Needs `base` and `cases[{label, prediction}]`. No contingency cases exist in inputs/. Do not run. |

## Gates and rules that will constrain the answer

Verifier (`verify_surrogate_solution`, per BRIEF rule 1–2 and DOMAIN-README):
- Independent verifier decides. `surrogateFeasibility` and `surrogateConfidence` never upgrade a status.
- Voltage: violation only if |V| is strictly outside [vMinPU, vMaxPU] (boundary is not a violation).
- Generator: violation if output is beyond its limits (P and Q). Thermal: violation if |S| > ratingPU (thermalSlack 0).
- Power balance: fails when |generation − load − losses| > 0.01 pu (powerBalancePU 0.01).
- Flow-voltage consistency: tolerance consistencyPU 0.05, and per DOMAIN-README it runs only "when admittance is supplied". Inputs contain no admittance data. ASSUMPTION: this check will be skipped or reported as not run. Must be confirmed from the verifier output, not assumed.

Disposition to status mapping (BRIEF status vocabulary; DOMAIN-README trust gate table):
- verifier feasible + surrogate feasible → disposition OPERATIONAL → `operational_advisory`.
- verifier feasible + surrogate infeasible or unknown → disposition REVIEW → `hold_for_review`.
- verifier bound/limit violations only → disposition WARM_START → `warm_start_only` if speedup ≥ 1.0, else `reject`.
- power-balance or flow-voltage-consistency breach → disposition REJECTED → `reject`.
- Any `operational_advisory` remains human-gated for actuation (brief; DOMAIN-README hooks, not visible, see Gaps).

Warm-start (`evaluate_warm_start`, BRIEF rule 3):
- speedup = baseline / warm. Speedup < 1.0 means the seed hurt, which forces `reject` for WARM_START items.
- Speedup far above the band is flagged for scrutiny, not celebrated (DOMAIN-README).

Confidence caps (BRIEF rule 4; DOMAIN-README OOD section):
- Evidence tiers: verified-solver 1.00 > surrogate-verified 0.90 > surrogate-raw 0.50 > extrapolated 0.30.
- A grid at or near the validated bus ceiling (≥90%) is OOD and capped at extrapolated (0.30).
- Tier ceilings: GridSFM-Open ≤4000 buses; GridSFM-Premier ≤80000 buses. A grid beyond the largest tier is refused (scale gate).
- 3700 / 4000 = 92.5%, which is ≥90%. Per the README this predicts OOD → cap 0.30. ASSUMPTION from README text; confirm with `assess_ood` before quoting.
- Deployment cap = lower of OOD cap and per-prediction cap. The per-prediction cap has no tool (see Gaps).
- Caps limit how confidently predictions may be described. They do not change status.

Calibrated language:
- Describe results as verifier findings ("the independent verifier found …"), not as "safe" or "feasible". Never repeat the surrogate's self-reported feasibility as evidence.
- Quote tool outputs for every number. No mental arithmetic (BRIEF rule 6).

## Gaps

1. The introspect slice (`tokn-self/introspect-slice.json`) lists the mode and domain names but no tool list. The live tool list is the ground truth used here.
2. DOMAIN-README describes 2 hooks (block actuation on non-OPERATIONAL predictions; flag unbacked feasibility claims) and 2 slash commands (`/gridfm`, `/tier`). None of these appear in my tool list. This is a README/tool-list disagreement: I cannot verify or invoke them. Actuation control must come from the brief's human-approval rule and reasoning.
3. Per-prediction confidence cap: no tool computes it. `surrogateConfidence` is self-reported and cannot be used as evidence. Reasoning only.
4. Full-network to pocket representativeness: no tool certifies that the 3-bus reduced pocket is representative of the 3700-bus network. `assess_ood` uses bus count only. This must be stated as a limitation.
5. Flow-voltage consistency needs admittance data that is absent from inputs/. Its result may be unavailable (see verifier gate above).
6. Disposition-to-status mapping, the speedup ≥ 1.0 rule, and the human-approval rule are not tools. They are applied by reasoning from BRIEF.md.
7. Timings are synthetic and the warm-start speedup is a single run per hour. No tool quantifies variance, so speedup claims are single-sample.
8. Verifier output format (violation kinds, residual values) is not known until `verify_surrogate_solution` runs. Reporting "violations by kind" depends on that output.
