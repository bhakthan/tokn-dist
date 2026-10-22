# Example: Agent Loop Essentials

> "Add a --shout flag to the greeting CLI, keep greet() unchanged, and prove it with a test."

A plain agent run works, but it can drift on a task like this. It forgets the goal after many tool calls, edits files it did not mean to touch, and gives you no record of how predictable the run was. This walkthrough uses four loop features on one small Python task so you can see each one in the output.

| Capability | What you see |
|---|---|
| Task Anchor | The goal, acceptance criteria, and live plan are shown on every turn. The agent keeps them current with the `update_plan` tool. |
| `repo_map` tool | The agent asks for a compact map of the repo, then the callers of a symbol, before it edits. |
| Tool-explore budget | Caps how many read-only calls a change task may make before the agent is told to converge on an edit. |
| Predictable Results (`--predict`) | Applies a determinism level, checks an outcome contract, and saves a Predictability Report under `.nospace/predict/`. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The loop flags and tools shown here ship in this version. | `tokn version` |
| Community tier (no trial) | Default mode and these loop features are free. No `tokn license trial` step is needed. | `tokn agent-run --help` lists `--predict` and `--no-task-anchor` |
| An LLM provider | TOKN calls a model for every turn of the loop. | See [../../SETUP.md](../../SETUP.md) |
| Python 3.9+ (optional) | Only for the offline report checker. The fixture code is not run in this walkthrough. | `python --version` |

**What leaves your machine:** the prompt in `task.md`, the files TOKN reads from the scratch copy of `greeting-app/`, and tool results. All of it goes to the LLM provider you configure. All data in this example is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state into the repo it works on. Run it on a copy.

```bash
cp -r examples/agent-loop-essentials ~/loop-run
cd ~/loop-run
```

```powershell
Copy-Item -Recurse examples\agent-loop-essentials $HOME\loop-run
Set-Location $HOME\loop-run
```

After this step the folder contains `greeting-app/`, `task.md`, `contract.json`, and `check_predict_report.py`.

## 2. Configure the LLM

Replace the placeholders with your own values. See [../../SETUP.md](../../SETUP.md) for other providers.

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

## 3. Read the task and the contract before the run

Open `task.md` and `contract.json`. The contract is the outcome check. It lists what the final answer must mention, which files must change, the expected status, and the step budget.

The contract fields are:

- `acceptance`: substrings the final answer must contain.
- `expect_files_changed`: repo-relative paths the run should change.
- `expect_status`: the status the run should end with.
- `max_steps`: the step budget the run should stay within.

## 4. Run the loop with all four features on

```bash
tokn agent-run --repo-root greeting-app --prompt-file task.md --max-steps 12 --no-confirm --predict --predict-level strict --predict-contract contract.json --tool-explore-budget 4
```

```powershell
tokn agent-run --repo-root greeting-app --prompt-file task.md --max-steps 12 --no-confirm --predict --predict-level strict --predict-contract contract.json --tool-explore-budget 4
```

What each flag does:

| Flag | Effect |
|---|---|
| `--repo-root greeting-app` | Limits file access and commands to the fixture repo. |
| `--prompt-file task.md` | Reads the task from a file, which avoids shell quoting problems. |
| `--max-steps 12` | Caps the number of turns. Matches `max_steps` in the contract. |
| `--no-confirm` | Approves tool calls without prompting. Use it only on the scratch copy. |
| `--predict --predict-level strict` | Uses temperature 0 and writes a Predictability Report at the end. |
| `--predict-contract contract.json` | Checks the run against the contract. |
| `--tool-explore-budget 4` | Sends the "converge" advisory after 4 read-only calls on a change task. The default is 8. |

The Task Anchor is on by default, so you do not pass a flag for it. The prompt asks the agent to call `repo_map` for the callers of `greet` before it edits.

## 5. Read the Predictability Report

```bash
python check_predict_report.py greeting-app
```

```powershell
python check_predict_report.py greeting-app
```

The script reads the newest `report-*.json` under `greeting-app/.nospace/predict/` and prints its top-level fields. It is offline and uses only the standard library.

## 6. Optional: compare with the Task Anchor off

Run the same task again with the anchor disabled. The flag is `--no-task-anchor`. The environment variable `TOKN_NO_TASK_ANCHOR` does the same thing.

```bash
tokn agent-run --repo-root greeting-app --prompt-file task.md --max-steps 12 --no-confirm --no-task-anchor
```

```powershell
tokn agent-run --repo-root greeting-app --prompt-file task.md --max-steps 12 --no-confirm --no-task-anchor
```

Two runs will not produce identical text, even with `--predict-level strict`. Compare the plan the agent keeps and whether it still reports `--shout` at the end.

## 7. Clean up

Delete the scratch folder when you are done. The original `examples/agent-loop-essentials/` is unchanged because you only ran TOKN on the copy.

## What to look for

Expected, not a recorded run:

- The Task Anchor block shows the goal, the acceptance text (`--shout`), and a live plan. The plan is updated through `update_plan`.
- The agent calls `repo_map` with `symbol` set to `greet` and `direction` set to `callers` before it edits `app/cli.py`.
- After about four read-only calls, the converge advisory appears.
- `check_predict_report.py` prints a report with a determinism level, the run status, a confidence value, and a contract result.
- `app/greet.py` keeps the same `greet(name)` signature. Only `app/cli.py` and `tests/test_greet.py` should change, which matches `expect_files_changed`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `unknown flag: --predict` or `--no-task-anchor` | Your TOKN is older than v0.3.57. Run `tokn version`, then update. |
| The checker says no report was found | The run must finish for the report to be written. Check that `--predict` was on, and that the report sits under `greeting-app/.nospace/predict/`. |
| The model asks for a provider you have not set | Set `NOSPACE_MODEL_PROVIDER` and the matching key, as in step 2. |
| The agent edits `greet()` | The task forbids it. Rerun with a stricter prompt, and check that `greet` is not in `expect_files_changed`. |
| The run stops at the step budget | Raise `--max-steps` and the contract's `max_steps` together. |
