# Example: a bounded self-improvement loop for a prompt bundle

> *Improve the support-bot prompt against a training split, keep the held-out split
> sealed until the end, and export the winning version outside the repository.*

TOKN's `rrsi` command adapts a declared bundle of text files (prompts, tool guidance)
in a copy of your repository. It works within explicit budgets, records every round in a
hash-chained history, evaluates the held-out split at most once, and never applies its
result to your repository. You review and apply the export yourself.

| Capability | What it shows here |
|---|---|
| **Plan** (`tokn rrsi plan`) | Prints the budgets, splits, bundle, and preflight checks. Runs nothing. |
| **Calibrate** (`tokn rrsi calibrate`) | Scores the starting bundle several times to measure noise, so a small change is not mistaken for progress. |
| **Run** (`tokn rrsi run`) | The bounded, copy-only loop. This is the step that calls a model. |
| **Status** (`tokn rrsi status`) | Read-only view of a run's state. |
| **Held-out** (`tokn rrsi heldout`) | One-shot comparison on the sealed split. |
| **Export** (`tokn rrsi export`) | Writes the verified bundle and a diff outside the repository. Never applies it. |

> **Scope.** `rrsi` is the user-facing self-improvement command in this release. The
> internal RWSI engine (`internal/agent/rwsi`) has no CLI command of its own; its
> live demo runs only as a Go test with a build tag. This example does not use it.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Current release with `tokn rrsi` | `tokn version` |
| Licence tier: **Community** | No `rrsi` gate was found in the licence policy. Confirm on your machine. | `tokn license features` |
| A git repository you can copy | `rrsi` works on a copy, and records the repository root | `git status` |
| An LLM provider and key (steps 5–6 only) | The proposer, critic, and evaluator call a model | see [SETUP.md](../../SETUP.md) |

> **What leaves your machine.** `plan`, `calibrate`, `status`, and `export` make no model
> call. `run` and `heldout` send prompts and task text to the provider you configure.
> Use synthetic task text only.

## 1. Confirm the flags against your binary

Read the help before you write a spec. Nothing runs.

```bash
tokn rrsi --help
tokn rrsi plan --help
```

```powershell
tokn rrsi --help
tokn rrsi plan --help
```

Expected, not a recorded run: the subcommands are `plan`, `calibrate`, `run`, `status`,
`heldout`, and `export`. The `--spec` flag takes the path to `rrsi.json`. Relative spec
paths resolve against `--repo-root`.

## 2. Create a scratch bundle

macOS / Linux:

```bash
mkdir -p ~/tokn-rrsi/bundle/prompts && cd ~/tokn-rrsi
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-rrsi\bundle\prompts | Out-Null
Set-Location $HOME\tokn-rrsi
```

Save this synthetic prompt as `bundle/prompts/support_bot.txt`:

```text
You are a support assistant for a fictional product called Widgetly.
Answer the customer's question in two sentences. If the answer is not in the
provided notes, say you will escalate it. Never invent order numbers.
```

## 3. Write the spec

Save the following as `rrsi.json` in `~/tokn-rrsi`. The keys come from the spec loader in
`internal/agent/rrsi/spec.go`. Fill in the placeholders for your evaluator. The evaluator
command is the part of this example you must supply; this walkthrough does not provide one.

```json
{
  "name": "support-bot",
  "bundle": {
    "root": "bundle",
    "files": ["prompts/support_bot.txt"],
    "components": { "prompts/support_bot.txt": "prompt" },
    "allow_new_under": []
  },
  "evolve_eval": { "argv": ["<your-evaluator>", "--split", "evolve"], "timeout_sec": 600 },
  "heldout_eval": { "argv": ["<your-evaluator>", "--split", "heldout"], "timeout_sec": 600 },
  "evolve_task_ids": ["<task-id-1>", "<task-id-2>"],
  "heldout_task_ids": ["<task-id-3>"],
  "deny_patterns": ["order number", "refund amount"],
  "budget": { "max_evals": 40, "max_proposer_tokens": 200000, "max_wall_sec": 3600 }
}
```

Keep the budgets small for a first run. Lower them further if your evaluator is slow.

## 4. Plan and calibrate (no model calls)

```bash
tokn rrsi plan --spec rrsi.json --repo-root .
tokn rrsi calibrate --spec rrsi.json --repeats 3 --yes --repo-root .
```

```powershell
tokn rrsi plan --spec rrsi.json --repo-root .
tokn rrsi calibrate --spec rrsi.json --repeats 3 --yes --repo-root .
```

`plan` prints what a run would do. Read the splits and the budget before you go on.
`calibrate` scores the starting bundle three times. The spread it reports is the noise
band. A change in score smaller than that band is not progress.

## 5. Run the bounded loop

Configure the LLM as in [SETUP.md](../../SETUP.md). For Anthropic:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

```bash
tokn rrsi run --spec rrsi.json --repo-root . --yes
```

```powershell
tokn rrsi run --spec rrsi.json --repo-root . --yes
```

The model is taken from the `NOSPACE_*` settings above, so `run` takes no provider flag.

Note the run name it prints (`support-bot-<timestamp>`). If the run stops early, resume it
with `--resume <run-name>` instead of starting over.

## 6. Check status, then evaluate the held-out split once

```bash
tokn rrsi status
tokn rrsi status <run-name>
```

```powershell
tokn rrsi status
tokn rrsi status <run-name>
```

`status` is read-only. Without a run name it lists runs.

When you are satisfied, run the held-out comparison. It is one-shot and seals the run.

```bash
tokn rrsi heldout <run-name> --spec rrsi.json --repo-root . --yes
```

```powershell
tokn rrsi heldout <run-name> --spec rrsi.json --repo-root . --yes
```

## 7. Export outside the repository

```bash
tokn rrsi export <run-name> --out ../rrsi-export --diff ../rrsi.diff --repo-root .
```

```powershell
tokn rrsi export <run-name> --out ..\rrsi-export --diff ..\rrsi.diff --repo-root .
```

`export` verifies the snapshots and writes the bundle and a unified diff outside the
repository. It never applies the change. Read the diff, and apply it yourself if you agree
with it.

### What to look for

- **The noise band.** Changes smaller than the `calibrate` spread are not treated as
  improvements.
- **The budget stop.** The run should stop on a budget or a stall, and `status` should say
  why. A run that stops on budget is not a success just because it finished.
- **One held-out look.** `heldout` can be run once per run. Do not re-run it to shop for a
  better number.
- **Nothing applied.** After `export`, your repository should be unchanged until you apply the
  diff yourself.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `unknown flag` on a subcommand | Re-check the flags with `tokn rrsi <subcommand> --help` |
| `plan` fails on the spec | Check the keys against the list in step 3 and the paths against `--repo-root` |
| `run` asks for confirmation and stops | Add `--yes` only after `plan` and `calibrate` look right |
| Run stops immediately with no model call | The LLM is not configured. Re-check step 5 |
| `heldout` refuses | The held-out split was already evaluated for this run. Start a new run. |
