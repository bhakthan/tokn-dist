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

### Input table A — from `inputs/case_bank.json`

| item | `chief_complaint` (→ `ed_triage`) | `sample_text` (→ `ed_phi_attest`) |
|---|---|---|
| ED-01 | `chest pain` | `Synthetic case 01. 58-year-old presenting with two hours of pressure-like chest pain radiating to the left arm. Troponin T elevated on the sandbox panel; ECG without ST elevation.` |
| ED-02 | `fever and cough` | `Synthetic case 02. 71-year-old with fever, productive cough and right lower lobe consolidation on plain chest X-ray. Registration note: MRN 00482913.` |
| ED-03 | `abdominal pain` | `Synthetic case 03. 24-year-old with periumbilical pain migrating to the right iliac fossa, rebound tenderness and leukocytosis. Point-of-care reagent lot 404-17-882 logged.` |
| ED-04 | `shortness of breath` | `Synthetic case 04. 66-year-old with known COPD, increased dyspnoea and purulent sputum over three days; SpO2 86% on room air.` |
| ED-05 | `chest pain` | `Synthetic case 05. 45-year-old with atypical chest pain, normal serial troponins and a normal ECG; pain reproducible on palpation.` |
| ED-06 | `dysuria` | `Synthetic case 06. 33-year-old with dysuria, frequency and suprapubic pain; urine dipstick nitrite positive. Follow-up queries to triage.desk@sandbox-ed.example.` |

### Input table B — from `inputs/working_diagnoses.json`

| item | `system` | `code` | `label` |
|---|---|---|---|
| ED-01 | `ICD-10` | `I21.4` | `Non-ST elevation myocardial infarction` |
| ED-02 | `ICD-10` | `J18.9` | `Pneumonia, unspecified organism` |
| ED-03 | `ICD-10` | `K35.80` | `Acute appendicitis, unspecified` |
| ED-04 | `ICD10` | `J44.1` | `COPD with acute exacerbation` |
| ED-05 | `ICD-10` | `R07.90` | `Chest pain, unspecified` |
| ED-06 | `SNOMED-CT` | `68566005` | `Urinary tract infectious disease (disorder)` |

Note on ED-04: `system` is `ICD10`, with no hyphen. Pass it **exactly** like that. Do not correct it. The guard's answer decides the outcome.

### Per-item steps (repeat for each item X in ED-01, ED-02, ED-03, ED-04, ED-05, ED-06)

**Step X.1 — open the case**
- Covers: item X.
- Tool: `ed_triage`
- Input: `{"chief_complaint": <Table A chief_complaint for X>}`
- Effect on status: none directly. This call opens the encounter. If it is refused, follow Contingency C1.

**Step X.2 — PHI screen (gate of record)**
- Covers: item X.
- Tool: `ed_phi_attest`
- Input: `{"sample_text": <Table A sample_text for X>}`. Pass only this key.
- Effect on status:
  - `residual_phi: true` → status is fixed as **`phi_blocked`**. **Skip Step X.3.** Do not submit a diagnosis.
  - `residual_phi: false` → go on to Step X.3.
  - No `residual_phi` field, or an error → follow Contingency C2.

**Step X.3 — diagnosis record (only if X.2 returned `residual_phi: false`)**
- Covers: item X.
- Tool: `ed_diagnosis_record`
- Input: `{"system": <Table B system>, "code": <Table B code>, "label": <Table B label>}`. Pass these exactly.
- Effect on status:
  - Call allowed and output contains `ordered: true` → **`accepted`**.
  - Call refused by the constrained-output guard as an unenrolled / "uncoded value" `{system, code}` → **`code_rejected`**. Quote the refusal text verbatim.
  - Anything else (a refusal for another reason, `ordered: false` with no "uncoded" refusal, an error) → follow Contingency C3.
- **Do not retry** a rejected `ed_diagnosis_record` with an altered value. Never retry it at all for a `code_rejected` item. (The tabu guard trips after 2 failures, and retrying with "fixed" values breaks brief rule 3.)

Concrete expansion (for clarity, 6 × up to 3 calls):

