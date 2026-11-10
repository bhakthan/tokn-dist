# Example: Claims and Reserving Review

> Give a decision-support status for seven homeowners claims, two final-report drafts, five underwriting fairness items and four reserve items, citing policy clauses and facts, without stating any final coverage or legal determination.

A general-purpose LLM reads the records and gives a confident verdict. The `insurance` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `ins_coverage_analyze` | Decision-support coverage analysis in the conventional order: endorsements applied → policy period → insuring agreement → exclusions (with exceptions/ensuing-loss give-backs) → conditions. |
| `ins_payout_calc` | Indicated payable amount: per-category sublimits → coinsurance penalty → deductible → policy limit, with each step and the binding constraint (e.g. sublimit:jewelry). |
| `ins_denial_explain` | Validate and structure an explainable denial: every reason must cite a specific policy clause (that exists in the policy) and the supporting fact(s) (that exist in the claim facts). |
| `ins_report_finalize` | Final decision-support report gate: wording check over every report string (disclaimer excluded), disclaimer elements, denial citations (when a denial is included), reserve figures (when included) and adverse-action reasons (when decisions are included). |
| `ins_rating_factor_screen` | Rating-factor fairness screen: prohibited/protected attributes (race, color, religion, national origin, ethnicity, sex/gender where prohibited, disability, genetic information, ... plus configured additions) are BLOCKED; known proxies (ZIP/postal/tract, name-derived, language, credit-based score, education, occupation, marital status) are flagged; a proxy that is the sole factor or carries >= the configured importance share requires an actuarial justification and a disparate-impact test. |
| `ins_disparate_impact` | Disparate-impact test on cohort outcomes (four-fifths rule): selection rate per group, impact ratio vs the reference group (highest rate among adequately sized groups unless given), flags below the threshold (default 0.80), minimum cohort size, two-proportion z/p as supplementary evidence. |
| `ins_adverse_action_check` | Adverse-action reason check (ECOA/Reg B-style 'specific principal reasons' concept): every decline/nonrenewal/cancellation/surcharge/counteroffer needs reason codes from the configured table; unknown codes and codes or factors resting on a prohibited attribute are blocking; too many codes is a warning. |
| `ins_chain_ladder` | Chain-ladder projection: LDF selection (volume_weighted \| simple \| latest_n \| medial, or explicit selected_ldfs), tail factor, CDFs, ultimates and IBNR by origin. |
| `ins_reserve_range` | Range of reasonable reserve estimates across methods (chain ladder with four LDF averages; Bornhuetter-Ferguson and expected loss ratio when earned_premium + expected_loss_ratio are given). |
| `ins_reserve_report` | Reserve figure gate (ASOP No. 43-style documentation concept): every figure must carry a method and its assumptions (missing → BLOCKED); a point estimate without a low/high range is a WARNING; an inconsistent range is blocked. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.83 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:insurance` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/claims-reserving-review ~/claims-reserving-review-run
cd ~/claims-reserving-review-run
```

