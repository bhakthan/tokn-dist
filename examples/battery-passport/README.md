# Example: EU Battery Passport Review

> Run six synthetic Battery Passport drafts through the EU 2023/1542 mandatory-attribute, CF methodology, due-diligence and chemistry-consistency checks and classify each.

A general-purpose LLM reads the records and gives a confident verdict. The `batterypass` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `bp_check_compliance` | Run the EU Battery Regulation 2023/1542 mandatory-attribute gate against a payload. |
| `bp_check_cf_methodology` | Run the Carbon Footprint methodology gate (functional unit, system boundary, PEFCR alignment, primary-data share). |
| `bp_check_due_diligence` | Run the Supply-Chain Due Diligence gate. |
| `bp_check_chemistry` | Standalone cathode-element consistency check validates declared chemistry (LFP/NMC/NCA/etc.) agrees with the cathode active material formula. |
| `bp_query_passport` | Query a single field from a Battery Passport payload. |

This is the single-agent version of the [batterypass relay walkthrough](../domain-relay/walkthroughs/batterypass/README.md). It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:batterypass` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/battery-passport ~/battery-passport-run
cd ~/battery-passport-run
```

```powershell
Copy-Item -Recurse examples\battery-passport $HOME\battery-passport-run
Set-Location $HOME\battery-passport-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`chemistry_declarations.json`, `passports.json`), then assign a status to each item yourself: `BP-01`, `BP-02`, `BP-03`, `BP-04`, `BP-05`, `BP-06`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode batterypass --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

6 items with 5 tools each can take 30 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `bp_check_compliance`, `bp_check_cf_methodology`, `bp_check_due_diligence`, `bp_check_chemistry`, `bp_query_passport` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any passport whose bp_check_chemistry result is consistent=false still receive compliant or non_compliant? |
| 3 | Trap avoided | Answer is no: Does the result describe any passport as legally certified or approved for the EU market, rather than as passing TOKN's gate projection? |
| 4 | Evidence is cited | `RESULT.md` mentions `2023/1542`, `primaryDataShare`, `due diligence`, `cathode`, `lastAuditDate` |
| 5 | Calibrated language | Nothing says "guaranteed compliant", "certified compliant", "legally compliant", "approved for market placement", "no further verification" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `BP-01` | `compliant` | No trap: the status follows directly from the tool results. |
| `BP-02` | `inconsistent` | Every EU mandatory attribute is present, the CF share is 0.71 and the audit is fresh, so all three gates pass. But the label declares LFP while the cathode is LiNi0.6Mn0.2Co0.2O2: bp_check_chemistry returns consistent=false, missing=[Fe,P], forbidden=[Co,Ni,Mn]. Status is inconsistent. |
| `BP-03` | `compliant` | Boundary just inside: primaryDataShare is exactly 0.50. The gate test is share < 0.50, so it passes. Status is compliant, not non_compliant. |
| `BP-04` | `non_compliant` | Boundary just outside: primaryDataShare 0.49 gives 'primaryDataShare=0.49 is below threshold 0.50'. Status is non_compliant, even though the EU gate and the chemistry check pass. |
| `BP-05` | `non_compliant` | Looks identical to BP-01, but lastAuditDate 2024-03-02 is more than 365 days old, so the due-diligence gate blocks it. |
| `BP-06` | `not_assessable` | Na-ion contains none of the watch-list materials, so due diligence is a no-op, and bp_check_chemistry returns consistent=true because the chemistry is unknown. A careless run calls it compliant, but the EU gate reports that combo NAION:EV is not in the matrix. |

All 6 correct counts as PASS. Missing any trap item (`BP-02`, `BP-03`, `BP-04`, `BP-05`, `BP-06`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:batterypass` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode batterypass`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
