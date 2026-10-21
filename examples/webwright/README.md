# Example: code-first browser automation with webwright

Most browser agents act one click at a time, and each step is a new guess.
Webwright takes a different approach. The agent writes **one re-runnable
Playwright script** and treats the script and its logs as the durable result.
The browser is only used while the script is being developed.

This walkthrough runs that pattern on a small, public, read-only task:

> *Open https://example.com, read the main heading and the first link, save
> both values to `result.json`, and take a screenshot.*

| Feature | What it does here |
|---|---|
| **`tokn agent-run --mode webagent`** | Runs the browser agent. It can use TOKN's five webagent tools. |
| **Code-first artifact** | The agent saves a single `final_script.py` plus `trace.jsonl` and `screenshots/` under `.tokn/web-runs/<id>/`. |
| **Reference script** (`example_domain_check.py`) | The kind of script the agent should produce. You can run it without TOKN. |

Only `https://example.com` is contacted. The run is read-only: no forms are
submitted and nothing is clicked that changes state.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Current `agent-run` webagent flags | `tokn version` |
| Python **3.10+** | Runs Playwright and the reference script | `python --version` |
| Playwright for Python + Chromium | The browser the script drives | see [step 1](#1-preflight-install-python-playwright-and-chromium) |
| An OpenAI API key | The `openai` webagent backend | see [step 3](#3-set-your-model-key) |

**Tier.** Trial or Community. Run `tokn license features` to see what your
install has. If `agent-run` reports a licence error, start a 14-day trial with
`tokn license trial`.

> **What leaves your machine.** Your model provider receives the task text and
> the page content the agent reads from `example.com`. Nothing else is sent.
> The reference script (`example_domain_check.py`) makes one request to
> `example.com` and sends nothing to a model.

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

## 2. Try the reference script

This is the artifact you want the agent to end up with. You can run it on its
own to see what it does.

bash or PowerShell (run from the `tokn-dist` root):

```bash
python examples/webwright/example_domain_check.py
```

Expected output is a small JSON object:

```json
{
  "heading": "Example Domain",
  "first_link": "More information..."
}
```

The script writes `out/result.json`, `out/page.png` and `out/run.log` next to
itself. It writes nothing anywhere else.

## 3. Set your model key

The `openai` webagent backend reads `OPENAI_API_KEY`. Replace the placeholder
with your own key, which should never be committed.

bash:

```bash
export OPENAI_API_KEY=<your key>
```

PowerShell:

```powershell
$env:OPENAI_API_KEY = "<your key>"
```

For other providers, see [SETUP.md](../../SETUP.md).

## 4. Run the webwright agent

Run from `examples/webwright`. The prompt is in `task.txt`.

bash:

```bash
cd examples/webwright
tokn agent-run --mode webagent --webagent-backend openai \
  --prompt-file task.txt --headless --no-confirm --max-steps 12
```

PowerShell:

```powershell
Set-Location examples\webwright
tokn agent-run --mode webagent --webagent-backend openai `
  --prompt-file task.txt --headless --no-confirm --max-steps 12
```

What the flags do:

| Flag | Meaning |
|---|---|
| `--mode webagent` | Use the webagent mode, which exposes the browser tools |
| `--webagent-backend openai` | Use the OpenAI backend for the agent's model calls |
| `--prompt-file task.txt` | Read the task from the file |
| `--headless` | Run the browser without a window |
| `--no-confirm` | Skip per-tool approval prompts. Use this only for this read-only task. |
| `--max-steps 12` | Cap on agent turns |

## 5. Check the result

Each run gets its own folder under `.tokn/web-runs/<id>/`. Look in the newest one:

| File | What to check |
|---|---|
| `final_script.py` | The re-runnable script. It should be one file with a clear flow, not a list of clicks. |
| `final_script_log.txt` | The script's own log. It should show the heading and link read, and no errors on the last run. |
| `screenshots/` | At least one screenshot of `example.com`. |
| `trace.jsonl` | The record of agent turns, if you want to see how it got there. |

Then rerun the artifact by itself to prove it is re-runnable:

```bash
python .tokn/web-runs/<id>/final_script.py
```

Replace `<id>` with the folder name. The script should print the same heading
and link as the reference script.

## What to look for

- **One script, not a transcript.** The agent should write one file that does
  the whole job. If it only describes clicks, the run did not follow the pattern.
- **The log tells the story.** A failing selector shows up in the log. The
  agent should fix the script and rerun the whole thing, not click around.
- **Honesty about failures.** If `example.com` is down or a selector breaks,
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
| `example.com` times out | Network or proxy issue | Check that `https://example.com` opens in a normal browser |
