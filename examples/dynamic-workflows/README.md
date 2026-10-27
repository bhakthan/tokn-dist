# Example: Dynamic workflows — background agent fleets from one prompt

> "Research this properly, check every claim, and only show me the final answer."

A **dynamic workflow** is a graph of sub-agents that TOKN runs in the background
while your conversation goes on. Each node is a real `tokn agent-run`
subprocess with its own context, so drafts, votes and critiques never fill your
session; you get back only the final answer. This walkthrough covers:

| Feature | What it does |
|---|---|
| Bundled workflows | Ready-made graphs: `deep-research`, `adversarial-verification`, `multi-angle-draft`, `vote`, `adversarial-review`, `iterative-refine`, `find-and-refute` |
| `iterative-refine` | A *dynamic* controller: it drafts, then decides which quality templates to spawn, round after round |
| `ultrawork` keyword | One word in a prompt asks the model to use a background workflow for maximum effort |
| `/workflows` | `list`, `status`, `logs`, `result`, `stop`, `save`, `saved`, `resume` |
| Saved workflows | Turn a finished run into a reusable spec, then run it again by name |
| Domain capsules | In a domain mode, every node knows that domain's gates; the text is a file you can override |

Custom graphs that you write yourself are covered in
[flows](../flows/README.md). The `find-and-refute` workflow is covered in
[loops-and-ship-ready](../loops-and-ship-ready/README.md).

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.67 or later | Ships the workflow tools, `ultrawork` and `/workflows save/resume` | `tokn version` |
| A model provider | The REPL and every node call a model | see [SETUP.md](../../SETUP.md) |
| Trial tier (step 7 only) | Domain modes such as `finrisk` | `tokn license` |

Workflow tools are registered in the interactive session (`tokn agent-repl`),
not in one-shot `tokn agent-run`.

### What leaves your machine

- Every node is a model call to the provider you configured. A bundled
  workflow typically runs several nodes; `iterative-refine` can run more. Use
  a cheap model while you try this out.
- Run state, node logs and results stay on disk in `.tokn/workflows/` inside
  the project you started from. Saved workflows are JSON files in
  `.nospace/workflows/` (or `~/.tokn/workflows/` with `user` scope).

### Budgets

Every run has hard limits, so a runaway graph cannot run up a bill: at most
**16 live sub-agents**, **1000 sub-agent runs in total**, and **2 hours** of
wall clock. A node that would pass a limit fails with
`workflow budget: … cap reached`.

## 1. Start a session in a scratch folder

bash:

```bash
mkdir -p "$HOME/tokn-workflows-demo" && cd "$HOME/tokn-workflows-demo"
git init -q
tokn agent-repl
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\tokn-workflows-demo" | Out-Null
Set-Location "$HOME\tokn-workflows-demo"
git init -q
tokn agent-repl
```

## 2. Run a bundled workflow

Ask for one by name. The model calls the `start_workflow` tool with
`bundled` and `input`:

```text
Use the deep-research workflow: what are the trade-offs between SQLite WAL mode
and the default rollback journal for a small desktop app?
```

Expected: the tool returns straight away with a run id and the note
*"Running in background. Poll workflow_status; fetch the final answer with
workflow_result."* The REPL is free while the run goes on. Keep chatting, or
look at the run:

```text
/workflows list
/workflows status <run_id>
/workflows logs <run_id>
```

`status` shows each node's state. `logs` shows what each node did. When every
node is done, ask the model for the answer, or fetch it yourself:

```text
/workflows result <run_id>
```

Only this final, synthesized answer enters your conversation. The notes from
each research angle stay in the run folder.

Other bundled workflows to try the same way:

| Ask for | Good for |
|---|---|
| `adversarial-verification` | A claim you want attacked before you trust it |
| `multi-angle-draft` | Several independent drafts, merged into one |
| `vote` | Independent answers, majority decision |
| `adversarial-review` | A draft reviewed by critics, then revised |

Stop a run you no longer need: `/workflows stop <run_id>`.

## 3. Let the controller decide: `iterative-refine`

`iterative-refine` is not a fixed graph. A controller drafts an answer, then
picks which quality templates (`multi-angle-draft`, `vote`,
`adversarial-review`) to spawn next, and stops when it judges the answer good
enough:

