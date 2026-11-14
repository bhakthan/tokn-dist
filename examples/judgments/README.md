# Governed judgments: the guard rails

This folder holds the offline judgment walkthrough. The main cases (clean and
error runs) are described in the top-level [examples README](../README.md#judgments).
This page adds the behaviours those cases do not show. Every evaluation here
uses the local `rules` provider, so no model or API key is needed. These are
checks of supplied run evidence, not proof that an answer is correct.

Install TOKN v0.3.57 or newer (`tokn version`). No Python or model runtime is
needed. Start from the `tokn-dist` root, then copy the requests to a new
scratch directory you own. These commands create that directory and write
the bundle there.

```bash
mkdir -p ~/judgments-run
cp examples/judgments/*.json ~/judgments-run/ && cd ~/judgments-run
tokn judgments example > bundle.json
```

```powershell
New-Item -ItemType Directory -Force $HOME\judgments-run | Out-Null
Copy-Item examples\judgments\*.json $HOME\judgments-run\; Set-Location $HOME\judgments-run
tokn judgments example | Set-Content -Encoding ascii bundle.json
```

The PowerShell form also works in Windows PowerShell 5.1, whose `>` operator
would otherwise write a JSON file in the wrong encoding. Use a fresh folder
if you need to preserve an earlier `bundle.json`.

The evaluations need no network. To disable TOKN's separate startup
registration and update checks, set `TOKN_NO_REGISTER=1` and
`TOKN_NO_UPDATE_CHECK=1` in your shell too.

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

Expected, not a recorded run: exit `0` with the local rules result. This
bundle still selects `rules`; `--allow-external` grants permission but does
not select a different provider. An externally configured bundle is
required to exercise external-provider refusal.

<a id="disabled-mode-needs-nothing"></a>

## Disabled mode still validates inputs

`--mode disabled` skips provider evaluation. It still requires a valid bundle
and request; it is not a test of provider credentials or answer quality.

```bash
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode disabled --air-gap
```

```powershell
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode disabled --air-gap
```

## Audit files are created once and never overwritten

`--audit-file` writes hashes and references, not the raw state. The path must be
absolute and must not exist. A second run against the same path fails and
leaves the first record unchanged.

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
| Audit is create-once | A second run against the same audit path exits non-zero |
| Strict input | A duplicate key is refused |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `--audit-file must be an absolute, new file` | Use a full path to a file that does not exist yet. Choose a new name. |
| `tokn: command not found` | Install TOKN v0.3.57 or newer and open a new terminal. |
| `bundle.json` is missing or unreadable | Generate it in the same folder using the setup command for your shell; Windows PowerShell 5.1 needs the explicit encoding shown above. |

Keep the scratch folder if you want to inspect the results later. Otherwise
remove it, including any audit file you explicitly created. Nothing here
applies a recommendation to a repository or production system.
