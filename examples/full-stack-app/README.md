# Example: Full-Stack App From a Spec

> "Build the TaskFlow application described in spec.md in this folder."

TOKN reads a written spec, writes a Python API and a TypeScript front end, and
writes a README for both. Then an offline checker confirms the files exist and
parse. The spec is invented, and no data leaves the folder except what the model
needs to do the work.

| Capability | What it shows |
|---|---|
| `rw` mode | The agent can create and edit files in the working folder. |
| Spec-driven build | The agent follows a file layout and API table, not a free-form idea. |
| Multi-language output | Python backend and TypeScript frontend in one run. |
| Offline check | A stdlib-only script confirms the output without running it. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | `rw` mode and `agent-run` flags ship in this version. | `tokn version` |
| Community tier (no trial needed) | `rw` is a Community mode. | `tokn license features` |
| Python 3.11+ | Runs the offline checker. | `python --version` |
| An LLM provider | TOKN calls a model to write the files. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, `spec.md`, and the files the agent reads
and writes in the scratch folder. These go to the LLM provider you configure. The
spec is synthetic.

## 1. Copy the example to a scratch folder

Run the build outside this repo. TOKN writes `.nospace/` state and the generated
`taskflow/` tree into the working folder.

```bash
cp -r examples/full-stack-app ~/taskflow-run   # any scratch folder you own
cd ~/taskflow-run
```

```powershell
Copy-Item -Recurse examples\full-stack-app $HOME\taskflow-run
Set-Location $HOME\taskflow-run
```

## 2. Configure the LLM

Use the same placeholders as [grid-screening](../grid-screening/README.md#2-configure-the-llm).
Replace them with your own values.

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

For other providers, see [../../SETUP.md](../../SETUP.md).

## 3. Run the build

The agent writes into the current folder, so use a scratch copy. Run it with
`--mode rw`. This mode is the one that allows file writes.

```bash
tokn agent-run --mode rw --repo-root . --prompt-file prompt.md --max-steps 60 --no-confirm
```

```powershell
tokn agent-run --mode rw --repo-root . --prompt-file prompt.md --max-steps 60 --no-confirm
```

`--no-confirm` approves tool calls without prompting, so use it only in a scratch
copy. If the run stops early, raise `--max-steps`.

## 4. Check the output offline

The checker reads files only. It makes no network calls and writes nothing.

```bash
python check_taskflow.py .
```

```powershell
python check_taskflow.py .
```

## 5. Check the result

Expected, not a recorded run. Your output will differ in wording and detail.

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The backend folder exists | `backend/app.py`, `models.py`, `database.py`, and `routes/` are present |
| 2 | The frontend folder exists | `index.html`, `styles.css`, and `src/` with three components are present |
| 3 | The Python parses | The checker reports no syntax errors |
| 4 | The tsconfig is valid JSON | The checker reports no JSON errors |
| 5 | The HTML shell has its IDs | `#app`, `#sidebar`, `#content`, and `#task-list` are found |
| 6 | No framework was added | No React, Vue, Tailwind, or Bootstrap import or dependency |

Scoring: the checker prints `PASS` when all expected files are present and parse.
Any `FAIL` line names the file and the problem.

## What to look for

- The agent follows the layout in `spec.md` rather than inventing its own.
- The routes match the API table, including the `status` filter on `GET /api/tasks`.
- The agent does not add a build step, because the spec forbids one.
- The README gives separate backend and frontend run steps.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tokn: command not found` | Install TOKN v0.3.57 or newer and open a new terminal. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME`, and your key. See [../../SETUP.md](../../SETUP.md). |
| The run stops at the step limit | Increase `--max-steps`. |
| Files are missing after the run | Confirm `--mode rw` is set. Read-only modes do not write files. |
| `FAIL missing file` from the checker | Re-run the build, or raise `--max-steps` so the agent reaches the frontend. |
| `FAIL python syntax error` | Ask the agent to fix the named file, then re-run the checker. |
