# Example: Permission, Ask-or-Act, and Stuck Signals in a Run

> "Stop before a risky step when the answer matters, notice when the agent is going in circles, and fall back to a safer posture."

This example explains four behaviours that govern how much an agent does on its own. Two of them
you can see and tune from the command line. The other two live inside the agent and are only
visible through their effects. Most of what proves these behaviours is an offline Go test suite in
the source repository, which you cannot run from the released binary. This walkthrough shows what
you can check with the released binary, with no model call, and then an optional short model step.

| Frame | What it does | How you see it with the released binary |
|---|---|---|
| Permission grants | Each tool approval is recorded, and a grant can expire | `--no-confirm` auto-approves; `--headless` denies any action that would prompt (exit code 3) |
| Ask-or-act (value of information) | Asks the human only when the answer is worth the interruption | Internal. You see it as a question versus an action. No flag |
| Posture ladder | plan, default, accept_edits, autopilot; a stuck signal moves toward plan | Internal to the host approval flow. No `agent-run` flag |
| Stuck detection | Counts steps with no progress and offers a help cue | `--stuck-threshold` (default 3, 0 disables) and `--plan-stale-steps` (default 6, 0 disables) |

## What this example does and does not prove

The offline proof in the source repository is a set of Go tests, one per frame, that drive the
decision functions directly. The released `tokn` binary does not expose a command that runs those
tests. So this walkthrough does two things:

1. **Offline (no model, no network):** confirm the version and the flags that control each frame,
   and read the exit-code contract that governs headless runs.
2. **Optional model step:** run one short task with the stuck cue made sensitive and headless
   mode on, then read the outcome.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The flags below are in this version | `tokn version` |
| Community tier (the default) | Steps 1 and 3 use `default` mode, which the free tier includes | `tokn license status` |
| An LLM provider (step 3 only) | The agent loop calls a model | See step 3 |
| Nothing else for steps 1 and 2 | Steps 1 and 2 do not call a model | n/a |

**What leaves your machine:** nothing in steps 1 and 2. In step 3, the prompt, the files the agent
reads, and tool results go to the LLM provider you configure. Use only the synthetic folder this
example creates.

## 1. Confirm the version and the frame controls (offline)

Run these from any folder.

**bash**
```bash
tokn version
tokn agent-run --help | grep -E "stuck-threshold|plan-stale-steps|headless|no-confirm|deny-tool"
```

**PowerShell**
```powershell
tokn version
tokn agent-run --help | Select-String -Pattern "stuck-threshold|plan-stale-steps|headless|no-confirm|deny-tool"
```

Expected, not a recorded run: the help lines show the defaults `3` for stuck threshold and `6`
for plan-stale steps, and describe `--headless` as "never read a terminal, deny any approval that
would prompt".

## 2. Read the headless exit-code contract (offline)

`--headless` gives you a machine-readable outcome. From the help text:

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 1 | Task failure |
| 2 | Usage error |
| 3 | Denied or blocked (an approval would have been needed, or a tool was denied) |

Exit code 3 is the permission frame made visible: the run stopped rather than acting without
approval. Nothing to run here. Keep this table for step 3.

## 3. Optional: a short model run with a stuck cue and headless approvals

Configure the LLM with placeholders. Replace each `<...>` with your own value. See
[SETUP.md](../../SETUP.md) for provider details.

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

Create a small synthetic workspace with one text file, then run the agent against it.

**bash**
```bash
mkdir -p frames-demo
printf "Shopping list: apples, rice, lemons\n" > frames-demo/list.txt
tokn agent-run \
  --prompt "Rename list.txt to groceries.txt, then add a line 'eggs' to it. Do not delete anything." \
  --repo-root ./frames-demo \
  --mode default \
  --stuck-threshold 2 \
  --plan-stale-steps 3 \
  --max-steps 12 \
  --headless \
  --deny-tool run_command \
  --output-format json > frames-demo-result.json
echo "exit code: $?"
```

**PowerShell**
```powershell
New-Item -ItemType Directory -Force -Path frames-demo | Out-Null
Set-Content -Path frames-demo\list.txt -Value "Shopping list: apples, rice, lemons"
tokn agent-run `
  --prompt "Rename list.txt to groceries.txt, then add a line 'eggs' to it. Do not delete anything." `
  --repo-root .\frames-demo `
  --mode default `
  --stuck-threshold 2 `
  --plan-stale-steps 3 `
  --max-steps 12 `
  --headless `
  --deny-tool run_command `
  --output-format json | Out-File -Encoding utf8 frames-demo-result.json
"exit code: $LASTEXITCODE"
```

`--deny-tool run_command` is an example name taken from the flag's help text. If your mode exposes
a different shell tool name, use that name instead. Denying a tool that the task needs should make
the run stop with exit code 3 rather than act.

## What to look for

- The JSON result (`frames-demo-result.json`) has the fields `status`, `result`, `exit_code`,
  `steps`, `usage`, and `errors`. Read `exit_code` first.
- Expected, not a recorded run: with the shell tool denied and the rename done through the file
  tools, the run can finish with exit 0. If the task needs the shell tool, expect exit 3 and an
  entry in `errors` that names the denial.
- A low `--stuck-threshold` (2 here) makes the stuck cue fire sooner. A stuck cue may appear in the
  log on stderr. Its exact wording can change between versions, so search for "stuck" rather than
  matching a fixed phrase.
- Ask-or-act decisions are not logged as flags. If the agent stops to ask you something in an
  interactive run, that is the value-of-information gate at work. In `--headless` mode the same
  decision becomes a denial instead of a question.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `tokn: command not found` | TOKN is not on your PATH | Reinstall from the release page, or add its folder to PATH |
| Exit code 2 | A flag is misspelled or a value is missing | Re-run `tokn agent-run --help` and copy the flag names exactly |
| Exit code 3 on step 3 when you expected success | An approval was needed and denied in headless mode | Expected behaviour. To allow the action, remove the matching `--deny-tool` entry and review the action first |
| No model response | The LLM variables are not set in this shell | Set them again (they do not persist between shells) |
| `frames-demo` already exists | You ran step 3 before | Delete the folder and re-create it, or pick a new name |
