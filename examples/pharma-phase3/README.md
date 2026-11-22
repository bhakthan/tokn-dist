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
| Model provider configured | The agent needs an LLM to write the package. Use a model capable of the required tool calls; provider charges and number of turns depend on the run. A missing/failed tool result is unassessed, not a pass. | `tokn doctor --provider anthropic` (static; see [SETUP.md](../../SETUP.md)) |
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
export NOSPACE_MODEL_PROVIDER='anthropic'
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
```

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "YOUR_MODEL_ID"
$env:ANTHROPIC_API_KEY      = Read-Host 'Anthropic key' -MaskInput   # pwsh 7.1+; or read it from your secret store
```

Use the key variable that matches your provider. Do not commit your key.
`tokn doctor --provider anthropic` checks the configuration statically; it does
not prove the key works.

### 3. Run the agent

Stage only `inputs/` into a new `work/` folder and run from there. This README
(with the expected labels) and `check_gate.py` stay outside the agent's read
scope. The run reads the brief from `inputs/task-prompt.md` and writes the
package to `work/analysis-package/`.

**bash**
```bash
mkdir work
cp -r inputs work/
cd work
mkdir analysis-package
tokn agent-run --mode default --repo-root . \
  --prompt-file inputs/task-prompt.md \
  --model-provider "$NOSPACE_MODEL_PROVIDER" \
  --model-name "$NOSPACE_MODEL_NAME" \
  --permission-mode default --max-steps 12 \
  --capture-trajectory --export json
cd ..
```

**PowerShell**
```powershell
New-Item -ItemType Directory work | Out-Null
Copy-Item inputs work\ -Recurse
Set-Location work
New-Item -ItemType Directory analysis-package | Out-Null
tokn agent-run --mode default --repo-root . `
  --prompt-file inputs/task-prompt.md `
  --model-provider $env:NOSPACE_MODEL_PROVIDER `
  --model-name $env:NOSPACE_MODEL_NAME `
  --permission-mode default --max-steps 12 `
  --capture-trajectory --export json
Set-Location ..
```

`--permission-mode default` asks before each file write or command, so approve
only writes into `analysis-package/`. `mkdir work` fails if `work/` already
exists; rename or delete the old one first. `--max-steps` limits turns; it is
not a spend cap.

Flags used: `--mode`, `--repo-root`, `--prompt-file`, `--model-provider`,
`--model-name`, `--permission-mode`, `--max-steps`, `--capture-trajectory`,
`--export`. `--capture-trajectory` and `--export` are advanced flags: they are
listed by `tokn agent-run --help-all`, not by the short `--help`.

Before you accept the fictional package, grade it from outside `work/` with the
fixture checker (step 5), and record who signed off. A model's sign-off text is
not human sign-off.

### 4. Review the package

Open `work/analysis-package/endpoint-register.json` and `decision-memo.md`.
Check that every claim has an SAP source and that the LAWFUL / QUARANTINED
labels match the SAP.

The package is acceptable only when **all** of these hold:

1. Every claim in the register names its endpoint source in the SAP excerpt or
   the locked Phase 2 summary. A claim with no traceable source is rejected,
   whatever its label.
2. The checker in step 5 exits `0`.
3. A named human reviewer, not the model, has read the memo and recorded the
   decision and the date outside `work/`. Without that sign-off the package
   stays a draft, even when 1 and 2 pass.

### 5. Run the checker (optional)

The checker tests each claim against the SAP rules. Run it from this folder,
outside `work/`. It reads only the register you pass it.

**bash**
```bash
python check_gate.py work/analysis-package/endpoint-register.json
```

**PowerShell**
```powershell
python check_gate.py work\analysis-package\endpoint-register.json
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
| `missing: work\analysis-package\endpoint-register.json` | The run did not finish, or a write was declined. Re-run step 3 in a fresh `work/` and check its output |
| Checker exits `2` | Run it from the `pharma-phase3` folder, or pass the full path |
| Checker exits `1` | Expected if the agent marked a quarantined claim as green-light. Review the memo |
