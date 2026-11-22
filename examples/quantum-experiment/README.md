# Example: Quantum experiment plan review (quantumsci)

> "Here is a synthetic experiment plan and two device specs. Check each experiment against the error-budget, tier, ZNE and NISQ/fault-tolerant gates, and tell me which claims are blocked."

This example runs TOKN's quantum science domain (`--mode quantumsci`) on synthetic plans. The two device specs are invented for the exercise; they describe no real backend, and nothing here runs on quantum hardware. The expected behaviour is that the error-budget gate blocks a deep circuit on a noisy device, that tier labels are required, that ZNE is rejected when the fit does not suit the noise, and that a fault-tolerant claim is refused when either the two-qubit fidelity or the qubit overhead falls short.

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
| An LLM provider you can reach | TOKN's agent loop needs a model. See [SETUP.md](../../SETUP.md). Use a model capable of the required tool calls; provider charges and number of turns depend on the run. A missing/failed tool result is unassessed, not a pass. | `tokn doctor --provider anthropic` (static; the first run tests the key) |
| 14-day trial | Domain modes such as `quantumsci` need the trial. Community grants only `domains:basic`. | `tokn license features` |

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
export NOSPACE_MODEL_PROVIDER='anthropic'
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
```

PowerShell:
```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "YOUR_MODEL_ID"
$env:ANTHROPIC_API_KEY = Read-Host 'Anthropic key' -MaskInput   # pwsh 7.1+; or read it from your secret store
```

Set only the key variable that matches your provider. See [SETUP.md](../../SETUP.md) for the full list.

### 3. Start the trial (once)

```bash
tokn license trial
```

### 4. Review the plans in quantumsci mode

Stage only the prompt and the two JSON inputs into a new `work/` folder. This README (with the expected outcomes) and `check_plan.py` stay outside the agent's read scope, and the result is saved outside `work/`.

Bash:
```bash
mkdir work
cp prompt.md devices.json experiments.json work/
cd work
tokn agent-run --mode quantumsci --prompt-file prompt.md --repo-root . \
  --permission-mode plan --max-steps 12 --output-format json > ../result.json
cd ..
```

PowerShell:
```powershell
New-Item -ItemType Directory work | Out-Null
Copy-Item prompt.md, devices.json, experiments.json work\
Set-Location work
tokn agent-run --mode quantumsci --prompt-file prompt.md --repo-root . `
  --permission-mode plan --max-steps 12 --output-format json > ..\result.json
Set-Location ..
```

`--permission-mode plan` keeps the run read-only: the task is a report, so the agent needs no file writes or commands. `mkdir` fails if `work/` already exists; delete or rename the old one first. The answer is the `result` field of `result.json`; use it only if `status` is `success`.

### 5. Recompute the gates offline

Bash:
```bash
python3 check_plan.py
```

PowerShell:
```powershell
python check_plan.py
```

The checker reads `devices.json` and `experiments.json`, prints the fidelity and each issue, and exits with code 1 if any CRITICAL issue is found. It recomputes the gates independently; it does not read the agent's answer. Grade the run from this folder by comparing each verdict in `result.json` with the checker's output, experiment by experiment.

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
- Three kinds of claim stay separate. A **simulator estimate** (`[EXACT-SIM]`, `[NOISY-SIM]`, `[ANALOG-SIM]`) is a computed expectation. **Hardware evidence** (`[HARDWARE:…]`) exists only where a plan records a hardware run; here that label is synthetic too. Anything the run did not compute, or computed with a failed tool call, is **unassessed**, not PASS.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The mode is not recognised | Your TOKN is older than v0.3.57. Update it. |
| Mode refuses to start, or a domain-licence error appears | Run `tokn license trial`, then `tokn license features`. |
| The agent makes no tool calls | Raise `--max-steps`, and check the model settings in step 2 with `tokn doctor --provider anthropic`. For other agent flags, see `tokn agent-run --help-all`. |
| `python` not found on Windows | Use `py` instead, or install Python from python.org. |
| Checker reports a missing file | Run it from this folder. The JSON files must sit next to `check_plan.py`. |
| Checker exits 1 | Expected for this dataset. exp-1 and exp-3 are BLOCKED. |