| # | item | tool | input |
|---|---|---|---|
| 1 | ED-01 | `ed_triage` | chief_complaint = `chest pain` |
| 2 | ED-01 | `ed_phi_attest` | sample_text = Table A ED-01 |
| 3 | ED-01 | `ed_diagnosis_record` (if 2 clean) | `ICD-10` / `I21.4` / `Non-ST elevation myocardial infarction` |
| 4 | ED-02 | `ed_triage` | chief_complaint = `fever and cough` |
| 5 | ED-02 | `ed_phi_attest` | sample_text = Table A ED-02 |
| 6 | ED-02 | `ed_diagnosis_record` (if 5 clean) | `ICD-10` / `J18.9` / `Pneumonia, unspecified organism` |
| 7 | ED-03 | `ed_triage` | chief_complaint = `abdominal pain` |
| 8 | ED-03 | `ed_phi_attest` | sample_text = Table A ED-03 |
| 9 | ED-03 | `ed_diagnosis_record` (if 8 clean) | `ICD-10` / `K35.80` / `Acute appendicitis, unspecified` |
| 10 | ED-04 | `ed_triage` | chief_complaint = `shortness of breath` |
| 11 | ED-04 | `ed_phi_attest` | sample_text = Table A ED-04 |
| 12 | ED-04 | `ed_diagnosis_record` (if 11 clean) | `ICD10` / `J44.1` / `COPD with acute exacerbation` |
| 13 | ED-05 | `ed_triage` | chief_complaint = `chest pain` |
| 14 | ED-05 | `ed_phi_attest` | sample_text = Table A ED-05 |
| 15 | ED-05 | `ed_diagnosis_record` (if 14 clean) | `ICD-10` / `R07.90` / `Chest pain, unspecified` |
| 16 | ED-06 | `ed_triage` | chief_complaint = `dysuria` |
| 17 | ED-06 | `ed_phi_attest` | sample_text = Table A ED-06 |
| 18 | ED-06 | `ed_diagnosis_record` (if 17 clean) | `SNOMED-CT` / `68566005` / `Urinary tract infectious disease (disorder)` |

### Step 19 — batch clinician review (once, after all six items are finished)
- Covers: the whole batch (ED-01 … ED-06).
- Tool: `ed_clinician_review`
- Input: `{}` (no inputs).
- Effect on status: none. It records that the batch **awaits** physician sign-off. It is **not** the sign-off itself. Quote its output in RESULT.md. Call it exactly once. Do **not** follow it with `ed_disposition`.

### Contingencies (mechanical; record every one in the evidence)
- **C1 — `ed_triage` refused.**
  - If the refusal cites the PHI gate (e.g. `phi_before_patient_data`, because a prior item left the gate closed): run Step X.2 for this item first, then retry `ed_triage` **once** with the same input, then run Step X.3 if it applies. Status is still decided only by X.2 and X.3.
  - If the refusal has any other cause: still run X.2 (and X.3 if X.2 is clean). Note the triage refusal verbatim in the evidence.
  - A triage refusal never changes the status by itself.
- **C2 — `ed_phi_attest` gives no usable `residual_phi`.** Retry once with the identical input. If there is still no boolean `residual_phi`, do **not** infer it from the patterns in the brief. Set status `unresolved` (see Decision rule R4), skip X.3, and record the raw output.
- **C3 — `ed_diagnosis_record` result is neither `ordered: true` nor an "uncoded value"/unenrolled refusal.** This includes a refusal by the `phi_input_screen` hook on the diagnosis input. Do not retry with altered values. Set status `unresolved` (R4) and record the raw output verbatim.
- **Stop condition:** if `MaxTurns` (20) or the tabu guard (2 consecutive failures of the same order) blocks further calls, stop. Mark the unfinished items `unresolved` and say so in RESULT.md. Do not guess their statuses.

## Decision rules

Apply them in this order, for each item. The first rule that matches wins. This follows the brief's precedence `phi_blocked` > `code_rejected` > `accepted`.

