# Factory evidence tour

Follow TOKN's deterministic local Factory demo, then inspect its evidence. This
is a scripted replay, not an LLM service or a cloud deployment.

## What you'll learn

- How the offline demo moves a synthetic change through review, approval,
  delivery, and verification.
- How to inspect the generated repository and verify its evidence chain.
- How a dry-run migration template and model preflight differ from the demo.

## Before you start

| Requirement | Why |
|---|---|
| TOKN on `PATH` | Commands were verified with v0.3.118; check `tokn --help-all` for your build and the [download guide](../../README.md#1-download) |
| Git | Used by the demo's generated repository |
| PowerShell or Bash | Creates an isolated scratch workspace |
| Python 3 | Only for the optional receipt checker |
| Model, key, network | Not needed for the demo |

The root `.env.example` is reference-only. Do not source it or put real values
in it. All generated files belong in a fresh scratch folder, never this checkout.

## 1. Run the model-free demo

**PowerShell**

```powershell
$EX = (Get-Location).Path
$WORK = Join-Path $env:TEMP ("factory-evidence-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $WORK | Out-Null
$env:TOKN_NO_REGISTER = "1"
$env:TOKN_NO_UPDATE_CHECK = "1"
Set-Location $WORK
tokn factory demo --dir demo
```

**Bash**

```bash
EX="$PWD"
WORK="${TMPDIR:-$HOME}/factory-evidence-$$"
mkdir "$WORK"
export TOKN_NO_REGISTER=1 TOKN_NO_UPDATE_CHECK=1
cd "$WORK"
tokn factory demo --dir demo
```

The demo creates its repository under `demo/repo`. Inspect its JSON status and
verify the evidence chain.

**PowerShell**

```powershell
tokn factory status --repo-root demo\repo --json
tokn factory verify --repo-root demo\repo --json
```

**Bash**

```bash
tokn factory status --repo-root demo/repo --json
tokn factory verify --repo-root demo/repo --json
```

To run the optional checker, first copy it from `$EX` into the scratch folder:

```powershell
Copy-Item "$EX\check-receipt.py" .
python --version
python check-receipt.py demo\repo
```

```bash
cp "$EX/check-receipt.py" .
python --version
python check-receipt.py demo/repo
```

## 2. Explore the blank-project and model-binding paths

In a separate empty scratch directory, `tokn factory init --kind migration
--dry-run` prints a template without creating a configured project. Run
`tokn factory models --help` to see the preflight options. To preflight the
demo's generated bindings, run this from `demo/repo`.

**PowerShell**

```powershell
Set-Location demo\repo
tokn factory models --preflight --air-gap --json
```

**Bash**

```bash
cd demo/repo
tokn factory models --preflight --air-gap --json
```

This is a static/local preflight; an air-gap refusal is expected for a spec
that names remote role bindings. Do not approve or apply any changes as part
of this tour.

## What you should see

**Observed** with TOKN 0.3.118 in a fresh scratch workspace: the demo reported
13/13 steps complete. `factory verify` returned `ok: true` and a valid chain.
IDs, timestamps, and digests vary by run. `factory models` was confirmed with
`--help`; its optional preflight is not required for the worked run.

`expected/receipt-summary.json` is a compact, curated summary of the observed
result, not a captured runtime log. `expected/reference-receipt.json` records
the input digest scope, checker, status, and limitations.

## Troubleshooting

| Symptom | Action |
|---|---|
| `--dir` is not empty | Choose a new scratch path; do not overwrite existing work |
| Git is unavailable | Install Git, reopen the shell, and retry |
| No factory spec found | Run status/verify from `demo/repo`, not its parent |
| Preflight rejects a role | Expected in air-gap mode when the generated binding is remote |

## Cleanup

Remove only the scratch directory you created after inspecting it:

```powershell
Set-Location $HOME
Remove-Item -LiteralPath $WORK -Recurse
```

```bash
cd "$HOME"
rm -rf -- "$WORK"
```

## Try it

Read `challenge.md`, then explain which observed receipt proves that delivery
was reconciled rather than merely requested. Do not treat a successful demo
as evidence about a real deployment.
