# Example: emulating a synthetic clinical trial with the clintrial safety hooks

> **Not for clinical use.** The cohort and the trial specification are synthetic.
> TOKN's clinical-trial mode is decision support for a research team. Its output
> is not clinical evidence and does not replace a randomised trial.

This walkthrough takes a synthetic two-arm trial through TOKN's `clintrial`
mode. It checks the specification, looks for confounding, runs the validation
the spec asks for, and stops before any evidence is emitted:

> *Emulate a synthetic target trial of two EGFR inhibitors on an 8-patient
> synthetic cohort. Restate the estimand, check for confounding, estimate the
> effect naively and after adjustment, run the placebo and negative-control
> checks, and stop before emitting the evidence summary.*

| Hook | What it protects against | Observable output cue |
|---|---|---|
| `estimand_completeness` | An analysis that starts before the question is fully specified | Inspect the reached gate's status and evidence in the agent run output. |
| `phi_before_model` / `phi_input_screen` | Identifiers reaching the model | Inspect the reached gate's status and evidence in the agent run output. |
| `positivity_before_emulate` | An estimate computed where one arm has no overlap | Inspect the reached gate's status and evidence in the agent run output. |
| `validation_before_emit` | Evidence emitted before the validation suite runs | Inspect the reached gate's status and evidence in the agent run output. |
| `human_in_loop_before_emit` | Evidence emitted without a human decision | Inspect the reached gate's status and evidence in the agent run output. |
| `no_silent_artifact` | Output written with no visible record | Inspect the reached gate's status and evidence in the agent run output. |
| `calibrated_language` / `decision_support_disclaimer` | Overstated certainty, or output without the disclaimer | Inspect the reached gate's status and evidence in the agent run output. |

The offline fixture checker validates the input structure only. Counting a hook
name in saved output does not establish that its gate passed.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with this example's hook names | `tokn version` |
| **14-day trial** (`tokn license trial`) | `--mode clintrial` is a domain mode. The Community tier grants only `domains:basic`, so the run is refused without a trial. | `tokn license features` |
| Python 3.8+ (optional) | Runs the local input and output checker. Standard library only. | `python --version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |

Non-domain features in TOKN work on either the trial or Community. This
example's run needs the trial.

> **What leaves your machine.** The model provider receives the prompt and the
> files the agent reads, which are the synthetic inputs in this folder. Starting
> the trial also sends a one-time anonymous install registration (a machine hash
> and the TOKN version). Set `TOKN_NO_TELEMETRY=1` to opt out.

## 1. Copy the example into a working folder

macOS / Linux:

```bash
cp -r examples/clintrial ~/tokn-clintrial
cd ~/tokn-clintrial
```

Windows PowerShell:

```powershell
Copy-Item examples\clintrial $HOME\tokn-clintrial -Recurse
Set-Location $HOME\tokn-clintrial
```

You now have:

```text
tokn-clintrial/
  prompt.md                        # the emulation task
  inputs/target-trial-spec.json    # estimand, confounders, validation plan
  inputs/synthetic-cohort.json     # 8 synthetic patients
  check_inputs.py                  # optional local checker
```

## 2. Start the trial

```bash
tokn license trial
tokn license features
```

```powershell
tokn license trial
tokn license features
```

`tokn license trial` runs once per machine. The second command shows the tier and
days remaining.

## 3. Check the inputs (optional, local only)

```bash
python check_inputs.py inputs/
```

```powershell
python check_inputs.py inputs\
```

This validates the estimand fields, confirms both files are marked synthetic,
and confirms both treatment arms are present. It reads local files only.

## 4. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME='YOUR_MODEL_NAME'
read -rs -p 'Anthropic API key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "YOUR_MODEL_NAME"
$secret = Read-Host "Anthropic API key" -AsSecureString
$env:ANTHROPIC_API_KEY      = [System.Net.NetworkCredential]::new('', $secret).Password
```

Keep keys in your shell or `~/.tokn/config/credentials.env`. Never commit a key.

## 5. Run the emulation task

