# Example: Loops, find-and-refute, /ship-ready and /rewind

> "Keep fixing until the tests pass, attack the fix with skeptics, check it is shippable, and undo anything that went wrong."

This walkthrough covers recent interactive features (TOKN v0.3.60), on a tiny Python pricing module with one discount bug:

| Feature | What it does |
|---|---|
| `/loop define` | A goal with a check and a stop, driven until the check passes |
| `/loop 15m …`, `/loop auto …` | Re-run a prompt on an interval, or let the agent pace itself |
| find-and-refute workflow | Parallel hunters raise findings; independent skeptics try to refute each one |
| `/ship-ready` / `tokn ship-ready` | READY or NOT READY: working tree, format, vet, tests, secrets, runtime artifacts |
| `/rewind` | Restore files **and** conversation to before a prompt; `/rewind undo` reverses it |
| REPL keys | Ctrl+T, Shift+Tab, Ctrl+V / Alt+V, Esc, Ctrl+B, Esc Esc |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.60 or later | Ships these commands and keys | `tokn version` |
| Git | `/rewind` snapshots the working tree; `ship-ready` reads `git status` | `git --version` |
| Python 3.8+ | Creates the fixture and runs its tests | `python --version` |
| A model provider | Every step inside the REPL calls a model. `tokn ship-ready` (step 2) does not | see [SETUP.md](../../SETUP.md) |

### What leaves your machine

- `tokn ship-ready` is read-only and local. It never commits, pushes or changes files, and makes no model call. Only `--deep` (REPL only) starts a model-backed review.
- In the REPL, prompts and the files the agent reads go to the model provider you configured.
- `/rewind` snapshots are local git objects under `refs/tokn/checkpoints/`. Nothing is pushed.

## 1. Create the fixture repository

bash:

```bash
python make_repo.py "$HOME/tokn-loops-demo/pricing"
cd "$HOME/tokn-loops-demo/pricing"
python -m unittest
```

PowerShell:

```powershell
python make_repo.py "$HOME\tokn-loops-demo\pricing"
Set-Location "$HOME\tokn-loops-demo\pricing"
python -m unittest
```

Expected: `FAILED (failures=3)`. `apply_discount` subtracts the percentage as an amount instead of a percentage. The script also leaves an untracked `server.log` behind on purpose.

## 2. Is it ready to ship? (no model)

Run the read-only check from inside the repo. `--quick` skips tests and TOKN's own generator checks:

```bash
tokn ship-ready --quick
```

Expected (recorded on a fresh fixture):

```text
  [FAIL] runtime-artifacts  1 runtime artifact would be committed by `git add -A`.
         · server.log (log file, untracked)
Verdict: NOT READY — 1 failing, 1 warning, 5 skipped, 4 passed
```

The exit status is 1 for NOT READY and 0 for READY, so the command works as a CI gate. Warnings never block. Here, the warning is that the repo has no `v*` release tag yet.

Fix what it found, then check again:

bash:

```bash
rm server.log
echo "*.log" >> .gitignore
tokn ship-ready --quick
```

PowerShell:

```powershell
Remove-Item server.log
Add-Content .gitignore "*.log"
tokn ship-ready --quick
```

Expected: `Verdict: READY`. Note that `ship-ready` checks the working tree, not your tests: with `--quick`, the failing tests do not appear yet. Other useful forms:

```bash
tokn ship-ready --json
tokn ship-ready --only secrets,runtime-artifacts
```

Without `--quick`, `go test` runs on changed Go packages. TOKN's manifest, wiki, package-map and introspect checks are skipped outside a TOKN source checkout.

TOKN writes its own session logs under `.tokn/logs/` with a `.gitignore` beside them, so they can never be committed. That is why `ship-ready` does not report them.

## 3. Start the REPL

```bash
tokn agent-repl
```

All the remaining steps are typed at the REPL prompt. Lines starting with `/` are slash commands; everything else is a normal prompt.

## 4. A loop with a goal, a check and a stop

A loop must have a goal, a concrete check, and at least one stop condition, or TOKN refuses to run it. Here the check is the test suite. It stops after 5 iterations, or after 2 passes that make no progress.

```text
/loop define Fix apply_discount so every test in test_pricing.py passes, without editing the tests --check-cmd "python -m unittest" --max-iter 5 --no-progress 2
/loop run
/loop status
/loop report
```

Expected, not a recorded run: one or two iterations change `apply_discount` to `round(total * (100 - percent) / 100, 2)`, `python -m unittest` prints `OK`, and the loop stops on the passing check. `/loop report` shows each iteration and its check result.

Optional: `--worker <model> --checker <model>` gives the loop a strong model to do the work and a cheaper one to judge each pass.

## 5. Undo with /rewind

Before every prompt you type, TOKN saves a checkpoint: a working-tree snapshot plus the conversation position. Try it with a deliberately bad change:

```text
Rename apply_discount to discount everywhere, including the tests
/rewind
```

`/rewind` lists the checkpoints. Pick the one before the rename:

