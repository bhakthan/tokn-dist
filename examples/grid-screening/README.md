# Example: let TOKN improve its own harness on a grid-planning task

This walkthrough takes one small but real piece of domain work, from start to
finish:

> *Screen five substations for transformer loading and N-1 security, then
> recommend an action for each.*

It uses two TOKN features that are new in this release:

| Feature | What it does here |
|---|---|
| **Harness tree** (`tokn harness show` / `validate`) | Shows the eight editable parts of TOKN's harness for this folder: system prompt, guardrails, memory, tool guidance, subagents, skills, scripts and plugins. |
| **Propose–Probe–Compose** (`tokn harness evolve`) | TOKN runs the task with its current harness and reads the evidence. It then proposes better harness edits, tries them in throwaway copies, and keeps the best one. A judge grades every result against a rubric that the agent never sees. |

A **decision model** sits inside the loop. TOKN does the arithmetic with
ordinary tools, then asks a typed decision model (`system_one_batch`) to choose
each substation's action. The decision is **advisory**: a deterministic
engineering rule always overrides it.

All data in `workspace/data/` is synthetic.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.56 or newer** | First release with `tokn harness` | `tokn version` |
| `git` | `evolve` seals its inputs and works in a git repo | `git --version` |
| An LLM provider and key | Runs the agent, the proposers and the judge | see [SETUP.md](../../SETUP.md) |
| A decision-model backend | Chooses the per-substation action | see [step 3](#3-configure-a-decision-model) |

Trial and Community tiers both run this example. Model calls are billed by
your own providers, not by TOKN.

> **What leaves your machine.** The model provider receives the task and the
> files the agent reads. The decision backend receives only the `state` that
> the agent sends with each decision (the computed figures). Nothing is sent
> anywhere until step 6. Steps 1–5 make no model call.

## 1. Copy the example into a scratch git repo

macOS / Linux:

```bash
cp -r examples/grid-screening/workspace ~/tokn-grid && cp examples/grid-screening/task.json ~/tokn-grid/
cd ~/tokn-grid && git init -q && git add -A && git commit -qm "grid screening example"
```

Windows PowerShell:

```powershell
Copy-Item examples\grid-screening\workspace $HOME\tokn-grid -Recurse
Copy-Item examples\grid-screening\task.json $HOME\tokn-grid\
Set-Location $HOME\tokn-grid; git init -q; git add -A; git commit -qm "grid screening example"
```

You now have:

```text
tokn-grid/
  task.json                               # the task, the rubric, the step budget
  data/loads.csv, data/transformers.csv   # synthetic source of record
  .nospace/instructions.md                # harness: memory
  .nospace/prompts/guidance-guardrails.md # harness: guardrails
```

## 2. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a Claude model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a Claude model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Use your shell or `~/.tokn/config/credentials.env` for keys. Never commit a
key to the repo.

## 3. Configure a decision model

List the supported models and their settings (this works offline):

```bash
tokn system-one models
```

Pick **one** backend:

| Backend | Settings |
|---|---|
| Jev (default) | `JEV_API_KEY=<key>` |
| OpenAI Decisions API | `SYSTEMONE_BACKEND=openai`, `OPENAI_API_KEY=<key>` |
| Microsoft Decision-1 | `SYSTEMONE_BACKEND=microsoft`, `DECISION_API_ENDPOINT=https://<resource>.cognitiveservices.azure.com`, `DECISION_API_KEY=<key>` (or Entra ID via `az login`) |
| Self-hosted open weights (for example Clef) | `SYSTEMONE_BACKEND=compatible`, `SYSTEMONE_BASE_URL=https://<host>`, `SYSTEMONE_MODEL=<model>` |

Destinations such as `SYSTEMONE_BACKEND` and `DECISION_API_ENDPOINT` are
**never** read from a repository `.env`. Set them in your shell or in
`~/.tokn/config/credentials.env`.

Verify the backend without making a call:

```bash
tokn system-one status
```

## 4. Look at the harness TOKN will evolve

```bash
tokn harness show --repo-root .
tokn harness validate --repo-root .
```

`show` lists the eight components and which ones this folder sets. Here those
are memory and guardrails. `validate` exits `0` when the tree is well formed.

## 5. Preview the plan (no model call)

```bash
tokn harness evolve --task-spec task.json --mode seq --k 1 --repo-root . --dry-run
```

With `--k 1` the plan has these stages:

| Stage | What happens |
|---|---|
| `base-1` | The agent runs the task with the current harness |
| `inv-1` | A proposer reads that run's evidence and edits the harness to fix what it saw going wrong |
| `dom-1` | A second proposer edits the harness using domain knowledge |
| `c-1` | A composer merges the useful edits, then the agent re-runs the task |
| `judge-*` | The judge grades base and selected outputs against the rubric |

Budget: R = 4k rollouts and P = 3k sessions. Cap spend with `--max-usd`.

## 6. Run it

```bash
tokn harness evolve --task-spec task.json --mode seq --k 1 --repo-root . --max-usd 5
```

Expect roughly 10–20 minutes. Each rollout runs in a throwaway temp copy.
Your `data/` folder and harness files are sealed before the run and checked
again after every stage.

**What one of our runs looked like** (`--k 1`, a fast Claude model, Microsoft
Decision-1; your numbers will differ):

| Rollout | Correct | Steps | Tokens | Tool calls |
|---|---|---|---|---|
| base-1 (harness as shipped) | 5/5 | 10 | 432k | 14 |
| c-1 (evolved harness) | 5/5 | 6 | 231k | 4 |

To get there, TOKN wrote itself a small tested screening script and a skill
that routes the arithmetic to the script and the action choice to the
decision model. The model writes only the rationale. The judge scored both
rollouts 5/5. The run took about 11 minutes and cost about US$2.50 in model
calls.

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Healthy run: a candidate was selected and judged |
| non-zero | **Degraded**. The reasons are printed and recorded in `result.json`. Examples: every session fell back, nothing was delivered, the judge could not grade, or the selected candidate scored **below** the base. The result is still written. |

A degraded exit is the run telling you something true. A run that silently
reported success would be worse.

## 7. Read the result

Everything goes to `.nospace/ppc/<run-id>/`:

| File | Read it for |
|---|---|
| `result.json` | The selected candidate, judge scores, spend, and degraded reasons. Per stage: steps, tokens, `tool_names` (look for `system_one_batch`) and changed files |
| `context/deliverables/<label>/` | Each rollout's own `screening.json` and `report.md` |
| `context/rollouts/<label>.md` | A compact trajectory of each rollout, which is the evidence the proposers read |
| `context/decisions/<label>.md` | Why each proposer changed the harness the way it did |
| `context/pool/<label>/.nospace/` | Each candidate harness |
| `judge/<label>.json` | The judge's per-rubric verdicts |

Check the arithmetic yourself:

| Substation | loading % | N-1 % | status |
|---|---|---|---|
| S1 | 82.1 | 164.2 | n1_violation |
| S2 | 41.7 | 83.3 | ok |
| S3 | 103.3 | — (single unit) | overloaded |
| S4 | 53.6 | 134.0 | n1_violation |
| S5 | 49.1 | 73.7 | ok |

S1, S3 and S4 must get `load_transfer` or `upgrade`, whatever the decision
model said.

### What to look for

- **Efficiency.** Compare the steps, tokens and tool calls of `base-1` and `c-1`.
  An evolved harness usually reaches the same correct answer in fewer steps.
- **Decision-model use.** `tool_names` should include `system_one_batch`. Each
  confidence in `screening.json` comes from the decision model.
- **Judge vs. you.** The judge saw the rubric; the agent did not. If they
  disagree, `result.json` says so.

## 8. Keep the improvement (optional)

```bash
tokn harness evolve --task-spec task.json --mode seq --k 1 --repo-root . --adopt
git diff .nospace/
```

This is a second paid run. To adopt on the first run, add `--adopt` in step 6.
`--adopt` writes the selected harness changes into `.nospace/`, but only after
the changes validate and the seal holds. It **refuses** a candidate that scored
below the base. Use `git diff` to review the change, and commit it only if you
agree with it.

Every run also records its selected harness in a per-domain library. Later
runs in this repo read that library first. To view it:

```bash
tokn harness library --repo-root . --domain power-distribution-planning
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `unknown command "harness"` | Upgrade to v0.3.56 or newer |
| Every stage reports `fell_back` | The LLM is not configured. Re-check step 2, then run `tokn agent-run --help` |
| No `system_one_*` in `tool_names` | The decision backend is not set. Run `tokn system-one status` |
| `seal violated` | Something changed `data/` or `.nospace/` during the run. Restore them with `git checkout .` and run again |
| Rate-limit (`429`) messages | TOKN retries them automatically. Lower your concurrency or try again later |
