# Task: trust disposition for grid foundation-model OPF predictions

You are a power-systems engineer on an operator-support team. A GridSFM surrogate produces hour-ahead AC optimal-power-flow predictions in milliseconds, and the desk wants to use them as dispatch advisories. Before any prediction reaches an operator, it must be independently checked against power-flow physics — the surrogate's own feasibility flag and confidence are not evidence.

The data is synthetic but realistic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/predictions.json` | Six surrogate predictions (`PRED-A`…`PRED-F`) for a 3-bus reduced pocket: buses, generators, loads, branches, losses, and the surrogate's self-reported feasibility and confidence |
| `demo-input/warm_start_timings.json` | Classical AC-OPF solve time per hour, cold start vs. seeded with the prediction |
| `demo-input/deployment_context.json` | The size of the full operating model the pocket is cut from, and the requested use |

## Items to assess

`PRED-A`, `PRED-B`, `PRED-C`, `PRED-D`, `PRED-E`, `PRED-F`

## Status vocabulary (use exactly one per item)

- `operational_advisory`: the independent verifier finds no violations and the surrogate also reports feasible (disposition OPERATIONAL). It may inform the operator; actuation stays human-approved.
- `hold_for_review`: the verifier finds no violations but the surrogate reports itself infeasible or unknown (disposition REVIEW).
- `warm_start_only`: the verifier finds only voltage, generator-limit or thermal violations (disposition WARM_START) and seeding a classical solver with it is at least as fast as a cold start (speedup ≥ 1.0).
- `reject`: the verifier finds a power-balance or flow-voltage-consistency violation (disposition REJECTED), or the disposition is WARM_START but the seeded solve is slower than the cold start (speedup < 1.0).

## Rules

1. **The independent verifier decides.** Run `verify_surrogate_solution` on each prediction exactly as given; the surrogate's `surrogateFeasibility` and `surrogateConfidence` never upgrade a status.
2. Verifier limits: bus voltage strictly outside [vMinPU, vMaxPU], generator output beyond its limits, or branch |S| above its rating is a violation; a value exactly at a limit is not. Power balance fails when |generation − load − losses| exceeds 0.01 pu.
3. Run `evaluate_warm_start` for every prediction whose disposition is WARM_START; speedup = baseline / warm.
4. Run `select_model_tier` and `assess_ood` on the full-network bus count. The deployment confidence cap is the lower of the OOD cap and the per-prediction cap; it limits how confidently you may describe any prediction but does not change its status.
5. Report, per item: disposition, violations by kind, power-balance residual, and (where run) the warm-start speedup.
6. Every number you report must come from a tool call, not mental arithmetic.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"PRED-A": "<status>"}`.
