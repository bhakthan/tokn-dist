# Task: pre-submission work queue for six professional claims

You are the revenue-cycle lead for a multi-specialty outpatient group. Six professional claims (837P-style) are sitting in the pre-submission work queue on **2026-11-09**. Before today's batch goes out, the billing manager needs a defensible disposition for each claim: submit it, hold it for documentation, hold it for prior authorization, send it back for a coding correction, or stop because it cannot be processed as received.

The data is synthetic but realistic. No real patients, providers or payers appear anywhere. The payers (`SYN-PAYER-A`, `SYN-PAYER-B`, `SYN-MEDICARE-FFS`), their filing limits and prior-authorization rules, the coverage policies and the NCCI/MUE values all come from the healthrcm synthetic reference tables that the `hrcm_*` tools carry. CPT codes appear as numbers only.

| File | Contents |
|---|---|
| `demo-input/claims.json` | Six claims, each with `claim_id`, `payer_id`, pseudonymous `patient_ref`, billing NPI, place of service, ICD-10-CM `diagnoses`, `service_lines` (code, modifiers, units, charge, `dos_from`, `dx_pointers`, `distinct_service_documented`), and where relevant `prior_auth`, `conservative_therapy_weeks`, `plan_of_care_certified`, `visit_number`. Every claim has `as_of` = 2026-11-09. |

## Items to assess

`CLM-1001`, `CLM-1002`, `CLM-1003`, `CLM-1004`, `CLM-1005`, `CLM-1006`

## Status vocabulary (use exactly one per item)

- `ready_to_submit`: the scrub has no errors, every NCCI PTP edit is either not triggered or legitimately bypassed, MUEs are within limits, each line's linked diagnosis meets the coverage policy, any required prior authorization is on file, and the claim is within the timely-filing limit. Submission still needs a credentialed human coder's attestation.
- `hold_for_documentation`: nothing needs recoding, but the record does not yet support what is billed: for example a bypass modifier on an indicator-1 edit without documentation of a distinct service, units above a clinical MUE without supporting documentation, or coverage criteria not yet documented.
- `hold_for_auth`: the payer requires prior authorization for a line and none valid is on file.
- `correct_and_rescrub`: the claim must be recoded or corrected: a scrub error, an NCCI edit that cannot be bypassed (modifier indicator 0, or an invalid bypass modifier), a policy MUE exceeded, or a diagnosis that does not support the procedure.
- `blocked`: the claim cannot be processed as received because the record carries direct patient identifiers; the PHI gate refuses it.

## Rules

1. Precedence is `blocked`, then `correct_and_rescrub`, then `hold_for_auth`, then `hold_for_documentation`, then `ready_to_submit`.
2. Pass each claim to the tools exactly as given. Do not add modifiers, documentation flags or authorizations, and do not strip or redact fields yourself. HIPAA minimum necessary applies: if the PHI gate blocks a claim, report it `blocked` and ask for a de-identified record from the source system.
3. A modifier bypasses an NCCI PTP edit only when the edit's modifier indicator is 1 **and** documentation supports a distinct service. Indicator 0 can never be bypassed. Modifier 25 belongs on the E/M code.
4. Timely filing is computed from the date of service with the payer's limit; a claim received on the deadline date is timely.
5. Use `hrcm_claim_scrub`, `hrcm_ncci_ptp_check`, `hrcm_mue_check`, `hrcm_medical_necessity_check`, `hrcm_prior_auth_check` and `hrcm_timely_filing` (or `hrcm_claim_readiness`, which runs the first five together). Every number and deadline you report must come from a tool call or the input file.
6. Use calibrated language. A coding pattern is a risk signal for compliance review, never an accusation. Passing the edits is not a promise of payment; adjudication belongs to the payer.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"CLM-1001": "<status>"}`.
