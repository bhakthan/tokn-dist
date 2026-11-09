# Example: Green Energy Project Screen

> Screen three electrolysers and two renewable generators for green-bond eligibility using the hydrogen carbon-intensity, yield and EU Taxonomy DNSH tools, and classify each project.

A general-purpose LLM reads the records and gives a confident verdict. The `greenenergy` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `compute_hydrogen_production` | Compute electrolytic hydrogen output, LCOH and carbon-intensity gate. |
| `screen_eu_taxonomy` | Screen an activity against the EU Taxonomy (Delegated Reg. (EU) 2021/2139). |
| `run_solar_yield` | Run an hourly PVWatts v5 solar yield simulation. |
| `run_wind_yield` | Compute wind-farm AEP from a power curve and wind distribution. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:greenenergy` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/green-project-screen ~/green-project-screen-run
cd ~/green-project-screen-run
```

```powershell
Copy-Item -Recurse examples\green-project-screen $HOME\green-project-screen-run
Set-Location $HOME\green-project-screen-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`generation_projects.json`, `hydrogen_projects.json`, `taxonomy_screens.json`), then assign a status to each item yourself: `GH-1`, `GH-2`, `GH-3`, `GH-4`, `GH-5`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode greenenergy --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

5 items with 4 tools each can take 20 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `compute_hydrogen_production`, `screen_eu_taxonomy`, `run_solar_yield`, `run_wind_yield` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any project whose Taxonomy screen or yield run returned an error (GH-1 or GH-5) still receive eligible or not_eligible instead of rework? |
| 3 | Trap avoided | Answer is no: Is the GH-3 hydrogen, at a carbon intensity above the RFNBO threshold, described as green or eligible? |
| 4 | Evidence is cited | `RESULT.md` mentions `P90`, `RFNBO`, `DNSH`, `carbon intensity` |
| 5 | Calibrated language | Nothing says "guaranteed yield", "certified green", "zero-carbon", "emission-free" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `GH-1` | `rework` | Looks like the best project — lowest carbon intensity (2.10, classified green) — but its Taxonomy screen omits the biodiversity DNSH objective, so screen_eu_taxonomy errors and the project must be reworked. |
| `GH-2` | `eligible` | Boundary item: carbon intensity is exactly 3.38, equal to the threshold; the tool uses <=, so it is green and the project is eligible. A careless run treats equality as a failure. |
| `GH-3` | `not_eligible` | Just outside the boundary: 3.41 exceeds 3.38 by 0.03, so the tool returns grey with a ci_warning; every call completes, so it is not_eligible, not rework. |
| `GH-4` | `eligible` | No trap: the status follows directly from the tool results. |
| `GH-5` | `rework` | Turbine spec is plausible and the data source is TMY, but P90 (291000) is above P50 (288000), so run_wind_yield returns an exceedance-ordering error — rework, not eligible. |

All 5 correct counts as PASS. Missing any trap item (`GH-1`, `GH-2`, `GH-3`, `GH-5`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:greenenergy` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode greenenergy`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
