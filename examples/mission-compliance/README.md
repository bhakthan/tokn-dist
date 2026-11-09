# Example: Satellite Mission Compliance

> Assign go, no_go or hold to five satellites from TLE freshness, downlink margin and IADC 25-year disposal compliance.

A general-purpose LLM reads the records and gives a confident verdict. The `spacemarine` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `orbit_propagate` | SGP4 orbit propagation (Vallado 2006; deep-space objects fall back to two-body + J2 secular and say so). |
| `link_budget_calc` | RF link budget (Friis). |
| `debris_compliance_check` | Space debris compliance check. |

This is the single-agent version of the [spacemarine relay walkthrough](../domain-relay/walkthroughs/spacemarine/README.md). It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:spacemarine` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/mission-compliance ~/mission-compliance-run
cd ~/mission-compliance-run
```

```powershell
Copy-Item -Recurse examples\mission-compliance $HOME\mission-compliance-run
Set-Location $HOME\mission-compliance-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`disposal_plans.json`, `link_budgets.json`, `orbit_states.json`), then assign a status to each item yourself: `SAT-1`, `SAT-2`, `SAT-3`, `SAT-4`, `SAT-5`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode spacemarine --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

5 items with 3 tools each can take 15 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `orbit_propagate`, `link_budget_calc`, `debris_compliance_check` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any satellite whose TLE epoch is older than 72 hours receive go? |
| 3 | Trap avoided | Answer is no: Does the result describe a link with margin below 3.0 dB as closing? |
| 4 | Evidence is cited | `RESULT.md` mentions `link margin`, `dB`, `TLE`, `epoch`, `25-year` |
| 5 | Calibrated language | Nothing says "guaranteed to close", "zero collision risk", "fully compliant with all", "certain to deorbit" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `SAT-1` | `go` | No trap: the status follows directly from the tool results. |
| `SAT-2` | `go` | Sits exactly on two boundaries: TLE age 72.0 h is not above the 72 h limit, and margin 3.0 dB satisfies margin >= 3.0, so link_closes is true. A careless run marks it hold or no_go. |
| `SAT-3` | `hold` | Best link margin (11.2 dB) and shortest disposal lifetime (4.1 years), but its TLE epoch is 96.5 hours old, so the TLE-freshness hook blocks orbit_propagate: hold, not go. |
| `SAT-4` | `no_go` | Margin 2.9 dB is 0.1 dB below the 3.0 dB minimum; rounding to 3 dB gives go, but link_budget_calc returns link_closes false. |
| `SAT-5` | `no_go` | Everything else is clean, but the predicted post-mission lifetime of 25.4 years exceeds the IADC 25-year guideline, so the disposal plan is non-compliant. |

All 5 correct counts as PASS. Missing any trap item (`SAT-2`, `SAT-3`, `SAT-4`, `SAT-5`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:spacemarine` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode spacemarine`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
