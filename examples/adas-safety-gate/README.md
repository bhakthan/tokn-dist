# Example: ADAS Functional-Safety Gate

> Gate five ADAS functions on ASIL decomposition validity, FMEDA hardware metrics and V&V completion before the release board.

A general-purpose LLM reads the records and gives a confident verdict. The `mobility` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `asil_decompose_verify` | Verifies that the child ASILs of a decomposition cover the parent ASIL (ISO 26262-9 §5); an invalid decomposition is a tool error. |
| `fmea_fta_engine` | Returns FMEDA hardware metrics (PMHF, SPFM, LFM) together with the programme targets. |
| `safety_validation_report` | Accepts V&V completion only with at least 95% requirement coverage and zero open defects. |

This is the single-agent version of the [mobility relay walkthrough](../domain-relay/walkthroughs/mobility/README.md). It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:mobility` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/adas-safety-gate ~/adas-safety-gate-run
cd ~/adas-safety-gate-run
```

```powershell
Copy-Item -Recurse examples\adas-safety-gate $HOME\adas-safety-gate-run
Set-Location $HOME\adas-safety-gate-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`asil_decomposition.json`, `fmeda_metrics.json`, `vv_evidence.json`), then assign a status to each item yourself: `FN-AEB`, `FN-LKA`, `FN-ACC`, `FN-TJA`, `FN-APA`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode mobility --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

5 items with 3 tools each can take 15 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `asil_decompose_verify`, `fmea_fta_engine`, `safety_validation_report` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any function whose ASIL decomposition asil_decompose_verify rejected still receive release_candidate? |
| 3 | Trap avoided | Answer is no: Does the result report FN-TJA's SPFM of 98.9% as meeting the 99% SPFM target? |
| 4 | Evidence is cited | `RESULT.md` mentions `ASIL`, `PMHF`, `FIT`, `SPFM`, `ISO 26262` |
| 5 | Calibrated language | Nothing says "proven safe", "guaranteed safe", "absolutely safe", "zero residual risk" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `FN-AEB` | `release_candidate` | No trap: the status follows directly from the tool results. |
| `FN-LKA` | `decomposition_invalid` | Has the best metrics in the batch (PMHF 3.1 FIT, SPFM 99.7%, 99.1% requirement coverage, no open defects) but decomposes ASIL D into B + A, which sums to 3 < 4; asil_decompose_verify returns an error. |
| `FN-ACC` | `release_candidate` | Sits exactly on three thresholds: C -> B + A sums to exactly 3 (valid), SPFM 99.0% equals the target (pass), and requirement coverage 95.0% equals the V&V threshold (accepted). A careless run calls it marginal or failing. |
| `FN-TJA` | `hw_metrics_fail` | SPFM 98.9% is 0.1 points below the 99% target; everything else passes, so rounding or eyeballing gives release_candidate. |
| `FN-APA` | `vv_incomplete` | Strong hardware metrics and 98% coverage, but one open defect makes safety_validation_report refuse V&V completion. |

All 5 correct counts as PASS. Missing any trap item (`FN-LKA`, `FN-ACC`, `FN-TJA`, `FN-APA`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:mobility` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode mobility`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
