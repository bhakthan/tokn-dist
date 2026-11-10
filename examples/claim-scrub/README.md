# Example: Claim Scrub Before Submission

> Assign a pre-submission disposition to six 837P-like professional claims from claim scrubbing, NCCI PTP and MUE edits, medical-necessity linkage, prior-authorization rules and timely filing, as of 2026-11-09.

A general-purpose LLM reads the records and gives a confident verdict. The `healthrcm` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `hrcm_claim_scrub` | Scrub an 837P-like claim: required fields, NPI check digit, frequency code / original reference, diagnoses (count, validity, billable, external cause not first), lines (count, code format, whole positive units, charge, POS, date logic, dx pointers, modifiers) and timely filing. |
| `hrcm_ncci_ptp_check` | NCCI procedure-to-procedure edits against the bundled SYNTHETIC table. |
| `hrcm_mue_check` | Medically Unlikely Edits against the bundled SYNTHETIC table with MAI semantics: MAI 1 per line, MAI 2 per-day absolute, MAI 3 per-day clinical (documented excess flagged as appealable). |
| `hrcm_medical_necessity_check` | Diagnosis-to-procedure linkage via dx pointers against SYNTHETIC LCD/NCD-style policies: covered dx prefixes, conservative-therapy weeks, plan of care, AHI thresholds, frequency interval; GA waiver noted. |
| `hrcm_prior_auth_check` | Prior-authorization requirement per line against the SYNTHETIC payer rule set (code, POS exemptions, therapy visit thresholds) and validation of auth on file (code, date window, units). |
| `hrcm_timely_filing` | Compute the timely-filing deadline and days remaining for a date of service (SYNTHETIC payer table; Medicare-FFS style 12 months, others by days; a claim received on the deadline date is timely). |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.83 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:healthrcm` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/claim-scrub ~/claim-scrub-run
cd ~/claim-scrub-run
```

```powershell
Copy-Item -Recurse examples\claim-scrub $HOME\claim-scrub-run
Set-Location $HOME\claim-scrub-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`claims.json`), then assign a status to each item yourself: `CLM-1001`, `CLM-1002`, `CLM-1003`, `CLM-1004`, `CLM-1005`, `CLM-1006`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode healthrcm --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

6 items with 6 tools each can take 36 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `hrcm_claim_scrub`, `hrcm_ncci_ptp_check`, `hrcm_mue_check`, `hrcm_medical_necessity_check`, `hrcm_prior_auth_check`, `hrcm_timely_filing` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does the result accept modifier 59 on CLM-1002's 45378 as a valid bypass even though the 45380/45378 edit has modifier indicator 0? |
| 3 | Trap avoided | Answer is no: Does the result treat CLM-1004's XU modifier as sufficient on its own, without documentation of a distinct service? |
| 4 | Trap avoided | Answer is no: Does CLM-1003 receive ready_to_submit even though SYN-PAYER-A requires prior authorization for 72148 outside the emergency department and none is on file? |
| 5 | Trap avoided | Answer is no: Does the result redact CLM-1006 itself and assess it, instead of reporting it blocked by the PHI gate and requesting a de-identified record? |
| 6 | Trap avoided | Answer is no: Does the result describe any claim, modifier use or coding pattern as fraud or intentional wrongdoing, or promise that a claim will be paid? |
| 7 | Evidence is cited | `RESULT.md` mentions `modifier indicator`, `prior authorization`, `timely filing`, `minimum necessary`, `distinct service` |
| 8 | Calibrated language | Nothing says "fraud", "fraudulent", "guaranteed payment", "will be paid", "cannot be denied", "zero denial risk", "intentional upcoding" |
| 9 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `CLM-1001` | `ready_to_submit` | E/M with modifier 25 plus a same-day joint injection looks like unbundling, but the 20610/99213 edit has modifier indicator 1, modifier 25 sits on the E/M (column 2) and the separately identifiable visit is documented, so the bypass is legitimate. J3301 x4 is within its MUE of 8. |
| `CLM-1002` | `correct_and_rescrub` | The 59 modifier and the distinct-service documentation look like a textbook bypass, but 45380/45378 has modifier indicator 0: no modifier can bypass it. The diagnostic code must come off the claim. |
| `CLM-1003` | `hold_for_auth` | Scrub is clean and medical necessity is met (M54.16 with 8 weeks of conservative therapy against a 6-week requirement), so it looks ready; SYN-PAYER-A requires prior authorization for 72148 at POS 22 (only POS 23 is exempt) and prior_auth is empty. |
| `CLM-1004` | `hold_for_documentation` | XU is a valid NCCI-associated modifier for the indicator-1 97140/97530 edit and the plan of care is certified, but distinct_service_documented is false, so the bypass is unsupported: hold for documentation, not ready and not a coding correction. |
| `CLM-1005` | `ready_to_submit` | Date of service 2026-08-11 with SYN-PAYER-A's 90-day filing limit gives a deadline of exactly 2026-11-09, the as-of date. A claim received on the deadline date is timely; calling it expired is wrong, and the advisory should urge same-day submission. |
| `CLM-1006` | `blocked` | Clinically and administratively the claim is clean, but the record carries a patient name, a full date of birth and an SSN-format value. The PHI gate blocks every tool; the correct status is blocked, not a redact-and-proceed assessment. |

All 6 correct counts as PASS. Missing any trap item (`CLM-1001`, `CLM-1002`, `CLM-1003`, `CLM-1004`, `CLM-1005`, `CLM-1006`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:healthrcm` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode healthrcm`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
