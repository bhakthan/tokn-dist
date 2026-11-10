# Example: Expedited Case Triage

> Assign a disposition to seven synthetic individual case safety reports (validity, duplicate check, seriousness, expectedness against the reference safety information, causality, regional reportability and the expedited clock) and classify two disproportionality results, as of 2026-11-09, region SYN-REGION-A.

A general-purpose LLM reads the records and gives a confident verdict. The `pharmacovig` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `pv_case_assess` | Run the full case pipeline: PHI screen, validity, duplicate check (existing_cases), seriousness, expectedness, causality, reportability, clock and optional coding validation; returns one disposition (duplicate > invalid_follow_up > expedited category > periodic) and records all evidence. |
| `pv_icsr_validity` | Check the four ICSR minimum criteria (identifiable patient, identifiable reporter, suspect product, adverse event; ICH E2D / GVP Module VI). |
| `pv_duplicate_check` | Score a case against existing cases on patient initials, age, sex, event onset, suspect product and event term; sex or large age contradictions cap the score. probable_duplicate >= probable threshold, possible_duplicate >= possible threshold. |
| `pv_expectedness` | Assess expectedness of every event against the supplied reference safety information for each suspect product: unlisted, more severe than listed, or fatal when a fatal outcome is not listed => unexpected; missing RSI, uncoded event or unknown grade => treated as unexpected (conservative); matched on pt_code only. |
| `pv_causality_assess` | Normalise company and reporter causality per event (category string, {method: who_umc, ...} or {method: naranjo, answers}) and combine for expedited reporting: EITHER party's 'related' counts; unassessable opinions and a single opinion with the other party absent do not exclude a relationship. |
| `pv_reportability` | Classify expedited reportability against the regional rule table (SYNTHETIC by default): derives serious/unexpected/related/fatal-or-LT per event and returns the most stringent matching rule (expedited_7_day, expedited_15_day, ... or periodic). |
| `pv_expedited_clock` | Compute the expedited reporting clock: day 0 = the earliest date anyone in the organisation (including sales, medical information or a partner) held the minimum criteria; due = day 0 + N calendar days; the due date itself is on time, the day after is overdue. |
| `pv_meddra_validate` | Validate event coding structure against a SUPPLIED dictionary (none bundled; MedDRA is licensed): 8-digit code format, LLT level, current status, the primary LLT->PT->HLT->HLGT->SOC path and the recorded PT; also reports dictionary integrity issues. |
| `pv_signal_detect` | Disproportionality analysis on supplied report counts: PRR and ROR with 95% CI and chi-square (Yates), minimum case count. |
| `pv_phi_screen` | Detect patient/reporter direct identifiers (names, national ids, record numbers, full DOB, address, phone, email) in text or a record. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.83 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:pharmacovig` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/expedited-case-triage ~/expedited-case-triage-run
cd ~/expedited-case-triage-run
```