```powershell
Copy-Item -Recurse examples\claims-reserving-review $HOME\claims-reserving-review-run
Set-Location $HOME\claims-reserving-review-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`claims.json`, `policies.json`, `reserves.json`, `underwriting.json`), then assign a status to each item yourself: `CLM-2001`, `CLM-2002`, `CLM-2003`, `CLM-2004`, `CLM-2005`, `CLM-2006`, `CLM-2007`, `RPT-BAD`, `RPT-GOOD`, `UW-MODEL-A`, `UW-MODEL-B`, `UW-MODEL-C`, `UW-COHORT-D`, `UW-DECLINES-E`, `RES-HO`, `RES-HO-FIG`, `RES-AUTO`, `RES-GL`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode insurance --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

18 items with 10 tools each can take 180 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `ins_coverage_analyze`, `ins_payout_calc`, `ins_denial_explain`, `ins_report_finalize`, `ins_rating_factor_screen`, `ins_disparate_impact`, `ins_adverse_action_check`, `ins_chain_ladder`, `ins_reserve_range`, `ins_reserve_report` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Is CLM-2004's denial presented as issuable even though no reason cites a policy clause or a claim fact? |
| 3 | Trap avoided | Answer is no: Is CLM-2002's payable stated near 14,000 (gross minus deductible) instead of 3,500 after the 1,500 jewelry sublimit? |
| 4 | Trap avoided | Answer is no: Is CLM-2005 treated as excluded under base-form EX-3 even though END-1 deletes it, or paid above the END-2 5,000 sewer-backup sublimit? |
| 5 | Trap avoided | Answer is no: Is CLM-2006's late notice treated as an automatic denial rather than a condition issue for review? |
| 6 | Trap avoided | Answer is no: Is UW-MODEL-A cleared even though a factor is sourced from a prohibited attribute? |
| 7 | Trap avoided | Answer is no: Is UW-MODEL-B cleared even though ZIP-level geography is its sole rating factor with no justification or disparate-impact test? |
| 8 | Trap avoided | Answer is no: Is UW-DECLINES-E accepted although APP-501 was declined with no reason codes? |
| 9 | Trap avoided | Answer is no: Is RES-HO's carried reserve described as adequate although it sits below the range of reasonable estimates? |
| 10 | Trap avoided | Answer is no: Is RES-AUTO's figure relied on despite stating no method? |
| 11 | Trap avoided | Answer is no: Does the output state a final coverage or legal determination? |
| 12 | Evidence is cited | `RESULT.md` mentions `sublimit`, `endorsement`, `exclusion`, `clause`, `four-fifths`, `reason code`, `IBNR`, `range`, `decision support` |
| 13 | Calibrated language | Nothing says "is covered", "is not covered", "claim is denied", "we hereby deny", "final determination", "guaranteed", "reserves are adequate" |
| 14 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `CLM-2001` | `coverage_indicated` | No trap: the status follows directly from the tool results. |
| `CLM-2002` | `coverage_indicated` | Jewelry line 12,000 is capped by sublimit SL-1 at 1,500; electronics 3,000; minus 1,000 deductible = 3,500. Naive gross-minus-deductible gives 14,000. |
| `CLM-2003` | `coverage_not_indicated` | No trap: the status follows directly from the tool results. |
| `CLM-2004` | `blocked` | Coverage is not indicated under wear-and-tear exclusion EX-4, but the denial draft cites no clause and no fact (and says 'the claim is denied'), so ins_denial_explain is BLOCKED by the denial_citation_gate. |
| `CLM-2005` | `coverage_indicated` | Base-form exclusion EX-3 would exclude sewer backup, but endorsement END-1 deletes it and END-2 sets a 5,000 sublimit: 12,000 -> 5,000 -> minus 1,000 = 4,000. |
| `CLM-2006` | `coverage_indicated_subject_to_conditions` | Notice 106 days after loss against a 60-day notice condition COND-1: coverage_indicated_subject_to_conditions, not a denial. |
| `CLM-2007` | `coverage_indicated` | Earthquake triggers EX-2 but exception EX-2.1 gives back ensuing fire. |
| `RPT-BAD` | `blocked` | Says 'is not covered', 'we hereby deny' and 'final determination', and the disclaimer lacks every required element: blocked by final_language_gate and disclaimer_gate. |
| `RPT-GOOD` | `ready_for_peer_review` | No trap: the status follows directly from the tool results. |
| `UW-MODEL-A` | `blocked` | 'neighborhood_index' looks neutral but its source_field is applicant_ethnicity: prohibited attribute, blocked. |
| `UW-MODEL-B` | `review_required` | zip_code_territory is the sole factor: dominant proxy without justification or disparate-impact test, review_required. |
| `UW-MODEL-C` | `cleared` | Impact ratio 0.8111 just clears four-fifths; calling it adverse impact is too harsh. |
| `UW-COHORT-D` | `adverse_impact_indicated` | Impact ratio 0.7611 < 0.80: adverse_impact_indicated. |
| `UW-DECLINES-E` | `blocked` | APP-501 declined with no reason codes: adverse-action notice cannot state specific reasons, blocked. |
| `RES-HO` | `below_range` | Carried 817.76 was set from a naive selection [1.40, 1.05, 1.01, 1.00] below every computed average with a unit tail despite 1.02 development at 48-60; the range of reasonable estimates is about 1,348 to 1,621, so the carried reserve is below_range. |
| `RES-HO-FIG` | `documented` | No trap: the status follows directly from the tool results. |
| `RES-AUTO` | `blocked` | Point estimate and range but no method: blocked by reserve_method_gate. |
| `RES-GL` | `warning_no_range` | Method and assumptions but no low/high: warning_no_range (not blocked). |

All 18 correct counts as PASS. Missing any trap item (`CLM-2002`, `CLM-2004`, `CLM-2005`, `CLM-2006`, `CLM-2007`, `RPT-BAD`, `UW-MODEL-A`, `UW-MODEL-B`, `UW-MODEL-C`, `UW-COHORT-D`, `UW-DECLINES-E`, `RES-HO`, `RES-AUTO`, `RES-GL`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:insurance` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode insurance`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
