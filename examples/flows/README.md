# Example: Declarative Multi-Step Flows

> "Read the meeting notes, pull out the decisions, then find the open risks and write a summary."

A flow is a small graph of steps. Each step is a focused sub-agent prompt, and a
step can wait for others. TOKN runs the graph in the background, so you can keep
working while it finishes. This example runs a three-step graph over a short
synthetic notes file.

| Capability | What it shows |
|---|---|
| `start_workflow` with `nodes` | You define the steps yourself as a graph. |
| `depends_on` | A step waits for the steps it depends on. |
| `final_node` | Chooses which step's output is the result. |
| `/workflows` | Lists, inspects, and fetches the result of background runs. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The workflow tools and `/workflows` ship in this version. | `tokn version` |
| Community tier (no trial needed) | The workflow tools are not in the premium-mode list. | `tokn license features` |
| An LLM provider | Each step is a model call. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** each step's prompt, `sample-notes.md`, and tool
results. These go to the LLM provider you configure. The notes are synthetic.

**Surface note:** the released binary exposes flows through the interactive
session (`tokn agent-repl`). The `start_workflow` tool is registered there. This
example uses that path. It does not use `tokn agent-run`, and it does not depend
on the internal `create_flow` or `run_flow` tools, which are not reachable from
the released binary.

## 1. Copy the example to a scratch folder

```bash
cp -r examples/flows ~/flows-run   # any scratch folder you own
cd ~/flows-run
```

```powershell
Copy-Item -Recurse examples\flows $HOME\flows-run
Set-Location $HOME\flows-run
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

## 3. Start the session

```bash
tokn agent-repl --repo-root .
```

```powershell
tokn agent-repl --repo-root .
```

## 4. Launch the flow

At the prompt, paste the instruction below. It asks the model to call
`start_workflow` with the graph in `notes-review.json`.

```text
Call start_workflow with a custom workflow. Use the JSON in notes-review.json
as the value of the nodes list, name, and final_node. Do not change the node
prompts. Then tell me the run_id it returns.
```

The model should return a run id. The run continues in the background.

## 5. Inspect the run

Type these commands at the prompt. Replace `<run_id>` with the id from step 4.

```text
/workflows list
/workflows status <run_id>
/workflows result <run_id>
```

`/workflows result` returns the output of the `final_node`. Use `/workflows logs <run_id>`
if you want to see what each step did.

## 6. Check the result

Expected, not a recorded run. Your output will differ in wording.

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The run starts | `start_workflow` returns a run id |
| 2 | The steps run in order | `extract` finishes before `risks`, and `final` is last |
| 3 | The facts come from the file | The decisions match the four dated lines in `sample-notes.md` |
| 4 | The risk step cites a source | The one stated risk is tied to its bullet |
| 5 | The summary uses both headings | `Decisions` and `Open risks` appear in the result |

Score it by hand: five passes count as PASS, three or four as partial, fewer as FAIL.

## What to look for

- The `extract` step lists the four dated decisions and nothing invented.
- The `risks` step reports the backup gap from 2026-03-12 and names its owner.
- The `final` step uses only what the earlier steps produced.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tokn: command not found` | Install TOKN v0.3.57 or newer and open a new terminal. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME`, and your key. See [../../SETUP.md](../../SETUP.md). |
| The model does not call `start_workflow` | Paste the instruction again, and say "call the start_workflow tool". |
| `/workflows` says the manager is unavailable | Workflow tools are set up in the interactive session only. Start with `tokn agent-repl`. |
| `/workflows status` shows `not found` | Use the run id from step 4. Run `/workflows list` to see all runs. |
