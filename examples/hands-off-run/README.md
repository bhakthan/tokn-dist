# Example: Hands-Off Run to a Verified Finish

> "Write the spec, set the limits, walk away, and check the result yourself."

This example runs one hard-ish coding task unattended. You write the spec and the acceptance test.
The agent writes the code, runs the tests, and stops when they pass or when a limit is reached. You
stay at oversight: you set the budget and stop conditions, watch progress, and verify the finish
with a checker that does not trust the agent's own report.

The task is a small arithmetic expression evaluator in Python with precedence, right-associative
power, and error cases. It is synthetic and small enough to finish in one session.

| Capability | How this example uses it | Flag or command |
|---|---|---|
| Autonomous run from a prompt file | Agent reads the spec and writes the code | `tokn agent-run --prompt-file` |
| Budgets and limits | Cap steps and token spend | `--max-steps`, `--token-budget`, `--step-timeout` |
| Verify after each edit | Run the acceptance test after every change | `--verify-after-edit --verify-cmd` |
| Stuck and stale-plan detection | Notice when the agent is looping | `--stuck-threshold`, `--plan-stale-steps` |
| No prompts during the run | Approvals do not stop the run | `--no-confirm --headless` |
| Machine-readable result | A checker reads the outcome | `--output-format json` |
| Checkpoints and resume | Continue after an interruption | `--resume` |
| Readable transcript | Keep a human-readable record | `--export markdown` |
| Optional structured predictions | Ask the agent to state expected outcomes | `--predict`, `--predict-level` |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The flags above are in this version | `tokn version` |
| Community tier (the default) | `default` mode runs with the free tier | `tokn license status` |
| Python 3.9 or newer | Runs the acceptance test and the finish checker | `python --version` |
| An LLM provider | The agent loop calls a model | See step 2 and [SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the spec, the files the agent reads, and the tool output
go to the LLM provider you configure. Everything in this folder is synthetic. The example asks you
to copy it into a separate work folder, so the shipped spec and test stay unchanged.

## 1. Set up a work folder

Copy the task into a separate folder. Do not run the agent inside this example folder.

**bash**
```bash
cp -r task hands-off-work
cd hands-off-work
python -m unittest discover -s tests -v   # expect failures: expr.py does not exist yet
```

**PowerShell**
```powershell
Copy-Item -Recurse task hands-off-work
Set-Location hands-off-work
python -m unittest discover -s tests -v   # expect failures: expr.py does not exist yet
Set-Location ..
```

The first test run should fail with an import error. That is the starting state.

## 2. Configure the model (placeholders)

**bash**
```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<your model name>
export ANTHROPIC_API_KEY=<your key>
```

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<your model name>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

## 3. Set the controls for the long run

These are the controls you choose before you walk away.

| Control | Value in this example | What it does |
|---|---|---|
| `--max-steps` | `40` | Hard cap on agent steps |
| `--token-budget` | `400000` | Cap on tokens spent across the run |
| `--step-timeout` | `3m` | Maximum time for one step (Go duration format) |
| `--stuck-threshold` | `3` | Steps with no progress before the stuck cue fires |
| `--plan-stale-steps` | `8` | Steps before a stale plan is flagged |
| `--verify-after-edit` + `--verify-cmd` | the unit test command | Runs the acceptance test after each edit |
| `--no-confirm --headless` | on | No prompts; anything that would prompt is denied |
| `--output-format json` | on | One machine-readable result at the end |

**bash**
```bash
tokn agent-run \
  --prompt-file prompt.md \
  --repo-root ./hands-off-work \
  --mode default \
  --max-steps 40 \
  --token-budget 400000 \
  --step-timeout 3m \
  --stuck-threshold 3 \
  --plan-stale-steps 8 \
  --verify-after-edit \
  --verify-cmd "python -m unittest discover -s tests -v" \
  --no-confirm \
  --headless \
  --output-format json > run-result.json
echo "exit code: $?"
```

**PowerShell**
```powershell
tokn agent-run `
  --prompt-file prompt.md `
  --repo-root .\hands-off-work `
  --mode default `
  --max-steps 40 `
  --token-budget 400000 `
  --step-timeout 3m `
  --stuck-threshold 3 `
  --plan-stale-steps 8 `
  --verify-after-edit `
  --verify-cmd "python -m unittest discover -s tests -v" `
  --no-confirm `
  --headless `
  --output-format json | Out-File -Encoding utf8 run-result.json
"exit code: $LASTEXITCODE"
```

Exit codes with `--headless`: 0 success, 1 task failure, 2 usage error, 3 denied or blocked.

## 4. Watch progress

The agent prints step progress to the terminal. The JSON result is written only at the end, so
for live progress run the same command without `--output-format json`, or start a second terminal
and count the files in the work folder.

**bash**
```bash
ls -la hands-off-work
python -m unittest discover -s hands-off-work/tests -v 2>&1 | tail -n 3
```

**PowerShell**
```powershell
Get-ChildItem hands-off-work
python -m unittest discover -s hands-off-work\tests -v 2>&1 | Select-Object -Last 3
```

## 5. Resume after an interruption

If the run stops early (a closed terminal, a network drop, or the budget cap), resume the same
prompt. It continues from the last checkpoint for that prompt instead of starting over.

**bash**
```bash
tokn agent-run --prompt-file prompt.md --repo-root ./hands-off-work --mode default \
  --max-steps 40 --token-budget 400000 --resume --headless --no-confirm \
  --verify-after-edit --verify-cmd "python -m unittest discover -s tests -v" \
  --output-format json > run-result.json
```

**PowerShell**
```powershell
tokn agent-run --prompt-file prompt.md --repo-root .\hands-off-work --mode default `
  --max-steps 40 --token-budget 400000 --resume --headless --no-confirm `
  --verify-after-edit --verify-cmd "python -m unittest discover -s tests -v" `
  --output-format json | Out-File -Encoding utf8 run-result.json
```

## 6. Verify the finish yourself

Do not trust the agent's own "done" message. Run the acceptance test in the work folder, then the
offline checker in this folder. The checker confirms that the shipped test file is unchanged and that
the run exited 0.

**bash**
```bash
(cd hands-off-work && python -m unittest discover -s tests -v)
python check_finish.py hands-off-work run-result.json
```

**PowerShell**
```powershell
Push-Location hands-off-work; python -m unittest discover -s tests -v; Pop-Location
python check_finish.py hands-off-work run-result.json
```

Expected, not a recorded run: the unit tests report `OK` with 13 tests, and the checker prints
`PASS`. A `FAIL` line names the first problem.

## 7. Optional: a predicted-outcome run

`--predict` asks the agent to state what each step should change before it acts. Use it when you
want a record of expected versus actual outcomes. Predictions add tokens, so keep this off for
budget-sensitive runs.

**bash**
```bash
tokn agent-run --prompt-file prompt.md --repo-root ./hands-off-work --mode default \
  --predict --predict-level strict --max-steps 40 --headless --no-confirm
```

**PowerShell**
```powershell
tokn agent-run --prompt-file prompt.md --repo-root .\hands-off-work --mode default `
  --predict --predict-level strict --max-steps 40 --headless --no-confirm
```

## What to look for

- Step count and token use stay under your caps. If a cap is hit, the run stops and reports it.
- The acceptance test passes in the work folder, and `check_finish.py` prints `PASS`.
- The shipped `task/tests/test_expr.py` is unchanged. The checker compares its hash.
- If the stuck cue appears in the log, the agent was repeating itself. It is worth reading the
  transcript, but a single cue on its own is not a failure.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Exit code 3 | An action would have needed approval | Expected under `--headless`. Review the denied action in the log |
| Run stops at the step cap | Task is harder than the cap | Resume with `--resume` and a larger `--max-steps` |
| `check_finish.py` reports the test file differs | The agent edited the acceptance test | Re-copy `task/tests/test_expr.py` and re-run; treat the run as not verified |
| Tests fail with import errors | `expr.py` is not in the work folder root | Check the agent wrote it to the root, not a subfolder |
| No model response | LLM variables are not set in this shell | Set them again |
