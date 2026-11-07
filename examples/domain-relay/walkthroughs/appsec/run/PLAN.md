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

3. **Surfaces (all items).** Call `appsec_record_surface` once per surface, exactly as in `inputs/candidates.json`:
   - SURF-SEARCH, "Order search API", injection, ["api/orders/search"]
   - SURF-PROFILE, "Profile rendering", output-encoding, ["web/profile"]
   - SURF-UPLOAD, "Archive upload", file-handling, ["api/uploads"]
   - SURF-WEBHOOK, "Outbound webhook fetcher", network, ["api/webhooks"]
   - SURF-LOGIN, "Login redirect", authentication, ["web/login"]
   - SURF-SESSION, "Session cookie decoding", serialization, ["api/session"]
   Do steps 3 and 4 in the same run, because a candidate whose surface was not recorded is rejected as unknown.

4. **Identity check, then log (all items).** First apply identity rules I1–I4 (see Decision rules) by reasoning. Then call `appsec_log_candidate` for every item with its exact id, rule_id, anchor, surface, description and paths, leaving out `title`:
   - AS-01: rule_id `sql-injection.order-search-query`, anchor `OrderRepository.Search`, SURF-SEARCH, ["api/orders/search"]
   - AS-02: rule_id `xss.profile-bio-render`, anchor `ProfileView.renderBio`, SURF-PROFILE, ["web/profile"]
   - AS-03: rule_id `path-traversal.archive-extract-L214`, anchor `ArchiveExtractor.extractEntry`, SURF-UPLOAD, ["api/uploads"]
   - AS-04: rule_id `ssrf.webhook-callback-fetch`, anchor `WebhookClient.deliver`, SURF-WEBHOOK, ["api/webhooks"]
   - AS-05: rule_id `open-redirect.login-return-url`, anchor `LoginController.completeLogin`, SURF-LOGIN, ["web/login"]
   - AS-06: rule_id `deserialization.session-cookie-decode`, anchor `1187`, SURF-SESSION, ["api/session"]
   Description: copy each item's `description` text from candidates.json.
   **What changes status:** if an item fails I1–I4, or the ledger rejects its identity, the item is blocked, and Steps 5–8 are skipped for it.
   Expected result: AS-03 is blocked because its rule_id contains `L214`. AS-06 is blocked because its anchor `1187` is only a number. Even if the ledger accepts these two, they stay blocked, since the brief's rule overrides ledger acceptance.

5. **Dataflow (non-blocked items only).** Call `appsec_trace_dataflow` with source, sink, transformations and sanitized from `inputs/dataflows_and_controls.json`:
   - AS-01: "request.query.term" → "db.rawQuery()", ["trim","string concatenation into SELECT"], sanitized=false
   - AS-02: "profile.bio" → "template.writeHTML()", ["markdownToText","escapeHtml"], sanitized=true
   - AS-04: "webhook.callback_url" → "http.get()", ["parseUrl","allowlistHost (initial request only)","follow redirects"], sanitized=false
   - AS-05: "request.query.returnTo" → "response.redirect()", ["urlDecode"], sanitized=false
   Record the `sanitized` value the tool **returns**. If it returns true, the item is suppressed.

6. **Control (non-blocked items only).** Call `appsec_check_control` with sink, control_type, location, effective and gaps:
   - AS-01: "db.rawQuery()", validator, "OrderRepository.Search", effective=false, gaps "length check only; no parameterized query"
   - AS-02: "template.writeHTML()", sanitizer, "ProfileView.renderBio", effective=true, gaps ""
   - AS-04: "http.get()", validator, "WebhookClient.deliver", effective=false, gaps "host allowlist is not re-applied after an HTTP redirect"
   - AS-05: "response.redirect()", validator, "LoginController.completeLogin", effective=true, gaps "relative-path-only check enforced before redirect"
   Record the `effective` value the tool **returns**. If it returns true, the item is suppressed.

7. **Suppress (each item that D2 makes suppressed; expected AS-02 and AS-05).** Call `appsec_suppress_candidate` with candidate_id and a rationale that quotes the returned booleans. Examples: "AS-02: trace sanitized=true; control effective=true (sanitizer at ProfileView.renderBio)" and "AS-05: trace sanitized=false; control effective=true (relative-path-only check before redirect)".

8. **Validate (one disposition per non-blocked item).** Call `appsec_validate_candidate` with:
   - candidate_id;
   - disposition `reportable` or `suppressed`, as D2/D3 decide;
   - evidence: the returned sanitized and effective values plus `gaps`;
   - validation_method: "static review of recorded dataflow and control; no dynamic validation";
   - rationale and proof_gap as appropriate.
   Never call this tool for a blocked item. Never pass `deferred` or `not_applicable` as a stand-in for blocked.

