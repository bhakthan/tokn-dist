# Governed judgments: the guard rails

This folder holds the offline judgment walkthrough. The main cases (clean and
error runs) are described in the top-level [examples README](../README.md#judgments).
This page adds the behaviours those cases do not show. Every command runs offline
with the local `rules` provider, so no API key is needed.

Run these from a scratch directory you own. The commands write files there.
Copy the request files in with the bundle.

```bash
cp examples/judgments/*.json ~/judgments-run/ && cd ~/judgments-run
tokn judgments example > bundle.json
```

```powershell
Copy-Item examples\judgments\*.json $HOME\judgments-run\; Set-Location $HOME\judgments-run
tokn judgments example > bundle.json
```

## Judgments never authorise an action

Every envelope reports `decision.applied`. It is always `false`. A judgment is a
recommendation, and nothing in TOKN acts on it automatically.

```bash
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --air-gap
```

```powershell
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --air-gap
```

Expected, not a recorded run: the output contains `"applied": false`.

## Enforced mode is refused

Only `disabled`, `shadow`, and `advisory` are accepted. Asking for `enforced`
exits with an error that says enforced authority is not supported.

```bash
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode enforced --air-gap; echo "exit=$?"
```

```powershell
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode enforced --air-gap; "exit=$LASTEXITCODE"
```

Expected, not a recorded run: a non-zero exit code.

## External providers are off by default

With `--air-gap`, the external adapter is forbidden even if you also pass
`--allow-external`. Without `--allow-external`, an external provider is refused.
The rules provider always works.

```bash
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --allow-external --air-gap; echo "exit=$?"
```

```powershell
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --allow-external --air-gap; "exit=$LASTEXITCODE"
```

Expected, not a recorded run: a non-zero exit code.

## Disabled mode needs nothing

`--mode disabled` skips judgment and needs no external provider. Use it to confirm
that a configuration works before you turn judgments on.

```bash
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode disabled --air-gap
```

```powershell
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode disabled --air-gap
```

## Audit files are created once and never overwritten

`--audit-file` writes hashes and references, not the raw state. The path must be
absolute and must not exist. TOKN creates the file with exclusive-create, so a
second run against the same path fails and leaves the first record unchanged.

```bash
AUDIT=/absolute/path/to/new/judgment-audit.jsonl
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --air-gap --audit-file "$AUDIT"; echo "first=$?"
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --air-gap --audit-file "$AUDIT"; echo "second=$?"
```

```powershell
$Audit = "C:\absolute\path\to\new\judgment-audit.jsonl"
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --air-gap --audit-file $Audit; "first=$LASTEXITCODE"
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --air-gap --audit-file $Audit; "second=$LASTEXITCODE"
```

Expected, not a recorded run: `first=0`, then `second` is non-zero, and the file
from the first run is unchanged.

## Duplicate keys are refused

`request-duplicate-key.json` repeats the `tool_errors` key with two values. Strict
JSON parsing rejects it, because a silent last-value-wins would let a bad
request pass.

```bash
tokn judgments evaluate --bundle bundle.json --file request-duplicate-key.json --mode advisory --air-gap; echo "exit=$?"
```

```powershell
tokn judgments evaluate --bundle bundle.json --file request-duplicate-key.json --mode advisory --air-gap; "exit=$LASTEXITCODE"
```

Expected, not a recorded run: a non-zero exit code and an error about a duplicate
input key.

## What to look for

| Behaviour | Pass signal |
|---|---|
| Advisory only | `"applied": false` in every envelope |
| No enforcement | `--mode enforced` exits non-zero |
| No silent egress | External provider refused with `--air-gap` or without `--allow-external` |
| Audit is append-once | A second run against the same audit path exits non-zero |
| Strict input | A duplicate key is refused |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `--audit-file must be an absolute, new file` | Use a full path to a file that does not exist yet. Choose a new name. |
| `tokn: command not found` | Install TOKN v0.3.57 or newer and open a new terminal. |
| `bundle.json` is missing | Run `tokn judgments example > bundle.json` first, in the same folder. |