```text
Use the iterative-refine workflow: write a one-page incident runbook for a
web app whose database runs out of connections.
```

Watch it with `/workflows status <run_id>`. The node list grows between
rounds, because the controller adds nodes as it goes.

## 4. One word: `ultrawork`

Put the word `ultrawork` anywhere in a prompt:

```text
ultrawork: compare three ways to add full-text search to a Go service, with
benchmarks to run and the risks of each.
```

Expected: the REPL prints

```text
⚡ "ultrawork" detected — encouraging a background, context-isolated workflow for maximum effort. Inspect with /workflows.
```

and adds a short instruction that asks the model to use a background workflow
(for example `iterative-refine`) for a non-trivial task. The model still
decides: a simple question gets a direct answer. The keyword only matches as a
whole word, so `ultraworking` does not trigger it.

The instruction text is a prompt file you can change without rebuilding. Put
your own wording in `~/.tokn/prompts/intent-ultrawork.md`.

## 5. Save a run and run it again

When a run turned out well, save its graph as a reusable workflow:

```text
/workflows save <run_id> sqlite-tradeoffs
/workflows saved
```

Expected: the spec is written to `.nospace/workflows/sqlite-tradeoffs.json`.
Add `user` at the end (`/workflows save <run_id> sqlite-tradeoffs user`) to
save it to `~/.tokn/workflows/` for every project instead.

Run it again with a new question:

```text
Run the saved workflow sqlite-tradeoffs with the input: Postgres logical vs
physical replication for a read-heavy API.
```

The model calls `start_workflow` with `saved: "sqlite-tradeoffs"`. TOKN also
reads (but never writes) specs in `.claude/workflows/`.

## 6. Resume a run that stopped

If a run failed half-way (a provider outage, a budget limit, or you stopped
it), resume it:

```text
/workflows resume <run_id>
```

Nodes that already finished are reused from the cache. Only the rest run
again.

## 7. Optional: domain-aware workflows (trial)

In a domain mode, every node of a workflow runs as a sub-agent in that same
domain, so the domain's gates and validators apply to each one. TOKN also adds
a short **capsule** to every node's prompt. It tells the controller and
reviewers which gates the work must pass, so the controller does not stop
early and reviewers judge against the domain's rules.

```bash
tokn agent-repl --mode finrisk
```

```text
workflow: assess the liquidity risk in a synthetic mid-size bank's balance
sheet and draft the board summary.
```

Curated capsules exist for 13 domains (synbio, nucsci, precmed, oncology,
structbio, quantumsci, powergrid, finrisk, legalai, geospatial, atmchem,
batterypass, clintrial). Other domains get a generic one. Coding mode gets
none.

To change a capsule, write a file named after the prompt key
`domain/<domain>/workflow.capsule`, with `/` replaced by `-` and `.md` added:

| Scope | Path |
|---|---|
| You, in every repo | `~/.tokn/prompts/domain-finrisk-workflow.capsule.md` |
| This repo only | `.nospace/prompts/domain-finrisk-workflow.capsule.md` (read only after `tokn trust`) |

A repo cannot change TOKN's prompts until you trust it, because a cloned repo
was written by someone else. Overrides longer than 2,000 characters are cut
short. A capsule only informs the model; the real gates still run on every
tool call.

## What to look for

- The run id comes back at once. Your session is not blocked while nodes run.
- `/workflows result` gives one synthesized answer. The drafts and critiques
  are not in your context.
- `iterative-refine` adds nodes between rounds; the bundled graphs do not.
- A saved workflow runs again with a new input and no graph to rewrite.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The model answers directly instead of starting a workflow | Name the workflow ("use the deep-research workflow") or say "call start_workflow". |
| `start_workflow` is not available | You are in `tokn agent-run`. Use `tokn agent-repl`. |
| A node fails with `workflow budget: … cap reached` | The run hit a limit (16 live, 1000 total, 2 h). Narrow the question, then `/workflows resume <run_id>`. |
| `ultrawork` does nothing | It must be a whole word, and it only works in an interactive `tokn agent-repl`. |
| My capsule override is ignored | Check the file name (`domain-<d>-workflow.capsule.md`). For a repo-level file, run `tokn trust` and check with `tokn trust status`. |
