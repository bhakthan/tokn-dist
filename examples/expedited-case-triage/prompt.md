# Brief: safety case intake queue as of 2026-11-09

You are the pharmacovigilance case-processing lead at **Synthetica Therapeutics**, a fictional sponsor. Seven individual case safety reports (ICSRs) for two fictional products are in this morning's intake queue on **2026-11-09**: **SYNPRO-101**, investigational and in clinical study SYN-STUDY-3, and **SYNPRO-202**, which is marketed. The safety lead needs a defensible disposition for every case and wants overdue clocks raised first. You also have two disproportionality results from the safety database.

All data is synthetic. The sponsor, products, patients and reporters are invented, and patient and reporter references are pseudonymous. The terminology dictionary is **synthetic and is not MedDRA**: every code (9xxxxxxx) and term name is made up, and no licensed content is included. The regional reporting rules are the plug's bundled **SYNTHETIC** tables (`SYN-REGION-A`), which follow the public ICH E2A, 21 CFR 312.32 / 314.80 and GVP Module VI timeframe patterns.

| File | Contents |
|---|---|
| `demo-input/cases.json` | Seven cases. Each has `case_id`, `report_type`, `region`, `receipt_date`, a de-identified `patient`, a `reporter`, `products` with roles, and `events`. Each event carries synthetic codes, onset, outcome, the seriousness criteria, severity grade, and both company and reporter causality. Cases also carry `awareness` (every date anyone in the organisation first held the information, with their role) and a `narrative`. |
| `demo-input/rsi.json` | Reference safety information: the SYNPRO-101 Investigator's Brochure RSI section and the SYNPRO-202 label listing. Each listed event has a maximum severity grade and whether a fatal outcome is listed. |
| `demo-input/synthetic_dictionary.json` | Synthetic LLT→PT→HLT→HLGT→SOC hierarchy for coding-structure validation (not MedDRA). |
| `demo-input/signal_counts.json` | Two product–event 2×2 count tables (`SIG-1`, `SIG-2`). |

## Items to assess

`CASE-PV-001` … `CASE-PV-007`, `SIG-1`, `SIG-2`

## Status vocabulary (use exactly one per item)

**Cases:**

- `expedited_7_day`: a fatal or life-threatening SUSAR, reportable within 7 calendar days of day 0, with a follow-up report 8 days later.
- `expedited_15_day`: one of these, reportable within 15 calendar days of day 0:
  - another SUSAR (clinical trial: serious, unexpected, and related in either party's opinion), or
  - a serious, unexpected postmarketing report.
- `periodic`: a valid case that matches no expedited rule. It goes into periodic or aggregate reporting.
- `invalid_follow_up`: the case lacks one of the four minimum criteria (identifiable patient, identifiable reporter, suspect product, adverse event). It is not reportable, but it stays tracked and needs a follow-up request.
- `duplicate`: a probable duplicate of an earlier case in this queue. Merge it; do not report it separately.
- `blocked_phi`: the case carries direct patient identifiers. The PHI gate refuses it.

**Signals:**

- `signal_for_medical_review`: the disproportionality criteria and the minimum case count are met.
- `insufficient_cases`: fewer reports than the minimum case count.
- `no_signal`: the criteria are not met.

## Rules

1. For cases, precedence is `blocked_phi`, then `duplicate`, then `invalid_follow_up`, then the reportability category.
2. Pass each case to the tools exactly as given. Do not edit causality, dates or seriousness, and do not strip or redact fields yourself. If the PHI gate blocks a case, report it `blocked_phi` and request a de-identified case from the source.
3. **Day 0** is the first date anyone in the organisation held the minimum criteria. That includes sales, medical information and partners, not only the safety department. Count calendar days. The due date itself is on time; the day after it is overdue.
4. **Expectedness** is judged against the supplied RSI. An event that is unlisted, more severe than listed, or fatal when a fatal outcome is not listed is unexpected.
5. **Causality:** keep both opinions. For expedited reporting, a "related" opinion from either the reporter or the company counts.
6. Use `pv_case_assess`, or the individual tools (`pv_icsr_validity`, `pv_duplicate_check`, `pv_seriousness`, `pv_expectedness`, `pv_causality_assess`, `pv_reportability`, `pv_expedited_clock`, `pv_meddra_validate`), plus `pv_signal_detect`. Every date, category and number you report must come from a tool call or the input files.
7. **Calibrated language:**
   - Never write that a product caused an event. Report the assessed causality category, or "a reasonable possibility of a relationship".
   - Disproportionality is a statistical signal for medical review, not a causal conclusion.
   - Submission requires a qualified human medical reviewer's attestation.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"CASE-PV-001": "<status>"}`.