Keep the run's read scope to the task and synthetic inputs. Do not put the
worked provenance/disposition fixture or this README in `work/`.

```bash
mkdir -p work/inputs
cp prompt.md work/prompt.md
cp inputs/*.json work/inputs/
cd work
```

```powershell
New-Item -ItemType Directory -Force work\inputs | Out-Null
Copy-Item prompt.md work\prompt.md
Copy-Item inputs\*.json work\inputs\
Set-Location work
```

```bash
tokn agent-run --mode clintrial --prompt-file prompt.md --repo-root . \
  --max-steps 12 --output-format json > result.json
```

```powershell
tokn agent-run --mode clintrial --prompt-file prompt.md --repo-root . `
  --max-steps 12 --output-format json > result.json
```

`--output-format json` prints one final object, with `status`, `result`,
`exit_code`, `steps`, `usage` and `errors`. Save it and check it.

## 6. Check the hooks (optional, local only)

From the scratch-folder root, run the checker against the original fixture and
then inspect the saved run in `work/`. The input check is offline; the run-output
mode counts hook-name mentions and does not validate gate outcomes.

```bash
cd ..
python check_inputs.py inputs/
python check_inputs.py work/result.json
```

```powershell
Set-Location ..
python check_inputs.py inputs\
python check_inputs.py work\result.json
```

Both checks make no network calls. Read gate evidence and disposition in the run
output; a hook-name mention is not a pass.

## Synthetic provenance and disposition fixture

`grading/provenance-disposition.json` is a static, synthetic example—not output
from an agent run. It pairs the fixture-input digests and checker scope with the
disposition `hold_for_human_review`; it contains no treatment recommendation or
clinical conclusion. The offline input checker does not verify these digests or
evaluate clinical evidence.

## 7. Expected outcomes

The following are expected outcomes for the synthetic fixture; they are not a
recorded run. The offline fixture checker validates input structure only. It is
separate from an optional licensed agent review.

| Step in `prompt.md` | Observable expected gate result |
|---|---|
| 1. Restate the estimand | All six elements are present in `target-trial-spec.json`, so `estimand_completeness` passes. |
| 2. Confirm synthetic data | Both files are marked `synthetic: true`. Any real identifier is a `phi_*` block. |
| 3. Confounding | Frailty, age and brain metastasis are visibly unbalanced between arms. The treated arm is healthier, so the naive estimate is likely to overstate the benefit. |
| 4. Estimate | A naive and an adjusted hazard ratio are reported, with uncertainty stated. The language is calibrated, and it says eight records are illustrative only. `positivity_before_emulate` checks overlap first. |
| 5. Validation | The placebo (null) check and the negative-control outcome are run. The E-value is compared against the spec's threshold of 1.5. |
| 6. Stop | `human_in_loop_before_emit` and `validation_before_emit` hold. No evidence summary is emitted as a final artifact. |

## What to look for

- **The naive and adjusted estimates differ.** That difference is the
  confounding the spec warns about. Look for the agent to say so.
- **Uncertainty is stated.** With eight patients the interval is wide. An
  answer with a single confident number is a failure of `calibrated_language`.
- **Nothing is emitted as final.** The run stops before the evidence summary,
  and a clinical reviewer decides what happens next.
- **The disclaimer is present** in the output.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Run refused or falls back to the community tier | No trial running, or the trial has expired | `tokn license trial` (once per machine), then `tokn license features` to confirm |
| `tokn license trial` refuses to start | One trial per machine, already used | Keep using the active trial. After it expires TOKN falls back to Community, which cannot run domain modes. |
| `unknown flag` on `agent-run` | Older TOKN build | Upgrade to v0.3.57 or newer and check with `tokn agent-run --help-all` |
| Run ends with `max steps` before the hooks | Step budget too small | Raise `--max-steps` (for example 16) and rerun |
| `check_inputs.py` reports missing fields | An edited input file | Restore `inputs/` from this folder and rerun |
| Model call fails at start | Missing `NOSPACE_MODEL_PROVIDER` or key | See step 4 and [SETUP.md](../../SETUP.md) |
