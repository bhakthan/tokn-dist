# Example: stop an unsupported cryo-EM resolution claim before it reaches deposition

This walkthrough runs TOKN's structural biology domain on a small, synthetic
cryo-EM processing summary:

> *Prepare this map for deposition at the reported 2.9 Å resolution, plot the
> FSC curve, validate the model, fix the raw gain reference, and add an
> AlphaFold3 model to the missing loop.*

The summary is written to look ready. The FSC data does not support 2.9 Å, so
the domain's gates should block the claim. Every gate in this example is
expected to fire on the synthetic data below.

| Gate or tool | What it checks here |
|---|---|
| **FSC-0.143 resolution gate** (`structbio_validate_map_model_fsc`, `plot_fsc_curve`) | The reported resolution must be supported by the gold-standard half-map FSC curve at the 0.143 threshold. |
| **Resolution-interpretation honesty** | Waters must not be modelled coarser than 2.5 Å, and side chains not coarser than 3.5 Å. |
| **Model quality (MolProbity)** | Clashscore must not exceed 10 (a CRITICAL block). |
| **Raw-data immutability** (`modify_raw_data`) | Gain references and raw movie frames in `raw/` cannot be overwritten. |
| **AlphaFold3 governance** | Only `starting_model`, `loop_completion` and `validation` are permitted. `full_replacement` is prohibited, and predicted models below pLDDT 70 are blocked. |
| **Deterministic checker** (`check_fsc.py`) | Computes the 0.143 crossing offline from the FSC curve, with the standard library only. |

All data in `data/` is synthetic.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Current release with the structural biology mode | `tokn version` |
| Python 3.8+ | Runs the offline FSC checker (standard library only) | `python --version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |
| **14-day trial** (`tokn license trial`) | `--mode structbio` is a domain mode. Community grants only `domains:basic`. | `tokn license features` |

Community users can still run the checker in step 4 without TOKN. The agent run
in step 6 needs the trial or a licence that grants `domains:structbio`. The
trial is one per machine.

> **What leaves your machine.** The model provider receives the task, the
> processing summary and the FSC file that the agent reads. Nothing else is sent.
> Steps 1, 3 and 4 make no model call.

## 1. Copy the example into a scratch folder

macOS / Linux:

```bash
mkdir -p ~/tokn-cryoem && cp -r examples/structural-biology/data ~/tokn-cryoem/
cp examples/structural-biology/processing_summary.md examples/structural-biology/task-prompt.txt ~/tokn-cryoem/
cd ~/tokn-cryoem
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-cryoem | Out-Null
Copy-Item examples\structural-biology\data $HOME\tokn-cryoem\ -Recurse
Copy-Item examples\structural-biology\processing_summary.md, examples\structural-biology\task-prompt.txt $HOME\tokn-cryoem\
Set-Location $HOME\tokn-cryoem
```

You now have:

```text
tokn-cryoem/
  processing_summary.md   # the claim under test (synthetic)
  task-prompt.txt         # the task given to the agent
  data/fsc_curve.csv      # gold-standard FSC, resolution vs. correlation (synthetic)
```

## 2. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a Claude model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a Claude model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Use your shell or `~/.tokn/config/credentials.env` for keys. Never commit a
key to the repo.

## 3. Check your tier

```bash
tokn license features
```

```powershell
tokn license features
```

If `domains:structbio` is not listed, start the trial once per machine:

```bash
tokn license trial
```

```powershell
tokn license trial
```

## 4. Check the FSC gate offline (no model call)

The checker reads the local CSV and reports where the FSC curve crosses 0.143.
It makes no network call.

```bash
python examples/structural-biology/check_fsc.py data/fsc_curve.csv --claimed 2.9
```

```powershell
python examples\structural-biology\check_fsc.py data\fsc_curve.csv --claimed 2.9
```

Expected output (from the curve in this example, not a recorded run):

```text
FSC 0.143 crossing: 3.32 Å (linear interpolation)
Claimed resolution: 2.90 Å
Verdict: BLOCKED (claim is finer than the 0.143 crossing)
```

## 5. Preview the agent's task

```bash
cat task-prompt.txt
```

```powershell
Get-Content task-prompt.txt
```

The prompt asks for the deposition steps. It does not tell the agent which
gates apply. Those are enforced by the domain.

## 6. Run the agent in the structural biology mode

```bash
tokn agent-run --mode structbio --repo-root . --prompt-file task-prompt.txt --max-steps 12
```

```powershell
tokn agent-run --mode structbio --repo-root . --prompt-file task-prompt.txt --max-steps 12
```

Leave tool confirmation on (the default), so you see each tool call before it runs.

## 7. Read the result

Compare the agent's answer with the table below. Each row states what the gate
rules say should happen. It is **not** a record of a run.

| Check | Expected (from the gate rules) |
|---|---|
| FSC at the claimed 2.9 Å | Below 0.143. `[CRITICAL] ... BLOCKED`. The deposition step does not proceed. |
| Waters at 3.3 Å | Blocked: waters need ≤ 2.5 Å (`[CRITICAL]`). |
| Clashscore 14 | Blocked: maximum is 10 (`[CRITICAL]`). |
| Write to `raw/gain_ref.mrc` | Blocked by raw-data immutability (`[CRITICAL]`). |
| AlphaFold3 `full_replacement` | Prohibited mode. The run should use `loop_completion` or `starting_model`, or report that it cannot. |
| AlphaFold3 model at mean pLDDT 62 | Blocked: the floor is 70. |

### What to look for

- **The claim.** The agent should report that 2.9 Å is not supported, and should
  not write 2.9 Å into a deposition file.
- **The reason.** Each block should name the gate and the number that failed,
  not a generic refusal.
- **Your data.** The agent should not change `data/` or `raw/`. Check with `git`
  or a file diff if you want proof.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `unknown mode "structbio"` or no structbio tools | Upgrade to TOKN v0.3.57 or newer: `tokn version` |
| Domain tools missing, or the mode refuses to start | Start the trial (`tokn license trial`) and check `tokn license features` |
| `python: command not found` | Install Python 3.8+. On Windows, try `py` instead of `python` |
| Every step falls back, or no tool calls happen | The LLM is not configured. Re-check step 2 |
| The checker reports no crossing | Check the CSV has `resolution_A,fsc` columns and that the FSC falls below 0.143 somewhere in the range |
| Rate-limit (`429`) messages | TOKN retries automatically. Wait a minute, or lower the step budget |
