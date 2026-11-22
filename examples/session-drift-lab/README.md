# Session drift lab

Grade synthetic, already-completed support sessions without making a new model
call, then compare a categorical disposition metric across cycles.

## What you'll learn

- Inspect the deterministic flywheel plan before approving compute.
- Grade local NDJSON traces with inference skipped.
- Detect a categorical-metric change across historical cycles.

## Before you start

| Requirement | Why |
|---|---|
| TOKN on `PATH` | Commands were verified with v0.3.118; check `tokn --help-all` for your build |
| PowerShell or Bash | Copies fixtures and creates report folders |
| Model, key, network | Not needed for session grading or drift |

`.env.example` is reference-only. Run from a fresh scratch copy; reports and
`.tokn/` state must not be written into this example folder.

## 1. Inspect the offline plan

Run this from the example folder to create a fresh scratch workspace.

**PowerShell**

```powershell
$EX = (Get-Location).Path
$WORK = Join-Path $env:TEMP ("session-drift-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $WORK | Out-Null
$env:TOKN_NO_REGISTER = "1"
$env:TOKN_NO_UPDATE_CHECK = "1"
Set-Location $WORK
tokn flywheel run --demo
```

**Bash**

```bash
EX="$PWD"
WORK="${TMPDIR:-$HOME}/session-drift-$$"
mkdir "$WORK"
export TOKN_NO_REGISTER=1 TOKN_NO_UPDATE_CHECK=1
cd "$WORK"
tokn flywheel run --demo
```

Read the plan and decline confirmation. This inspects the deterministic demo
plan; it does not run the cycle.

## 2. Stage and grade the synthetic sessions

Continue in the same shell so `$EX` and `$WORK` still refer to the example
folder and scratch workspace.

**PowerShell**

```powershell
Copy-Item "$EX\sessions","$EX\reference-cycles" $WORK -Recurse
Copy-Item "$EX\disposition.json" $WORK
Set-Location $WORK
$REPORTS = Join-Path $WORK "reports"
New-Item -ItemType Directory -Path $REPORTS -Force | Out-Null
Copy-Item "$WORK\reference-cycles\cycle-*.json" $REPORTS
tokn flywheel grade-sessions --sessions sessions --categorical disposition.json --target-metric review_disposition --out-dir reports --cycle 7
```

**Bash**

```bash
cp -R "$EX/sessions" "$EX/reference-cycles" "$WORK/"
cp "$EX/disposition.json" "$WORK/"
cd "$WORK"
mkdir reports
cp reference-cycles/cycle-*.json reports/
tokn flywheel grade-sessions --sessions sessions --categorical disposition.json --target-metric review_disposition --out-dir reports --cycle 7
```

One recorded answer intentionally has a different disposition. For a basic
substring check, add `--expect REVIEW`; that is only a liveness-style check,
not a correctness grade. The categorical rules in `disposition.json` count
`CLOSE` as a bad bucket. Repeat the categorical command with `--cycle 8` and
`--cycle 9`. These repeated runs exercise the window calculation; they are not
evidence of three independent production periods.

## 3. Detect the drift

```sh
tokn flywheel drift --reports reports --metric review_disposition --window 3 --json
```

The six included reference reports form the baseline history; cycles 7–9 are
the recent synthetic grading runs. The `--window 3` option requires at least
six compatible cycle reports. For optional paired comparison, inspect
`tokn flywheel compare --help-all` and approve its plan before supplying a
reviewed runs file.

## What you should see

**Observed** with TOKN 0.3.118: `flywheel run --demo` displayed an offline,
deterministic plan and stopped when confirmation was not supplied.

**Expected** from grading: inference is skipped because the inputs already
contain answers; the categorical report counts five `REVIEW` and one `CLOSE`.
The reference fixtures contain six compatible reports at a good fraction of
1.0; the repeated challenge cycles measure 5/6. Exact reports and drift output
are not captured runtime logs. `expected/reference-receipt.json` records the
fixture digest scope and limits.

## Troubleshooting

| Symptom | Action |
|---|---|
| No sessions found | Point `--sessions` at the directory containing `.ndjson` files |
| `review_disposition` missing | Confirm `disposition.json` is copied into scratch and passed with `--categorical` |
| Too few cycles | Include all six reference reports and cycles 7–9 |
| Session is skipped | Check that its stream has a `run.end` answer or `agent.message` |

## Cleanup

Remove only the scratch directory after review:

```powershell
Set-Location $HOME
Remove-Item -LiteralPath $WORK -Recurse
```

```bash
cd "$HOME"
rm -rf -- "$WORK"
```

## Try it

Make a scratch copy where the wrong disposition is replaced by `REVIEW`.
Grade it as a new cycle, then explain why metric recovery does not prove
that a human-approved disposition is correct.
