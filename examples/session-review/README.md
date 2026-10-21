# Example: review what an agent session did, with `/review`

This walkthrough runs one short agent session on a small synthetic repo that
has a planted bug, then uses the REPL's `/review` command to see what changed.

> *Fix the failing test in a tiny pricing module, then review what the agent
> changed before you accept it.*

| Feature | What it does here |
|---|---|
| **Agent run** (`tokn agent-run`) | Runs one task against the repo: the agent reads the tests, finds the bug and edits `pricing.py`. |
| **Session review** (`/review` in `tokn agent-repl`) | Reads the working tree with local `git status` and `git diff`. It groups changed files by domain, flags TODO and stub markers, and prints a checklist. |

Everything in `fixture/` is synthetic. The bug is one slice in `order_total`
that drops the last item.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with the `/review` subcommands shown here | `tokn version` |
| `git` | `/review` reads the working tree with `git status` and `git diff` | `git --version` |
| Python 3 (optional) | Runs the fixture's unit tests, so you can watch them fail first | `python --version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |

Trial and Community tiers both run this example. The features used here are
in the Community feature set (`core:*`, `workflow:*`). Model calls are billed
by your own provider, not by TOKN.

> **What leaves your machine.** The model provider receives the task and the
> files the agent reads or edits. `/review` runs only local `git` commands and
> prints; it makes no model call. Nothing is sent anywhere until step 3.

## 1. Copy the fixture into a scratch git repo

macOS / Linux:

```bash
cp -r examples/session-review/fixture ~/tokn-review-demo
cd ~/tokn-review-demo && git init -q && git add -A && git commit -qm "baseline with planted bug"
python3 -m unittest    # optional: watch the test fail before the session
```

Windows PowerShell:

```powershell
Copy-Item examples\session-review\fixture $HOME\tokn-review-demo -Recurse
Set-Location $HOME\tokn-review-demo; git init -q; git add -A; git commit -qm "baseline with planted bug"
python -m unittest    # optional: watch the test fail before the session
```

The baseline commit matters: `/review` compares the working tree with `HEAD`,
so the session's edits are what it reports.

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

## 3. Run a short agent session

`--no-confirm` auto-approves tool calls, which is acceptable in this scratch
repo. Leave it off if you want to approve each edit.

macOS / Linux:

```bash
tokn agent-run --repo-root . --prompt-file task.md --no-confirm --max-steps 8
```

Windows PowerShell:

```powershell
tokn agent-run --repo-root . --prompt-file task.md --no-confirm --max-steps 8
```

`task.md` is the copy in the scratch repo. It asks the agent to run the tests,
fix the bug with the smallest change, and not touch the tests.

## 4. Open the REPL and run `/review`

Stay in the same scratch repo:

Same command on macOS, Linux and Windows PowerShell:

```bash
tokn agent-repl --repo-root .
```

At the prompt, run:

```text
/review
/review files
/review stubs
/review checklist
```

`/review` with no argument is `summary`. The other subcommands are `diff`,
`files`, `checklist`, `stubs` and `agent`. Run `/help review` to see them.

## 5. Read the result

Expected output, from the subcommand names and headings in
`environment-manager/internal/agent/commands/review_cmd.go`:

| Command | What it prints | Expected here |
|---|---|---|
| `/review` (summary) | Header `Session Review — Summary`, a line `Changed files: N across M domain(s)`, a per-domain table, then `Post-feature checklist` | `pricing.py` is the changed file; test edits would show here too |
| `/review files` | Header `Session Review — Files by Domain` | The same file, grouped |
| `/review diff` | The `git diff HEAD` text | The one-line fix to `order_total`, for example iterating over the whole list |
| `/review stubs` | Header `Session Review — Stub / TODO scan` | No hits unless the agent left a `TODO` or similar marker |
| `/review checklist` | Header `Post-feature Checklist (AGENTS.md)` | Items written for TOKN's own repo. They are informational in this demo repo. |
| `/review agent` | Prints a suggested review prompt | It does **not** start a sub-agent. The REPL only prepares the prompt for you to copy. |

If the agent changed nothing, the summary says `No changes detected in working
tree.`

Check the fix yourself:

```bash
python3 -m unittest    # or: python -m unittest
```

All tests should pass. If they do not, the review still tells you what changed.

### What to look for

- **Scope.** Did the session touch only `pricing.py`? Test edits in the
  summary are a red flag, because the task said not to change the tests.
- **The diff.** `/review diff` should show a small change to `order_total`
  and nothing else.
- **Stubs.** `/review stubs` shows whether the agent left a `TODO` or
  placeholder in code it touched.
- **Checklist items.** They describe TOKN's own release checklist. Ignore
  them in a demo repo.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Not a git repository` from `/review` | Run step 1's `git init` in the scratch repo, then start the REPL from that folder |
| `No changes detected` after a session | The agent did not edit files. Check the `agent-run` output, or run it again with `--max-steps 12` |
| `git status failed` | Check `git --version` and that the repo is not locked by another process |
| The agent cannot run `python -m unittest` | Install Python 3, or change the task to ask for a different test command |
| `/review` shows nothing new after a second session | `/review` reads the working tree against `HEAD`. Commit the first session's fix if you want to review the second session on its own |
