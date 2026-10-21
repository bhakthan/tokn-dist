# Example: stress-test a design proposal with frontier critique

This walkthrough runs one design review, from start to finish:

> *Critique this helpdesk triage bot proposal. Find what breaks, revise it, and
> keep every disagreement on the record.*

It uses critique mode (`--mode critique`). Eight roles each attack the same
proposal from a different angle. A synthesizer merges their critiques into one
revised proposal. Disagreements are recorded as dissent rather than averaged
away. The input is a synthetic proposal with four planted flaws, so you can see
whether the roles find them.

| Feature | What it does here |
|---|---|
| **Critique mode** (`--mode critique`) | Runs eight critique roles over the artifact, then synthesizes a revision. |
| **Eight roles** | adversary, synthesizer, pragmatist, visionary, domain expert, user advocate, contrarian, integrator. |
| **Convergence** | Rounds stop once the roles' positions agree across rounds. The result reports how confident it is. |
| **Documented dissent** | Minority positions are kept in the output, not dropped. |
| **Optional council** (`--council-members`) | Adds more than one model. Each provider takes a role. Not required. |

All data in `synthetic/` is invented.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with this example's flags | `tokn version` |
| **Trial** licence (premium mode) | Critique is a premium mode. Community does not include `mode:critique`. | `tokn license status` |
| An LLM provider and key | Runs the roles | see [SETUP.md](../../SETUP.md) |
| Python 3 (optional) | Runs the stdlib checker in step 5 | `python --version` |

**Tier:** critique mode needs the 14-day trial. Start it once with
`tokn license trial`.

**Multi-model is optional.** One provider runs all eight roles on that model.
Two or more providers (via `--council-members`) switch to the council path,
where each provider takes one role. You do not need two providers to run this
example.

> **What leaves your machine.** Each model provider you use receives the prompt
> and the proposal file. With a council, every provider you name receives the
> proposal. Starting the trial also sends a one-time anonymous install
> registration (a machine hash, no personal data).

## 1. Set up a scratch folder

Keep runs outside the repo so no result files are committed.

macOS / Linux:

```bash
mkdir -p ~/tokn-critique && cp -r examples/critique/synthetic examples/critique/prompt.md examples/critique/check_results.py ~/tokn-critique/
cd ~/tokn-critique
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-critique | Out-Null
Copy-Item examples\critique\synthetic, examples\critique\prompt.md, examples\critique\check_results.py $HOME\tokn-critique -Recurse
Set-Location $HOME\tokn-critique
```

## 2. Start the trial

```bash
tokn license trial
tokn license status
```

```powershell
tokn license trial
tokn license status
```

## 3. Configure the LLM

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

Keep keys in your shell or `~/.tokn/config/credentials.env`. Never commit one.

## 4. Run the critique

Flags come from `tokn agent-run --help`: `--mode`, `--prompt-file`,
`--repo-root`, `--max-steps`, `--no-confirm`, `--output-format`. Logs go to
stderr, and `--output-format json` writes one final JSON object to stdout.

Single model (the default):

bash:

```bash
tokn agent-run --mode critique --prompt-file prompt.md --repo-root . \
  --max-steps 20 --no-confirm --output-format json > result.json
```

PowerShell:

```powershell
tokn agent-run --mode critique --prompt-file prompt.md --repo-root . `
  --max-steps 20 --no-confirm --output-format json > result.json
```

Optional council (two or more `provider:model` specs; each provider needs its
own credentials, see [SETUP.md](../../SETUP.md)). Replace the placeholders:

```bash
tokn agent-run --mode critique --prompt-file prompt.md --repo-root . \
  --council-members "anthropic:<model-a>,openai:<model-b>" \
  --max-steps 20 --no-confirm --output-format json > result.json
```

```powershell
tokn agent-run --mode critique --prompt-file prompt.md --repo-root . `
  --council-members "anthropic:<model-a>,openai:<model-b>" `
  --max-steps 20 --no-confirm --output-format json > result.json
```

`--no-confirm` auto-approves tool calls. The agent here only needs to read one
file, so this is safe for the example.

## 5. Check the result (optional)

```bash
python check_results.py result.json
```

```powershell
python check_results.py result.json
```

The checker reads only `result.json` and makes no network call. It checks that
the JSON has a `result`, that role names are cited, that dissent and
confidence or convergence are mentioned, and that each planted flaw is raised.
It is a text check. A WARN means "look at the output", not "the run failed".

## 6. What the proposal plants

The proposal has four flaws that a good review should raise:

| Planted flaw | Role most likely to raise it |
|---|---|
| Personal data sent to a hosted model, with no retention rule | Adversary, domain expert, user advocate |
| The classifier is a single point of failure, with no fallback | Integrator, pragmatist |
| The "95% auto-resolved" metric has no method or baseline | Pragmatist, domain expert |
| Escalation to humans is "may", not defined | Integrator, user advocate |

## What to look for

- **All eight roles appear.** Each gives its own critique, not a copy of another.
- **Dissent is kept.** Where roles disagree, the output records both sides.
- **The revision says what changed and why.** Each change traces to a critique.
- **Confidence is stated with a reason.** A high score with no reason is a weak result.
- **Council runs only.** The per-provider view shows which model took which role.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Run refused with a tier or licence message | Community tier (`mode:critique` is not in Community) | Run `tokn license trial`, then `tokn license status`. |
| `--mode critique` not accepted | TOKN older than v0.3.57 | Upgrade, then check `tokn version`. |
| Council run fails for one provider | That provider's key is missing | Set its credentials per [SETUP.md](../../SETUP.md), or drop it from `--council-members`. |
| `result.json` has extra text, or fails to parse | Stdout mixed with other output | Use `--output-format json` and redirect stdout only. |
| Run stops before the final JSON | `--max-steps` reached | Raise `--max-steps` and rerun. |
