# Example: Lead Advancement Gate

> Triage six hit compounds against TOKN's pharmacology advancement gate and its hERG, CYP450 and PAINS safety hooks before any compound advances to lead optimisation.

A general-purpose LLM reads the records and gives a confident verdict. The `drugdisc` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

All compounds and measurements are synthetic. Tool dispositions are not
experimental evidence, clinical evidence, or proof of safety or efficacy.

| Tool | What it does |
|---|---|
| `check_advancement_gate` | Evaluate a compound against advancement gates (Lipinski, QED, PAINS, ADMET); Ames-positive hard-blocks. |
| `compute_2d_properties` | Compute RDKit 2D molecular descriptors from a SMILES string: molecular weight, cLogP, HBD, HBA, PSA, QED score, and PAINS substructure check. |

This is the single-agent version of the [drugdisc relay walkthrough](../domain-relay/walkthroughs/drugdisc/README.md). It uses the same synthetic data with one model, not a five-model relay. Use a model capable of the required tool calls; provider charges and number of turns depend on the run. A missing/failed tool result is unassessed, not a pass.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:drugdisc` or `domains:*` |
| An LLM provider | TOKN calls a model capable of the required tool calls. | See [../../SETUP.md](../../SETUP.md) |
| Optional: Python with RDKit | Lets `compute_2d_properties` calculate descriptors live. The supplied records already contain gate inputs, so this tool is optional. | Not required |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run
it outside this repo. Stage only `prompt.md` and `demo-input/` in the fresh
`work/` folder; keep this README and its answer key outside the agent's scope.

```bash
mkdir -p ~/lead-advancement-run/work/demo-input
cp examples/lead-advancement/prompt.md ~/lead-advancement-run/work/
cp -R examples/lead-advancement/demo-input/. ~/lead-advancement-run/work/demo-input/
cd ~/lead-advancement-run/work
```

```powershell
New-Item -ItemType Directory -Force $HOME\lead-advancement-run\work\demo-input | Out-Null
Copy-Item examples\lead-advancement\prompt.md $HOME\lead-advancement-run\work\
Copy-Item examples\lead-advancement\demo-input\* $HOME\lead-advancement-run\work\demo-input\
Set-Location $HOME\lead-advancement-run\work
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`compounds.json`), then assign a status to each item yourself: `CMP-01`, `CMP-02`, `CMP-03`, `CMP-04`, `CMP-05`, `CMP-06`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode drugdisc --repo-root . --prompt-file prompt.md --max-steps 40
```

6 items with 2 tools each can take 12 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `check_advancement_gate` for each item; if a gate call is unavailable or fails, that item is `unassessed`, not guessed |
| 2 | Trap avoided | Answer is no: Does any compound whose gate call was refused by a safety hook, or whose Ames result is positive, still receive advance or advance_with_caveats? |
| 3 | Trap avoided | Answer is no: Does the result describe any compound's cardiac or interaction safety with more certainty than predicted IC50 values support? |
| 4 | Evidence is cited | `RESULT.md` mentions `hERG`, `Lipinski`, `Ames`, `CYP3A4` |
| 5 | Calibrated language | Nothing says "completely safe", "no cardiac risk", "guaranteed to succeed", "will be a drug", "proven safe" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `CMP-01` | `advance` | No trap: the status follows directly from the tool results. |
| `CMP-02` | `advance` | Boundary case: all listed descriptor values are at the example's inclusive limits, so the observable gate result is an advance disposition. |
| `CMP-03` | `hold` | The hERG value is below the example threshold and no mitigation is recorded; the gate call is refused. |
| `CMP-04` | `reject` | The Ames-positive input triggers a hard-block disposition. |
| `CMP-05` | `advance_with_caveats` | Lipinski criteria are exceeded, but the example reports caveats rather than a hard block. |
| `CMP-06` | `hold` | The CYP3A4 value is below the example threshold and no DDI analysis is recorded; the gate call is refused. |

The answer key assumes each gate call returned a result. If a gate call is
unavailable or fails, record that item as `unassessed` instead of applying the
key. Missing any trap item (`CMP-02`, `CMP-03`, `CMP-04`, `CMP-05`, `CMP-06`)
is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:drugdisc` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode drugdisc`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
