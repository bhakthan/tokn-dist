## Domain tools that apply

Items ED-01 to ED-06 come from `inputs/case_bank.json` (`chief_complaint`, `sample_text`) and `inputs/working_diagnoses.json` (`system`, `code`, `label`). All six items carry every field listed below.

| tool (exact name) | Applies to | Input fields needed, and whether present in `inputs/` |
|---|---|---|
| `ed_triage` | ED-01 to ED-06 | `chief_complaint`: present for all six |
| `ed_phi_attest` | ED-01 to ED-06 | `sample_text` only (must not pass `synthetic`): present for all six |
| `ed_diagnosis_record` | ED-01 to ED-06, only where the excerpt is not `residual_phi: true` | `system`, `code`, `label`: present for all six, as given |
| `ed_clinician_review` | Batch, once, after all items | No inputs required |

Tools that exist in my list but do not apply to this brief: `ed_disposition` (the brief forbids it), `ed_lab_request`, `ed_radiology_request`, `ed_medication_order`, `ed_procedure_order`, `ed_patient_dialogue`, `ed_physical_exam`, `ed_plan`, `ed_review_results`. No tool name was invented.

## Gates and rules that will constrain the answer

- **PHI screen (`ed_phi_attest`, fail-closed):** the brief names these patterns: `ddd-dd-dddd` (SSN-shaped), `MRN` followed by 4 or more digits, `DOB` followed by a date, and any email address. The `residual_phi` value returned by the tool is the gate of record. It must not be overridden in either direction.
- **README PHI hooks:** `phi_before_patient_data` (blocking), `phi_input_screen` (blocking, "refuses any tool input matching heuristic PHI patterns"). The README is ambiguous on whether `phi_input_screen` covers `ed_triage` and `ed_diagnosis_record`, or only "patient-data tools". Record that ambiguity, don't resolve it.
- **Constrained-output guard (`constrained_output`, blocking):** refuses any order whose `{system, code}` is not enrolled. Matching is exact and case-sensitive (brief rule 3). Per the README, applies to `ed_diagnosis_record`. Nothing may be "corrected".
- **Status precedence (brief):** `phi_blocked` > `code_rejected` > `accepted`. `phi_blocked` cases get no diagnosis submission.
- **Clinician review (`RequireHumanReviewBeforeClose: true`):** `ed_clinician_review` records only that the batch awaits physician sign-off. It does not itself constitute sign-off. The answer must say the batch awaits review.
- **Tabu guard:** `FailuresBeforeTabu` = `2`. Relevant only if an order fails twice in a row.
- **Turn budget:** `MaxTurns` = `20`. Exhaustion forces ADMIT. Not expected to bind for six items.
- **Authority scope:** `MaxTier: T1_Reversible`. edagent proposes decision support and cannot take irreversible clinical action.
- **Calibrated language (`Disclaimer`, `decision_support_disclaimer`):** "decision-support, NEVER replacement"; evaluation is "retrospective/simulated"; "prospective validation is required". Do not describe any case as cleared for real patient use. A clinician must review the batch.
- **Sandbox-only:** no live EHR. `FailClosedEHR` refuses orders when no sandbox is configured. No order tool is used in this brief, so this constrains nothing here.

## Gaps

1. **No case-bank write tool.** The brief describes adding cases to a "sandboxed case bank". None of the 13 tools writes to it. "Accepted" can only mean the two tool outcomes, `ed_phi_attest` `residual_phi: false` and `ed_diagnosis_record` `ordered: true`, which is what the brief defines.
2. **No terminology lookup tool.** I cannot list the enrolled `{system, code}` pairs. Enrolment is known only through the `ed_diagnosis_record` guard's answer, so `code_rejected` can be established only by running the tool.
3. **Possible system-name mismatch (ED-04).** `working_diagnoses.json` gives `system: "ICD10"`. The README names the system `ICD-10`, and the other five items use `ICD-10` or `SNOMED-CT`. The brief forbids correcting it. Whether the guard rejects it is unknown until the tool runs. This is an observation, not an assessment.
4. **Chief complaints are not PHI-screened.** `ed_phi_attest` screens only `sample_text`. The brief's rule 1 passes `chief_complaint` to `ed_triage` without a screen. The strings here look clean, but no tool checks them.
5. **Pattern-spec gap.** The README gives no thresholds for the PHI heuristic. The exact patterns come from the brief, not the README. The README says the screen has "known false-negative possibilities". The brief's rule 2 therefore governs.
6. **Results-review gate not exercised.** The brief stops at `ed_clinician_review` and does not call `ed_disposition`, so `ed_review_results` is not needed. This is the brief's design, not a missing tool.
7. **Subagents not applicable.** The README's subagents (`ed-diagnostician`, `pharmacist-safety`, `disposition-reviewer`) are not used for this intake. No subagent tool is in my list.
8. **Terminology files are illustrative.** The README says the embedded `data/` terminology files are "illustrative ED-relevant subsets, not complete terminologies". Enrolment in the guard is therefore not evidence of clinical correctness of any code.
9. **Clinical content is not assessed.** Whether each excerpt supports its diagnosis is outside every tool here and was not assessed in this scouting step.
