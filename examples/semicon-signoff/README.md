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

This is the single-agent version of the [semicon relay walkthrough](../domain-relay/walkthroughs/semicon/README.md). It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the semicon guard and tool fixes this example relies on. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:semicon` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic. No real design data, PDK files or EDA licenses are needed.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/semicon-signoff ~/semicon-run
cd ~/semicon-run
```

```powershell
Copy-Item -Recurse examples\semicon-signoff $HOME\semicon-run
Set-Location $HOME\semicon-run
```

## 2. Configure the LLM

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<your model name>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<your model name>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

For other providers, see [../../SETUP.md](../../SETUP.md).

## 3. Before you run: make your own call

Open the three files in `demo-input/` and assign a status to each block yourself. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode semicon --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

```powershell
tokn agent-run --mode semicon --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
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

| Block | Status | Why |
|---|---|---|
| `BLK-CPU` | `tapeout_ready` | All checks clean. |
| `BLK-DSP` | `tapeout_ready` | WNS 0.000 ns is closed, and 0.80 utilization is not above the 80% target. Both sit exactly on a boundary. |
| `BLK-USB` | `fail_signoff` | Best timing in the batch, but 2 LVS discrepancies. |
| `BLK-SRAMCTL` | `ready_with_caveats` | Utilization 0.82 is above the target but within the 84% limit: a warning, not a failure. |
| `BLK-DMA` | `fail_signoff` | WNS −0.003 ns. Rounding it to zero is the trap. |
| `BLK-PCIE` | `blocked` | Clean DRC/LVS and +0.150 ns WNS look ready, but the STA run has no SDC, so the slack is unconstrained. Rerun timing with constraints. |

Six correct counts as PASS. Calling `BLK-PCIE` ready, or `BLK-USB`/`BLK-DMA` anything but `fail_signoff`, is a FAIL even if the rest are right.

</details>

## Reflect

- Which block did you get wrong in step 3? Most people trust `BLK-PCIE`'s slack or round `BLK-DMA` to zero.
- The best-looking timing (`BLK-USB`) failed on a different check. What does that say about ranking blocks by one metric?
- Edit `demo-input/sta_runs.json` to give `BLK-PCIE` an SDC path (for example `constraints/blk_pcie.sdc`) and rerun. It should move from `blocked` to `tapeout_ready`, because the hook now lets `static_timing` judge the recorded slack. In a real flow, the timing run itself would have to be redone with constraints.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:semicon` is missing | Run `tokn license trial`, then `tokn license features`. |
| The constraints hook never fires | Confirm `--mode semicon`. Other modes do not load the semicon hooks. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
