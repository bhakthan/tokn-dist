# Example: measure and improve an agent with the Quality Flywheel

This walkthrough runs one small agent evaluation from start to finish, over two
cycles:

> *Give an agent five instruction-following prompts and check each answer with
> a fixed rule. Then change the agent, run the same prompts again, and gate the
> change against the first run.*

It uses the flywheel's core loop: **prepare → infer → grade → compare**.

| Feature | What it does here |
|---|---|
| **Flywheel run** (`tokn flywheel run`) | Runs the dataset through your candidate command, grades every answer, and writes a cycle report. |
| **Deterministic grader** (`expect_contains`) | Passes a case when the answer contains the expected text, ignoring case. No model grades anything. |
| **Baseline gate** (`--baseline`) | Compares cycle 2 with cycle 1. The gate blocks the cycle when the target metric does not improve. |
| **Cycle reports** (`cycle-N.json`) | One file per cycle, which you can keep, diff and compare. |

The dataset is five synthetic prompts in `dataset.json`. Each one checks a
single, unambiguous answer.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Ships `tokn flywheel run` and `--candidate-cmd` | `tokn version` |
| An LLM provider and key | The candidate runs each case through `tokn agent-run` | see [SETUP.md](../../SETUP.md) |
| `python3` (macOS / Linux only) | `candidate.sh` reads the run log with the standard library | `python3 --version` |

Trial and Community tiers both run this example; the flywheel command has no
license gate. If a command refuses to run, start the 14-day trial with
`tokn license trial`. Model calls are billed by your own provider, not by TOKN.

> **What leaves your machine.** Each case's prompt is sent to the provider you
> configure in step 2, and nothing else. The grading is local: the `expect_contains`
> check runs on your machine and sends nothing.

## 1. Open the example folder

macOS / Linux:

```bash
cd examples/quality-flywheel
```

Windows PowerShell:

```powershell
Set-Location examples\quality-flywheel
```

You now have:

```text
quality-flywheel/
  dataset.json      # five cases, each with an input and expect_contains
  candidate.sh      # the candidate for macOS / Linux
  candidate.ps1     # the candidate for Windows PowerShell
  .gitignore        # keeps the scratch folder and cycle reports out of git
```

The candidate creates a `scratch/` folder for each run of `agent-run`.
Nothing is written outside this folder.

## 2. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
export TOKN_BIN=tokn            # or the full path to your tokn binary
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
$env:TOKN_BIN               = "C:\path\to\tokn.exe"   # or just tokn if it is on PATH
```

Use your shell or `~/.tokn/config/credentials.env` for keys. Never commit a key.

Check that TOKN can see the provider. This makes no model call:

```bash
tokn agent-run --help
```

## 3. Preview the plan (no model call)

Run the flywheel without `--yes`. It prints the plan and waits for you to
confirm. Answer `n` to stop before any inference.

macOS / Linux:

```bash
tokn flywheel run --dataset dataset.json --candidate-cmd "bash candidate.sh" --out-dir cycles --cycle 1
```

Windows PowerShell:

```powershell
tokn flywheel run --dataset dataset.json --candidate-cmd "powershell -NoProfile -ExecutionPolicy Bypass -File candidate.ps1" --out-dir cycles --cycle 1
```

The plan lists the five cases, the grader and the output directory.

## 4. Run cycle 1 (the baseline)

macOS / Linux:

```bash
tokn flywheel run --dataset dataset.json --candidate-cmd "bash candidate.sh" --out-dir cycles --cycle 1 --yes
```

Windows PowerShell:

```powershell
tokn flywheel run --dataset dataset.json --candidate-cmd "powershell -NoProfile -ExecutionPolicy Bypass -File candidate.ps1" --out-dir cycles --cycle 1 --yes
```

With no `--baseline`, cycle 1 becomes the reference. It writes `cycles/cycle-1.json`.
Expect a few seconds per case.

## 5. Run cycle 2 against the baseline

Change something you want to test. For example, edit the `NOSPACE_MODEL_NAME`
to a different model, or change the wording of a candidate. Then run:

macOS / Linux:

```bash
tokn flywheel run --dataset dataset.json --candidate-cmd "bash candidate.sh" --out-dir cycles --cycle 2 --baseline cycles/cycle-1.json --target-metric pass_rate --yes
```

Windows PowerShell:

```powershell
tokn flywheel run --dataset dataset.json --candidate-cmd "powershell -NoProfile -ExecutionPolicy Bypass -File candidate.ps1" --out-dir cycles --cycle 2 --baseline cycles/cycle-1.json --target-metric pass_rate --yes
```

The gate compares the `pass_rate` in cycle 2 with cycle 1. If it does not
improve, the command exits with `flywheel gate BLOCKED` and writes the report
anyway. That is the correct result when the agent already passes every case,
so a blocked gate here is not a bug.

## 6. Read the result

Each cycle writes `cycles/cycle-<N>.json`. Open it and look for:

| Field | What it tells you |
|---|---|
| `pass_rate` | The fraction of cases that passed. `1.0` means all five passed. |
| Per-case results | Which case failed, with the output it produced and the expected text |
| `gate` | Whether the cycle was accepted or blocked, and why |

To see a failure, make the candidate weaker on purpose, for example by setting
`NOSPACE_MODEL_NAME` to a small model, and rerun cycle 2. The report will then
show which cases the model got wrong.

### What one of our runs looked like

Our internal run used a fast frontier model. Cycle 1 passed 5/5 cases and cycle 2
was blocked because nothing changed. Your numbers will differ.

## What to look for

- **The gate is strict on purpose.** A cycle that passes the same cases is
  blocked. Improvements must show up in the metric.
- **The grader is not a model.** Each case passes or fails on the text. If you
  change a case's expected text, the grade changes with it.
- **Failures are data.** A failed case is an input for the next cycle, not a
  reason to hide the report.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Every case fails with `candidate: NOSPACE_MODEL_PROVIDER is not set` | Set the variables in step 2 in the same shell that runs `tokn flywheel run` |
| `candidate: tokn not found` | Set `TOKN_BIN` to the full path of your tokn binary |
| `candidate: no assistant answer` | The provider call failed. Check the key and model name, then read `scratch/agent.err` |
| `python3 not found` (macOS / Linux) | Install Python 3 or use the PowerShell candidate on Windows |
| `flywheel gate BLOCKED` in cycle 2 | Expected when the metric did not improve. Read `gate` in `cycle-2.json` for the reason |
| `unknown flag` | Upgrade to v0.3.57 or newer, then run `tokn flywheel run --help` |
