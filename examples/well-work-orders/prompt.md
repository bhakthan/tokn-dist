# Task: pre-job safety and design review for six pad work orders

You are the well-site engineering lead for an onshore gas-condensate pad. Six work orders — drilling, perforating, fracturing, compression and an emissions disclosure — are queued for next week. Each must clear the harness's well-control, well-integrity, process-safety and emissions gates and agree with its own design calculation before crews mobilise. A missed barrier or an over-confident emissions figure is a regulatory and safety event, not a paperwork issue.

The data is synthetic but realistic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/work_orders.json` | `OG-1`…`OG-6`: ordered tool steps with exact `payload`s, plus any `plan` fields |
| `demo-input/operating_limits.json` | The asset's limits (MAASP, design envelope, emissions confidence caps, mud-weight margins) |

## Items to assess

`OG-1`, `OG-2`, `OG-3`, `OG-4`, `OG-5`, `OG-6`

## Status vocabulary (use exactly one per item)

- `approve`: every step completed without a gate refusal and the plan agrees with the tool outputs.
- `revise`: every step completed, but the plan disagrees with a tool output (mud weight outside the computed window, planned compressor stages not equal to the computed stages, or a drilling status other than `operating`). The engineer must redesign.
- `blocked`: a domain gate refused a step (two-barrier rule, kick indicators, MAASP or casing test, design envelope, undeclared emissions method or confidence above its cap). The job does not proceed.

## Rules

1. **Run every step in order with its payload unchanged.** Do not correct a payload to get past a gate.
2. **Precedence:** `blocked` > `revise` > `approve`.
3. **Mud weight:** the drilling `mud_weight_ppg` must lie within [`min_mud_weight_ppg`, `max_mud_weight_ppg`] returned by `og_mud_weight` for the same well, inclusive. `og_drill_operation` alone does not check the trip or kick-tolerance margins.
4. **Compression:** compare `plan.planned_stages` with the `stages` returned by `og_compression_design`; report the compression ratio.
5. MAASP is exceeded only when treating pressure is strictly above it. Report each emissions figure with its method and confidence cap.
6. Every number you report must come from a tool call, not mental arithmetic.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"OG-1": "<status>"}`.
