# Example: Shipment Release Review

> Assign a decision-support disposition to seven fictional export shipments from party screening (fuzzy names, aliases, aggregate ownership), USML-first jurisdiction and ECCN classification against supplied technical criteria, country-chart license determination, end-use / end-user red flags and HS / value / origin documentation checks, as of 2026-11-09. All reference data (screening list, country chart, control criteria) is synthetic and supplied in inputs/.

A general-purpose LLM reads the records and gives a confident verdict. The `tradecomp` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `trade_party_screen` | Screen parties against a USER-SUPPLIED screening list (fuzzy name + alias matching with address and country corroboration, configurable thresholds) and apply the aggregate 50% ownership rule. |
| `trade_ownership_aggregate` | Aggregate (direct and indirect) ownership by listed persons. |
| `trade_classification_check` | Check declared classifications against USER-SUPPLIED technical control criteria, USML first: invalid_format \| jurisdiction_conflict \| misclassified (e.g. |
| `trade_jurisdiction_review` | ITAR-vs-EAR jurisdiction review (order of review: USML first). |
| `trade_license_determination` | Determine license requirements from a USER-SUPPLIED country chart: reasons for control of the ECCN vs the destination's columns (X = license required); USML -> ITAR authorization required; EAR99 -> not required unless embargoed; unknown ECCN/destination/column -> undetermined (blocks). |
| `trade_red_flag_check` | KYC-style end-use / end-user red flags: reluctance to state end use, product vs business mismatch, freight forwarder as final destination, unusual payment, military end use for a restricted destination, unusual routing, declined installation/training/warranty, unfamiliarity, vague delivery, evasiveness. |
| `trade_hs_validate` | Validate HS codes: 2/4/6-digit international structure, national 8/10-digit extensions (US-HTS 10, EU-CN 8, EU-TARIC 10), reserved chapter 77 and invalid chapter 00, heading ending 00, declared chapter/heading consistency, HS section. |
| `trade_shipment_review` | Run every check on a shipment (screening + ownership, classification USML-first, license, deemed exports, red flags, HS/value/origin) and derive one disposition: hold_sanctions > hold_screening_review > hold_jurisdiction > hold_classification > hold_license > hold_red_flag > correct_documentation > ready_for_officer_review. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data and one model, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.83 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:tradecomp` or `domains:*` |
| An LLM provider | TOKN calls a model. | See [../../SETUP.md](../../SETUP.md) |

Use a model capable of the required tool calls; provider charges and number of
turns depend on the run. A missing/failed tool result is unassessed, not a pass.

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

Create a new work folder outside this checkout. Copy only `prompt.md` and
`demo-input/` into it; do not copy this README or `grading/`. TOKN writes
`.nospace/` state and output files into the work folder.

```bash
mkdir -p ~/shipment-release-review-run/demo-input
cp examples/shipment-release-review/prompt.md ~/shipment-release-review-run/
cp -r examples/shipment-release-review/demo-input/. ~/shipment-release-review-run/demo-input/
cd ~/shipment-release-review-run
```

```powershell
New-Item -ItemType Directory -Force $HOME\shipment-release-review-run\demo-input | Out-Null
Copy-Item examples\shipment-release-review\prompt.md $HOME\shipment-release-review-run\
Copy-Item examples\shipment-release-review\demo-input\* $HOME\shipment-release-review-run\demo-input\
Set-Location $HOME\shipment-release-review-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`control_criteria.json`, `country_chart.json`, `screening_list.json`, `shipments.json`), then assign a status to each item yourself: `SHP-001`, `SHP-002`, `SHP-003`, `SHP-004`, `SHP-005`, `SHP-006`, `SHP-007`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

The answer key remains in `grading/` outside the staged work folder. Grade
`RESULT.md` after the run from the example checkout, not from the agent's
workspace.

```bash
tokn agent-run --mode tradecomp --repo-root . --prompt-file prompt.md --max-steps 40
```

7 items with 8 tools each can take 56 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `trade_party_screen`, `trade_ownership_aggregate`, `trade_classification_check`, `trade_jurisdiction_review`, `trade_license_determination`, `trade_red_flag_check`, `trade_hs_validate`, `trade_shipment_review` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does SHP-002 receive a clear screening result even though 'Evgrafov Mashinostroi Holding LLC' is a transliteration variant of list entry SYN-001 'Yevgrafov Mashinostroy Holding'? |
| 3 | Trap avoided | Answer is no: Does SHP-003 pass screening because neither Grell Strategic Holdings (30%) nor Ostrova Capital Group (25%) owns 50% on its own, instead of aggregating them to 55%? |
| 4 | Trap avoided | Answer is no: Does SHP-004 keep its EAR99 declaration even though the integrated circuit's total dose rating (600 krad(Si)) meets the supplied 3A001.a.1 criterion? |
| 5 | Trap avoided | Answer is no: Does SHP-005 accept the EAR routing (6A003.b.4) even though the specs meet the supplied USML Category XII(c) criterion, which the order of review checks first? |
| 6 | Trap avoided | Answer is no: Does SHP-006 pass even though the only consignee is a freight forwarder and no ultimate consignee or end user is identified? |
| 7 | Trap avoided | Answer is no: Does SHP-007 accept HS 7701.90 even though chapter 77 is reserved in the Harmonized System? |
| 8 | Trap avoided | Answer is no: Does the result say any shipment is cleared, approved or legal to export, instead of 'ready for compliance-officer review'? |
| 9 | Evidence is cited | `RESULT.md` mentions `potential match`, `50%`, `order of review`, `EAR99`, `freight forwarder`, `HS`, `compliance officer`, `decision support` |
| 10 | Calibrated language | Nothing says "cleared to export", "cleared for export", "approved for export", "legally cleared", "fully compliant", "guaranteed compliance", "zero risk", "safe to ship", "smuggler", "front company", "sanctions evader" |
| 11 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

See the [grader-only answer key](grading/answer-key.md). It is outside the staged work folder.
</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?
- Every result is decision support only, not a sanctions determination or export authorization. A compliance officer must review it. Missing or failed tool results are unassessed, never a pass.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:tradecomp` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode tradecomp`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
