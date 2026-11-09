# Task: triaging a static-analysis queue before the release review

You are an application-security engineer. A static-analysis pass over a synthetic order-portal service raised six candidate findings. The release board wants a defensible triage before Friday's review. This is **defensive triage only**: decide what goes into the report. Do not write or describe exploit code.

The data is synthetic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/threat_model.json` | Assets, trust boundaries, attacker capabilities and objectives. Pass it to `appsec_build_threat_model` as-is |
| `demo-input/candidates.json` | Six attack surfaces and six candidates. Each candidate has a `rule_id`, a semantic `anchor` and a surface |
| `demo-input/dataflows_and_controls.json` | Per candidate, the reviewer's source→sink trace and the control check on that sink |

## Items to assess

`AS-01`, `AS-02`, `AS-03`, `AS-04`, `AS-05`, `AS-06`

## Status vocabulary (use exactly one per item)

- `reportable`: the identity is stable, the dataflow is not sanitized, and the control on the sink is not effective. It goes in the report as an unvalidated candidate.
- `suppressed`: the identity is stable, and either the dataflow is sanitized or the sink's control is effective. Record the reason it was dropped.
- `blocked`: TOKN's identity-stability rules reject the candidate's `rule_id` or `anchor`. It cannot be tracked across scans, so it goes back to the analyzer for re-identification. Do not triage it further.

## Rules

1. **Identity comes first.** Record each surface with `appsec_record_surface`, then log each candidate with `appsec_log_candidate` using the exact `rule_id` and `anchor` given. A `rule_id` must have the form `<category>.<control-family>`. It must not contain a file extension, a line number (`L214`, `line-12`, `:12`) or a scan ID. An `anchor` must not be just a number. If an identity breaks these rules, the item is `blocked`, whatever its severity looks like. Do not rewrite the identity to make it pass.
2. Run `appsec_trace_dataflow` and `appsec_check_control` with the values given, and use the `sanitized` and `effective` booleans the tools return. The name of a transformation is not evidence. A sanitizer that appears in the path does not count unless `sanitized` is `true`.
3. A candidate is `suppressed` if `sanitized` is `true` or `effective` is `true`. Otherwise it is `reportable`.
4. Nothing here has been validated dynamically. Describe every `reportable` item as a candidate, not a confirmed vulnerability. Coverage is **partial**: say so explicitly.
5. Name the trust boundary each reportable candidate crosses, taken from the threat model.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"AS-01": "<status>"}`.
