# Example: Meeting Minutes to Design Plan to PoC

> "Read the minutes of our feedback planning meeting, write a design plan, and scaffold a small proof of concept."

A planning meeting ends with a page of notes, and the decisions in it are easy to lose. This walkthrough turns those minutes into a short design plan and a runnable Go proof of concept. TOKN reads the minutes, writes the plan with explicit sections, and scaffolds the code. A small offline checker then confirms the output has the expected shape.

Path A is the default. It uses a synthetic minutes file and any model provider you configure that can make tool calls; you need no Microsoft 365 access. Path B is optional. It pulls the minutes from your own Microsoft 365 work or school account through WorkIQ, and its generation step uses an Azure OpenAI deployment (`tokn workiq demo --help`), not an arbitrary provider.

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
| An LLM provider | TOKN calls a model to write the plan and the code. Use a model capable of the required tool calls; provider charges and number of turns depend on the run. A missing/failed tool result is unassessed, not a pass. | See [../../SETUP.md](../../SETUP.md); static config check: `tokn doctor --provider <id>` |
| **Path B only:** an Azure OpenAI deployment | `tokn workiq demo` sends the retrieved context to the configured Azure OpenAI deployment. | `NOSPACE_MODEL_PROVIDER=azure-openai` plus `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT`; `tokn doctor --provider azure-openai` |
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

Set these in a trusted shell. `.env.example` lists the names for reference; do not source it or commit a populated `.env`.

```bash
export NOSPACE_MODEL_PROVIDER='anthropic'
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
tokn doctor --provider anthropic
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "YOUR_MODEL_ID"
# Supply ANTHROPIC_API_KEY from a trusted secret store or session, not a command containing the key.
tokn doctor --provider anthropic
```

`tokn doctor` checks static configuration only; it does not prove the key works. For other providers, see [../../SETUP.md](../../SETUP.md).

## 3. Path A: run the flow on the synthetic minutes

Read `minutes.md` first. It is a fictional planning meeting with made-up attendees and a generic customer-feedback idea. `prompt.md` tells the agent to write `design-plan.md` and a `poc/` folder.

**Before you run, write your own acceptance criteria.** Outside the working folder, write two or three checks the PoC must meet that the prompt does not spell out, plus a small CSV of your own (a `text` column with a dozen feedback lines) and the top-five tag counts you expect. The agent never sees these, so they are an out-of-sample test, unlike `check_poc.py`, which only checks shape.

Stage only the minutes and the prompt in `work/`, so the checker and this README stay outside the agent's read scope:

```bash
mkdir work && cp minutes.md prompt.md work/
cd work
tokn agent-run --mode rw --repo-root . --prompt-file prompt.md --max-steps 20 --permission-mode default
cd ..
```

```powershell
New-Item -ItemType Directory work | Out-Null; Copy-Item minutes.md, prompt.md work\
Set-Location work
tokn agent-run --mode rw --repo-root . --prompt-file prompt.md --max-steps 20 --permission-mode default
Set-Location ..
```

`--permission-mode default` asks before each edit or mutating command, so you approve each file the agent writes. Do not add `--no-confirm` to this run: it auto-approves every tool call, including code generation and shell commands. If the run stops early, raise `--max-steps`. To work interactively instead, start `tokn agent-repl` in `work/` and paste the contents of `prompt.md`.

Expected output, not a recorded run: `work/design-plan.md` and a `work/poc/` folder with `go.mod`, `main.go`, and `README.md`.

## 4. Check the output offline

The checker reads local files only. It makes no network calls.

```bash
python3 check_poc.py --plan work/design-plan.md --poc work/poc
```

```powershell
python check_poc.py --plan work\design-plan.md --poc work\poc
```

It fails if a required heading (`Scope`, `Approach`, `Risks`, `Open Questions`) is missing, if a scaffold file is missing, if `main.go` has 200 or more lines, or if `main.go` imports a non-standard package. A word count outside 200 to 400 words prints a note, not a failure.

Optional: check that the PoC compiles. This needs Go installed. It writes no binary.

```bash
cd work/poc && go vet ./... ; cd ../..
```

```powershell
Set-Location work\poc; go vet ./...; Set-Location ..\..
```

Then run the PoC on the CSV you wrote before the run (`go run . ../../my-feedback.csv` from `work/poc`, if you saved it as `my-feedback.csv` beside `work/`; see `poc/README.md` describes) and compare its top five with your expected counts. A shape pass from `check_poc.py` plus a wrong count is a fail. If you find yourself repeating this generate-check-fix cycle on the same codebase, that is the job of `tokn factory`, which keeps work items, gates and human approvals in one ledger; see the [RNA-seq software factory](../rnaseq-software-factory/README.md) example.

## 5. Path B (optional): pull the minutes from your own Microsoft 365 account

Use this path only with a meeting you are allowed to share with your Azure OpenAI deployment. It needs provider access on two sides: Microsoft 365 (WorkIQ retrieval) and Azure OpenAI (generation, `NOSPACE_MODEL_PROVIDER=azure-openai` plus `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` and a credential). Replace the placeholders with your own values. Do not paste real meeting content into this repo. The demo writes generated files into a new folder without per-file approval, so read them before you build or run anything.

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

`tokn workiq demo --help` lists the other flags. Start with `--dry-run`, which prints the plan and scaffold to stdout instead of writing files. The demo writes `design-plan.md`, `main.go`, `go.mod`, and `README.md` directly into the output folder, so the checker takes the same folder for `--poc`.

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