- **R1 → `phi_blocked`**: the item's `ed_phi_attest` output contains `residual_phi: true`. This holds whatever any other tool returned, and whatever the text "looks like". The tool's boolean is final in both directions. Do not overrule it with the brief's pattern list, and do not overrule it on the grounds that "this is not a patient identifier".
- **R2 → `code_rejected`**: `ed_phi_attest` returned `residual_phi: false`, **and** `ed_diagnosis_record` was refused by the constrained-output guard because the `{system, code}` pair is not enrolled. The refusal text says "uncoded value", "not enrolled", or names the `constrained_output` guard.
- **R3 → `accepted`**: `ed_phi_attest` returned `residual_phi: false`, **and** `ed_diagnosis_record` was allowed and its output contains `ordered: true`.
- **R4 → `unresolved` (not a brief status; only for tool failure)**: none of R1 to R3 matched (Contingencies C2/C3/stop condition). Never convert `unresolved` into one of the three statuses by judgment. Flag it as an incomplete deliverable (see Acceptance criteria).

Things that must **not** affect the status: clinical plausibility of the diagnosis, the wording of the label, whether the code "looks right", `ed_triage` output, and `ed_clinician_review` output.

## Gates

1. **PHI gate — `ed_phi_attest`, fail-closed (gate of record).** It must return `residual_phi: false` for the item's `sample_text`, screened from the text itself (no `synthetic` flag), before the item can get any positive status. It must also return that before `ed_diagnosis_record` is called for the item. README hooks `phi_before_patient_data` and `phi_input_screen` are blocking. If either blocks a call, record it verbatim (C1/C3).
2. **Constrained-output guard — `constrained_output`, blocking, on `ed_diagnosis_record`.** The exact, case-sensitive `{system, code}` pair must be enrolled, so the call returns `ordered: true`. That is required for `accepted`.
3. **Human-review gate — `RequireHumanReviewBeforeClose: true`.** `ed_clinician_review` must be called once after all items. Even then, "accepted" means only that the case passed intake checks for the **sandboxed synthetic** bank, pending physician sign-off. It is never "cleared for real patient use". `ed_disposition` is not called.
4. **Authority scope — `MaxTier: T1_Reversible`; decision-support disclaimer.** No irreversible clinical action. Outputs must use calibrated, decision-support-only language (retrospective/simulated; prospective validation required).

A positive status (`accepted`) needs Gate 1 **and** Gate 2 to pass for that item. The batch deliverable is complete only once Gate 3 has been recorded.

## Acceptance criteria

`result.json` is complete only if all of the following hold:

1. It contains exactly six item entries, with `item` values `ED-01`, `ED-02`, `ED-03`, `ED-04`, `ED-05`, `ED-06`, each appearing once.
2. Each entry has a `status` that is exactly one of `accepted`, `phi_blocked`, `code_rejected`. If any entry is `unresolved`, the file must say so explicitly (e.g. top-level `"complete": false`) and RESULT.md must explain why.
3. Each entry's evidence quotes the tool output verbatim:
   - `residual_phi` (true/false) from `ed_phi_attest`, for every item;
   - for non-`phi_blocked` items, either `ordered` (true) or the verbatim refusal text from `ed_diagnosis_record`;
   - for `phi_blocked` items, an explicit note that `ed_diagnosis_record` was **not** called.
4. Each entry records the inputs as passed: `chief_complaint`, `sample_text` (or a reference to it), and, where submitted, `system`/`code`/`label` exactly as in `inputs/working_diagnoses.json`. ED-04's `system` must appear as `ICD10`.
5. Status consistency holds: `accepted` ⇒ `residual_phi: false` ∧ `ordered: true`; `code_rejected` ⇒ `residual_phi: false` ∧ a guard refusal; `phi_blocked` ⇒ `residual_phi: true` ∧ no diagnosis call.
6. There is a batch-level record that `ed_clinician_review` was called once, with its output quoted. The batch is described as **awaiting physician/clinician review**.
7. There is a statement that `ed_disposition` was not called, that `synthetic: true` was never passed, and that no input value was altered.
8. It contains the decision-support disclaimer: synthetic data, sandbox only, decision-support not replacement, no case cleared for real patient use, prospective validation required.
9. It lists the known gaps carried over from CAPABILITIES.md: no case-bank write tool, no terminology lookup, chief complaints not PHI-screened, PHI heuristic may have false negatives, enrolment ≠ clinical correctness, clinical content not assessed.

`RESULT.md` must state the same per-item statuses and evidence in human-readable form, and must also meet criteria 6–9.
