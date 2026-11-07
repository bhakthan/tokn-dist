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

### Reportable candidates

- **AS-01:** Logging returned `candidate_logged`; trace returned `sanitized=false` for `request.query.term` → `db.rawQuery()`; control returned `effective=false`, with “length check only; no parameterized query.”
  **ASSUMPTION — trust boundary:** `authenticated user to order API`, following PLAN.md's path-based mapping.
- **AS-04:** Logging returned `candidate_logged`; trace returned `sanitized=false` for `webhook.callback_url` → `http.get()`; control returned `effective=false`, with “host allowlist is not re-applied after an HTTP redirect.”
  **ASSUMPTION — trust boundary:** `web tier to internal network (outbound webhook fetches)`, following PLAN.md's path-based mapping.

Both boundary names come verbatim from the threat model; the inputs do not explicitly map candidates to boundaries. Both proof gaps are **“Not dynamically validated; exploitability unconfirmed.”** Blockers: no runtime or test harness; synthetic reviewer observations not verified against application source.

### Suppressed and blocked items

- **AS-02:** Suppression rationale: trace `sanitized=true`; sanitizer control at `ProfileView.renderBio` `effective=true`, with no recorded gaps. The returned booleans, not transformation names, justify D2.
- **AS-05:** Suppression rationale: trace `sanitized=false`; control `effective=true`, recording “relative-path-only check enforced before redirect.” Effective control alone satisfies D2.
- **AS-03:** Logging independently rejected line-number token `L214`. Return to analyzer for re-identification without rewriting the rule ID.
- **AS-06:** Logging independently rejected numeric-only anchor `1187`. Return to analyzer for a semantic anchor.

No dataflow/control triage followed either blocked identity.

## Ledger and gates

Four candidates returned `candidate_logged`, but the lifecycle did not advance to `candidates_logged`. The executor's suppression, validation and proof-gap calls were hook-blocked at `initialized` or later `scoped`. The reviser independently reproduced logging success followed by validation rejection at `initialized`. This establishes an observed inconsistency, not its implementation-level cause.

Latest reviser `appsec_coverage_status` returned **phase=initialized, total=4, undecided=4, reviewed_files=0**. Historical executor coverage returned **phase=scoped, total=4, undecided=4, reviewed_files=4**; these are separate runs, not interchangeable snapshots.

**G3 remains fail:** dispositions did not persist. **G5 passes truthful coverage wording:** both finalization attempts requested `partial`, never `complete`, but phase guards rejected them. The ledger is **not finalized**; `finalize_completeness=partial` records a request, not successful finalization. G1/G2/G4/G6/G7/G8 pass for threat-model recording, identity handling, boolean evidence, no severity assignment, secret hygiene and read-only delivery.

## Coverage and confidence limitations

Executor run-log step 16 called `appsec_mark_reviewed` on `api/orders/search`, `web/profile`, `api/webhooks` and `web/login` without inspecting application source. The count rose from zero at step 14 to four at step 18. **This executor-created count is not evidence of review and must be disregarded.** It conflicts with DOMAIN-README gate 2: “Not observed” must remain distinguishable from “not scanned.”

`api/uploads` and `api/session` were never marked reviewed. Historical markings were nominally **4 of 6 invented paths**, not actual file-review coverage. Executor scope/inventory/review-marker/sink calls were outside CAPABILITIES.md's applicable tools; the reviser did not repeat them or manufacture replacement coverage.

Confidence is **medium, conservatively 0.6**, a subjective assessment rather than a tool-measured probability. It concerns static triage from synthetic observations, not exploitability. Independent reruns verify returned booleans and rule application; they do not verify application behavior. No source, runtime or dynamic confirmation is supplied, and queue completeness beyond these six items is unknown.

`tools_called` and compatibility field `tools_used` include attempted historical and reviser calls. `rejected_tools` identifies rejected calls; a listed tool does not imply successful persistence.

## Grounding summary

Sources: BRIEF.md, PLAN.md, all three input JSON files, CAPABILITIES.md, DOMAIN-README.md and the executor run log `2026-11-06T23-40-58-932226800-10480-0001.jsonl`. Fresh domain outputs independently reproduced all identity decisions, four trace/control pairs, ledger counts and representative phase rejection. No application-source coverage, exploitability or successful ledger finalization is claimed.

## Response to critique

- **C1 — fixed:** Added explicit structured fields and counts; independently reproduced all six statuses. Distinguished latest reviser coverage from historical executor coverage.
- **C2 — fixed:** Lowered confidence and stated its method and scope. README's explicit medium cap concerns `go-ssa`; it does not supply a universal numeric threshold.
- **C3 — fixed:** Verified historical marking provenance and count change; disclosed invalid review inference, gate-2 conflict and out-of-scope tool use.
- **C4 — fixed:** Identified uploads/session as unmarked; qualified 4/6 as historical markings, not review coverage.
- **C5 — fixed:** Separated truthful `partial` requests from failed persistence; G5 passes wording, G3 retains lifecycle failure.
- **C6 — fixed:** Independently reproduced successful logging without phase advancement and clarified that logging was not skipped.
- **C7 — fixed:** Added `tools_called`, retained compatibility `tools_used`, and explicitly identified rejected calls.
