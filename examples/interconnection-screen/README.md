# Example: Interconnection N-1-1 Screen

> Dispose five interconnection requests using the N-1-1 cascading-outage screen and the IEEE 2800 IBR stability gate.

A general-purpose LLM reads the records and gives a confident verdict. The `grideng` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `powergrid_n1_1_screen` | Screens N-1-1 outage pairs against post-contingency voltage and thermal limits and grades each violation HIGH or CRITICAL. |
| `powergrid_ibr_stability_gate` | Blocks an expansion that adds grid-following capacity with no grid-forming capacity and pushes zonal GFL penetration past the threshold. |
| `run_n1_contingency_screen` | N-1 contingency screen over a network model or supplied single-outage results. |

This is the single-agent version of the [powergrid relay walkthrough](../domain-relay/walkthroughs/powergrid/README.md). It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:grideng` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/interconnection-screen ~/interconnection-screen-run
cd ~/interconnection-screen-run
```

```powershell
Copy-Item -Recurse examples\interconnection-screen $HOME\interconnection-screen-run
Set-Location $HOME\interconnection-screen-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`ibr_registry.json`, `n11_study.json`), then assign a status to each item yourself: `IR-1`, `IR-2`, `IR-3`, `IR-4`, `IR-5`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode grideng --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

5 items with 3 tools each can take 15 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `powergrid_n1_1_screen`, `powergrid_ibr_stability_gate`, `run_n1_contingency_screen` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any request whose expansion the IBR stability gate blocks still receive approve or approve_with_conditions? |
| 3 | Trap avoided | Answer is no: Is any value sitting exactly at an N-1-1 limit (115.0% loading, 0.85 pu, 1.10 pu) or exactly at the 30.0% GFL threshold treated as a violation? |
| 4 | Evidence is cited | `RESULT.md` mentions `N-1-1`, `IEEE 2800`, `grid-forming\|grid forming\|GFM`, `penetration` |
| 5 | Calibrated language | Nothing says "fully secure", "guaranteed reliable", "no risk of cascading", "proven stable", "zero risk" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `IR-1` | `approve` | No trap: the status follows directly from the tool results. |
| `IR-2` | `approve_with_conditions` | L-203 at 131.0% looks severe and exceeds the 100% N-1 criterion the baseline screen tool prints, but N-1-1 CRITICAL needs > 132.25% (115% x 1.15); it is HIGH only, so approve_with_conditions, not reject. |
| `IR-3` | `blocked` | Cleanest N-1-1 screen in the batch (max 101% loading, all voltages >= 0.92 pu), but it adds 60 MW grid-following with no grid-forming capacity, pushing Z-SOUTH GFL penetration to 34.8% > 30% — the IBR gate blocks it. |
| `IR-4` | `approve` | Boundary item: L-403 at exactly 115.0%, B-42 at exactly 0.85 pu, B-44 at exactly 1.10 pu, and post-expansion GFL penetration exactly 30.0% — none exceeds its strict limit, so it is a clean approve. |
| `IR-5` | `reject` | Every loading and voltage is inside limits; the only signal is stability_loss on the L-501\|L-502 pair, which is CRITICAL. |

All 5 correct counts as PASS. Missing any trap item (`IR-2`, `IR-3`, `IR-4`, `IR-5`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:grideng` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode grideng`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
