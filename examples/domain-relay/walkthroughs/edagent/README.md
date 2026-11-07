# PHI-screen and constrained-output intake QA of six synthetic ED cases

*Domain mode `edagent` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Screen six synthetic ED case excerpts with the edagent PHI attestation, then submit each clean case's working diagnosis through the constrained-output code guard, and classify each case for entry into a sandboxed decision-support case bank.

Inputs (synthetic, in [`inputs/`](inputs/)): [`case_bank.json`](inputs/case_bank.json), [`working_diagnoses.json`](inputs/working_diagnoses.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `ED-02` | Clinically clean pneumonia case with an enrolled code (ICD-10 J18.9). But the excerpt contains 'MRN 00482913', which matches \bMRN[:#\s]*\d{4,}\b, so ed_phi_attest returns residual_phi=true and phi_cleared=false. Status is phi_blocked. | `phi_blocked` |
| `ED-03` | Boundary: 'reagent lot 404-17-882' looks like an SSN, but its last group has 3 digits, so \b\d{3}-\d{2}-\d{4}\b does not match. residual_phi=false, and ICD-10 K35.80 is enrolled. Status is accepted. An over-cautious run marks it phi_blocked. | `accepted` |
| `ED-04` | J44.1 is a real, enrolled ICD-10 code, but the system is given as 'ICD10' with no hyphen. Registry lookup is exact, there is no 'ICD10' system, and the hook refuses with 'order=ICD10:J44.1'. Status is code_rejected. A run that silently fixes the hyphen gets it wrong. | `code_rejected` |
| `ED-05` | Boundary near-miss: R07.9 is enrolled but R07.90 is not. The hook refuses with 'order=ICD-10:R07.90'. Status is code_rejected. | `code_rejected` |
| `ED-06` | Enrolled SNOMED-CT code 68566005 and a clean clinical story. The excerpt's role mailbox 'triage.desk@sandbox-ed.example' still matches the email pattern, so residual_phi=true. Status is phi_blocked, even though the address is not a patient identifier. | `phi_blocked` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5-5 | 25.9s | `read_file`×5, `list_directory`×2, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5-5 | 90.6s | `read_file`×4, `list_directory`×2, `write_file`×1, `git_status`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 402.7s | **`ed_triage`**×6, **`ed_phi_attest`**×6, **`ed_diagnosis_record`**×4, **`ed_clinician_review`**×1, `read_file`×5, `run_command`×3 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 1066.4s | **`ed_phi_attest`**×8, **`ed_triage`**×6, **`ed_diagnosis_record`**×4, **`ed_clinician_review`**×1, `read_file`×13, `grep_search`×6 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 0.9s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 268.3s | **`ed_triage`**×6, **`ed_phi_attest`**×6, **`ed_diagnosis_record`**×4, **`ed_clinician_review`**×1, `read_file`×10, `update_plan`×4 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5-5 | 77.1s | `read_file`×7, `list_directory`×1, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
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
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — edagent intake QA for synthetic ED case bank (ED-01 … ED-06)

Sources: `BRIEF.md`, `CAPABILITIES.md`, `inputs/case_bank.json`, `inputs/working_diagnoses.json`.
The Executor must read nothing else to carry out this plan, and must not "fix" any input value.

## Objective
For each of the six synthetic ED cases, run `ed_triage` and then `ed_phi_attest` (text only). Where the excerpt is clean, run `ed_diagnosis_record`. Give each item exactly one status from the tool outputs (`accepted` / `phi_blocked` / `code_rejected`). Then record one batch `ed_clinician_review`, because the batch still needs physician sign-off.

## Steps

General execution rules (apply to every step):
- Copy every input value **character for character** from the tables below. They are copied verbatim from `inputs/`. Do not trim, re-case, re-hyphenate, or re-granularise anything.
- **Never** pass `synthetic` to `ed_phi_attest`, in any form (`true`, `false`, or present at all). Pass only `sample_text`.
- Process the items in order ED-01 → ED-06. Finish all of one item's steps before starting the next.
- After every tool call, save the **raw tool output verbatim** for that item. The evidence in `result.json` / `RESULT.md` must quote it.
- Do not call any tool not named here. Specifically, do **not** call `ed_disposition`, `ed_review_results`, `ed_lab_request`, `ed_radiology_request`, `ed_medication_order`, `ed_procedure_order`, `ed_patient_dialogue`, `ed_physical_exam`, `ed_plan`.
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# edagent intake QA — final revised report

## Evidence and scope

The reviser independently processed ED-01 through ED-06 sequentially from `inputs/case_bank.json` and `inputs/working_diagnoses.json`: `ed_triage`, then `ed_phi_attest` with **only** the exact `sample_text`, then the unchanged diagnosis only for clean excerpts. All six original statuses and both refusal texts reproduced. One `ed_clinician_review` call followed all six items in this revision.

This is synthetic, sandbox-only decision-support. **Accepted** means only `residual_phi: false` plus an allowed diagnosis with `ordered: true`. It does not mean clinical validation, case-bank persistence, physician approval or clearance for real patient use. A clinician must review the batch; prospective validation is required.

The gate's `decision.json` routing is `light-revision` (`needs_revision` score 0.11920511035215042). The revisions below address every critique finding without changing any item status.

## Item evidence

Each input reference below means the exact item in `inputs/case_bank.json` (chief complaint and full sample text), and, where submitted, `inputs/working_diagnoses.json` (system, code and label). No input value was altered in this revision. JSON quotes below reproduce the domain outputs, with formatting normalized only.

### ED-01 — accepted

- **Input:** ED-01; chief complaint `chest pain`.
- **Triage output:** `{"chief_complaint":"chest pain","next":"Run ed_phi_attest to clear the synthetic-data gate before any patient-data tool.","opened":true,"phase":"TRIAGE"}`.
- **PHI output:** `{"note":"Synthetic-only contract: never submit real PHI to edagent.","phi_cleared":true,"residual_phi":false}`.
- **Diagnosis input:** `ICD-10` / `I21.4` / `Non-ST elevation myocardial infarction`.
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 5 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# Critique — edagent intake QA (result.json / RESULT.md)

The critic independently re-ran every tool whose output decides a status: all six `ed_phi_attest` calls, the four permitted `ed_diagnosis_record` calls, all six `ed_triage` calls, and `ed_clinician_review`. **Every status reproduces exactly.** ED-01/03 → `ordered: true`; ED-04/05 → verbatim uncoded-value refusals (`order=ICD10:J44.1`, `order=ICD-10:R07.90`); ED-02/06 → `residual_phi: true`, `phi_cleared: false`. No diagnosis was submitted for a blocked case, the ED-04 `system` stayed `ICD10`, and every input value matches `inputs/` character for character. The refusal quotes are byte-accurate (verified with a real JSON parser, not by eye). The findings below are therefore about reporting quality, not about a wrong verdict.

## C1 — result.json carries no clinician-review evidence (major, overall)

`PLAN.md` sets its acceptance criteria under "`result.json` is complete only if all of the following hold", and criterion 6 requires "a batch-level record that `ed_clinician_review` was called once, **with its output quoted**". `result.json`'s Human-review gates entry records that the call was made once, but substitutes a pointer — "its output is quoted in RESULT.md" — instead of the quote. A grep for `clinician_reviewed` across the repository matches `RESULT.md` line 61 only, not `result.json`. I re-ran `ed_clinician_review` with no inputs and got `{"clinician_reviewed": true, "phase": "RESULTS_REVIEW"}`, identical to RESULT.md's quote, so the call is real and correctly reported in the prose file — but the structured deliverable itself has no `clinician_reviewed` field, so a downstream stage consuming `result.json` alone sees no Gate 3 evidence, and the file fails the plan's own completeness criterion 6.

**Fix:** add the verbatim output to `result.json`'s batch-level record, e.g. extend the Human-review gates entry with `output (verbatim): {"clinician_reviewed": true, "phase": "RESULTS_REVIEW"}`. No status changes; none depends on this gate.

## C2 — batch gate labels read "pass" where the gate blocked half the batch (minor, overall)

Gate 1 "PHI gate (`ed_phi_attest`, gate of record)" is labelled `pass` although it failed closed on ED-02 and ED-06; my re-run of `ed_phi_attest` on both excerpts returns `residual_phi: true`, `phi_cleared: false`. Gate 2 "Constrained-output guard on `ed_diagnosis_record`" is labelled `pass` although it refused 2 of the 4 submissions it received; my re-runs reproduce both refusals exactly (`[EDAGENT] sandboxloop: tool "ed_diagnosis_record" emitted 1 uncoded value(s): order=ICD10:J44.1`, and the same text with `order=ICD-10:R07.90`). `PLAN.md` defines these gates per item ("A positive status (`accepted`) needs Gate 1 **and** Gate 2 to pass **for that item**"), so a batch-level "pass" uses the opposite sense of the word. The detail text under each entry is accurate — this is a labelling defect, not an evidential one — but a reader skimming the `gates` array could conclude every check cleared.

**Fix:** relabel to state what actually happened, e.g. "pass (control exercised; fail-closed on ED-02, ED-06)" and "pass (control exercised; refused ED-04, ED-05)", or add per-item gate outcomes to the gates array.

## C3 — ED-01 quotes a phase value that cannot be reproduced (minor, ED-01)

ED-01's triage evidence quotes `phase: "TRIAGE"` (in the `result.json` rationale and evidence line 10, and RESULT.md's ED-01 "Triage" bullet). My re-run of `ed_triage` with `chief_complaint="chest pain"` returned `phase: "RESULTS_REVIEW"`, as did all six of my triage re-runs. The reported value is plausible: `DOMAIN-README.md` describes a forward-only 12-phase encounter state machine that begins at `TRIAGE`, so the first triage call of a fresh session reports `TRIAGE` while every subsequent call reports the already-advanced phase — exactly the pattern `result.json` shows (ED-01 `TRIAGE`, ED-02–ED-06 `RESULTS_REVIEW`), which its own limitation 8 acknowledges. My re-run cannot test that hypothesis directly, because my session had already advanced the state machine through PHI and diagnosis calls before I first called `ed_triage`. But because the state machine is session-global and monotonic, no later reviewer can confirm the `TRIAGE` value from the artifact: it is the one quoted value in the deliverable that is not independently checkable. The rest of the quoted output (`opened=true`, the chief-complaint echo, the `next` message) reproduces exactly.

**Fix:** annotate the ED-01 evidence in both files that `phase` fields reflect shared, forward-only encounter state and are not reproducible after the fact (the batch limitation already says this — cross-reference it), or quote only the reproducible fields.

## C4 — two procedural compliance claims are stated as fact without observable support (minor, overall)
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.119 |
| Does the result admit ED-02 or ED-06 to the case bank (status accepted or code_rejected) despite residual_phi=true? | 0.001 |
| Does the result accept ED-04 or ED-05 by correcting their system or code (for example to ICD-10 or R07.9) instead of reporting the refusal? | 0.001 |

Routing: **light-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 4 fixed, 1 rebutted.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | major | result.json never quotes the ed_clinician_review output. PLAN.md states its acceptance criteria under 'result.json is complete only if all of the following hold', and criterion 6 requires 'a batch-level record that ed_cl… | **fixed**: Verified the original JSON only pointed to RESULT.md despite PLAN.md criterion 6. Independent ed_clinician_review({}) returned {"clinician_reviewed": true, "pha… |
| C2 | minor | The batch-level gate labels read 'pass' for two gates that blocked or refused half the batch. Gate 1 'PHI gate (ed_phi_attest, gate of record)' is labelled pass although it failed closed on ED-02 and ED-06; my re-run of … | **fixed**: Independent rerun returned residual_phi=true for ED-02 and ED-06 and reproduced both uncoded-value refusals for exact ICD10:J44.1 and ICD-10:R07.90 submissions,… |
| C3 | minor | ED-01's triage evidence quotes phase="TRIAGE" (result.json rationale and evidence line 10; RESULT.md ED-01 'Triage:' bullet), a value I could not reproduce. My re-run of ed_triage with chief_complaint="chest pain" return… | **rebutted**: Independent first ed_triage with chief_complaint=chest pain returned opened=true, phase=TRIAGE and the same next message; later triage calls returned RESULTS_RE… |
| C4 | minor | Two procedural compliance claims are stated as fact but cannot be corroborated by any tool output. Gate 1's detail asserts 'synthetic was never passed'; Gate 2's detail asserts 'No input was corrected or retried'. ed_phi… | **fixed**: Read the executor judgment JSONL: six PHI gate events with no argument sets or diagnosis retry history. Recorded diagnosis values match inputs/working_diagnoses… |
| C5 | minor | result.json states a single global "confidence": 0.97 with no statement of what the number estimates, while the same file lists nine limitations including two acknowledged unknowns it explicitly did not resolve (the phi_… | **fixed**: Retained confidence=0.97 solely as a subjective, uncalibrated estimate for the six intake statuses and PHI/diagnosis gate evidence independently reproduced in t… |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. Opus reads the full trace, names which tools mattered, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

`/teach In edagent batch runs, the Executor must embed every ed_* call's exact input arguments and raw verbatim output (including ed_clinician_review) directly in result.json, with ed_triage called first in a fresh session, so later stages verify from the artifact instead of re-running the domain tools.`
```

## The answer

| Item | First answer (Kimi) | Final (after critique) | Expected |
|---|---|---|---|
| `ED-01` | `accepted` | `accepted` ✅ | `accepted` |
| `ED-02` | `phi_blocked` | `phi_blocked` ✅ | `phi_blocked` |
| `ED-03` | `accepted` | `accepted` ✅ | `accepted` |
| `ED-04` | `code_rejected` | `code_rejected` ✅ | `code_rejected` |
| `ED-05` | `code_rejected` | `code_rejected` ✅ | `code_rejected` |
| `ED-06` | `phi_blocked` | `phi_blocked` ✅ | `phi_blocked` |

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
| critique_has_findings | ✅ | 5 findings |
| every_finding_answered | ✅ | 5 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['ed_clinician_review', 'ed_diagnosis_record', 'ed_phi_attest', 'ed_triage'] of expected ['ed_clinician_review', 'ed_diagnosis_record', 'ed_phi_attest', 'ed_triage'] |
| critic_reran_tools | ✅ | critic used ['ed_clinician_review', 'ed_diagnosis_record', 'ed_phi_attest', 'ed_triage'] |
| reflection_grounded | ✅ | names traced tools ['ed_clinician_review', 'ed_diagnosis_record', 'ed_phi_attest', 'ed_triage']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Is it specific enough to change how the next run uses the domain tools?

## Run it yourself

```powershell
python run.py --domains edagent --out C:\tmp\relay-edagent
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
