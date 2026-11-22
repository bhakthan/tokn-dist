# Migration parity lab

Port a tiny event formatter without changing per-order event order. The
fixtures are fictional and the scripts run as ordinary local processes; TOKN
does not sandbox them.

## What you'll learn

- Record a legacy command's output as a fixture corpus.
- Detect a regression with the `events` oracle and ratchet known gaps.
- Keep the fixture count stable and inspect the corpus digest.

## Before you start

| Requirement | Why |
|---|---|
| TOKN on `PATH` | Commands were verified with v0.3.118; check `tokn --help-all` for your build |
| Python 3 | Runs the small fixture scripts |
| PowerShell or Bash | Copies the examples to a scratch workspace |
| Model, key, network | Not needed |

`.env.example` is reference-only. Do not source it. Keep every generated
fixture, ledger, and `.tokn/` file in a fresh scratch workspace.

## 1. Stage the synthetic fixture

Run this from this example folder.

**PowerShell**

```powershell
$EX = (Get-Location).Path
$WORK = Join-Path $env:TEMP ("migration-parity-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $WORK | Out-Null
$env:TOKN_NO_REGISTER = "1"
$env:TOKN_NO_UPDATE_CHECK = "1"
python --version
Copy-Item "$EX\inputs" $WORK -Recurse
Copy-Item "$EX\legacy.py","$EX\target.py" $WORK
Set-Location $WORK
```

**Bash**

```bash
EX="$PWD"
WORK="${TMPDIR:-$HOME}/migration-parity-$$"
mkdir "$WORK"
export TOKN_NO_REGISTER=1 TOKN_NO_UPDATE_CHECK=1
python --version
cp -R "$EX/inputs" "$WORK/"
cp "$EX/legacy.py" "$EX/target.py" "$WORK/"
cd "$WORK"
```

## 2. Record, compare, and ratchet

```sh
tokn factory init --kind migration --dry-run
tokn migrate oracles
tokn migrate record --command "python legacy.py {input}" --inputs inputs --out fixtures.json --oracle events
tokn migrate verify --fixtures fixtures.json --command "python target.py {input}" --oracle events --event-key order_id --expect-cases 3 --json
tokn migrate ratchet --fixtures fixtures.json --command "python target.py {input}" --oracle events --event-key order_id --ledger gaps.json --init --reason "synthetic order-event regression" --json
```

The first verification is expected to return a nonzero status: the supplied
candidate reverses the order of events within each order. Compare it with
`reference/target-fixed.py` from outside the candidate's working directory,
then copy that file over `target.py` in the scratch workspace and run:

```sh
tokn migrate ratchet --fixtures fixtures.json --command "python target.py {input}" --oracle events --event-key order_id --ledger gaps.json --tighten --json
```

The initial ledger records known gaps; `--tighten` closes them only after the
candidate passes. A corpus digest identifies the recorded inputs and outputs;
approve and pin a digest before using a corpus for a real migration.
The fixed reference script is visible to the learner; do not include it in any
agent's read scope when evaluating an automated candidate.

## 3. Guided domain-oracle variants

Copy either `guided/atmchem` or `guided/batterypass` to a new scratch folder.
From that folder, use the matching recorder and candidate:

```sh
tokn migrate record --command "python legacy.py {input}" --inputs inputs --out fixtures.json --oracle atmchem
tokn migrate verify --fixtures fixtures.json --command "python candidate.py {input}" --oracle atmchem --json
```

For the passport-schema variant, use `--oracle batterypass` for recording and:

```sh
tokn migrate verify --fixtures fixtures.json --command "python candidate.py {input}" --oracle batterypass --max-severity patch --json
```

These are synthetic starter comparisons, not evidence that a migration is
regulatorily compliant. The `atmchem` oracle checks paired model-output series;
the `batterypass` oracle classifies JSON Schema changes. Read the oracle list
and your domain's acceptance policy before changing tolerances.

## What you should see

**Observed** with the event fixture in TOKN 0.3.118: recording created three
cases; the reversed candidate mismatched all three; `--init` recorded three
gaps; the fixed-order candidate matched all three and `--tighten` closed them.
The corpus digest and case IDs vary with fixture bytes. The domain-oracle
variants are guided exercises; their outputs are **expected**, not recorded
transcripts. `expected/reference-receipt.json` records the input digest scope
and limitations.

## Troubleshooting

| Symptom | Action |
|---|---|
| `python` is unavailable | Install Python 3 and confirm `python --version` |
| `--expect-cases` fails | Re-record only after reviewing and approving the corpus change |
| `verify` reports errors, not mismatches | Check the script's exit status and JSON Lines output |
| A command cannot find its input | Run it from the scratch folder that contains `inputs/` |

## Cleanup

After review, remove only `$WORK`:

```powershell
Set-Location $HOME
Remove-Item -LiteralPath $WORK -Recurse
```

```bash
cd "$HOME"
rm -rf -- "$WORK"
```

## Try it

In a new scratch copy, add one event and update the approved corpus. Explain
why an unchanged count does not prove that the corpus contents are unchanged.
