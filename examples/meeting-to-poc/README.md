# Example: Meeting Minutes to Design Plan to PoC

> "Read the minutes of our feedback planning meeting, write a design plan, and scaffold a small proof of concept."

A planning meeting ends with a page of notes, and the decisions in it are easy to lose. This walkthrough turns those minutes into a short design plan and a runnable Go proof of concept. TOKN reads the minutes, writes the plan with explicit sections, and scaffolds the code. A small offline checker then confirms the output has the expected shape.

Path A uses a synthetic minutes file, so you need no Microsoft 365 access. Path B is optional. It pulls the minutes from your own Microsoft 365 work or school account through WorkIQ.

| Capability | What it does here |
|---|---|
| `tokn agent-run --mode rw` | Reads the minutes and writes the design plan and the `poc/` scaffold in the working folder. |
| `tokn workiq demo` (Path B) | Pulls meeting context through WorkIQ, asks the LLM for a plan and a stdlib-only `main.go`, and writes the files to an output folder. |
| `tokn workiq login` / `status` (Path B) | Signs in to WorkIQ and checks the connection. |
| `check_poc.py` | Offline, stdlib-only check of the design plan headings and the scaffold layout. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The `rw` mode and `tokn workiq` ship in this version. | `tokn version` |
| Community tier (no trial needed) | The `workiq` and `rw` modes are free in the Community tier. | `tokn license features` |
| An LLM provider | TOKN calls a model to write the plan and the code. | See [../../SETUP.md](../../SETUP.md) |
| Python 3.9 or newer | Runs the offline checker. | `python --version` (Windows) or `python3 --version` (macOS, Linux) |
| **Path B only:** a Microsoft 365 work or school account | WorkIQ pulls context from your own tenant. Personal accounts are not supported. | Sign in with your work account. |
| **Path B only:** WorkIQ access | Check with your organisation's admin whether your account needs a Microsoft 365 Copilot licence for WorkIQ, and whether tenant admin consent is required for the WorkIQ app. Do not assume either. | Ask your admin. `tokn workiq status` shows the error if the account is not ready. |
| **Path B only:** Node.js with npm | The demo's retrieval step uses the npm package `@microsoft/workiq`. | `node --version` and `npm --version` |

### Dependency preflight and install commands

Path A needs TOKN and Python. Path B also needs Node.js and the WorkIQ npm package. Check everything first:

```bash
tokn version
python3 --version
node --version
npm --version
```

```powershell
tokn version
python --version
node --version
npm --version
```

Install what is missing.

| OS | Node.js | Python 3 | Go (optional, to build the PoC) |
|---|---|---|---|
| Windows | `winget install OpenJS.NodeJS.LTS` | `winget install Python.Python.3.12` | `winget install GoLang.Go` |
| macOS | `brew install node` | `brew install python` | `brew install go` |
| Linux (Debian or Ubuntu) | `sudo apt install nodejs npm` | `sudo apt install python3` | `sudo apt install golang-go` |

For Path B, install the WorkIQ npm package once:

```bash
npm install -g @microsoft/workiq
```

```powershell
npm install -g @microsoft/workiq
```

If you do not use Path B, skip the Node.js and npm install steps.

**What leaves your machine:**

- **Path A:** the prompt, `minutes.md`, and the files TOKN reads from the working folder. These go to the LLM provider you configure. Everything here is synthetic.
- **Path B:** your question goes to Microsoft 365 through WorkIQ, which searches your account for meeting context. The returned excerpts and your prompt then go to the LLM provider you configure. Only use meetings you are allowed to share with that provider. Check your organisation's data policy first.

## 1. Copy the example to a scratch folder

TOKN writes output files and `.nospace/` state into the working folder. Run the example outside this repo.

```bash
cp -r examples/meeting-to-poc ~/meeting-to-poc-run   # any scratch folder you own
cd ~/meeting-to-poc-run
```

```powershell
Copy-Item -Recurse examples\meeting-to-poc $HOME\meeting-to-poc-run
Set-Location $HOME\meeting-to-poc-run
```

## 2. Configure the LLM

Replace the placeholders with your own values.

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<a model you have access to>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

For other providers, see [../../SETUP.md](../../SETUP.md).

## 3. Path A: run the flow on the synthetic minutes

Read `minutes.md` first. It is a fictional planning meeting with made-up attendees and a generic customer-feedback idea. `prompt.md` tells the agent to write `design-plan.md` and a `poc/` folder.

