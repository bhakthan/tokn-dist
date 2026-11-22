# Example: code-first browser automation with webwright

Most browser agents act one click at a time, and each step is a new guess.
Webwright takes a different approach. The agent writes **one re-runnable
Playwright script** and treats the script and its logs as the durable result.
The browser is only used while the script is being developed.

This walkthrough runs that pattern on a local fixture you control:

> *Open the local fixture, read the main heading and the first link, save
> both values to `result.json`, and take a screenshot.*

| Feature | What it does here |
|---|---|
| **`tokn agent-run --mode webagent`** | Runs the browser agent. It can use TOKN's five webagent tools. |
| **Code-first artifact** | The agent saves a single `final_script.py` plus `trace.jsonl` and `screenshots/` under `.tokn/web-runs/<id>/`. |
| **Reference script** (`example_domain_check.py`) | The kind of script the agent should produce. You can run it without TOKN. |

The browser contacts only a loopback server serving the synthetic fixture.
The generator sends its prompt to your configured model provider; inspect the
script before running it. Do not substitute arbitrary or unauthorized targets.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Minimum version for this walkthrough's webagent flags | `tokn version` |
| Python **3.10+** | Runs Playwright and the reference script | `python --version` |
| Playwright for Python + Chromium | The browser the script drives | see [step 1](#1-preflight-install-python-playwright-and-chromium) |
| An OpenAI API key | The `openai` webagent backend | see [step 3](#3-set-your-model-key) |

**Tier.** Trial or Community. Run `tokn license features` to see what your
install has. If `agent-run` reports a licence error, start a 14-day trial with
`tokn license trial`.

> **What leaves your machine.** The generating model receives the task text.
> Script replay sends no data to a model or public site; it reads the local
> fixture over loopback.

## 1. Preflight: install Python, Playwright and Chromium

TOKN does not install these for you. Check each one, then install what is
missing.

| Piece | Check | Install (Windows) | Install (macOS) | Install (Linux, Debian/Ubuntu) |
|---|---|---|---|---|
| Python 3.10+ | `python --version` | `winget install Python.Python.3.12` | `brew install python@3.12` | `sudo apt-get install -y python3 python3-pip` |
| Playwright package | `python -c "import playwright"` | `pip install playwright` | `pip install playwright` | `pip install playwright` |
| Chromium browser | `python -m playwright --version` | `python -m playwright install chromium` | `python -m playwright install chromium` | `python -m playwright install --with-deps chromium` |

`pip install playwright` alone is not enough. The `install chromium` step
downloads the browser itself. On a Linux server, `--with-deps` also installs the
system libraries Chromium needs.

Windows PowerShell, all three in order:

```powershell
winget install Python.Python.3.12
pip install playwright
python -m playwright install chromium
```

macOS / Linux bash, all three in order (use the Linux line for the browser on Linux):

```bash
brew install python@3.12                 # macOS; on Linux use apt-get, see table
pip install playwright
python -m playwright install chromium    # Linux: python -m playwright install --with-deps chromium
```

Confirm the preflight:

```bash
python -c "from playwright.sync_api import sync_playwright; print('playwright ok')"
```

Make a fresh, uniquely named scratch copy outside the repository. It must
contain `example_domain_check.py`, `task.txt` and `site/fixture.html`. Keep the
printed path; use it for the rest of the walkthrough.

```powershell
$WORK = Join-Path $env:TEMP "tokn-webwright-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path (Join-Path $WORK 'site') | Out-Null
Copy-Item examples\webwright\example_domain_check.py, examples\webwright\task.txt $WORK\
Copy-Item examples\webwright\site\fixture.html (Join-Path $WORK 'site')
Write-Output $WORK
```

For macOS / Linux bash, from the `tokn-dist` root:

```bash
WORK="$HOME/tokn-webwright-$(date +%Y%m%d%H%M%S)-$$"
mkdir -p "$WORK/site"
cp examples/webwright/example_domain_check.py examples/webwright/task.txt "$WORK/"
cp examples/webwright/site/fixture.html "$WORK/site/"
printf 'Work folder: %s\n' "$WORK"
```

In another terminal, serve the fixture directory from that scratch copy:

```powershell
Set-Location 'PASTE_THE_PRINTED_WORK_PATH\site'
python -m http.server 8000 --bind 127.0.0.1
```

On macOS / Linux, use `cd /paste/the/printed/work/path/site` before starting
the same server command.

Keep the server running during the replay steps; stop it with Ctrl+C afterward.

## 2. Try the reference script

This deterministic replay does not use TOKN or a model. Run it from the fresh
scratch copy, not from the source checkout.

bash or PowerShell:

```bash
cd "$WORK"
python example_domain_check.py
```

Expected output is a small JSON object:

```json
{
  "heading": "Local Webwright Fixture",
  "first_link": "Read-only details"
}
```

The script writes `out/result.json`, `out/page.png` and `out/run.log` inside
the scratch copy.

## 3. Set your model key

The `openai` webagent backend reads `OPENAI_API_KEY`. Replace the placeholder
with your own key, which should never be committed.

bash:

```bash
read -rs -p 'OpenAI API key: ' OPENAI_API_KEY; echo; export OPENAI_API_KEY
```

PowerShell:

```powershell
# Set OPENAI_API_KEY from a trusted secret store or your protected shell session.
```

For other providers, see [SETUP.md](../../SETUP.md).

## 4. Run the webwright agent

Run from the fresh scratch copy. The prompt is in `task.txt`.

bash:

```bash
cd "$WORK"
tokn agent-run --mode webagent --permission-mode default --webagent-backend openai \
  --prompt-file task.txt --headless --max-steps 12
```

PowerShell:

```powershell
Set-Location $WORK
tokn agent-run --mode webagent --permission-mode default --webagent-backend openai `
  --prompt-file task.txt --headless --max-steps 12
```

What the flags do:

| Flag | Meaning |
|---|---|
| `--mode webagent` | Use the webagent mode, which exposes the browser tools |
| `--webagent-backend openai` | Use the OpenAI backend for the agent's model calls |
| `--prompt-file task.txt` | Read the task from the file |
| `--headless` | Run the browser without a window |
| Normal approvals | Keep interactive tool approvals enabled while generating the script. |
| `--max-steps 12` | Cap on agent turns |

## 5. Check the result

The agent only generates the script; it does not execute it. Each run gets its
own folder under `.tokn/web-runs/<id>/`. Inspect the script, then explicitly
replay it only if it targets the local fixture:

| File | What to check |
|---|---|
| `final_script.py` | The re-runnable script. It should be one file with a clear flow, not a list of clicks. |
| `final_script_log.txt` | The script's own log. It should show the heading and link read, and no errors on the last run. |
| `screenshots/` | A screenshot of the local fixture after replay. |
| `trace.jsonl` | The record of agent turns, if you want to see how it got there. |

After inspection, replay the artifact by itself. This deterministic browser
step uses Python and Playwright but no model call; model generation and replay
are separate, and only the generation step may incur provider charges:

```bash
python .tokn/web-runs/<id>/final_script.py
```

Replace `<id>` with the folder name. The script should print the same heading and link as the reference script.

## What to look for

- **One script, not a transcript.** The agent should write one file that does
  the whole job. If it only describes clicks, the run did not follow the pattern.
- **The log tells the story.** A failing selector shows up in the log. The
  agent should fix the script and rerun the whole thing, not click around.
- **Honesty about failures.** If the local server is down or a selector breaks,
  the log and the summary should say so. A run should never claim success it
  did not get.
- **Read-only task.** Nothing in this run should submit a form or change state.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `python: command not found` (or `python3`) | Python is not installed or not on `PATH` | Install Python 3.10+ from the table in step 1 |
| `ModuleNotFoundError: No module named 'playwright'` | The Playwright package is not installed | `pip install playwright` |
| `Executable doesn't exist ... chromium` | The browser was not downloaded | `python -m playwright install chromium` |
| Browser fails to start on a Linux server | Missing system libraries | `python -m playwright install --with-deps chromium` |
| `OPENAI_API_KEY` error from `agent-run` | The key is not set in this shell | Set it again (step 3). Keys set in another terminal do not carry over. |
| `tokn: command not found` | The binary is not on `PATH` | Add the folder that contains `tokn` to `PATH` |
| Licence error from `agent-run` | Trial ended and this feature needs a trial | `tokn license trial` |
| Run hits the step cap | The task needed more turns | Raise `--max-steps`, or simplify `task.txt` |
| Local fixture does not load | The loopback server is not running from `site/` | Start `python -m http.server 8000 --bind 127.0.0.1` there and retry |
