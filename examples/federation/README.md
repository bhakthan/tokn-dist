# Example: Fan a task out across two TOKN workers

> "Run one change across two independent TOKN workers and collect what they did."

This walkthrough runs two TOKN instances on one machine, then uses a third TOKN process as the **leader** to split a small job between them. You will see the wave schedule, the per-worker results, and how to bring the work back into a repository.

Everything here uses a tiny synthetic repository that you create yourself.

## What this example shows

| Capability | What you will do | Command |
|---|---|---|
| Worker role | Serve a TOKN agent over HTTP on localhost | `tokn agent-worker` |
| Leader role | Health-check workers, dispatch tasks in waves, collect results | `tokn agent-leader` |
| Work plan | Describe tasks and their dependencies as JSON | `--plan plan.json` |
| Seeding | Give remote workers a copy of your committed repo | `--seed-repo` |
| Applying results | Stage worker changes back into a repo (no commit) | `--apply-to` |
| Dry run | Check worker health and the schedule without dispatching | `--dry-run` |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Ships the `agent-worker` and `agent-leader` commands | `tokn version` |
| Licence tier: **Community** | These commands are not behind a premium mode gate; no trial needed | `tokn license` |
| Git | Workers run in git worktrees; the sample repo must be committed | `git --version` |
| A model provider for the workers | Each worker runs an agent, which calls a model | see [SETUP.md](../../SETUP.md) |
| `openssl` (optional) | Generates the shared token; PowerShell has a built-in fallback | `openssl version` |

Configure the model on each worker through environment variables. Use placeholders only:

```
NOSPACE_MODEL_PROVIDER=anthropic
NOSPACE_MODEL_NAME=<a model you have access to>
ANTHROPIC_API_KEY=<your key>
```

Put these in your shell before starting each worker, or in a `.env` file that TOKN reads from the repository root. See [SETUP.md](../../SETUP.md).

### What leaves your machine

- Each worker sends its agent prompts and file contents to the model provider you configured.
- The leader sends task prompts and, with `--seed-repo`, a copy of the **committed** files of your repo to each worker. Both workers are on `127.0.0.1` here, so nothing crosses the network.
- Nothing is pushed or committed by these commands.

## 1. Create the synthetic repository

Create a new folder, make it a git repository, and commit two small files.

`convert.py`:

```python
def convert_length(value, unit):
    factors = {"km": 1000.0, "m": 1.0, "cm": 0.01}
    return value * factors[unit]
```

`greet.py`:

```python
def greet(name):
    return "Hello, " + name
```

bash:

```bash
mkdir fanout-sample && cd fanout-sample
git init -q
# create convert.py and greet.py with the contents above
git add convert.py greet.py
git -c user.name=demo -c user.email=demo@example.invalid commit -q -m "sample"
cd ..
```

PowerShell:

```powershell
New-Item -ItemType Directory fanout-sample | Out-Null; Set-Location fanout-sample
git init -q
# create convert.py and greet.py with the contents above
git add convert.py greet.py
git -c user.name=demo -c user.email=demo@example.invalid commit -q -m "sample"
Set-Location ..
```

Keep the working tree clean. `--apply-to` refuses to stage into a repo with uncommitted changes.

Steps 3 to 6 assume your terminal is in the folder that **contains** `fanout-sample`.

## 2. Create a shared worker token

Both workers and the leader must share one secret, passed in the `TOKN_WORKER_TOKEN` environment variable. There is no unauthenticated mode.

bash:

```bash
export TOKN_WORKER_TOKEN="$(openssl rand -base64 32)"
```

PowerShell (uses the cryptographic random number generator):

```powershell
$b = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
$env:TOKN_WORKER_TOKEN = [Convert]::ToBase64String($b)
```

Set the variable in **every** terminal you use below. Never write the token into a file you commit.

## 3. Start two workers (two terminals)

Terminal A (worker `a`, port 8099):

bash:

```bash
export TOKN_WORKER_TOKEN="<same value as step 2>"
tokn agent-worker --listen 127.0.0.1:8099 --worker-id a --repo-root ./fanout-sample --max-concurrent 1
```

PowerShell:

```powershell
$env:TOKN_WORKER_TOKEN = "<same value as step 2>"
tokn agent-worker --listen 127.0.0.1:8099 --worker-id a --repo-root .\fanout-sample --max-concurrent 1
```

Terminal B (worker `b`, port 8100): the same command with `--listen 127.0.0.1:8100` and `--worker-id b`.

Use `127.0.0.1` so each worker only accepts connections from this machine. Leave both terminals running.

Expected, not a recorded run: each terminal logs that it is listening, and the process stays in the foreground.

## 4. Write the work plan

Create `plan.json` next to the sample repo. Two tasks run in the first wave because they do not depend on each other. The third runs in a second wave after both finish.

```json
{
  "objective": "Add a one-line docstring to each module function",
  "rationale": "Synthetic example: two independent edits, then a check",
  "repo_root": ".",
  "generated_at": "2025-01-01T00:00:00Z",
  "tasks": [
    {
      "id": "docs-convert",
      "type": "agent_run",
      "mode": "default",
      "title": "Document convert_length",
      "prompt": "Add a one-line docstring to convert_length in convert.py. Change nothing else.",
      "repo_root": ".",
      "priority": 1,
      "created_at": "2025-01-01T00:00:00Z",
      "max_retries": 0
    },
    {
      "id": "docs-greet",
      "type": "agent_run",
      "mode": "default",
      "title": "Document greet",
      "prompt": "Add a one-line docstring to greet in greet.py. Change nothing else.",
      "repo_root": ".",
      "priority": 1,
      "created_at": "2025-01-01T00:00:00Z",
      "max_retries": 0
    },
    {
      "id": "final-check",
      "type": "agent_run",
      "mode": "default",
      "title": "Check both docstrings",
      "prompt": "Confirm convert_length and greet each have a docstring. Make no edits.",
      "repo_root": ".",
      "priority": 1,
      "created_at": "2025-01-01T00:00:00Z",
      "max_retries": 0,
      "depends_on": ["docs-convert", "docs-greet"]
    }
  ]
}
```