```powershell
Copy-Item -Recurse examples\expedited-case-triage $HOME\expedited-case-triage-run
Set-Location $HOME\expedited-case-triage-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`cases.json`, `rsi.json`, `signal_counts.json`, `synthetic_dictionary.json`), then assign a status to each item yourself: `CASE-PV-001`, `CASE-PV-002`, `CASE-PV-003`, `CASE-PV-004`, `CASE-PV-005`, `CASE-PV-006`, `CASE-PV-007`, `SIG-1`, `SIG-2`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode pharmacovig --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

9 items with 10 tools each can take 90 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `pv_case_assess`, `pv_icsr_validity`, `pv_duplicate_check`, `pv_expectedness`, `pv_causality_assess`, `pv_reportability`, `pv_expedited_clock`, `pv_meddra_validate`, `pv_signal_detect`, `pv_phi_screen` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does the result start CASE-PV-002's clock on 2026-11-04 (safety logging) instead of 2026-10-30 (when the sales representative first heard of the death), and so miss that the 7-day report was due 2026-11-06 and is overdue? |
| 3 | Trap avoided | Answer is no: Is CASE-PV-001 either classified as reportable, or dropped without a follow-up request for an identifiable reporter? |
| 4 | Trap avoided | Answer is no: Is CASE-PV-003 called expected because the event term is listed, ignoring that grade 3 exceeds the listed maximum grade 2? |
| 5 | Trap avoided | Answer is no: Is CASE-PV-004 called non-reportable because the company assessed the event as unlikely, although the investigator considers it possibly related? |
| 6 | Trap avoided | Answer is no: Is CASE-PV-005 processed and reported as a separate case instead of being identified as a probable duplicate of CASE-PV-003? |
| 7 | Trap avoided | Answer is no: Does the result redact CASE-PV-006 itself and assess it, instead of reporting it blocked by the PHI gate and requesting a de-identified case? |
| 8 | Trap avoided | Answer is no: Is CASE-PV-004 (due 2026-11-09, the as-of date) called overdue rather than due today? |
| 9 | Trap avoided | Answer is no: Is SIG-1 described as proof that SYNPRO-202 causes the event, or is SIG-2 (2 cases) flagged as a signal? |
| 10 | Trap avoided | Answer is no: Does the result state that a product caused an event rather than reporting an assessed causality category? |
| 11 | Evidence is cited | `RESULT.md` mentions `day 0`, `minimum criteria`, `more severe than listed`, `reporter`, `medical review`, `overdue`, `follow-up` |
| 12 | Calibrated language | Nothing says "caused the death", "the drug caused", "SYNPRO-101 caused", "proves causation", "confirms causation", "completely safe", "no safety concern", "proven signal" |
| 13 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `CASE-PV-001` | `invalid_follow_up` | The event looks serious (hospitalisation) and the product is identified, which invites an expedited classification; but the anonymous web-form sender is not an identifiable reporter, so the case fails the four minimum criteria. It is not reportable and its clock has not started, yet it must stay tracked with a follow-up request. |
| `CASE-PV-002` | `expedited_7_day` | A fatal, unlisted, possibly related event in a clinical trial is a fatal SUSAR (7 calendar days, then a follow-up report 8 days later). Safety logged it on 2026-11-04, which would make it due 2026-11-11 and on time; but a sales representative heard of the death on 2026-10-30, and day 0 is the first receipt by anyone in the organisation: due 2026-11-06, 3 days overdue as of 2026-11-09. |
| `CASE-PV-003` | `expedited_15_day` | The event term is listed in the SYNPRO-202 label, so it looks expected; the listing covers severity grade 2 only and the case is grade 3. Greater severity than listed is unexpected, so with hospitalisation this is a 15-day postmarketing report due 2026-11-12. |
| `CASE-PV-004` | `expedited_15_day` | The company assessed the event as unlikely related, which would make it non-reportable on the company view; the investigator says possible. For expedited reporting either party's suspicion counts and the company cannot downgrade the reporter: a SUSAR, 15 days from 2026-10-25, due today (2026-11-09) and still on time. |
| `CASE-PV-005` | `duplicate` | A pharmacist's report of the same patient (initials K.L., 54, female), the same product, the same event and an onset one day apart from CASE-PV-003. It is a probable duplicate to be merged, not a second expedited report. |
| `CASE-PV-006` | `blocked_phi` | Clinically a clean serious case, but the narrative carries an invented patient name and full date of birth. The PHI gate blocks every tool; the correct status is blocked_phi, not a redact-and-proceed assessment. |
| `CASE-PV-007` | `periodic` | A clean non-serious, listed event in a postmarketing report: nothing to expedite. It goes to periodic reporting; calling it expedited would be over-reporting. |
| `SIG-1` | `signal_for_medical_review` | 12 reports with PRR about 7 and a lower confidence bound well above 1: a statistical signal for medical review, never a causal conclusion. |
| `SIG-2` | `insufficient_cases` | A large PRR from only 2 reports, below the minimum of 3 cases: insufficient cases, keep under monitoring. |

All 9 correct counts as PASS. Missing any trap item (`CASE-PV-001`, `CASE-PV-002`, `CASE-PV-003`, `CASE-PV-004`, `CASE-PV-005`, `CASE-PV-006`, `CASE-PV-007`, `SIG-1`, `SIG-2`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:pharmacovig` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode pharmacovig`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
