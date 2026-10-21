# Example: Loop engineering (lead-optimisation style shortlist)

> "Shortlist five candidates from properties.csv that meet every criterion in scoring.json, rank them by composite score, and keep going until a checker says the shortlist is right."

This example runs TOKN's loop engine on a synthetic screening problem. The "chemistry" is abstract: 16 invented candidates with two index values and a flag. There are no real compounds, no structures, and no synthesis routes. The point is the loop shape: a **goal**, a **check**, and a **stop**.

| Piece | In this example |
|---|---|
| Goal | Write `shortlist.csv` with the top five qualifying candidates (`prompt.md`) |
| Check | `python check_shortlist.py` recomputes every row and exits 0 only on PASS |
| Stop | `--max-iter 8`, `--no-progress 3`, `--max-wall 15m` |
| Inputs | `properties.csv` (16 rows), `scoring.json` (weights and thresholds) |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57+ | Ships the `/loop` command | `tokn version` |
| Trial or Community | `/loop` is not a domain mode, so no trial is required | `tokn license status` |
| An LLM provider configured | The loop's Worker and Checker are model calls | See step 2 |
| Python 3 (stdlib only) | Runs `check_shortlist.py`; no packages needed | `python --version` (macOS/Linux: `python3 --version`) |

## What leaves your machine

- The Worker and Checker prompts, plus the file contents the agent reads (`properties.csv`, `scoring.json`), go to the model provider you configure.
- `check_shortlist.py` runs locally and makes no network calls.

## 1. Copy the example

Copy this folder somewhere writable, so the loop can write `shortlist.csv` without touching the distribution repo.

bash:
```bash
cp -r examples/loop-engineering ~/loop-demo
cd ~/loop-demo
```

PowerShell:
```powershell
Copy-Item -Recurse examples\loop-engineering $HOME\loop-demo
Set-Location $HOME\loop-demo
```

## 2. Configure the LLM

Set your provider and key. See [../../SETUP.md](../../SETUP.md) for every supported provider.

bash:
```bash
export NOSPACE_MODEL_PROVIDER=<your provider>
export NOSPACE_MODEL_NAME=<your model>
export ANTHROPIC_API_KEY=<your key>
```

PowerShell:
```powershell
$env:NOSPACE_MODEL_PROVIDER = "<your provider>"
$env:NOSPACE_MODEL_NAME = "<your model>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

## 3. Start the REPL

The loop is a slash command inside the interactive REPL. Start it from the copied folder:

```
tokn agent-repl
```

`agent-repl` accepts `--repo-root` (default `.`). Run it from the copied folder, or pass the folder explicitly:

bash:
```bash
tokn agent-repl --repo-root .
```

PowerShell:
```powershell
tokn agent-repl --repo-root .
```

## 4. Define and run the loop

At the REPL prompt, define the loop. The goal is the task from `prompt.md`:

```
/loop define Shortlist five candidates from properties.csv that meet every criterion in scoring.json and write them to shortlist.csv --check-cmd "python check_shortlist.py" --max-iter 8 --no-progress 3 --max-wall 15m
```

On macOS or Linux, use `python3` in the `--check-cmd` value.

Then start it and watch it:

```
/loop run
/loop status
/loop report
```

`/loop clear` discards the definition.

Notes on the flags, all checked against `loop_cmd.go`:
- `--check-cmd` runs through `cmd /C` on Windows and `sh -c` elsewhere. The value ends at the next `--` token, so keep the command free of flags.
- `--max-wall` takes a Go duration such as `15m`.
- The check passes on exit code 0. `--pass-pattern` is an alternative and is not used here.
- The command is run from the REPL's working directory. This is an assumption, so run the REPL from the copied folder.

## 5. Check the result

Run the checker yourself, outside the loop:

bash:
```bash
python check_shortlist.py
```

PowerShell:
```powershell
python check_shortlist.py
```

The expected outcome is a single line starting with `PASS`. The best five by composite score are:

| Rank | candidate_id | composite_score (0.6 × activity + 0.4 × stability) |
|---|---|---|
| 1 | CAND-006 | 7.86 |
| 2 | CAND-010 | 7.64 |
| 3 | CAND-014 | 7.56 |
| 4 | CAND-001 | 7.52 |
| 5 | CAND-012 | 7.08 |

These values were computed by hand from the input file. The loop has **not been run**, so no model output is shown here.

Eight candidates qualify, and three are excluded by rank: CAND-005 (7.04), CAND-016 (6.94), and CAND-007 (6.60). Eight are excluded by a criterion: CAND-002, 003, 004, 008, 009, 011, 013, and 015.

## What to look for

- **The check is the only judge.** The Worker can claim success, but the loop only stops on a passing check or a stop condition. Read `/loop report` to see which one fired.
- **The check is only as good as its inputs.** The Worker could edit `properties.csv` or `scoring.json` to make the check pass. `prompt.md` forbids this, but nothing enforces it. Review the files after a run.
- **Stop conditions bound cost.** `--max-iter` caps attempts, `--no-progress` stops after repeated identical failures, and `--max-wall` caps elapsed time.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/loop` is not recognised | The REPL is older than v0.3.57 | Run `tokn version`, then update |
| `python` not found on macOS or Linux | The check uses `python` | Use `python3` in `--check-cmd` |
| The check always fails with "not found" | The REPL started outside the copied folder | Restart `tokn agent-repl` from `~/loop-demo` |
| `--check-cmd` value cut short | The value contains a `--` flag | Keep the check command free of flags |
| `--max-wall` rejected | Value is not a Go duration | Use `15m`, `90s`, and so on |
| Loop stops after `--no-progress` | The same failing result repeated | Read `/loop report`, then clarify `prompt.md` |