Notes:
- Task IDs must not contain commas.
- `depends_on` is the edge list. Tasks with no edges form the first wave.
- The plan is validated when loaded. You can also generate one with `tokn workplan`, which needs a model; this example writes it by hand so you do not need one for planning.

## 5. Health-check and preview the schedule (dry run)

Run this from the leader's terminal. It checks each worker and prints the wave schedule without dispatching anything.

bash:

```bash
cd fanout-sample
tokn agent-leader \
  --worker a=http://127.0.0.1:8099 \
  --worker b=http://127.0.0.1:8100 \
  --plan ../plan.json \
  --dry-run
```

PowerShell:

```powershell
Set-Location fanout-sample
tokn agent-leader `
  --worker a=http://127.0.0.1:8099 `
  --worker b=http://127.0.0.1:8100 `
  --plan ..\plan.json `
  --dry-run
```

Expected, not a recorded run: both workers report healthy, and the output lists wave 1 as `docs-convert` and `docs-greet`, and wave 2 as `final-check`.

If a worker fails the health check, the leader stops before dispatch. Fix that worker first.

## 6. Run the fan-out

Seed the workers with the committed repo, let them run, and stage the results back into the repo. The JSON summary goes to `results.json`.

bash:

```bash
tokn agent-leader \
  --worker a=http://127.0.0.1:8099 \
  --worker b=http://127.0.0.1:8100 \
  --plan ../plan.json \
  --seed-repo . \
  --apply-to . \
  --out ../results.json
```

PowerShell:

```powershell
tokn agent-leader `
  --worker a=http://127.0.0.1:8099 `
  --worker b=http://127.0.0.1:8100 `
  --plan ..\plan.json `
  --seed-repo . `
  --apply-to . `
  --out ..\results.json
```

Expected, not a recorded run: the leader prints progress per task, then a final summary. `results.json` lists each task with its status and worker ID.

### Important: what the workers see and what comes back

- **Remote workers start from an empty tree.** Without `--seed-repo`, a worker does not see your files. It only gets the task prompt. `--seed-repo` ships the **git-tracked, committed** content of the repo. Untracked and gitignored files are not sent, and the repo must have at least one commit.
- **Results land in your repo only with `--apply-to`.** It stages the workers' changes into the target repo and does not commit or push. It refuses if the target has uncommitted changes.
- **Without `--apply-to`, the only output is the `--out` JSON.** The repo stays unchanged.
- `--apply-partial` also stages work from failed tasks. It is off by default; leave it off here.

## 7. Review the result

bash:

```bash
cd fanout-sample
git status --short
git diff --staged
```

PowerShell:

```powershell
Set-Location fanout-sample
git status --short
git diff --staged
```

You should see one docstring added to each file, staged and not committed. Review, then commit it yourself or discard it with `git restore --staged . && git restore .`.

## 8. Optional: host a worker in a cloud container service

You can run a worker on any container platform, so the leader on your laptop can reach it over HTTPS. The steps are generic. Substitute your own values:

1. Write a Dockerfile that installs TOKN and starts a worker. Configure the listen address the way your platform's ingress expects; the leader only ever talks to the public HTTPS address.
2. Build and push the image to `<your-registry>`.
3. Deploy it to your container service, and set `TOKN_WORKER_TOKEN` and the model variables as secrets. Never bake them into the image.
4. Note the public HTTPS address of the app as `<your-app-url>`.
5. Point the leader at it, with the same token:

```bash
tokn agent-leader --worker cloud=https://<your-app-url> --plan ../plan.json --seed-repo . --apply-to . --out ../results.json
```

Remote workers are reached over the network, so the same rules apply: the leader sends a copy of the committed repo, and results return only with `--apply-to`.

## What to look for

| Check | Expected |
|---|---|
| `--dry-run` | Both workers healthy; wave 1 has two tasks, wave 2 has one |
| `results.json` | Three task entries, each with a status and worker ID |
| `git status` after `--apply-to` | Two modified files, staged, no new commit |
| Worker terminals | One task at a time per worker (`--max-concurrent 1`) |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Health check fails with unauthorized | Token differs between leader and a worker | Set the same `TOKN_WORKER_TOKEN` in every terminal |
| `--worker` rejected | URL missing `http://` or `https://` | Include the scheme, e.g. `a=http://127.0.0.1:8099` |
| Workers edit nothing | Workers started without `--seed-repo` | Pass `--seed-repo .` on the leader |
| `--apply-to` refuses | Target repo has uncommitted changes | Commit or stash, then rerun |
| Plan rejected | Duplicate ID, unknown `depends_on`, cycle, or comma in ID | Fix `plan.json`; rerun `--dry-run` |
| Task timeout | Model slow or unreachable | Raise `--task-timeout` on the leader, check the worker's model settings |
| Port in use | Another process on 8099 or 8100 | Choose other localhost ports on both worker and leader |

## Related

- [SETUP.md](../../SETUP.md): provider and model configuration.
- For a single-agent run on one repo, see `tokn agent-run` (hyphenated).
