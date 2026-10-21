# Example: let TOKN checkpoint its own work, then roll back a bad edit

This walkthrough covers one realistic mistake and its recovery:

> *Add a comment to `average()`. Then ask for a change that turns out to be
> wrong. Look at the checkpoint history, and undo the bad edit without losing
> the good one.*

TOKN saves a checkpoint each time a tool result comes back in a run. You can
list them, look inside one, and roll files back. The example uses a tiny
Python module with a unit test, so the bad edit is easy to spot.

| Feature | What it does here |
|---|---|
| **Automatic checkpoints** | Saved after each tool result, under `.nospace/checkpoints/` in the repo. |
| **`/checkpoint`** | Lists checkpoints, shows one in detail, and can save one by hand. |
| **`/undo`** | Restores tracked files to the last git commit. It can take a single file. |
| **`/rewind`** | Rolls the conversation back to a checkpoint. `--code` also restores files from that checkpoint. |

All code in this example is synthetic.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with this walkthrough's commands | `tokn version` |
| `git` | Checkpoints and `/undo` work through git | `git --version` |
| Python 3 | Runs the tiny unit test | `python3 --version` (macOS / Linux) or `python --version` (PowerShell) |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |

Checkpoints and `/undo` are **Community** features, so the free tier runs this
example. Model calls are billed by your own provider.

> **What leaves your machine.** Your prompts and the file contents the agent
> reads or edits go to your model provider. Checkpoints are written only to
> `.nospace/` inside the scratch repo, on your disk.

## 1. Create a scratch repository

Copy the fixture into a folder outside this repo and commit the starting state.
The commit matters: `/undo` restores to the last commit.

macOS / Linux:

```bash
cp -r examples/checkpoints/fixture ~/tokn-ckpt-demo
cd ~/tokn-ckpt-demo && git init -q && git add -A && git commit -qm "start"
python3 -m unittest -q && echo "tests pass"
```

Windows PowerShell:

```powershell
Copy-Item examples\checkpoints\fixture $HOME\tokn-ckpt-demo -Recurse
Set-Location $HOME\tokn-ckpt-demo
git init -q; git add -A; git commit -qm "start"
python -m unittest -q
```

You now have `calc.py` (one function) and `test_calc.py` (two tests, one of
which checks that `average` is the **mean**, not the median).

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

## 3. Good edit, then commit it

Open the REPL in the scratch repo:

```bash
tokn agent-repl --repo-root ~/tokn-ckpt-demo
```

```powershell
tokn agent-repl --repo-root $HOME\tokn-ckpt-demo
```

At the prompt, ask for a small, safe change:

```text
Add a one-line comment above average() in calc.py saying that it returns the mean.
```

TOKN edits the file. A checkpoint is saved after the tool result. Leave the
REPL open, and in a second terminal commit the good state:

```bash
cd ~/tokn-ckpt-demo && git commit -qam "comment on average" && python3 -m unittest -q && echo "tests pass"
```

## 4. Bad edit

Back in the REPL, ask for a change that conflicts with the test:

```text
Change average() so it returns the median instead of the mean.
```

TOKN edits `calc.py`. Another checkpoint is saved. Check the damage in the
second terminal:

```bash
cd ~/tokn-ckpt-demo && git diff --stat && python3 -m unittest -q
```

`test_mean_is_not_median` now fails, because the median of `[1, 2, 3, 10]` is
2.5, not 4.

## 5. Look at the checkpoint history

In the REPL:

```text
/checkpoint
```

You should see two or more checkpoints, one per tool result, each with a short
ID such as `cp-1`, `cp-2` and so on. Show the newest one in detail:

```text
/checkpoint cp-2
```

The detail view shows what was saved at that point, such as the conversation
state and the files it tracked.

## 6. Roll back the bad edit

Restore just the broken file to the last good commit:

```text
/undo calc.py
```

In the second terminal, confirm the good state is back:

```bash
cd ~/tokn-ckpt-demo && git status --short && python3 -m unittest -q && echo "tests pass"
```

`calc.py` matches the commit, and the tests pass again. The comment from step 3
is still there, because it was committed.

## 7. Optional: rewind the conversation too

`/rewind` takes you back to an earlier checkpoint. Without `--code` it restores
the conversation only, and the files are left as they are:

```text
/rewind cp-1
```

Adding `--code` also restores files from that checkpoint. That restore uses a
git stash snapshot, which is only saved when the working tree had changes at
the time. This example does not depend on it. If you try it, check `git status`
afterwards.

Type `/exit` when you are done.

## What to look for

- **Checkpoints are automatic.** You did not ask for one. Each tool result
  added one to `/checkpoint`.
- **`/undo` goes back to the last commit, not to a checkpoint.** That is why
  step 3 commits the good work first. Without the commit, `/undo calc.py`
  would also throw away the comment.
- **Checkpoints stay local.** They live in `.nospace/` in the scratch repo.
  `git status` shows `.nospace/` as untracked. Do not commit it: it is
  runtime data, not source.
- **Retention is bounded.** Checkpoints are capped (100 by default) and expire
  after 30 days by default. `/checkpoint clean` and `/checkpoint prune` remove
  old ones.
- **`/checkpoint save [description]`** saves one by hand, for example before
  you ask for a risky refactor.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/checkpoint` says "No checkpoints saved yet" | Nothing was edited, or the run had no tool calls | Run the step 3 prompt again |
| `/undo` says it is not a git repository | Wrong `--repo-root`, or no `git init` | Run step 1 again in the scratch folder |
| `/undo` reverted more than you wanted | Work was not committed before the undo | Use `/checkpoint` and `git` history, then commit before the next run |
| `--code` says no code snapshot is available | The working tree was clean when the checkpoint was saved | Use `/undo` instead |
| `git status` shows `.nospace/` | Expected: checkpoint data | Add `.nospace/` to `.gitignore` in the scratch repo, or leave it untracked |

Expected outcomes above are based on the source code and tests. They are
**expected, not a recorded run.**
