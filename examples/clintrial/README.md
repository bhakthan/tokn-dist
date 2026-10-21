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

| Hook | What it protects against | Where it lives |
|---|---|---|
| `estimand_completeness` | An analysis that starts before the question is fully specified | `clintrial/hooks.go` |
| `phi_before_model` / `phi_input_screen` | Identifiers reaching the model | `clintrial/hooks.go` |
| `positivity_before_emulate` | An estimate computed where one arm has no overlap | `clintrial/hooks.go` |
| `validation_before_emit` | Evidence emitted before the validation suite runs | `clintrial/hooks.go` |
| `human_in_loop_before_emit` | Evidence emitted without a human decision | `clintrial/hooks.go` |
| `no_silent_artifact` | Output written with no visible record | `clintrial/hooks.go` |
| `calibrated_language` / `decision_support_disclaimer` | Overstated certainty, or output without the disclaimer | `clintrial/hooks.go` |

The example uses tools such as `ct_estimand_check`, `ct_confounder_map`,
`ct_positivity_check`, `ct_propensity_weight`, `ct_evalue`, `ct_negative_control`
and `ct_validate_suite`, which are defined in `clintrial/tools*.go`.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with this example's hook names | `tokn version` |
| **14-day trial** (`tokn license trial`) | `--mode clintrial` is a domain mode. The Community tier grants only `domains:basic`, so the run is refused without a trial. | `tokn license` |
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
tokn license
```

```powershell
tokn license trial
tokn license
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
export NOSPACE_MODEL_NAME=<a Claude model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a Claude model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Keep keys in your shell or `~/.tokn/config/credentials.env`. Never commit a key.

## 5. Run the emulation task

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

```bash
python check_inputs.py result.json
```

```powershell
python check_inputs.py result.json
```

This counts how often each hook name appears in the saved run. It makes no
network calls. A mention is not a pass, so read the sentence around it.

## 7. Expected outcomes

These are the outcomes the hooks and the task are designed to produce, taken
from the source. They are **not** a recorded run.

| Step in `prompt.md` | Expected outcome |
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
| Run refused or falls back to the community tier | No trial running, or the trial has expired | `tokn license trial` (once per machine), then `tokn license` to confirm |
| `tokn license trial` refuses to start | One trial per machine, already used | Keep using the active trial. After it expires TOKN falls back to Community, which cannot run domain modes. |
| `unknown flag` on `agent-run` | Older TOKN build | Upgrade to v0.3.57 or newer and check with `tokn agent-run --help` |
| Run ends with `max steps` before the hooks | Step budget too small | Raise `--max-steps` (for example 16) and rerun |
| `check_inputs.py` reports missing fields | An edited input file | Restore `inputs/` from this folder and rerun |
| Model call fails at start | Missing `NOSPACE_MODEL_PROVIDER` or key | See step 4 and [SETUP.md](../../SETUP.md) |