```bash
tokn agent-run --mode rw --repo-root . --prompt-file prompt.md --max-steps 20 --no-confirm
```

```powershell
tokn agent-run --mode rw --repo-root . --prompt-file prompt.md --max-steps 20 --no-confirm
```

`--no-confirm` skips the approval prompts so the run can finish unattended. Use it only in a scratch folder. If the run stops early, raise `--max-steps`. To work interactively instead, start `tokn agent-repl` in the same folder and paste the contents of `prompt.md`.

Expected output, not a recorded run: a `design-plan.md` in the folder root and a `poc/` folder with `go.mod`, `main.go`, and `README.md`.

## 4. Check the output offline

The checker reads local files only. It makes no network calls.

```bash
python3 check_poc.py --plan design-plan.md --poc poc
```

```powershell
python check_poc.py --plan design-plan.md --poc poc
```

It fails if a required heading (`Scope`, `Approach`, `Risks`, `Open Questions`) is missing, if a scaffold file is missing, if `main.go` has 200 or more lines, or if `main.go` imports a non-standard package. A word count outside 200 to 400 words prints a note, not a failure.

Optional: check that the PoC compiles. This needs Go installed. It writes no binary.

```bash
cd poc && go vet ./... ; cd ..
```

```powershell
Set-Location poc; go vet ./...; Set-Location ..
```

To run it, `poc/README.md` describes the CSV columns. The synthetic minutes are not a CSV, so you need your own small sample CSV.

## 5. Path B (optional): pull the minutes from your own Microsoft 365 account

Use this path only with a meeting you are allowed to share with your LLM provider. Replace the placeholders with your own values. Do not paste real meeting content into this repo.

Sign in to WorkIQ once:

```bash
tokn workiq login
tokn workiq status
```

```powershell
tokn workiq login
tokn workiq status
```

If you use a non-default app registration or tenant, pass them as flags or environment variables. See `tokn workiq --help` for the exact names. Do not put tenant or app identifiers in files you share.

Run the demo. Its output folder must not exist yet.

```bash
tokn workiq demo -q "Summarise the decisions and action items from <your meeting title>" -o ~/meeting-to-poc-m365
python3 check_poc.py --plan ~/meeting-to-poc-m365/design-plan.md --poc ~/meeting-to-poc-m365
```

```powershell
tokn workiq demo -q "Summarise the decisions and action items from <your meeting title>" -o $HOME\meeting-to-poc-m365
python check_poc.py --plan $HOME\meeting-to-poc-m365\design-plan.md --poc $HOME\meeting-to-poc-m365
```

`tokn workiq demo --help` lists the other flags, such as `--dry-run`, which you can use to check the setup before a real run. The demo writes `design-plan.md`, `main.go`, `go.mod`, and `README.md` directly into the output folder, so the checker takes the same folder for `--poc`.

Expected output, not a recorded run: the demo prints its three steps (retrieve, generate, write), then the checker prints PASS.

## What to look for

- `design-plan.md` uses the four headings in order, and the Open Questions section names the gaps from the minutes instead of inventing answers.
- The Risks section mentions the privacy point about raw email addresses from the minutes.
- `poc/main.go` imports only standard-library packages and stays under 200 lines.
- The PoC reads a CSV path from the command line and does not reach the network.
- On Path B, the plan reflects your real meeting, and nothing in the output appears that the meeting did not contain.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tokn: command not found` | Install TOKN v0.3.57 or newer and open a new terminal. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME`, and your key. See [../../SETUP.md](../../SETUP.md). |
| The run stops at the step limit | Increase `--max-steps`. |
| `tokn workiq` says it is not connected or asks you to log in | Run `tokn workiq login`, then `tokn workiq status`. |
| WorkIQ reports that consent is required | Tenant admin consent is needed for the WorkIQ app. Ask your admin. Do not try to bypass it. |
| The account is not licensed for WorkIQ | Check with your organisation's admin whether a Microsoft 365 Copilot licence is required. |
| `workiq passthrough binary not found` | Run `npm install -g @microsoft/workiq`, then open a new terminal. |
| `python3: command not found` on Windows | Use `python` instead. |
| The demo refuses to run because the output folder exists | Choose a new `-o` folder name. The demo does not overwrite folders. |
| `check_poc.py` says a heading is missing | Ask the agent to rewrite `design-plan.md` with the four exact `## ` headings, then run the checker again. |
