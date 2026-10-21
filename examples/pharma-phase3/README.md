# Example: Phase 3 analysis package with an endpoint-provenance check

> "Prepare a synthetic Phase 3 trial analysis package for the go/no-go review
> of compound VTX-417. Register every claim, mark each one LAWFUL or
> QUARANTINED against the SAP, and deny any green-light the SAP does not
> support."

This example takes a fictional Phase 3 trial, its pre-specified analysis plan,
and a locked Phase 2 summary, and asks TOKN to produce an analysis package. A
small stdlib checker then tests the claims against the SAP rules. Everything
is fictional: the compound, sponsor, indication and data.

| Capability | How this example uses it |
|---|---|
| Agent run in `default` mode | Reads the task brief and the synthetic inputs, then writes the package |
| Endpoint register | One JSON entry per statistical claim, with its SAP source |
| Decision memo | A recommendation with a LAWFUL / QUARANTINED label per claim |
| Deterministic checker | `check_gate.py`, stdlib Python, reads one local file |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Earlier builds lack the flags used here | `tokn version` |
| Model provider configured | The agent needs an LLM to write the package | See [SETUP.md](../../SETUP.md) |
| Python 3.8+ (optional) | Only for the checker in step 5 | `python --version` |

**Tier:** this example uses `--mode default`, which relies on the `core:*`
feature set. That is part of the **Community** tier, so no trial is needed.

No domain mode is used here, so you do not need `tokn license trial`.

## What leaves your machine

The task brief and the synthetic inputs in `inputs/` are sent to the model
provider you configure. Nothing else is sent. The checker in step 5 makes no
network calls.

## Steps

### 1. Get the example

Work in the `examples/pharma-phase3` folder of your TOKN distribution.

**bash**
```bash
cd examples/pharma-phase3
```

**PowerShell**
```powershell
cd examples\pharma-phase3
```

### 2. Configure the model

Set your provider and model. Replace the placeholders with your own values.
See [SETUP.md](../../SETUP.md) for the provider list.

**bash**
```bash
export NOSPACE_MODEL_PROVIDER=<your provider>
export NOSPACE_MODEL_NAME=<your model>
export ANTHROPIC_API_KEY=<your key>
```

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "<your provider>"
$env:NOSPACE_MODEL_NAME     = "<your model>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Use the key variable that matches your provider. Do not commit your key.

### 3. Run the agent

The run reads the brief from `inputs/task-prompt.md` and writes the package to
`analysis-package/`.

**bash**
```bash
mkdir -p analysis-package
tokn agent-run --mode default --repo-root . \
  --prompt-file inputs/task-prompt.md \
  --model-provider "$NOSPACE_MODEL_PROVIDER" \
  --model-name "$NOSPACE_MODEL_NAME" \
  --no-confirm --max-steps 12 \
  --capture-trajectory --export json
```

**PowerShell**
```powershell
New-Item -ItemType Directory -Force analysis-package | Out-Null
tokn agent-run --mode default --repo-root . `
  --prompt-file inputs/task-prompt.md `
  --model-provider $env:NOSPACE_MODEL_PROVIDER `
  --model-name $env:NOSPACE_MODEL_NAME `
  --no-confirm --max-steps 12 `
  --capture-trajectory --export json
```

Flags used: `--mode`, `--repo-root`, `--prompt-file`, `--model-provider`,
`--model-name`, `--no-confirm`, `--max-steps`, `--capture-trajectory`,
`--export`. All were checked with `tokn agent-run --help`.

### 4. Review the package

Open `analysis-package/endpoint-register.json` and `decision-memo.md`. Check
that every claim has an SAP source and that the LAWFUL / QUARANTINED labels
match the SAP.

### 5. Run the checker (optional)

The checker tests each claim against the SAP rules. It reads only
`analysis-package/endpoint-register.json`.

**bash**
```bash
python check_gate.py analysis-package/endpoint-register.json
```

**PowerShell**
```powershell
python check_gate.py analysis-package\endpoint-register.json
```

Exit code `0` means no green-light claim was quarantined. Exit code `1` means
at least one was.

## Expected outcomes

Expected, not a recorded run. These are the outcomes the synthetic inputs are
designed to test.

| Claim | Expected label | Reason |
|---|---|---|
| Primary ITT result (p = 0.182) | QUARANTINED | Not significant; cannot support a green-light |
| Key secondary (p = 0.214) | QUARANTINED | Hierarchical test not reached |
| High-cTAG subgroup (p = 0.004) | QUARANTINED | Post-hoc, not in SAP, partial SDV, not ITT |
| cTAG biomarker (p = 0.03) | QUARANTINED | Assay not qualified |
| Overall recommendation | adaptive-redesign or kill | No lawful basis for a green-light |

The default posture is deny. A green-light needs every SAP rule to pass.

## What to look for

- A post-hoc subgroup with a striking p-value is still quarantined. The SAP
  and the SDV status decide, not the size of the p-value.
- The memo should name the gap, not invent data. "Not available" is a valid
  answer.
- The checker and the memo should agree. If they do not, trust the checker
  and check the register.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tokn: command not found` | Put the `tokn` binary on your PATH, or run `./tokn` from its folder |
| `tokn version` shows an older build | Download v0.3.57 or later from the distribution repo |
| Model or key error at step 3 | Re-check step 2; see [SETUP.md](../../SETUP.md) |
| `missing: analysis-package\endpoint-register.json` | The run did not finish. Re-run step 3 and check its output |
| Checker exits `2` | Run it from the `pharma-phase3` folder, or pass the full path |
| Checker exits `1` | Expected if the agent marked a quarantined claim as green-light. Review the memo |