```text
/rewind <checkpoint ID>
```

The files and the conversation go back to that point, and files created after it are removed. Files that git ignores, `.git` and anything outside the session directory are never touched.

| Form | Effect |
|---|---|
| `/rewind <target> --code-only` | files only; keep the conversation |
| `/rewind <target> --chat-only` | conversation only; keep the files |
| `/rewind last` | files back to before the last risky tool call |
| `/rewind undo` | undo the rewind itself |
| Esc Esc on an empty prompt | opens the same list as a picker |

Run `python -m unittest` in another terminal to confirm the fixed `apply_discount` is back.

## 6. Find-and-refute: findings that survive skeptics

One review pass that says "looks fine" is not evidence. Ask for the workflow in your own words. It spends real tokens:

```text
Use a find-and-refute workflow to audit pricing.py for bugs and edge cases
```

The workflow runs in the background:

1. **Fan out.** Parallel hunters each look from one angle: correctness, edge cases, security and evidence.
2. **Verify.** Each distinct finding goes to a fresh skeptic that sees only that finding and tries to refute it.
3. **Synthesize.** Only surviving findings are reported. Inconclusive ones are listed under "Needs human review", and refuted ones are dropped.

Watch it and read the answer:

```text
/workflows list
/workflows status <run_id>
/workflows result <run_id>
```

Expected, not a recorded run: the answer ends with a tally such as `N finding(s) independently challenged — X survived, Y refuted, Z inconclusive`. Likely survivors for this module are float rounding of money values and negative quantities in `order_total`. A run that challenged nothing is labelled UNVERIFIED.

`/ship-ready --deep` runs the static checks from step 2, then starts the same workflow over your uncommitted diff.

## 7. Prompt loops: more time, not more eyes

A prompt loop re-runs the same prompt on a rhythm. A firing never interrupts your own prompt; it waits until the agent is free.

```text
/loop 15m Run python -m unittest and tell me only what changed since the last run
/loop auto Re-run the tests until they pass twice in a row, then summarise --max-runs 10
/loop list
/loop stop all
```

- An interval loop needs at least `1m`, with an `s`, `m`, `h` or `d` suffix.
- `/loop auto` lets the agent choose each delay, from 1 minute to 1 hour, or stop itself.
- Every loop stops after `--max-runs` (default 100) or 3 errors in a row.
- Prompt loops live as long as the REPL. For durable schedules, use `tokn agent-daemon`.

Rule of thumb: more **time**, use a loop. More **eyes**, use a workflow.

## 8. REPL keys

| Key | When | Effect |
|---|---|---|
| Ctrl+T | any time | show or hide the task checklist (plan graph and background tasks) |
| Shift+Tab | at the prompt | cycle the permission mode: default → accept_edits → plan → autopilot. Plan mode blocks write tools, and only you can leave it |
| Ctrl+V (macOS/Linux) / Alt+V (Windows, WSL) | at the prompt | paste a clipboard screenshot into the next prompt |
| Esc | during a run | stop immediately |
| Ctrl+B | during a run | send it to the background; watch it with `/tasks` |
| Esc Esc | on an empty prompt | open the `/rewind` picker |

Try Shift+Tab until the mode shows `plan`, then ask "How would you add a tax rate to order_total?" You get a design, and no file is changed.

Screenshot paste needs a clipboard helper. TOKN names the one that is missing and how to install it: PowerShell on Windows and WSL, `pngpaste` or `osascript` on macOS, `wl-paste` or `xclip` on Linux.

## What to look for

| Check | Expected |
|---|---|
| `python -m unittest` before | `FAILED (failures=3)` |
| `tokn ship-ready --quick` before | `NOT READY`, `server.log` listed, exit 1 |
| `tokn ship-ready --quick` after the fix | `READY`, exit 0 |
| `/loop run` | Stops when `python -m unittest` prints `OK` |
| `/rewind <checkpoint>` | The rename is gone from files and conversation |
| find-and-refute result | A tally of survived, refuted and inconclusive findings |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/loop define` refused | No check or no stop condition | Add `--check-cmd` and `--max-iter` or `--no-progress` |
| `ship-ready` reports a clean tree you know is dirty | The files are ignored by git | `git check-ignore -v <file>` shows which rule ignores it |
| `/rewind` brings back files but not the chat | The turn recorded no conversation | Expected for plain REPL turns; TOKN says so |
| Ctrl+V pastes text, not an image (Windows) | The terminal owns Ctrl+V | Use Alt+V |
| New prompt refused after Ctrl+B | The backgrounded run is still busy | Watch it with `/tasks`; prompts are refused, not queued |
| Workflow seems slow | Many hunters and skeptics run in parallel | Watch with `/workflows status <run_id>` |

## Related

- [loop-engineering](../loop-engineering/README.md): `/loop define` in more depth.
- [checkpoints](../checkpoints/README.md): checkpoints, `/undo` and `/rewind`.
- [session-review](../session-review/README.md): `/review` of an agent session.
