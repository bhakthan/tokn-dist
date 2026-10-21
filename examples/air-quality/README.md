# Example: Air-quality model evaluation (atmchem)

> "Here is a synthetic model run for O3 and PM2.5 at one site. Check whether it passes the evaluation gate, and tell me whether the results support a regulatory compliance statement against NAAQS, EU AQD and WHO AQG."

This example runs TOKN's atmospheric chemistry domain (`--mode atmchem`) on a small synthetic dataset. The expected behaviour is that the evaluation gate measures bias and correlation, and that the regulatory layer refuses to claim compliance for any species that fails evaluation.

| Capability | What it does here |
|---|---|
| Evaluation gate | Checks NMB and r² per species against the EPA-style defaults (O3: NMB within ±15 %, r² ≥ 0.60; PM2.5: NMB within ±30 %, r² ≥ 0.50) |
| Validity layers | Exercises the evaluation and regulatory layers. The physical and emission layers need an emissions inventory and are not covered by this example. |
| Regulatory framing | Uses NAAQS, EU AQD and WHO AQG as framing only. The example does not check limit values. |
| Offline checker | `check_evaluation.py` recomputes the same metrics with the Python standard library |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Earlier builds do not have the `atmchem` mode or its tools | `tokn version` |
| Python 3.8+ | Runs the offline checker | `python --version` |
| An LLM provider you can reach | TOKN's agent loop needs a model. See [SETUP.md](../../SETUP.md). | `tokn agent-run --help` |
| 14-day trial | Domain modes such as `atmchem` need the trial. Community grants only `domains:basic`. | `tokn license status` |

**Tier:** `atmchem` is a domain mode. Start the trial with `tokn license trial` (14 days). Without it, the mode is not available. Everything else in this example (the checker and the CSV) is plain Python and needs no licence.

## What leaves your machine

- The prompt and the CSV contents are sent to the LLM provider you configure in step 2.
- TOKN may send a one-time anonymous registration. Set `TOKN_NO_TELEMETRY=1` to opt out.
- `check_evaluation.py` makes no network calls.

## Steps

### 1. Get the example files

Bash:
```bash
cd tokn-dist/examples/air-quality
```

PowerShell:
```powershell
Set-Location tokn-dist\examples\air-quality
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

### 4. Run the evaluation in atmchem mode

Bash:
```bash
tokn agent-run --mode atmchem --prompt-file prompt.md --no-confirm
```

PowerShell:
```powershell
tokn agent-run --mode atmchem --prompt-file prompt.md --no-confirm
```

`--no-confirm` skips interactive prompts. Remove it if you want to approve each step. Add `--max-steps 12` if the agent stops early.

### 5. Recompute the metrics offline

Bash:
```bash
python3 check_evaluation.py
```

PowerShell:
```powershell
python check_evaluation.py
```

The checker reads `data/modelled_vs_observed.csv` and prints NMB, r² and pass or fail for each species. It exits with code 1 if any species fails.

## Expected outcomes

These are expected from the gate rules. They are not a recorded run.

| Species | NMB (computed from CSV) | r² | Evaluation gate | Regulatory statement |
|---|---|---|---|---|
| O3 | about +7.2 % (limit ±15 %) | about 0.99 (min 0.60) | PASS | May be framed as passing evaluation. No limit-value compliance is claimed. |
| PM2.5 | about +38.8 % (limit ±30 %) | about 0.999 (min 0.50) | FAIL on NMB | Must not be framed as compliant. |

The PM2.5 row is the main lesson. Its correlation is almost perfect, but the model is biased high by about 39 %. High r² does not rescue bias.

## What to look for

- The agent reports NMB and r² for each species, not just r².
- PM2.5 is reported as failing the evaluation gate, and the agent does not claim regulatory compliance for it.
- Limit values are not asserted from memory. Any NAAQS, EU AQD or WHO AQG number the agent cites should be checked against the official source.
- The answer labels which numbers were computed from the file.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The mode is not recognised | Your TOKN is older than v0.3.57. Update it. |
| Mode refuses to start, or a domain-licence error appears | Run `tokn license trial`, then `tokn license status`. |
| The agent makes no tool calls | Raise `--max-steps`, and check the model settings in step 2. |
| `python` not found on Windows | Use `py` instead, or install Python from python.org. |
| Checker reports a missing file | Run it from this folder, or pass the CSV path as the first argument. |
| Checker exits 1 | Expected for this dataset. PM2.5 fails on NMB. |
