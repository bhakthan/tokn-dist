# CLI session lab

Learn the difference between help, an interactive session, a one-shot request,
checkpoint continuation, and transcript browsing. The changelog is fictional;
the offline path does not call a model.

## What you'll learn

- Discover available session options without configuring a provider.
- Feed a synthetic text file to a one-shot run.
- Distinguish continuing an unfinished checkpoint from browsing a past session.

## Before you start

| Requirement | Why |
|---|---|
| TOKN on `PATH` | Commands were verified with v0.3.118; check `tokn --help-all` for your build |
| PowerShell or Bash | Creates a scratch copy |
| A configured model | Only for the optional one-shot/interactive path |
| Network or key | Only if the selected provider requires it |

The root `.env.example` is reference-only. Do not source it or save credentials
in the example. All session state and logs must remain in the scratch workspace.

## 1. Offline discovery (no model)

Run this from this example folder.

**PowerShell**

```powershell
$EX = (Get-Location).Path
$WORK = Join-Path $env:TEMP ("cli-session-lab-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $WORK | Out-Null
$env:TOKN_NO_REGISTER = "1"
$env:TOKN_NO_UPDATE_CHECK = "1"
Copy-Item "$EX\changes.txt" $WORK
Set-Location $WORK
tokn agent-run --help-all
tokn agent-repl --help-all
tokn list-sessions --help-all
tokn load-session --help-all
```

**Bash**

```bash
EX="$PWD"
WORK="${TMPDIR:-$HOME}/cli-session-lab-$$"
mkdir "$WORK"
export TOKN_NO_REGISTER=1 TOKN_NO_UPDATE_CHECK=1
cp "$EX/changes.txt" "$WORK/"
cd "$WORK"
tokn agent-run --help-all
tokn agent-repl --help-all
tokn list-sessions --help-all
tokn load-session --help-all
```

`expected/route-table.md` summarizes which route to choose. Help is available
offline and does not prove a provider is configured.

## 2. Optional one-shot summary

Only continue after configuring a provider in your trusted shell. Hosted calls
may be billed; use only the synthetic file. The `.env.example` has blank secret
fields as a reminder, not usable credentials.

**PowerShell**

```powershell
# Set the provider/model in your trusted shell; source the secret from a secure store.
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "YOUR_MODEL_ID"
tokn doctor --provider anthropic
Get-Content -Raw changes.txt | tokn agent-run --mcp-disabled -p "Summarize the supplied synthetic changelog"
```

**Bash**

```bash
export NOSPACE_MODEL_PROVIDER='anthropic'
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic API key: ' ANTHROPIC_API_KEY; echo
export ANTHROPIC_API_KEY
tokn doctor --provider anthropic
tokn agent-run --mcp-disabled -p "Summarize the supplied synthetic changelog" < changes.txt
```

The static doctor checks configuration, not whether a credential or hosted
endpoint will work. Replace the model placeholder with a model your account
supports; never put the key in this file or command history.

For an in-app session, run `tokn agent-repl --mcp-disabled` and type a prompt.
Review each approval request; keep interactive approvals enabled. `/exit`
leaves the REPL. Ctrl+C stops the current run; Ctrl+Q queues a follow-up
prompt. These
interactive controls are **expected behavior**, not part of the offline help
exercise.

## 3. Checkpoint and transcript routes

`tokn agent-run -c` continues the last unfinished compatible checkpoint; it
does not reopen a completed transcript and fails if no such checkpoint exists.
Do not combine it with piped input. `tokn list-sessions` followed by
`tokn load-session SESSION_ID` browses a saved transcript; it does not restart
the run. `--resume` is best-effort, not a substitute for an explicit checkpoint.

Restore any original mode, model, and permission settings explicitly before
trying continuation. This walkthrough does not create or restore a checkpoint.

## What you should see

**Observed** with the local TOKN binary: `agent-run --help-all` exposes the
one-shot, model, checkpoint, and safety options; `agent-repl --help-all` exposes
interactive-session options. No model was called for this observation.

**Expected** from the optional one-shot step: a short summary of the release
changes in `changes.txt`. Wording varies by model; no transcript is recorded
or supplied as an answer key. See `expected/reference-receipt.json` for the
input digest, observed help checks, and limits.

## Troubleshooting

| Symptom | Action |
|---|---|
| Provider/model is missing | Configure one in a trusted shell; see the gallery setup guide |
| Summary has no input | Confirm `changes.txt` exists in the current scratch directory |
| `-c` finds no checkpoint | This exercise creates none; do not treat it as transcript browsing |
| A request asks for tool approval | Review the request; do not bypass approval controls |

## Cleanup

After inspecting the scratch copy, remove only `$WORK`:

```powershell
Set-Location $HOME
Remove-Item -LiteralPath $WORK -Recurse
```

```bash
cd "$HOME"
rm -rf -- "$WORK"
```

## Try it

Use the supplied file to write a question that distinguishes a shipped change
from a planned one. State the expected answer before choosing a model.
