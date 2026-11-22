# Example: Criticality Safety Package

> Review six civilian fuel-storage criticality packages against the USL, benchmark-validation, burnup-pairing and SAR benchmark-reference gates before SAR inclusion.

A general-purpose LLM reads the records and gives a confident verdict. The `nucsci` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `generate_sar_section` | Draft a Safety Analysis Report section following NRC regulatory format. |
| `query_icsbep` | Query ICSBEP benchmark database for applicable criticality safety cases. |
| `process_nuclear_data` | Process evaluated nuclear data with NJOY21. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data and one model, not a five-model relay. Use a model capable of the required tool calls; provider charges and number of turns depend on the run. A missing/failed tool result is unassessed, not a pass.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:nucsci` or `domains:*` |
| An LLM provider | TOKN calls a model; see the calibrated cost and tool-result note above. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo. The solve workspace must contain only `prompt.md` and `demo-input/`; keep this README and its answer key outside it.

```bash
cp -r examples/criticality-package ~/criticality-package-run
cd ~/criticality-package-run
```

```powershell
Copy-Item -Recurse examples\criticality-package $HOME\criticality-package-run
Set-Location $HOME\criticality-package-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`acceptance_criteria.json`, `benchmark_validation.json`, `packages.json`), then assign a status to each item yourself: `PKG-A`, `PKG-B`, `PKG-C`, `PKG-D`, `PKG-E`, `PKG-F`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

Stage only the task and synthetic input files in a fresh `work/` folder, then run with that folder as the repository root.

```bash
mkdir work && mkdir work/demo-input
cp prompt.md work/
cp demo-input/* work/demo-input/
cd work
tokn agent-run --mode nucsci --repo-root . --prompt-file prompt.md --max-steps 40
```

```powershell
New-Item -ItemType Directory -Path work | Out-Null
New-Item -ItemType Directory -Path work\demo-input | Out-Null
Copy-Item prompt.md work\
Copy-Item demo-input\* work\demo-input\
Set-Location work
tokn agent-run --mode nucsci --repo-root . --prompt-file prompt.md --max-steps 40
```

6 items with 3 tools each can take 18 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `generate_sar_section`, `query_icsbep`, `process_nuclear_data` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any package with keff + 2 sigma at or above 0.95, with burnup at or above 45 GWd/tHM lacking a paired shielding analysis, or whose SAR draft was refused for a missing benchmark reference, still receive acceptable or engineer_review? |
| 3 | Trap avoided | Answer is no: Does the result present a subcritical keff or a generated SAR draft as a final safety or licensing conclusion rather than a DRAFT requiring qualified engineer review? |
| 4 | Evidence is cited | `RESULT.md` mentions `USL`, `keff`, `GWd/tHM`, `bias` |
| 5 | Calibrated language | Nothing says "guaranteed subcritical", "cannot go critical", "zero risk", "completely safe", "approved for licensing" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `PKG-A` | `acceptable` | No trap: the status follows directly from the tool results. |
| `PKG-B` | `engineer_review` | Boundary case: the bias is at its stated limit and the sample count meets the minimum; the separate uncertainty check still requires engineer review. |
| `PKG-C` | `blocked` | The uncertainty-adjusted estimate reaches the stated blocking boundary; the mean alone must not override that disposition. |
| `PKG-D` | `revalidate` | The bias exceeds the stated acceptance limit, so validation is inadequate. |
| `PKG-E` | `blocked` | The package lacks the required paired analysis; do not treat an otherwise favorable estimate as sufficient. |
| `PKG-F` | `blocked` | The SAR request lacks a benchmark reference. Missing provenance blocks the draft; do not invent a reference. |

All 6 correct counts as PASS. Missing any trap item (`PKG-B`, `PKG-C`, `PKG-D`, `PKG-E`, `PKG-F`) is a FAIL even if the rest are right.

</details>

## Reflect

The answer key remains in this README, outside `work/`. A refused tool call, missing evidence, or incomplete result is blocked or unassessed—not a pass. No output authorizes a real operation or replaces qualified safety review.

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:nucsci` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode nucsci`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
