# CAPABILITIES — appsec triage of six static-analysis candidates (AS-01..AS-06)

Scout notes: sources read are BRIEF.md, inputs/threat_model.json, inputs/candidates.json, inputs/dataflows_and_controls.json, tokn-self/introspect-slice.json, tokn-self/DOMAIN-README.md. The appsec tool list visible to the scout has 20 `appsec_*` tools, matching the introspect slice. No item is assessed here.

## Domain tools that apply

| tool (exact name) | applies to | input fields needed and present in inputs/ |
|---|---|---|
| appsec_build_threat_model | whole run (call first) | assets, boundaries, attackers, objectives: all present in threat_model.json, pass as-is |
| appsec_record_trust_boundary | the 3 boundaries in threat_model.json | name, description, crosses: names present; description from boundaries text |
| appsec_record_surface | SURF-SEARCH, SURF-PROFILE, SURF-UPLOAD, SURF-WEBHOOK, SURF-LOGIN, SURF-SESSION | id, name, paths, risk_area: all present in candidates.json surfaces |
| appsec_log_candidate | AS-01..AS-06 (after their surface is recorded) | id, rule_id, anchor, surface, description, paths: present. `title` is NOT a parameter; drop it. Use rule_id and anchor verbatim |
| appsec_trace_dataflow | AS-01..AS-06 | source, sink, transformations, sanitized: present in dataflows_and_controls.json; use the `sanitized` boolean verbatim |
| appsec_check_control | AS-01..AS-06 | sink, control_type, location, effective, gaps: present; use the `effective` boolean verbatim |
| appsec_suppress_candidate | any item whose trace or control boolean makes it suppressed | candidate_id, rationale: rationale from the recorded booleans |
| appsec_validate_candidate | all six items (one disposition each) | candidate_id, disposition, rationale, evidence (tool outputs), validation_method (static review only), proof_gap: evidence and method present; disposition enum is reportable/suppressed/not_applicable/deferred (no "blocked", see Gaps) |
| appsec_record_proof_gap | each reportable item (no dynamic validation was performed) | candidate_id, gap, blockers: gap and blockers must be stated by reasoning; not in inputs |
| appsec_coverage_status | after all items (read-only check) | none |
| appsec_finalize_scan | end of run | completeness (must be "partial"), summary: summary text is reasoning |

Not applicable to this brief: appsec_scope_target, appsec_build_inventory, appsec_mark_reviewed, appsec_find_sinks (no repository is provided; inputs are synthetic JSON). appsec_assign_severity, appsec_author_finding, appsec_analyze_attack_path: no severity or attack-path output is requested by the brief; do not use them unless the brief changes. appsec_record_asset, appsec_record_exclusion: no asset or exclusion is requested beyond the threat model.

## Gates and rules that will constrain the answer

- Identity (BRIEF rule 1; DOMAIN-README "stable finding identity"): `rule_id` must be `<category>.<control-family>`, two segments, with no file extension, no line number (`L214`, `line-12`, `:12`), and no scan ID. `anchor` must not be just a number. An identity that breaks these rules is `blocked`, whatever its severity. Do not rewrite identities. Visible in inputs: AS-03 rule_id `path-traversal.archive-extract-L214` contains a line-number segment; AS-06 anchor `1187` is numeric-only. The planner must apply this rule; the scout assigns no status.
- Dataflow and control booleans (BRIEF rule 2): use the tools' `sanitized` and `effective` values. "The name of a transformation is not evidence"; a sanitizer in the path counts only when `sanitized` is `true`.
- Disposition (BRIEF rule 3, verbatim): "A candidate is `suppressed` if `sanitized` is `true` or `effective` is `true`. Otherwise it is `reportable`."
- Calibrated language (BRIEF rule 4): nothing is dynamically validated. Describe every reportable item as a candidate, not a confirmed vulnerability. Coverage is partial, and must be stated.
- Trust boundary (BRIEF rule 5): each reportable candidate must name the boundary it crosses, taken from threat_model.json boundaries.
- Coverage honesty (DOMAIN-README gate 2): "CompletenessUnknown never defaults to complete"; a partial review cannot finalize as an unstated claim of completeness.
- Confidence (DOMAIN-README "Confidence"): derived from the validation method actually used. Static review only means no dynamic confidence; absence of proof is not proof of absence; record the proof gap.
- Severity discipline (gate 3): hedged rationale blocks high/critical; a concrete attack path is required. No severity is requested, so do not assign one.
- Phase separation (gate 4): discovery logs candidates; validation assigns one disposition per candidate.
- Secret hygiene (gate 5): no credentials in finding text or evidence.
- Read-only authority (gate 1, stage instructions): write_file and all mutating tools are denied; deliverables are returned as blocks, not written.

## Gaps

1. Status "blocked" has no tool. appsec_validate_candidate accepts reportable/suppressed/not_applicable/deferred only. "blocked" must be handled by reasoning and recorded in the final answer. Do not map it to "deferred" or "not_applicable".
2. No tool checks identity stability. appsec_log_candidate may accept or reject an identity, but the rule set above is not confirmed as enforced by any tool. The planner must check identities by reasoning and must not depend on ledger acceptance.
3. No tool maps a candidate to a trust boundary. The mapping (surface and path to boundary) is reasoning from threat_model.json; the scout found no explicit surface-to-boundary field in the inputs.
4. No dynamic validation is available (no runtime, no network, no test harness). Every reportable item stays a candidate with a recorded proof gap.
5. No deliverable write path. result.json and RESULT.md cannot be written by any tool under this authority; they must be returned as blocks.
6. Disagreement, README vs tool list: the README and introspect slice say appsec has "8 hooks, 14 commands, 12-state lifecycle". None of these is visible in the scout's tool list, so they cannot be verified here; the tool list is trusted.
7. Disagreement, authority vs tool list: the scout's tool list still shows mutating tools (write_file, edit_file, apply_unified_diff, git_commit, run_command, and others). The README says the authority scope denies them. The denial is at authority level, not absence; they must not be used.
8. Deterministic engines (`go-ssa`, README "Deterministic analysis engines") are Go-only and are not exposed as a tool in the scout's list. The inputs contain no Go source. Not applicable.
9. Candidate-to-control mapping for AS-02 and AS-05 (controls effective, dataflow sanitized) and for AS-01, AS-03, AS-04, AS-06 (not effective) is recorded in inputs as reviewer observations. The scout has not verified them against source; the tools only record them.
10. Coverage of the candidate queue: the brief covers six items from a static pass. The queue's completeness beyond these six is unknown; the scan must be declared partial.