9. **Proof gap (each reportable item; expected AS-01 and AS-04).** Call `appsec_record_proof_gap`:
   - gap: "Not dynamically validated; exploitability unconfirmed".
   - blockers: ["no runtime or test harness", "synthetic inputs; reviewer observations not verified against source"].

10. **Coverage.** Call `appsec_coverage_status` (read-only). Record its counts.

11. **Finalize.** Call `appsec_finalize_scan` with completeness="partial" and a summary giving:
    - the count of each status;
    - that the results come from static review only;
    - the IDs of the blocked items.
    Never pass "complete".

## Decision rules
Apply the rules in order and stop at the first that matches.

**D1 — Blocked.** An item is blocked if any of the following holds:
- **I1:** the rule_id is not exactly two non-empty segments joined by one `.`;
- **I2:** the rule_id contains a file extension (e.g. `.go`, `.py`, `.js`, `.java`, `.ts`);
- **I3:** the rule_id contains a line-number token, i.e. matches the regex `(^|[-.:_])(L\d+|line-?\d+)($|[-.:_])` or `:\d+`, or contains a scan ID;
- **I4:** the anchor matches `^\d+$`;
- **I5:** `appsec_log_candidate` rejects the identity.

Do not run Steps 5–8 for a blocked item. Record which rule matched and the offending substring, plus "return to analyzer for re-identification".

**D2 — Suppressed.** The item is not blocked and either `sanitized` (as returned in Step 5) is true or `effective` (as returned in Step 6) is true. Transformation names such as `escapeHtml` or `allowlistHost` are not evidence; only the booleans count.

**D3 — Reportable.** The item is not blocked, and both `sanitized` and `effective` are false.

**D4 — Tool failure.** If Step 5 or 6 fails or returns no boolean for an item, the item cannot be judged under D2/D3. Mark it blocked with reason "tool evidence missing" and note this in the summary.

**D5 — Wording.** Describe every reportable item as an "unvalidated candidate", never as a "confirmed vulnerability".

**Trust boundary for reportable items** (reasoning from surface paths; flag it as an assumption in RESULT.md):
- AS-01 (api/orders/search): "authenticated user to order API"
- AS-04 (api/webhooks): "web tier to internal network (outbound webhook fetches)"
- Any other item that turns out reportable: SURF-PROFILE, SURF-LOGIN and SURF-SESSION map to "internet to web tier (anonymous HTTP requests)".

## Gates
- **G1 — Threat model:** Step 1 succeeds before any surface or candidate is recorded.
- **G2 — Identity:** no item may become reportable or suppressed until it passes I1–I5. Identity is checked before the dataflow and control steps.
- **G3 — Phase separation:** an item is logged (Step 4) before it is validated (Step 8), and gets exactly one disposition.
- **G4 — Evidence:** a reportable or suppressed status requires both booleans as returned by the tools in Steps 5 and 6.
- **G5 — Coverage honesty:** finalize with completeness="partial"; never "complete".
- **G6 — Severity discipline:** no severity is assigned, and neither `appsec_assign_severity` nor `appsec_author_finding` is called.
- **G7 — Secret hygiene:** no credentials in any evidence or text.
- **G8 — Read-only authority:** no mutating tools.

## Acceptance criteria
`result.json` is complete only if:
1. It contains exactly six item entries, `AS-01`..`AS-06`, each with exactly one `status` from {reportable, suppressed, blocked}.
2. Each entry includes:
   - `rule_id` and `anchor`, copied exactly;
   - `surface`;
   - `tools_called`;
   - `sanitized` and `effective` as returned by the tools, or null for blocked items;
   - `rationale`, which cites the decision rule applied (D1–D4).
3. Each blocked entry includes `identity_violation`: the rule (I1–I5) and the offending substring, e.g. `L214` or `1187`.
4. Each suppressed entry includes the suppression rationale from Step 7.
5. Each reportable entry includes:
   - `trust_boundary`, an exact string from threat_model.json;
   - `validation`: "static only; unvalidated candidate";
   - `proof_gap`, from Step 9.
6. At top level:
   - `coverage`: "partial";
   - `finalize_completeness`: "partial";
   - `coverage_status`, from Step 10;
   - status counts that add up to 6;
   - `dynamic_validation`: false;
   - the service name "order-portal-synthetic-01".
7. It contains no severity field, exploit content or credentials.
8. Expected values if the tools return the input booleans unchanged: AS-01 reportable, AS-02 suppressed, AS-03 blocked (I3, `L214`), AS-04 reportable, AS-05 suppressed, AS-06 blocked (I4, `1187`). If any tool output differs, apply D1–D4 to the actual output and explain the difference in RESULT.md.
