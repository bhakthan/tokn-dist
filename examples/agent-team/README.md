# Example: A small agent team builds a tiny project

> "Describe a team of agents as a JSON org, split a build into a task graph, and let TOKN run the dry-run plan first."

This walkthrough builds a small Python command-line unit converter. It uses two declarative specs that ship with this example:

- `org.json`: a team of three roles (planner, implementer, reviewer) with a budget, run by `tokn agentorg-run`.
- `swarm.json`: a four-task dependency graph, run by `tokn swarm-plan` and `tokn swarm-build`.

The project being built is a toy. TOKN itself is not modified. Every step first runs without a model, so you can see the structure before any tokens are spent.

## What this example shows

| Capability | What you will do | Command |
|---|---|---|
| Org spec | Declare roles, reporting lines, and a budget in JSON | `tokn agentorg-run --org` |
| Local spec check | Validate the org file offline with the Python checker | `python check_org.py` |
| Task graph | Compute waves and the critical path for a task spec | `tokn swarm-plan --spec` |
| Swarm build | Run tasks in git worktrees and merge onto an integration branch | `tokn swarm-build --spec` |
| Real sub-agents | Let each role or task run a real agent | `--real` (optional) |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Ships `agentorg-run`, `swarm-plan`, `swarm-build` | `tokn version` |
| Licence tier: **Community** | These commands run without a premium mode; default-mode sub-agents are included | `tokn license` |
| Git | Each role or task works in its own git worktree | `git --version` |
| Python 3.8+ | Runs the optional offline checker and the sample project | `python --version` |
| A model provider (only for `--real`) | Sub-agents call a model. Not needed for the dry runs | see [SETUP.md](../../SETUP.md) |

For `--real` runs only, configure the model with placeholders:

```
NOSPACE_MODEL_PROVIDER=anthropic
NOSPACE_MODEL_NAME=<a model you have access to>
ANTHROPIC_API_KEY=<your key>
```

See [SETUP.md](../../SETUP.md).

### What leaves your machine

- Dry runs (steps 2 to 5) make **no model calls** and send nothing anywhere.
- With `--real`, each sub-agent sends its prompt and the files it reads to the model provider you configured.
- Nothing is pushed. Each run leaves an integration branch in your local repo for you to review.

## 1. Create the sample project

Make a new folder, initialise git, and commit a single README. The commit gives the swarm a base branch.

bash:

```bash
mkdir unit-cli && cd unit-cli
git init -q -b main
printf "# unit-cli\n\nA tiny unit converter.\n" > README.md
git add README.md
git -c user.name=demo -c user.email=demo@example.invalid commit -q -m "init"
```

PowerShell:

```powershell
New-Item -ItemType Directory unit-cli | Out-Null; Set-Location unit-cli
git init -q -b main
Set-Content -Path README.md -Value "# unit-cli`n`nA tiny unit converter."
git add README.md
git -c user.name=demo -c user.email=demo@example.invalid commit -q -m "init"
```

Keep the working tree clean before each run. Both commands create branches and worktrees in your repo.

Copy `org.json` and `swarm.json` from this example folder into `unit-cli`, or refer to them by path. The commands below assume the files are in the `unit-cli` folder.

## 2. Check the org spec offline

`check_org.py` reads one local file and checks the structure: a charter, at least one worker, unique role IDs, a single planner, a budget, and valid `reports_to` and `gates` references. It uses only the Python standard library.

bash:

```bash
python check_org.py org.json
```

PowerShell:

```powershell
python check_org.py org.json
```

Expected, not a recorded run: `OK: org.json passes the local structure checks`.

The checker is a convenience. TOKN validates the spec again when you run it.

## 3. Dry-run the org (no model)

Without `--real`, `agentorg-run` uses a deterministic dry runner. It makes no model calls and needs no credentials.

bash:

```bash
tokn agentorg-run --org org.json --base main
```

PowerShell:

```powershell
tokn agentorg-run --org org.json --base main
```

Expected, not a recorded run: the output lists the three roles in dependency order (planner first, then implementer and reviewer), and reports an integration branch for review. Nothing is pushed.

