# Task: release gate for a quarterly energy & carbon board pack

You are the energy-analytics lead for a multi-site commercial organisation. Six analyses were requested for the Q3 board pack, each tied to a specific energy-domain tool with an analyst-prepared payload. The audit & risk committee will only accept figures that passed the harness's disclosure gates, so you must run each analysis exactly as submitted and decide what can be released.

The data is synthetic but realistic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/analysis_requests.json` | The six requests (`EN-1`…`EN-6`): purpose, the tool to call, and the exact `payload` |
| `demo-input/release_policy.json` | The release policy: which data layers need a caveat and how to word it |

## Items to assess

`EN-1`, `EN-2`, `EN-3`, `EN-4`, `EN-5`, `EN-6`

## Status vocabulary (use exactly one per item)

- `release`: the tool call completed and the result rests on metered or estimated data.
- `release_with_caveat`: the tool call completed but the result rests on modeled or assumed data; it ships labelled as a projection with its confidence.
- `blocked`: a domain gate refused the call (missing provenance, missing or zero discount rate, missing time horizon or assumptions, undeclared GHG scope or accounting method, missing market disclaimer, or a blocked certainty term in the payload). It does not ship this quarter.

## Rules

1. **Submit each payload exactly as given.** Do not add, remove, or correct fields — a gate refusal is the finding, not a problem to work around.
2. **Precedence:** `blocked` > `release_with_caveat` > `release`.
3. The data layer is the payload's `provenance` field when present; otherwise it is the `provenance` the tool returns.
4. A discount rate of 0.0 counts as an undisclosed discount rate.
5. For every blocked item, quote the gate's reason. For every released item, report the provenance and, where the tool returns one, the confidence.
6. Every number you report must come from a tool call, not mental arithmetic.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"EN-1": "<status>"}`.
