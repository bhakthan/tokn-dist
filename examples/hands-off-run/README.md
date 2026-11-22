# Example: Hands-Off Run to a Verified Finish

> "Write the spec, set the limits, stay available for approvals, and check the result yourself."

This example runs one bounded coding task with interactive approvals. You write
the spec and acceptance test. The agent proposes code changes and runs tests;
you review each requested mutation and check the finish with a separate checker.

The task is a small arithmetic expression evaluator in Python with precedence, right-associative
power, and error cases. It is synthetic and small enough to finish in one session.

| Capability | How this example uses it | Flag or command |
|---|---|---|
| Bounded run from a prompt file | Agent reads the spec and proposes code changes | `tokn agent-run --prompt-file` |
| Budgets and limits | Cap steps and token spend | `--max-steps`, `--token-budget`, `--step-timeout` |
| Verify after each edit | Run the acceptance test after every change | `--verify-after-edit --verify-cmd` |
| Stuck and stale-plan detection | Notice when the agent is looping | `--stuck-threshold`, `--plan-stale-steps` |
| Requested approvals | Review file and command mutations interactively | default permission mode |
| Machine-readable result | A checker reads the outcome | `--output-format json` |
| Checkpoints and resume | Continue the last unfinished run | `tokn agent-run -c` |
| Readable transcript | Keep a human-readable record | `--export markdown` |
| Optional structured predictions | Ask the agent to state expected outcomes | `--predict`, `--predict-level` |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The flags above are in this version | `tokn version` |
| Community tier (the default) | `default` mode runs with the free tier | `tokn license status` |
| Python 3.9 or newer | Runs the acceptance test and the finish checker | `python --version` |
| An LLM provider | The agent loop calls a model | See step 2 and [SETUP.md](../../SETUP.md) |

Check advanced options with `tokn agent-run --help-all`. This walkthrough keeps
interactive approvals enabled. `--no-confirm` auto-approves all tool calls; it
is an explicit opt-in only for a fresh throwaway work folder without unrelated
credentials or tools.

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
```

The first test run should fail with an import error. That is the starting state.

## 2. Configure the model (placeholders)

**bash**
```bash
export NOSPACE_MODEL_PROVIDER='anthropic'
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic API key: ' ANTHROPIC_API_KEY; echo
export ANTHROPIC_API_KEY
```

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "YOUR_MODEL_ID"
# Load the provider secret from a trusted secret store/session.
```

## 3. Set the controls for the long run

These are the controls you choose before the run. Stay available to review
approval requests.

| Control | Value in this example | What it does |
|---|---|---|
| `--max-steps` | `40` | Hard cap on agent steps |
| `--token-budget` | `400000` | Cap on tokens spent across the run |
| `--step-timeout` | `3m` | Maximum time for one step (Go duration format) |
| `--stuck-threshold` | `3` | Steps with no progress before the stuck cue fires |
| `--plan-stale-steps` | `8` | Steps before a stale plan is flagged |
| `--verify-after-edit` + `--verify-cmd` | the unit test command | Runs the acceptance test after each edit |
| Permission mode | default | Ask before edits or mutating commands |
| `--output-format json` | on | One machine-readable result at the end |

**bash**
```bash
tokn agent-run \
  --prompt-file prompt.md \
  --repo-root . \
  --mode default \
  --max-steps 40 \
  --token-budget 400000 \
  --step-timeout 3m \
  --stuck-threshold 3 \
  --plan-stale-steps 8 \
  --verify-after-edit \
  --verify-cmd "python -m unittest discover -s tests -v" \
  --permission-mode default \
  --output-format json > run-result.json
echo "exit code: $?"
```

**PowerShell**
```powershell
tokn agent-run `
  --prompt-file prompt.md `
  --repo-root . `
  --mode default `
  --max-steps 40 `
  --token-budget 400000 `
  --step-timeout 3m `
  --stuck-threshold 3 `
  --plan-stale-steps 8 `
  --verify-after-edit `
  --verify-cmd "python -m unittest discover -s tests -v" `
  --permission-mode default `
  --output-format json | Out-File -Encoding utf8 run-result.json
"exit code: $LASTEXITCODE"
```

## 4. Watch progress

The agent prints step progress to the terminal. The JSON result is written only at the end, so
for live progress run the same command without `--output-format json`, or start a second terminal
and count the files in the work folder.

**bash**
```bash
ls -la .
python -m unittest discover -s tests -v 2>&1 | tail -n 3
```

**PowerShell**
```powershell
Get-ChildItem .
python -m unittest discover -s tests -v 2>&1 | Select-Object -Last 3
```

## 5. Resume after an interruption

If the run stops early and leaves an unfinished checkpoint, continue it with
`tokn agent-run -c`. This required continuation fails when no unfinished
checkpoint exists; it is not transcript browsing. Reapply the mode, permissions,
verification command and limits shown below.

**bash**
```bash
tokn agent-run --repo-root . --mode default -c \
  --max-steps 40 --token-budget 400000 --permission-mode default \
  --verify-after-edit --verify-cmd "python -m unittest discover -s tests -v" \
  --output-format json > run-result.json
```

**PowerShell**
```powershell
tokn agent-run --repo-root . --mode default -c `
  --max-steps 40 --token-budget 400000 --permission-mode default `
  --verify-after-edit --verify-cmd "python -m unittest discover -s tests -v" `
  --output-format json | Out-File -Encoding utf8 run-result.json
```

## 6. Verify the finish yourself

Do not trust the agent's own "done" message. Run the acceptance test in the work folder, then the
offline checker in this folder. The checker confirms that the shipped test file is unchanged and that
the run exited 0.

**bash**
```bash
python -m unittest discover -s tests -v
python ../check_finish.py . run-result.json
```

**PowerShell**
```powershell
python -m unittest discover -s tests -v
python ..\check_finish.py . run-result.json
```

Expected, not a recorded run: the unit tests report `OK` with 13 tests, and the checker prints
`PASS`. A `FAIL` line names the first problem.

## 7. Optional: a predicted-outcome run

`--predict` asks the agent to state what each step should change before it acts. Use it when you
want a record of expected versus actual outcomes. Predictions add tokens, so keep this off for
budget-sensitive runs.

**bash**
```bash
tokn agent-run --prompt-file prompt.md --repo-root . --mode default \
  --predict --predict-level strict --max-steps 40
```

**PowerShell**
```powershell
tokn agent-run --prompt-file prompt.md --repo-root . --mode default `
  --predict --predict-level strict --max-steps 40
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
| Approval request appears | A write or mutating command needs review | Inspect the action before approving |
| Run stops at the step cap | Task is harder than the cap | Continue the unfinished checkpoint with `tokn agent-run -c` and a larger `--max-steps` |
| `check_finish.py` reports the test file differs | The agent edited the acceptance test | Re-copy `task/tests/test_expr.py` and re-run; treat the run as not verified |
| Tests fail with import errors | `expr.py` is not in the work folder root | Check the agent wrote it to the root, not a subfolder |
| No model response | LLM variables are not set in this shell | Set them again |
