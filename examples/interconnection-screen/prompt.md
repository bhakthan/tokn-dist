# Task: N-1-1 and grid-forming screen for an interconnection cluster

You are a transmission planning engineer. Five generation/storage interconnection requests in the same queue cluster each sit in a different zone. The planning committee meets next week and needs a defensible per-request disposition: the N-1-1 (NERC TPL-001-4 P6/P7) results are in, and the inverter-based-resource (IBR) registry has been updated with each request's proposed additions.

The data is synthetic but realistic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/n11_study.json` | Per request: the zone, the outage elements (`first_contingencies`), and post-contingency results for each outage pair (`pair_results`, keyed `firstID\|secondID`) |
| `demo-input/ibr_registry.json` | The existing IBR fleet (`resources`, GFM/GFL, MW, zone, IEEE 2800 validation) and each request's proposed `additions` |

## Items to assess

`IR-1`, `IR-2`, `IR-3`, `IR-4`, `IR-5`

## Status vocabulary (use exactly one per item)

- `approve`: the IBR stability gate passes and the N-1-1 screen reports no violations.
- `approve_with_conditions`: the IBR stability gate passes and the N-1-1 screen reports only HIGH-severity violations; approval is conditional on the corrective actions those violations require.
- `reject`: the N-1-1 screen reports at least one CRITICAL violation.
- `blocked`: the IBR stability gate blocks the request's expansion (adds grid-following capacity with no grid-forming capacity and pushes zonal GFL penetration past the threshold).

## Rules

1. **Precedence:** `blocked` > `reject` > `approve_with_conditions` > `approve`. A gate block overrides a clean N-1-1 screen.
2. Screen each request on its own: run `powergrid_n1_1_screen` with that request's `first_contingencies` and `pair_results`, and run `powergrid_ibr_stability_gate` with the full existing `resources` plus only that request's `additions`.
3. N-1-1 limits govern, not N-1 criteria: bus voltage must stay within 0.85–1.10 pu and branch loading at or below 115% of emergency rating. A thermal overload is CRITICAL only above 115% × 1.15; voltage below 0.80 pu or any loss of synchronism is CRITICAL. Values exactly at a limit are not violations.
4. The GFL penetration threshold is 30% of zonal IBR capacity; exactly 30.0% does not exceed it.
5. Report each request's post-expansion zonal GFL penetration as the gate returned it, and quote the violation severities the N-1-1 screen returned.
6. Every number you report must come from a tool call, not mental arithmetic.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"IR-1": "<status>"}`.
