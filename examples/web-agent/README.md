# Example: interactive web agent on a public page

TOKN's webagent mode lets the model drive a real browser one step at a time:
open a page, read it, act, and report. This walkthrough runs it on a small,
read-only public task.

> *Open https://example.com, read the main heading and the link text, and
> report both on one line.*

| Feature | What it does here |
|---|---|
| **`tokn agent-run --mode webagent`** | Runs the browser agent. It uses the five webagent tools (`web_agent_run`, `browser_run_script`, `web_run_self_reflect`, `web_run_save_skill`, `web_run_replay_skill`). |
| **`--webagent-backend`** | Picks the LLM the webagent calls. Set it explicitly. |
| **`--webagent-max-steps`** | Caps browser steps per run. Keeps a stuck run short. |

**How this differs from `webwright`.** Here the model decides each browser
action as the run goes. That is *interactive* mode. The
[webwright example](../webwright/README.md) is the other pattern: the agent
writes one re-runnable Playwright script and you keep the script. Use this
example to explore a page. Use webwright when you want a script you can run
again.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Current `agent-run` webagent flags | `tokn version` |
| Python **3.10+** | Runs the Playwright browser driver | `python --version` |
| Playwright for Python + Chromium | The browser the agent drives | step 1 |
| An LLM provider you can access | The model that chooses each action | step 2 |

**Tier.** Webagent is **Community**. No trial is needed. Check with
`tokn license features`.

> **What leaves your machine.** Your model provider receives the task text and
> the page text the browser reads from `example.com`. Nothing else is sent.

## 1. Preflight: Python, Playwright and Chromium

TOKN does not install these for you. Check each one and install what is
missing.

| Piece | Check | Windows | macOS | Linux (Debian/Ubuntu) |
|---|---|---|---|---|
| Python 3.10+ | `python --version` | `winget install Python.Python.3.12` | `brew install python@3.12` | `sudo apt-get install -y python3 python3-pip` |
| Playwright package | `python -c "import playwright"` | `python -m pip install playwright` | `python -m pip install playwright` | `python -m pip install playwright` |
| Chromium browser | `python -m playwright --version` | `python -m playwright install chromium` | `python -m playwright install chromium` | `python -m playwright install --with-deps chromium` |

`pip install playwright` alone is not enough. The `install chromium` step
downloads the browser. On a Linux server, `--with-deps` also installs the
system libraries Chromium needs.

Windows PowerShell, in order:

```powershell
python -m pip install playwright
python -m playwright install chromium
python -c "import playwright; print('playwright ok')"
```

macOS / Linux, in order:

```bash
python -m pip install playwright
python -m playwright install chromium
python -c "import playwright; print('playwright ok')"
```

Keep the browser cache outside the repository. Playwright stores it in your
user profile by default. Do not set a path inside `tokn-dist`.

## 2. Set the LLM placeholders

Use placeholders in your own shell or in a file outside the repo. Replace each
value with your own. Never paste a real key into a file you might commit.

bash:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

PowerShell:

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

For other providers and their variables, see [SETUP.md](../../SETUP.md).

## 3. Check the licence and the flags

bash or PowerShell (same commands):

```bash
tokn license features
tokn agent-run --help
```

In the `agent-run --help` output, confirm `--mode`, `--webagent-backend`
and `--webagent-max-steps`. These are the flags the commands below use.

## 4. Run the webagent

bash:

```bash
tokn agent-run --quiet --mode webagent --webagent-backend anthropic --webagent-max-steps 15 \
  "Open https://example.com. Report the main heading text and the text of the first link on one line, formatted as: HEADING = <text> | LINK = <text>. Do not submit forms or click anything that changes state."
```

PowerShell:

```powershell
tokn agent-run --quiet --mode webagent --webagent-backend anthropic --webagent-max-steps 15 `
  "Open https://example.com. Report the main heading text and the text of the first link on one line, formatted as: HEADING = <text> | LINK = <text>. Do not submit forms or click anything that changes state."
```

Expected, not a recorded run: a single final line in the form
`HEADING = Example Domain | LINK = ...`. The link text on the live page may
differ, and the run takes a few browser steps.

Run output stays local to the directory you ran it from.

## 5. Check the result

- The final line has the `HEADING = ... | LINK = ...` shape.
- The heading matches the page you opened. Open https://example.com in a
  browser to confirm.
- The run stopped within 15 steps. If it did not, see Troubleshooting.

## What to look for

- **One step at a time.** The model chooses each action after it sees the page.
  That is the difference from webwright, which fixes the actions in a script
  first.
- **Read-only task.** The prompt forbids forms and state changes. Keep that
  rule for any page you do not own.
- **Step cap.** `--webagent-max-steps` stops a run that cannot finish.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `playwright` import fails | Package not installed in this Python | Repeat the step 1 `pip install` with the same `python` |
| Chromium launch error | `install chromium` was not run, or Linux libraries are missing | Run `python -m playwright install chromium` (Linux: `--with-deps`) |
| The agent stops at the step cap | The page was not reached or the model looped | Raise `--webagent-max-steps` once, then check the model name |
| Provider auth error | A placeholder was not replaced, or the key is for another provider | Re-check step 2. Set `NOSPACE_MODEL_PROVIDER` to match the key. |
| Licence message | Trial ended, running Community | Informational. Webagent is Community. |

Expected, not a recorded run. The exact wording of the answer depends on the
model you choose.
