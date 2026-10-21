# Example: Dataflow-aware skill composition

> "Produce the build metrics report for this repository."

TOKN loads the skills in a folder and orders them by what each skill consumes and
produces. This example gives it three small skills, two of which chain together
correctly, and a third that asks for an input nothing produces. You check that
TOKN ordered the first two, flagged the third, and still finished the task.

| Capability | What you will see |
|---|---|
| Skill discovery | TOKN finds three skills under `.nospace/skills/` |
| Dataflow ordering | `harvest-metrics` runs before `chart-metrics` because one produces what the other consumes |
| Break detection | `publish-findings` is flagged because `deploy/manifest` is consumed but never produced |
| Non-blocking break | The run still continues and writes `metrics.csv` and `report.md` |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Dataflow ordering and break messages | `tokn version` |
| Tier: Community is expected to be enough | Skill composition and `agent-run` use core and workflow features | `tokn license features` lists `core:*` and `workflow:*` |
| An LLM API key | `agent-run` calls a model | See [SETUP.md](../../SETUP.md) |
| Any folder you can write to | The run creates files in a scratch copy | e.g. `~/tokn-dataflow` |

If `agent-run` reports a license error, run `tokn license trial` once and retry.

## What leaves your machine

- The text of `TASK.md`, the skill descriptions, and anything the model reads from
  the scratch folder are sent to the model provider you configure.
- Nothing else. The example makes no other network calls of its own.

## Steps

### 1. Copy the fixture to a scratch folder

bash:
```bash
cp -r ./fixture ~/tokn-dataflow
cd ~/tokn-dataflow
```

PowerShell:
```powershell
Copy-Item -Recurse .\fixture $HOME\tokn-dataflow
Set-Location $HOME\tokn-dataflow
```

### 2. Configure your model

Use the same placeholders as step 2 of [grid-screening](../grid-screening/README.md).
Replace `<your key>` with your real key.

bash:
```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<model name>
export ANTHROPIC_API_KEY=<your key>
```

PowerShell:
```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<model name>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

### 3. Run the task

Flags were checked against `tokn agent-run --help`. `--log-file` keeps the composition
lines in a file you can search afterwards.

bash:
```bash
tokn agent-run --prompt-file TASK.md --repo-root . --max-steps 8 --no-confirm \
  --log-level verbose --log-file run.log
```

PowerShell:
```powershell
tokn agent-run --prompt-file TASK.md --repo-root . --max-steps 8 --no-confirm `
  --log-level verbose --log-file run.log
```

### 4. Check the composition lines

TOKN writes its composition decisions as `skills.Compose:` lines.

bash:
```bash
grep "skills.Compose" run.log
```

PowerShell:
```powershell
Select-String -Path run.log -Pattern 'skills.Compose'
```

### 5. Check the outputs

bash:
```bash
ls metrics.csv report.md && cat report.md
```

PowerShell:
```powershell
Get-Item metrics.csv, report.md; Get-Content report.md
```

## What to look for

| Check | Expected |
|---|---|
| A. Order | A `skills.Compose: selected N skill(s)` line has `order=[` with `harvest-metrics` before `chart-metrics` |
| B. Break named | A `dataflow-break` line names `"publish-findings"` and `deploy/manifest` |
| C. Run continues | `metrics.csv` and `report.md` exist, so the break did not stop the run |
| D. Regime reason | A `regime=` line with a non-empty reason in parentheses |

Only the break is expected: `publish-findings` should never be run, and the
task says not to publish.

## What to expect

This example has no recorded run yet, so the table above is the expected outcome,
not a measured one. Your model and wording will vary, so check the four items
rather than matching text exactly.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `grep` finds no `skills.Compose` lines | Confirm `--log-level verbose` and `--log-file run.log` were both set; the file is written even when the console is quiet |
| `selected` line shows fewer than 3 skills | Re-run; the triggers in each `SKILL.md` must match the prompt. Check `TASK.md` still contains "build metrics" and "metrics report" |
| No `dataflow-break` line | Check `publish-findings/SKILL.md` still declares `consumes: deploy/manifest` |
| License error on `agent-run` | Run `tokn license trial` once, then `tokn license features` to confirm |
| No model response | Check the three `NOSPACE_*` and key variables from step 2 |
