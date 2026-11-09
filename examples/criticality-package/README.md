# Example: Criticality Safety Package

> Review six civilian fuel-storage criticality packages against the USL, benchmark-validation, burnup-pairing and SAR benchmark-reference gates before SAR inclusion.

A general-purpose LLM reads the records and gives a confident verdict. The `nucsci` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `generate_sar_section` | Draft a Safety Analysis Report section following NRC regulatory format. |
| `query_icsbep` | Query ICSBEP benchmark database for applicable criticality safety cases. |
| `process_nuclear_data` | Process evaluated nuclear data with NJOY21. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:nucsci` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

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

```bash
tokn agent-run --mode nucsci --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
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
| `PKG-B` | `engineer_review` | Boundary just inside: mean_bias -0.0100 is exactly at the limit; math.Abs(bias) > 0.01 is false (validation.go:306), and 20 cases meets the minimum (validation.go:299). It is engineer_review because keff + 2 sigma = 0.9060 >= 0.90 (validation.go:223), not revalidate. |
| `PKG-C` | `blocked` | Boundary: the mean 0.9400 looks under the USL, but 0.9400 + 2 x 0.0050 = 0.9500 exactly, and the gate blocks at keffUpper >= 0.95 (validation.go:214). A run that gates on the mean, or reads 'at or above' as 'above', gets this wrong. |
| `PKG-D` | `revalidate` | Subcritical (0.8912) with 24 cases, but mean_bias 0.0125 exceeds the 0.01 limit (validation.go:306), so validation is inadequate. |
| `PKG-E` | `blocked` | Looks best (keff + 2 sigma = 0.8664, 28 cases, small bias, SAR draft succeeds) but 48 GWd/tHM >= 45 with a decay-heat analysis and no shielding analysis fails the burnup pairing gate (burnup_gate.go:53). |
| `PKG-F` | `blocked` | Looks good (keff + 2 sigma = 0.8816, a passing 22-case report exists) but its sar_request has an empty benchmark_ref, so generate_sar_section refuses with ErrRegulatoryDocWithoutValidation (tools.go:722). Filling in VR-2026-016 by hand would hide the gate. |

All 6 correct counts as PASS. Missing any trap item (`PKG-B`, `PKG-C`, `PKG-D`, `PKG-E`, `PKG-F`) is a FAIL even if the rest are right.

</details>

## Reflect

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
