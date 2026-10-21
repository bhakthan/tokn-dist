# Example: Quantum experiment plan review (quantumsci)

> "Here is a synthetic experiment plan and two device specs. Check each experiment against the error-budget, tier, ZNE and NISQ/fault-tolerant gates, and tell me which claims are blocked."

This example runs TOKN's quantum science domain (`--mode quantumsci`) on synthetic plans. The expected behaviour is that the error-budget gate blocks a deep circuit on a noisy device, that tier labels are required, that ZNE is rejected when the fit does not suit the noise, and that a fault-tolerant claim is refused when either the two-qubit fidelity or the qubit overhead falls short.

| Capability | What it does here |
|---|---|
| Error-budget gate | Computes fidelity (1 − p₂)^gates and blocks above 50 % accumulated error |
| Decoherence gate | Compares execution time with T2 |
| Shot-count gate | Checks the 1000-shot floor and the 10000-shot publication floor |
| Tier labelling | Every result must carry `[EXACT-SIM]`, `[NOISY-SIM]`, `[HARDWARE:…]` or `[ANALOG-SIM]` |
| ZNE validity | Needs at least 3 scale factors within 1.0–3.0, and rejects Richardson fits for large accumulated error |
| NISQ/FT boundary | A fault-tolerant claim needs two-qubit fidelity ≥ 99.9 % and ≥ 100 physical qubits per logical qubit |
| Offline checker | `check_plan.py` recomputes the same gates with the Python standard library |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Earlier builds do not have the `quantumsci` mode | `tokn version` |
| Python 3.8+ | Runs the offline checker | `python --version` |
| An LLM provider you can reach | TOKN's agent loop needs a model. See [SETUP.md](../../SETUP.md). | `tokn agent-run --help` |
| 14-day trial | Domain modes such as `quantumsci` need the trial. Community grants only `domains:basic`. | `tokn license status` |

**Tier:** `quantumsci` is a domain mode. Start the trial with `tokn license trial` (14 days). Without it, the mode is not available. The checker and the JSON files need no licence.

## What leaves your machine

- The prompt and the JSON contents are sent to the LLM provider you configure in step 2.
- TOKN may send a one-time anonymous registration. Set `TOKN_NO_TELEMETRY=1` to opt out.
- `check_plan.py` makes no network calls.

## Steps

### 1. Get the example files

Bash:
```bash
cd tokn-dist/examples/quantum-experiment
```

PowerShell:
```powershell
Set-Location tokn-dist\examples\quantum-experiment
```

### 2. Configure the model

Bash:
```bash
export NOSPACE_MODEL_PROVIDER=<your provider>
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

PowerShell:
```powershell
$env:NOSPACE_MODEL_PROVIDER = "<your provider>"
$env:NOSPACE_MODEL_NAME = "<a model you have access to>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

Set only the key variable that matches your provider. See [SETUP.md](../../SETUP.md) for the full list.

### 3. Start the trial (once)

```bash
tokn license trial
```

### 4. Review the plans in quantumsci mode

Bash:
```bash
tokn agent-run --mode quantumsci --prompt-file prompt.md --no-confirm
```

PowerShell:
```powershell
tokn agent-run --mode quantumsci --prompt-file prompt.md --no-confirm
```

`--no-confirm` skips interactive prompts. Remove it if you want to approve each step. Add `--max-steps 12` if the agent stops early.

### 5. Recompute the gates offline

Bash:
```bash
python3 check_plan.py
```

PowerShell:
```powershell
python check_plan.py
```

The checker reads `devices.json` and `experiments.json`, prints the fidelity and each issue, and exits with code 1 if any CRITICAL issue is found.

## Expected outcomes

These are expected from the gate rules. They are not a recorded run.

| Experiment | Key numbers (computed from the JSON) | Expected result |
|---|---|---|
| exp-1 | Fidelity ≈ 0.366, error ≈ 63 %; execution 60 µs = 60 % of T2; 500 shots; no tier label; Richardson fit at 63 % accumulated error | BLOCKED (several CRITICAL) |
| exp-2 | Fidelity ≈ 0.818, error ≈ 18 %; execution 12 µs = 12 % of T2; 5000 shots; `[NOISY-SIM]` | Warnings only. Usable as a noisy-simulator result, not a publication result. |
| exp-3 | Same circuit as exp-2, plus a fault-tolerant claim with fidelity 0.998 and 80 physical qubits per logical qubit | BLOCKED on the FT claim (two CRITICAL). The circuit result itself stays NISQ-era. |
| exp-4 | Fidelity ≈ 0.984, error ≈ 1.6 %; execution 8 µs = 2.7 % of T2; 10000 shots; hardware tier label; FT claim with fidelity 0.9992 and 1000 physical qubits | PASS, with no issues |

exp-1 is the clearest block: the error budget, decoherence, shot count, tier label and ZNE fit all fail.

## What to look for

- The agent computes the fidelity and states the gate that fired for each experiment.
- exp-3's fault-tolerant claim is refused and labelled NISQ-era, even though the circuit itself is fine.
- The agent does not call a quantum advantage over classical methods, because the plans give no classical baseline.
- Each result carries a tier label in the answer.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The mode is not recognised | Your TOKN is older than v0.3.57. Update it. |
| Mode refuses to start, or a domain-licence error appears | Run `tokn license trial`, then `tokn license status`. |
| The agent makes no tool calls | Raise `--max-steps`, and check the model settings in step 2. |
| `python` not found on Windows | Use `py` instead, or install Python from python.org. |
| Checker reports a missing file | Run it from this folder. The JSON files must sit next to `check_plan.py`. |
| Checker exits 1 | Expected for this dataset. exp-1 and exp-3 are BLOCKED. |
