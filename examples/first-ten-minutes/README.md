# Example: First ten minutes

> "I just installed TOKN. What do I run first, and what should I see?"

A free-tier walkthrough in about ten minutes. You check the install, confirm your license is Community, point TOKN at a model, run one agent task on a tiny folder, look around the REPL, and run an offline governed judgment that needs no API key.

| Capability | Command | Needs a model? |
|---|---|---|
| Install check | `tokn version` | No |
| License check | `tokn license status` | No |
| First agent task | `tokn agent-run` | Yes |
| Interactive REPL | `tokn agent-repl` | Yes (to chat) |
| Offline judgment | `tokn judgments example` / `evaluate` | No (rules provider, `--air-gap`) |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Matches the commands in this walkthrough | `tokn version` |
| Community tier | Everything here runs on the free tier. No trial needed | `tokn license status` shows Community |
| A model provider (steps 3–4 only) | `agent-run` and the REPL chat need a model | [SETUP.md](../../SETUP.md) |

Tier: **Community**. Domain modes need `tokn license trial` (14 days). This walkthrough does not use them.

## What leaves your machine

- Steps 1–2 are local. Nothing is sent.
- Step 4 sends your prompt and the files the agent reads to the model provider you configured. Use a folder with no secrets, as in the example below.
- Step 6 runs with `--air-gap`. The rules provider makes no external call.

## Steps

### 1. Check the install

**bash**
```bash
tokn version
```

**PowerShell**
```powershell
tokn version
```

You should see a version of v0.3.57 or later, the build date, your OS and architecture, and `variant: public` (the distribution build). If the command is not found, see the Troubleshooting table.

### 2. Confirm the license tier

**bash**
```bash
tokn license status
```

**PowerShell**
```powershell
tokn license status
```

Expected: the tier is **Community**. You do not need a trial for this walkthrough. Expected output, not a recorded run.

### 3. Configure a provider (placeholders)

Set the three variables for the provider you use. The values below are placeholders. Replace them with your own. For other providers and the full list, see [SETUP.md](../../SETUP.md).

**bash**
```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Do not paste a real key into a file you might commit.

### 4. Run your first agent task on a tiny folder

Create a folder with one file to work on:

**bash**
```bash
mkdir -p ~/first-run
printf "# Notes\n\nTODO: say hello.\n" > ~/first-run/NOTES.md
tokn agent-run --repo-root ~/first-run --prompt "Read NOTES.md and summarise what it asks for. Do not change any files."
```

**PowerShell**
```powershell
New-Item -ItemType Directory -Force $HOME\first-run | Out-Null
Set-Content -Encoding ascii $HOME\first-run\NOTES.md "# Notes`n`nTODO: say hello."
tokn agent-run --repo-root $HOME\first-run --prompt "Read NOTES.md and summarise what it asks for. Do not change any files."
```

Expected: a short summary that mentions the TODO. This is expected, not a recorded run. The `--prompt` text is the only instruction the agent gets.

### 5. Look around the REPL

**bash**
```bash
tokn agent-repl --repo-root ~/first-run
```

**PowerShell**
```powershell
tokn agent-repl --repo-root $HOME\first-run
```

Try these inside the REPL:

```
/help
/learn community
```

- `/help` lists the slash commands. Type `??` for a quick version.
- `/learn community` shows the free-tier lesson.
- Type `/exit` to leave.

### 6. Run an offline governed judgment (no API key)

This uses the `rules` provider and the sample requests in the distribution repo. The sample files and the full explanation live in the judgments section of [examples/README.md](../README.md). Here are the commands in short form.

Run these from a folder you own. The commands write `bundle.json` into it.

**bash**
```bash
tokn judgments example > bundle.json
tokn judgments evaluate --bundle bundle.json --file path/to/tokn-dist/examples/judgments/request-clean.json --mode advisory --air-gap
tokn judgments evaluate --bundle bundle.json --file path/to/tokn-dist/examples/judgments/request-errors.json --mode advisory --air-gap
```

**PowerShell** (Windows PowerShell 5.1 writes UTF-16 with `>`, so pipe through `Set-Content -Encoding ascii`)
```powershell
tokn judgments example | Set-Content -Encoding ascii bundle.json
tokn judgments evaluate --bundle bundle.json --file path\to\tokn-dist\examples\judgments\request-clean.json --mode advisory --air-gap
tokn judgments evaluate --bundle bundle.json --file path\to\tokn-dist\examples\judgments\request-errors.json --mode advisory --air-gap
```

Expected, not a recorded run: the clean request returns `continue`, and the error request returns `revise`. Both commands exit with code `0`.

## What to look for

- `tokn version` reports v0.3.57 or later, and the variant is `public`.
- `tokn license status` reports Community.
- `agent-run` gives a summary of `NOTES.md` and changes nothing in the folder.
- The REPL shows `/help` and the `/learn community` lesson.
- The two judgments differ only in `decision.action`. That is the point of the example.

## Where to go next

Pick the next example by tier:

| Tier | Example | What it covers |
|---|---|---|
| Community | [codebase-graph](../codebase-graph/README.md) | Blast radius over a Go call graph with `/codebase` |
| Community | [examples index](../README.md) | Judgments and other walkthroughs |
| Trial (`tokn license trial`) | [grid-screening](../grid-screening/README.md) | Domain decision models; makes paid model calls |
| Trial | [session-review](../session-review/README.md) | Reviewing an agent session |

For the full install, see [GETTING_STARTED.md](../../GETTING_STARTED.md). For provider details, see [SETUP.md](../../SETUP.md).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `tokn: command not found` | Binary not on PATH | Add the folder that holds `tokn` (or `tokn.exe`) to PATH, then open a new shell |
| `tokn version` is older than v0.3.57 | Old binary | Upgrade. See [GETTING_STARTED.md](../../GETTING_STARTED.md) |
| Banner says the trial has ended | Expected on Community | Harmless for this walkthrough |
| `agent-run` fails with a provider or key error | Provider variables missing or wrong | Re-check step 3 and [SETUP.md](../../SETUP.md) |
| `bundle.json` is unreadable in Windows PowerShell 5.1 | `>` wrote UTF-16 | Use `Set-Content -Encoding ascii` as shown in step 6 |
| `evaluate` cannot find the request file | Relative path is wrong | Use the full path to `examples\judgments\request-*.json` in your clone |
