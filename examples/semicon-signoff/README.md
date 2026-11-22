# Example: Semiconductor Tapeout Signoff

> "Six macros came back from place-and-route. Which ones are ready for tapeout?"

A general-purpose LLM reads the numbers and ranks the blocks. The `semicon` domain mode runs each block through the signoff tools under signoff policy: constrained timing, zero DRC violations, zero LVS discrepancies, and a utilization target with a margin. It also refuses timing results that cannot be trusted.

| Capability | What it does |
|---|---|
| `floorplan` | Checks utilization against the 80% target. Inside the 5% margin it warns; above it, it fails. |
| `static_timing` | Reports worst negative slack (WNS). Timing is closed only when WNS ≥ 0 ns. |
| `drc_check` | Design-rule check, zero tolerance. |
| `lvs_check` | Layout-versus-schematic check, zero tolerance. |
| `enforce_constraints_present` hook | Blocks a timing run that has no SDC constraints file, because its slack means nothing. |

This is the single-agent version of the [semicon relay walkthrough](../domain-relay/walkthroughs/semicon/README.md). It uses the same synthetic data and one model, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the semicon guard and tool fixes this example relies on. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:semicon` or `domains:*` |
| An LLM provider | TOKN calls a model. | See [../../SETUP.md](../../SETUP.md) |

Use a model capable of the required tool calls; provider charges and number of
turns depend on the run. A missing/failed tool result is unassessed, not a pass.

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic. No real design data, PDK files or EDA licenses are needed.

## 1. Copy the example to a scratch folder

Create a new work folder outside this checkout. Copy only `prompt.md` and
`demo-input/` into it; do not copy this README or `grading/`. TOKN writes
`.nospace/` state and output files into the work folder.

```bash
mkdir -p ~/semicon-run/demo-input
cp examples/semicon-signoff/prompt.md ~/semicon-run/
cp -r examples/semicon-signoff/demo-input/. ~/semicon-run/demo-input/
cd ~/semicon-run
```

```powershell
New-Item -ItemType Directory -Force $HOME\semicon-run\demo-input | Out-Null
Copy-Item examples\semicon-signoff\prompt.md $HOME\semicon-run\
Copy-Item examples\semicon-signoff\demo-input\* $HOME\semicon-run\demo-input\
Set-Location $HOME\semicon-run
```

## 2. Configure the LLM

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic API key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "YOUR_MODEL_ID"
# Set ANTHROPIC_API_KEY from a trusted secret store or your protected shell session.
```

For other providers, see [../../SETUP.md](../../SETUP.md).

## 3. Before you run: make your own call

Open the three files in `demo-input/` and assign a status to each block yourself. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode semicon --repo-root . --prompt-file prompt.md --max-steps 40
```

```powershell
tokn agent-run --mode semicon --repo-root . --prompt-file prompt.md --max-steps 40
```

Six blocks with four tools each need about 24 tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | All four tools run on every block | `floorplan`, `static_timing`, `drc_check` and `lvs_check` each appear six times |
| 2 | The constraints hook fires | `static_timing` on one block is blocked for a missing SDC file |
| 3 | No invented inputs | The model does not create or substitute a constraints file |
| 4 | Boundaries are exact | A WNS of exactly 0.000 ns counts as closed; a few picoseconds negative does not |
| 5 | Caveats are named | The within-margin block names routing congestion as the risk |
| 6 | Calibrated language | Nothing claims "guaranteed to work in silicon" |

<details>
<summary>Answer key (open after your run)</summary>

See the [grader-only answer key](grading/answer-key.md). It is outside the staged work folder.
</details>

## Reflect

- Which block did you get wrong in step 3? Most people trust `BLK-PCIE`'s slack or round `BLK-DMA` to zero.
- The best-looking timing (`BLK-USB`) failed on a different check. What does that say about ranking blocks by one metric?
- Edit `demo-input/sta_runs.json` to give `BLK-PCIE` an SDC path (for example `constraints/blk_pcie.sdc`) and rerun. It should move from `blocked` to `tapeout_ready`, because the hook now lets `static_timing` judge the recorded slack. In a real flow, the timing run itself would have to be redone with constraints.
- A missing or failed tool result is unassessed, not a pass. These synthetic checks do not authorize a tapeout; a qualified human signoff is still required.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:semicon` is missing | Run `tokn license trial`, then `tokn license features`. |
| The constraints hook never fires | Confirm `--mode semicon`. Other modes do not load the semicon hooks. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