## 4. Look at the task graph

`swarm-plan` reads `swarm.json` and prints the waves and critical path without running anything.

bash:

```bash
tokn swarm-plan --spec swarm.json
```

PowerShell:

```powershell
tokn swarm-plan --spec swarm.json
```

Expected, not a recorded run: wave 1 holds `convert-core` and `cli-parse` (they have no dependencies). Wave 2 holds `tests` and `integrate`, which need `convert-core` and `cli-parse`. Check the exact grouping against your output.

## 5. Dry-build the swarm (no model)

`swarm-build` gives each task its own git worktree and merges completed task branches onto an integration branch named `swarm-build/<id>`. Without `--real`, each task writes a marker file instead of calling a model. This shows the mechanics without spending tokens.

bash:

```bash
tokn swarm-build --spec swarm.json --base main
```

PowerShell:

```powershell
tokn swarm-build --spec swarm.json --base main
```

Expected, not a recorded run: the command reports the integration branch and each task's merge. Inspect it:

```bash
git branch --list "swarm-build/*"
git log --oneline -n 5 swarm-build/<id>
```

Replace `<id>` with the suffix the command printed. Dry-run markers are not code, so the project will not work yet. The purpose of this step is to see how the graph merges.

If a merge conflicts, the build halts. A failed task blocks the tasks that depend on it.

## 6. Optional: a real build with sub-agents

This step calls a model. Run it only after steps 2 to 5 look right and your model is configured (see step 0). Choose a model you have access to:

bash:

```bash
tokn swarm-build --spec swarm.json --base main --real --worker-model "<your model name>" --max-steps 8 --max-parallel 2
```

PowerShell:

```powershell
tokn swarm-build --spec swarm.json --base main --real --worker-model "<your model name>" --max-steps 8 --max-parallel 2
```

`--max-steps` caps each sub-agent's turns. `--max-parallel` caps concurrent tasks. Each task runs as a sub-agent in its own worktree.

Expected, not a recorded run: each task's branch gains commits, and the integration branch holds the merged `convert.py`, `cli.py`, and `test_convert.py`.

Verify it yourself:

```bash
cd unit-cli
git log --oneline swarm-build/<id>
python -m pytest -q
python cli.py 5 --from km --to m
```

Replace `<id>` with the integration branch name printed by the run. If pytest is not installed, run `python -m pip install pytest` first, outside this example.

To run one agent on one prompt without the org or swarm machinery, use `tokn agent-run` (hyphenated). There is no `agent run` subcommand.

## 7. Review and clean up

Nothing is pushed or merged into `main`. Review the integration branch, then decide what to keep:

```bash
git diff main..swarm-build/<id> --stat
git checkout main
```

If you want to delete the integration branch after review, use `git branch -D swarm-build/<id>` yourself. Do this only after you have reviewed it.

## What to look for

| Check | Expected |
|---|---|
| `check_org.py` | `OK` with no FAIL lines |
| `agentorg-run --org` dry | Three roles in dependency order; an integration branch reported |
| `swarm-plan` | Wave 1 has two tasks; wave 2 has two tasks |
| `swarm-build` dry | Integration branch created; no model calls |
| `--real` build (optional) | Tests pass; `cli.py` converts `5 km` to `5000.0` metres |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `org: at most one root planner` | More than one role has `kind: planner` | Keep one planner; change others to `worker` or `verifier` |
| `reports_to references unknown role` | A role ID is misspelled | Match `reports_to` entries to existing `id` values |
| `a budget is required` | No budget in the org | Add a top-level `budget` with `max_tokens` or `max_cost_usd` |
| Build halts on merge | Two tasks changed the same lines | Resolve the conflict on the integration branch, or split the tasks |
| `--base` not found | Repo has no `main` branch | Use your own branch name, or create `main` with step 1 |
| Worktree errors | Uncommitted changes in `unit-cli` | Commit or stash, then rerun |
| Real build fails on a model call | Model not configured | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME`, and the key in your shell |

## Related

- [SETUP.md](../../SETUP.md): provider and model configuration.
- [federation](../federation/README.md): running workers on more than one TOKN instance.
