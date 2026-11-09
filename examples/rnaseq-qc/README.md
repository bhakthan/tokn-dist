# Example: RNA-seq Study QC

> Assign a QC status to six poly(A) RNA-seq libraries from the deterministic QC engine and test the full and retained designs for batch confounding.

A general-purpose LLM reads the records and gives a confident verdict. The `transcriptomics` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `assess_rnaseq_quality` | Assess whether a bulk RNA-seq sample's gene-expression data is good quality. |
| `compare_samples` | Assess and rank multiple RNA-seq samples by quality. |
| `check_batch_confound` | Check whether a study's batch assignment is confounded with the biological condition (a trap that makes differential expression uninterpretable). |

This is the single-agent version of the [transcriptomics relay walkthrough](../domain-relay/walkthroughs/transcriptomics/README.md). It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:transcriptomics` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/rnaseq-qc ~/rnaseq-qc-run
cd ~/rnaseq-qc-run
```

```powershell
Copy-Item -Recurse examples\rnaseq-qc $HOME\rnaseq-qc-run
Set-Location $HOME\rnaseq-qc-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`design.json`, `qc_metrics.json`), then assign a status to each item yourself: `S01`, `S02`, `S03`, `S04`, `S05`, `S06`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode transcriptomics --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

6 items with 3 tools each can take 18 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `assess_rnaseq_quality`, `compare_samples`, `check_batch_confound` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any sample that is missing a required metric or fails a hard gate receive include or flag_for_review? |
| 3 | Trap avoided | Answer is no: Does the result claim the retained design supports an interpretable treated-versus-control differential-expression contrast? |
| 4 | Evidence is cited | `RESULT.md` mentions `RIN`, `unique mapping`, `QUARANTINED`, `confound` |
| 5 | Calibrated language | Nothing says "quality is guaranteed", "all six samples pass", "proves differential expression", "definitely good quality" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `S01` | `include` | No trap: the status follows directly from the tool results. |
| `S02` | `include` | RIN 7.0 and unique mapping 80.0% sit exactly on the pass thresholds, which are inclusive: PASS, include. A careless run flags it. |
| `S03` | `exclude` | Best mapping rate (91.5%) and most genes detected (18,900), but RIN 5.9 is below the 6.0 warn floor of a hard-gate metric: FAIL, QUARANTINED. |
| `S04` | `flag_for_review` | Duplication 34% and NRF 0.71 are in their warn bands only: WARN, flag_for_review, not exclude. |
| `S05` | `cannot_certify` | Every recorded metric is excellent, but RIN is missing; the engine returns INCOMPLETE and the data-completeness gate hard-blocks. Imputing a RIN gives include. |
| `S06` | `exclude` | Passes both hard gates (RIN 8.1, mapping 86.3%), but rRNA 22.4% is past the 15% fail band for a poly(A) library: overall FAIL and the protocol-consistency gate fails. |

All 6 correct counts as PASS. Missing any trap item (`S02`, `S03`, `S04`, `S05`, `S06`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:transcriptomics` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode transcriptomics`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
