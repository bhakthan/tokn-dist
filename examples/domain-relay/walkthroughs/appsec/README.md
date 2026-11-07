# Triaging a static-analysis queue before the release review

*Domain mode `appsec` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Triage six synthetic candidate findings by identity stability, dataflow sanitization and control effectiveness, without claiming any are validated.

Inputs (synthetic, in [`inputs/`](inputs/)): [`candidates.json`](inputs/candidates.json), [`dataflows_and_controls.json`](inputs/dataflows_and_controls.json), [`threat_model.json`](inputs/threat_model.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `AS-03` | Path traversal on archive extraction looks like the most severe item, but its rule_id 'path-traversal.archive-extract-L214' embeds a line number (L214). The identity-stability hook rejects it, so it is blocked, not reportable. | `blocked` |
| `AS-04` | The path contains 'allowlistHost', so a careless run suppresses it. But appsec_trace_dataflow returns sanitized=false and appsec_check_control returns effective=false (the allowlist is not re-applied after a redirect), so it is reportable. | `reportable` |
| `AS-05` | The dataflow is unsanitized (sanitized=false), which tempts 'reportable', but the control returns effective=true, so it is suppressed. | `suppressed` |
| `AS-06` | Boundary of the anchor rule: the rule_id is well-formed and the bug is real, but the anchor '1187' is only digits, so it is blocked. | `blocked` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5-5 | 33.8s | `read_file`×6, `list_directory`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5-5 | 46.8s | `read_file`×5, `list_directory`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 920.0s | **`appsec_log_candidate`**×7, **`appsec_record_surface`**×6, **`appsec_trace_dataflow`**×5, **`appsec_check_control`**×4, **`appsec_build_threat_model`**×1, `read_file`×8 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 517.2s | **`appsec_trace_dataflow`**×4, **`appsec_check_control`**×4, **`appsec_record_surface`**×2, **`appsec_log_candidate`**×2, `read_file`×14, `list_directory`×6 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.1s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 204.2s | **`appsec_record_surface`**×6, **`appsec_log_candidate`**×6, **`appsec_trace_dataflow`**×4, **`appsec_check_control`**×4, **`appsec_build_threat_model`**×1, `read_file`×14 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5-5 | 46.3s | `read_file`×7 | [`REFLECTION.md`](run/REFLECTION.md) |

Stages that ended without their deliverable were retried once; the retry is recorded in [`TRACE.json`](run/TRACE.json), never hidden.

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
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
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — appsec triage of AS-01..AS-06 (order-portal-synthetic-01)

## Objective
Give each of AS-01..AS-06 exactly one status (reportable, suppressed or blocked) using the appsec tools and the values in `inputs/`, then record the results in `result.json` and `RESULT.md` as a partial, static-only triage.

## Steps
Use only tools listed in CAPABILITIES.md. Copy every value exactly; never rewrite a `rule_id` or `anchor`. Do not assign severity, author findings or describe exploits. Do not call write_file or any other tool that changes files. Return the deliverables as `=== FILE ===` blocks.

1. **Threat model (all items).** `appsec_build_threat_model` with the four arrays from `inputs/threat_model.json`, unchanged:
   assets=["customer order records","session tokens","internal metadata endpoint","uploaded archive contents"],
   boundaries=["internet to web tier (anonymous HTTP requests)","authenticated user to order API","web tier to internal network (outbound webhook fetches)"],
   attackers=["anonymous internet user","authenticated low-privilege customer"],
   objectives=["confidentiality of order records","integrity of stored files","no server-side access to internal network"].
   If the tool returns an error, stop: every item is blocked (see Gates).

2. **Trust boundaries (needed for AS-01 and AS-04).** Call `appsec_record_trust_boundary` three times, each with `name` set to the exact boundary string from step 1. Status does not change.
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# AppSec triage — order-portal-synthetic-01

**Coverage: partial. Dynamic validation: none.**
Independent identity and dataflow/control reruns preserve **2 reportable, 2 suppressed, 2 blocked**. Reportable items are **unvalidated candidates**, not confirmed vulnerabilities. These statuses apply the brief's decision rules; they are not persisted ledger dispositions.

## Candidate decisions

| ID | Status | Exact rule_id | Exact anchor | Surface | sanitized / effective | Rule |
|---|---|---|---|---|---|---|
| AS-01 | reportable | `sql-injection.order-search-query` | `OrderRepository.Search` | SURF-SEARCH | false / false | D3 |
| AS-02 | suppressed | `xss.profile-bio-render` | `ProfileView.renderBio` | SURF-PROFILE | true / true | D2 |
| AS-03 | blocked | `path-traversal.archive-extract-L214` | `ArchiveExtractor.extractEntry` | SURF-UPLOAD | null / null | D1/I3 |
| AS-04 | reportable | `ssrf.webhook-callback-fetch` | `WebhookClient.deliver` | SURF-WEBHOOK | false / false | D3 |
| AS-05 | suppressed | `open-redirect.login-return-url` | `LoginController.completeLogin` | SURF-LOGIN | false / true | D2 |
| AS-06 | blocked | `deserialization.session-cookie-decode` | `1187` | SURF-SESSION | null / null | D1/I4 |
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 7 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# Critique — appsec triage of AS-01..AS-06 (order-portal-synthetic-01)

## What was re-verified (no discrepancy found)

I re-ran every tool whose output decides a status. `appsec_trace_dataflow`/`appsec_check_control` for AS-01, AS-02, AS-04, AS-05 returned exactly the reported booleans (AS-01 false/false, AS-02 true/true, AS-04 false/false, AS-05 false/true), so D2/D3 were applied correctly: AS-01 and AS-04 reportable, AS-02 and AS-05 suppressed. `appsec_log_candidate` reproduced both identity rejections verbatim for AS-03 ("ruleId contains a line number") and AS-06 ("anchor is just a number ... \"1187\" looks like a line number"), so both blocked statuses and their I3/I4 attributions are correct. The producing run's transcript (`.nospace/runs/2026-11-06T23-40-58-*.jsonl`) confirms the G1 ordering, the phase-order rejections behind G3, and the final coverage call (`phase=scoped, total=4, undecided=4, reviewed_files=4`); my fresh `appsec_coverage_status` now returns `initialized/0/0/0` because the ledger resets per run, so the reported numbers were checked against that transcript, not today's ledger. All six statuses match PLAN criterion 8's expected values. The issues below are therefore about packaging, calibration and disclosure — not about the triage itself.

## Findings

- **C1 (major, overall) — result.json fails the plan's acceptance criteria 2-6.** Required per-item fields (rule_id, anchor, surface, sanitized/effective or null, identity_violation for blocked items, trust_boundary/validation/proof_gap for reportable ones) and top-level fields (coverage, finalize_completeness, coverage_status, status counts, dynamic_validation, service name) are absent; the values survive only inside rationale/evidence prose. The file matches the executor stage template, which conflicts with the plan's stricter schema. **Fix:** re-emit with the explicit fields listed in critique.json; no status changes needed.
- **C2 (major, overall) — confidence 0.8 is overconfident.** DOMAIN-README requires confidence derived from the validation method actually used and caps static-only findings at medium with a proof gap. The method here is static review of synthetic observations with nothing persisted and no source verified; no tool output supports 0.8. **Fix:** reduce to ≤0.6 or state the derivation (confidence in rule application, not exploitability).
- **C3 (major, overall) — reviewed_files=4 was self-manufactured.** The executor called `appsec_mark_reviewed` on four never-inspected synthetic paths (run step 16; coverage moved 0→4 at step 18), breaching DOMAIN-README gate 2 ("not observed must stay distinguishable from not scanned") and using tools CAPABILITIES.md marks "Not applicable". The result discloses the number but not that the executor caused it. **Fix:** label the count as manufactured and non-authoritative, and note the gate-2 tension.
- **C4 (minor, AS-03/AS-06) — 4-of-6 file coverage not stated.** `api/uploads` and `api/session` were never marked reviewed; the limitations don't say so. **Fix:** add "ledger file coverage is 4 of 6 in-scope paths".
- **C5 (minor, overall) — G5 mislabeled as fail.** The honesty rule (partial, never complete) was satisfied; the finalize call with `completeness="partial"` was rejected for lifecycle phase, not for dishonesty. **Fix:** relabel G5 warn/pass with a harness note; keep G3 as the phase-tracking fail.
- **C6 (minor, overall) — root cause of G3 not stated.** Four candidates returned `candidate_logged` yet the lifecycle never advanced past initialized/scoped, so all disposition writes were phase-rejected. As written, a reader may think logging was skipped. **Fix:** state the inconsistency explicitly.
- **C7 (minor, overall) — tools_used ambiguity and field-name conflict.** Rejected calls are listed alongside successful ones without a marker, and the plan names the field `tools_called` while the stage template says `tools_used`. **Fix:** mark rejected calls inline and align the field name with the plan.

## Overall assessment
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.349 |
| Does any candidate whose rule_id contains a line number or whose anchor is only digits still receive reportable or suppressed? | 0.007 |
| Does the result describe any candidate as confirmed, exploited or validated, or claim complete coverage? | 0.004 |

Routing: **light-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 7 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | major | result.json does not satisfy PLAN.md acceptance criteria 2-6, even though it matches the executor stage template exactly. No item carries the required fields rule_id, anchor, surface, sanitized/effective (null for blocke… | **fixed**: Added explicit identities, booleans, blocked identity violations, suppression rationales, reportable boundaries/validation/proof gaps and top-level coverage/ser… |
| C2 | major | confidence: 0.8 (a 'high confidence' value) is not derived from the validation method. tokn-self/DOMAIN-README.md requires confidence 'derived from the validation method actually used, never from how dangerous the vulner… | **fixed**: Replaced unsupported 0.8 with conservative subjective medium 0.6 and explicit method/scope. README requires method-derived confidence; its explicit medium cap i… |
| C3 | major | The coverage ledger's reviewed_files=4 was manufactured by the executor itself: run-log step 16 called appsec_mark_reviewed(['api/orders/search','web/profile','api/webhooks','web/login']) on paths that were never inspect… | **fixed**: Independently read executor run log steps 13-23: step 16 marked four invented, uninspected paths; coverage rose 0 to 4. Disclosed executor provenance, invalid r… |
| C4 | minor | Only 4 of the 6 in-scope paths were marked reviewed; api/uploads (AS-03) and api/session (AS-06) were never marked. The limitations say reviewed_files 'reflects marked synthetic paths' but never state that the two blocke… | **fixed**: Input inventory has six invented paths; executor step 16 lists only search/profile/webhooks/login. Disclosed uploads/session as unmarked and 4/6 as nominal hist… |
| C5 | minor | G5 'Coverage honesty' is marked fail, but the honesty rule itself (finalize with completeness='partial'; never 'complete') was satisfied: the run log shows the producer passed completeness='partial' and the harness rejec… | **fixed**: Executor step 26 requested partial and was rejected at scoped; reviser requested partial and was rejected at initialized. G5 now passes truthful coverage wordin… |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. Opus reads the full trace, which tools mattered, where the run stalled, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule
In appsec, after logging candidates call appsec_coverage_status, and if the phase is not candidates_logged do not call suppress/validate/proof_gap/finalize again; record the phase failure once, state that statuses come from the rules and are not saved, and never call appsec_mark_reviewed on paths you did not inspect.
```

## The answer

| Item | First answer (Kimi) | Final (after critique) | Expected |
|---|---|---|---|
| `AS-01` | `reportable` | `reportable` ✅ | `reportable` |
| `AS-02` | `suppressed` | `suppressed` ✅ | `suppressed` |
| `AS-03` | `blocked` | `blocked` ✅ | `blocked` |
| `AS-04` | `reportable` | `reportable` ✅ | `reportable` |
| `AS-05` | `suppressed` | `suppressed` ✅ | `suppressed` |
| `AS-06` | `blocked` | `blocked` ✅ | `blocked` |

Accuracy: first answer 1.0, final 1.0.

## How it was graded

No model grades itself. [`verify.py`](../../verify.py) checks the files and the run log:

| Check | Result | Detail |
|---|---|---|
| artifacts_present | ✅ | all 10 present |
| result_json_valid | ✅ | final result.json parses with an items list |
| status_vocabulary | ✅ | all statuses in vocabulary |
| all_items_assessed | ✅ | 6 items |
| ground_truth | ✅ | final 1.0 (v1 1.0) |
| must_mention | ✅ | all present |
| forbidden_phrases | ✅ | none found |
| critique_has_findings | ✅ | 7 findings |
| every_finding_answered | ✅ | 7 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['appsec_build_threat_model', 'appsec_check_control', 'appsec_log_candidate', 'appsec_record_surface', 'appsec_trace_dataflow'] of expected ['appsec_build_threat_model', 'appsec_check_control', 'appsec_log_candidate', 'appsec_record_surface', 'appsec_trace_dataflow'] |
| critic_reran_tools | ✅ | critic used ['appsec_check_control', 'appsec_log_candidate', 'appsec_record_surface', 'appsec_trace_dataflow'] |
| reflection_grounded | ✅ | names traced tools ['appsec_check_control', 'appsec_log_candidate', 'appsec_trace_dataflow']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Would it have prevented the stall recorded in [`TRACE.json`](run/TRACE.json)?

## Run it yourself

```powershell
python run.py --domains appsec --out C:\tmp\relay-appsec
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
