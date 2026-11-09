# Example: Neural Recording QC

> Assign each of six de-identified fMRI/EEG recordings a readiness status from the neurosci quality gates and the IRB/consent gate before they enter a group analysis.

A general-purpose LLM reads the records and gives a confident verdict. The `neurosci` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `inspect_nwb` | Read NWB file metadata: sessions, electrodes, units, optical physiology, and behavior modules. |
| `validate_bids` | Run bids-validator on a BIDS directory. |
| `compute_quality_metrics` | Compute SpikeInterface quality metrics (ISI violations, SNR, firing rate, presence ratio, isolation distance) with biological validity gates. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:neurosci` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |
| Optional: Python with `pynwb` and SpikeInterface, and `bids-validator` | Lets the tools compute live results. Without it, the prompt tells the agent to quote the dependency error and grade from the supplied data. | Not required |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/neuro-recording-qc ~/neuro-recording-qc-run
cd ~/neuro-recording-qc-run
```

```powershell
Copy-Item -Recurse examples\neuro-recording-qc $HOME\neuro-recording-qc-run
Set-Location $HOME\neuro-recording-qc-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`ethics.json`, `recordings.json`), then assign a status to each item yourself: `REC-01`, `REC-02`, `REC-03`, `REC-04`, `REC-05`, `REC-06`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode neurosci --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

6 items with 3 tools each can take 18 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `inspect_nwb`, `validate_bids`, `compute_quality_metrics` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any recording whose consented scope does not cover group_analysis, or that fails a modality quality gate, still receive ready or ready_with_caveats? |
| 3 | Trap avoided | Answer is no: Does the result exclude or flag REC-02 even though its FD 0.50 mm, censored fraction 20% and tSNR 40.0 sit exactly on thresholds that pass? |
| 4 | Evidence is cited | `RESULT.md` mentions `framewise displacement`, `tSNR`, `epoch acceptance`, `IRB`, `consent` |
| 5 | Calibrated language | Nothing says "all six recordings pass", "all recordings are ready", "guaranteed clean", "artifact-free", "no ethics concerns" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `REC-01` | `ready` | No trap: the status follows directly from the tool results. |
| `REC-02` | `ready` | Boundary: FD 0.50 mm, censored 0.20 and tSNR 40.0 are all exactly on threshold; validateFMRI uses strict > / < so all pass: ready. |
| `REC-03` | `ready_with_caveats` | Passes EEG gates (121 μV, 83%) and IRB is valid, but expires 2026-11-20, inside the 30-day warn window: ready_with_caveats, not ready. |
| `REC-04` | `exclude` | Epoch acceptance 81% looks fine, but peak amplitude 162 μV exceeds the 150 μV reject gate: exclude. |
| `REC-05` | `blocked` | Best signal in the batch (88 μV, 94% epochs, valid protocol ID) but consented scope is single_subject_clinical_review, which does not contain group_analysis: irb_scope fails, blocked. |
| `REC-06` | `exclude` | Mean FD 0.31 mm and tSNR 61.7 look good, but 27% censored frames exceeds the 20% gate: exclude. |

All 6 correct counts as PASS. Missing any trap item (`REC-02`, `REC-03`, `REC-04`, `REC-05`, `REC-06`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:neurosci` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode neurosci`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
