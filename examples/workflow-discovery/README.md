# Example: Workflow Discovery with a Procedural Graph

> "Classify the synthetic case, draft a research summary, and record a reviewer sign-off."

A model can follow a clinical-style workflow only if the workflow is written down as a graph of states and actions. This example shows how to write that graph, check it, and see what a model would be shown at each step. TOKN's `procgraph` package does this. Its evolver, which searches for a better graph, is only exercised by Go tests, so this walkthrough covers the user-reachable part.

| Capability | What the command does |
|---|---|
| `tokn procgraph skeleton` | Emits the bare `Start -> End` graph that discovery begins from. |
| `tokn procgraph validate` | Fail-closed structural check: cycles, reachability, and known tool names. |
| `tokn procgraph render` | Prints the compact text a guidance model reads. |
| `tokn procgraph localize` | Shows the neighbourhood around one action: the subgraph a model would actually be given. |
| `check_graph.py` | Offline stdlib-only check of the JSON shape. No network. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The `procgraph` commands ship in this version. | `tokn version` |
| 14-day trial (`tokn license trial`) | The workflow mirrors the `precmed` domain mode, which needs the trial. The `procgraph` commands were not checked for a licence gate of their own. | `tokn license` |
| Python 3.8 or newer | Optional offline checker. Standard library only. | `python --version` |
| An LLM provider | Not needed. These steps make no model calls. | Not required |

Activate the trial once per machine:

```bash
tokn license trial
```

```powershell
tokn license trial
```

**What leaves your machine:** the `procgraph` commands read local JSON and print to the terminal, with no model calls. Starting the trial sends a one-time anonymous install registration (as described in [../precmed-variant/README.md](../precmed-variant/README.md)). The graph is synthetic.

## 1. Copy the example to a scratch folder

`procgraph skeleton -o` is the only command here that writes a file. Keep your edits out of this repo.

```bash
cp -r examples/workflow-discovery ~/workflow-run   # any scratch folder you own
cd ~/workflow-run
```

```powershell
Copy-Item -Recurse examples\workflow-discovery $HOME\workflow-run
Set-Location $HOME\workflow-run
```

## 2. Start from the skeleton

Emit the bare graph that discovery starts from, then compare it with the hand-written `graph.json`.

```bash
tokn procgraph skeleton -o skeleton.json
```

```powershell
tokn procgraph skeleton -o skeleton.json
```

The skeleton has only `Start` and `End`. Open it, then open `graph.json` to see the states and actions that a discovery run would need to add.

## 3. Check the structure offline

This check reads local files only and needs no TOKN binary.

```bash
python check_graph.py graph.json
```

```powershell
python check_graph.py graph.json
```

Expected, not a recorded run: a first line like `9 nodes, 8 edges`, then `ok (structural checks only)`.

## 4. Validate with TOKN

Pass the tool names the agent may call, so the validator can check that every ACTION node names a real tool. The names below are placeholders for this example.

```bash
tokn procgraph validate graph.json --tool classify_case --tool draft_report --tool sign_off
```

```powershell
tokn procgraph validate graph.json --tool classify_case --tool draft_report --tool sign_off
```

Expected, not a recorded run: a summary line with node and edge counts and a terminals list, then `ok`. If a cycle appears, the command fails. `--allow-cycles` or `--repair` change that behaviour. Use `--repair` only to see which edge would be removed.

## 5. Render what the model reads

```bash
tokn procgraph render graph.json
```

```powershell
tokn procgraph render graph.json
```

The output is the compact text a guidance model receives. Check that every `guidance` and `pitfalls` line is present for the actions you care about.

## 6. Localize around one action

`localize` takes an optional last action name and returns the subgraph within a radius (default 2 hops).

```bash
tokn procgraph localize graph.json classify_case --hops 2
```

```powershell
tokn procgraph localize graph.json classify_case --hops 2
```

Expected, not a recorded run: a line `localized at "classify_case"` with a matched flag and hop count, then a subgraph count, then the rendered neighbourhood. If the name matches no node, the command prints a `FALLBACK` line and the model would receive the full graph.

## What to look for

- `validate` and the offline checker agree on the node and edge counts. A mismatch means a typo in an ID.
- The `localize` neighbourhood of `classify_case` includes the state before it and the state after it. It should not include `sign_off` unless `--hops` is raised.
- The sign-off pitfall (no sign-off with an unclassified finding) is visible in `render`, so a guidance model would see it.
- Changing a `pitfalls` string changes the `render` output but not the structure. This is the part a discovery run would refine.

## Scope and limits

- The iterative refiner (`procgraph.Evolver`) is **not** a CLI command. It is exercised by Go tests only (`internal/agent/procgraph`). This walkthrough does not run it.
- A live discovery run, in which a model proposes graph edits, needs a separate build tag and a model endpoint. It is not part of this example.
- The mirror of the precmed workflow lives in the `precmed` domain. The graph here is a small synthetic stand-in, not that workflow.
- This is a process-map exercise. It is not clinical guidance. The gate behaviour that TOKN enforces in `precmed` is described in [../precmed-variant/README.md](../precmed-variant/README.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tokn: command not found` | Install TOKN v0.3.57 or newer and open a new terminal. |
| `tokn procgraph` is missing | Check `tokn version`. Older builds do not ship the command. |
| `validate` reports an unknown tool | Add the name with `--tool`, or check the spelling against the ACTION node ID. |
| `localize` prints `FALLBACK` | The name does not match any node ID. Check the spelling. |
| `parse procedural graph` error | The JSON is malformed. Run `python check_graph.py graph.json` for a clearer message. |
| Tier shows Community | Run `tokn license trial` (once per machine), then `tokn license` to confirm. |
