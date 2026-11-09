# Example: Climate Ensemble Claims

> Classify five synthetic regional projection claims by physical plausibility of the field, model-family independence, and whether the stated IPCC likelihood term follows from the deduplicated ensemble agreement.

A general-purpose LLM reads the records and gives a confident verdict. The `climsci` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `query_cmip6_catalog` | Search the Pangeo CMIP6 catalog via intake-esm. |
| `compute_ensemble_stats` | Compute CMIP6 multi-model ensemble statistics with model family deduplication. |

This is the single-agent version of the [climsci relay walkthrough](../domain-relay/walkthroughs/climsci/README.md). It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:climsci` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |
| Optional: Python with `intake-esm` and `xarray`, plus network access to the Pangeo catalog | Lets the tools compute live results. Without it, the prompt tells the agent to quote the dependency error and grade from the supplied data. | Not required |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/climate-ensemble ~/climate-ensemble-run
cd ~/climate-ensemble-run
```

```powershell
Copy-Item -Recurse examples\climate-ensemble $HOME\climate-ensemble-run
Set-Location $HOME\climate-ensemble-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`catalog_requests.json`, `ensemble_claims.json`, `field_ranges.json`), then assign a status to each item yourself: `CL-01`, `CL-02`, `CL-03`, `CL-04`, `CL-05`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode climsci --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

5 items with 2 tools each can take 10 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `query_cmip6_catalog`, `compute_ensemble_stats` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does the result accept CL-02's stated likelihood 'likely' as correct for the deduplicated ensemble? |
| 3 | Trap avoided | Answer is no: Does the result treat the CL-04 ten-model ensemble as having at least five independent model families? |
| 4 | Evidence is cited | `RESULT.md` mentions `model famil\|families`, `independent`, `tolerance`, `about as likely as not` |
| 5 | Calibrated language | Nothing says "undoubtedly", "definitely", "clear evidence", "robust finding", "strong evidence" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `CL-01` | `supported` | Boundary: 9 of 10 independent families agree, so p = 0.90 exactly. 'likely' (0.66-0.90) also contains 0.90, but the scan is top-down and 'very likely' (0.90-0.99) matches first. Stated 'very likely' is correct, so supported, not miscalibrated. |
| `CL-02` | `miscalibrated` | The raw count is 9/12 = 0.75, which maps to 'likely' and matches the stated term. But the 12 models are only 7 families (CESM x3, EC-Earth x3, MPI-ESM x2). 4 of 7 agree, so p = 0.571, which is 'about as likely as not'. Status is miscalibrated. |
| `CL-03` | `implausible` | Looks good: 8 independent families, p = 0.875, stated 'likely' matches. But the pr field max is 18.4 in declared units of kg m-2 s-1, which is almost certainly mm/day mislabelled. It is far above the 0.0220001 tolerance limit, so the item is implausible. The rules forbid silently converting units to rescue it. |
| `CL-04` | `insufficient_ensemble` | Ten models, all agreeing, p = 1.0, stated 'virtually certain'. The family map collapses them to 4 families (UKESM, CNRM, IPSL, ACCESS), which is below 5. Status is insufficient_ensemble. |
| `CL-05` | `supported` | Two boundaries. The tos min of 265.8 K is below the 270 K plausible minimum but inside the 265.5 K tolerance band, so it is plausible. KIOST-ESM is not in the family map, so it counts as its own family: 6 families, 4 agree, p = 0.667 >= 0.66, which is 'likely'. Dropping KIOST-ESM gives 3/5 = 0.60, wrongly 'about as likely as not'. Status is supported. |

All 5 correct counts as PASS. Missing any trap item (`CL-01`, `CL-02`, `CL-03`, `CL-04`, `CL-05`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:climsci` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode climsci`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
