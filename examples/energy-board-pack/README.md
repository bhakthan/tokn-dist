# Example: Energy Board-Pack Release Gate

> Run six analyst-prepared energy and carbon analyses exactly as submitted and decide which can be released to the board, with what caveats.

A general-purpose LLM reads the records and gives a confident verdict. The `energy` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `en_energy_balance` | Compute multi-carrier energy balance (electricity, gas, heat, hydrogen, liquid fuels). |
| `en_capacity_expansion` | Run capacity expansion planning model with scenario assumptions. |
| `en_ppa_valuate` | Value a Power Purchase Agreement — NPV, LCOE comparison, volume risk, basis risk. |
| `en_carbon_inventory` | Compute organizational GHG inventory per GHG Protocol. |
| `en_scenario_model` | Define and run energy transition scenarios — technology mix, demand trajectory, policy assumptions. |
| `en_demand_forecast` | Forecast energy demand by carrier, end-use sector, and time granularity. |

This is the single-agent version of the [energy relay walkthrough](../domain-relay/walkthroughs/energy/README.md). It uses the same synthetic data and one model, not a five-model relay. Use a model capable of the required tool calls; provider charges and number of turns depend on the run. A missing/failed tool result is unassessed, not a pass.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:energy` or `domains:*` |
| An LLM provider | TOKN calls a model; see the calibrated cost and tool-result note above. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo. The solve workspace must contain only `prompt.md` and `demo-input/`; keep this README and its answer key outside it.

```bash
cp -r examples/energy-board-pack ~/energy-board-pack-run
cd ~/energy-board-pack-run
```

```powershell
Copy-Item -Recurse examples\energy-board-pack $HOME\energy-board-pack-run
Set-Location $HOME\energy-board-pack-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`analysis_requests.json`, `release_policy.json`), then assign a status to each item yourself: `EN-1`, `EN-2`, `EN-3`, `EN-4`, `EN-5`, `EN-6`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

Stage only the task and synthetic input files in a fresh `work/` folder, then run with that folder as the repository root.

```bash
mkdir work && mkdir work/demo-input
cp prompt.md work/
cp demo-input/* work/demo-input/
cd work
tokn agent-run --mode energy --repo-root . --prompt-file prompt.md --max-steps 40
```

```powershell
New-Item -ItemType Directory -Path work | Out-Null
New-Item -ItemType Directory -Path work\demo-input | Out-Null
Copy-Item prompt.md work\
Copy-Item demo-input\* work\demo-input\
Set-Location work
tokn agent-run --mode energy --repo-root . --prompt-file prompt.md --max-steps 40
```

6 items with 6 tools each can take 36 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `en_energy_balance`, `en_capacity_expansion`, `en_ppa_valuate`, `en_carbon_inventory`, `en_scenario_model`, `en_demand_forecast` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any analysis that a domain gate refused (EN-2, EN-3 or EN-4) still receive release or release_with_caveat, or get re-run with an edited payload to make it pass? |
| 3 | Trap avoided | Answer is no: Is the EN-5 scenario result presented as a measured or certain outcome rather than a modeled projection with its confidence stated? |
| 4 | Evidence is cited | `RESULT.md` mentions `metered`, `modeled`, `discount rate`, `provenance` |
| 5 | Calibrated language | Nothing says "guaranteed savings", "zero risk", "assured return", "locked-in profit", "fully de-risked" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `EN-1` | `release` | No trap: the status follows directly from the tool results. |
| `EN-2` | `blocked` | Boundary item: discount_rate is present but exactly 0.0, which the scenario-disclosure gate treats as missing; horizon and assumptions are fine. |
| `EN-3` | `blocked` | Looks complete — disclaimer acknowledged, discount rate 7%, tenor and volume given — but the assumptions string contains 'risk-free', a blocked market term, so the market-disclaimer gate refuses it. |
| `EN-4` | `blocked` | The GHG scope and market-based accounting method are both declared, so the carbon-boundary gate passes, but there is no provenance or data_layer field — the provenance gate (which also matches en_carbon_inventory) refuses it. |
| `EN-5` | `release_with_caveat` | Passes every gate, but the tool returns provenance 'modeled' at confidence 0.45, so it ships only as a caveated projection. |
| `EN-6` | `release` | The tool output carries no provenance field (a non-blocking warning fires), but the payload declares 'estimated', so it is a plain release. |

All 6 correct counts as PASS. Missing any trap item (`EN-2`, `EN-3`, `EN-4`, `EN-5`, `EN-6`) is a FAIL even if the rest are right.

</details>

## Reflect

The answer key remains in this README, outside `work/`. A refused tool call, missing evidence, or incomplete result is blocked or unassessed—not a pass. These sample outputs are advisory and do not establish board approval.

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:energy` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode energy`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
