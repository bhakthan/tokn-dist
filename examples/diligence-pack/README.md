# Example: Private-equity diligence pack with an evidence check

> "Prepare a diligence pack for Quillstone Industrial Software at a $600M ask.
> Count as ARR only executed or auto-renewed, undisputed contracts. Quarantine
> MOUs and verbal commitments, show the valuation gap, and state every
> contingent liability with its modeled reserve."

This example takes a fictional software target, its contract list, and
management's stated figures. TOKN writes a diligence pack, and a small stdlib
checker recomputes the ARR from the contract list. Everything is fictional:
the target, sponsor, customers and figures.

| Capability | How this example uses it |
|---|---|
| Agent run in `default` mode | Reads the brief and the contract list, then writes the pack |
| ARR register | One row per contract, marked authoritative or not |
| Valuation memo | Authoritative vs stated ARR, the implied multiple, and the gap |
| Risk memo | Concentration, change-of-control rights, contingent liabilities |
| Deterministic checker | `check_evidence.py`, stdlib Python, reads local files only |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Earlier builds lack the flags used here | `tokn version` |
| Model provider configured | The agent needs an LLM to write the pack | See [SETUP.md](../../SETUP.md) |
| Python 3.8+ (optional) | Only for the checker in step 5 | `python --version` |

**Tier:** this example uses `--mode default`, which relies on the `core:*`
feature set. That is part of the **Community** tier, so no trial is needed.

## What leaves your machine

The task brief and the synthetic inputs in `inputs/` are sent to the model
provider you configure. Nothing else is sent. The checker in step 5 makes no
network calls.

## Steps

### 1. Get the example

Work in the `examples/diligence-pack` folder of your TOKN distribution.

**bash**
```bash
cd examples/diligence-pack
```

**PowerShell**
```powershell
cd examples\diligence-pack
```

### 2. Configure the model

Replace the placeholders with your own values. See
[SETUP.md](../../SETUP.md) for the provider list.

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

The run reads the brief from `inputs/task-prompt.md` and writes the pack to
`diligence-pack/`.

**bash**
```bash
mkdir -p diligence-pack
tokn agent-run --mode default --repo-root . \
  --prompt-file inputs/task-prompt.md \
  --model-provider "$NOSPACE_MODEL_PROVIDER" \
  --model-name "$NOSPACE_MODEL_NAME" \
  --no-confirm --max-steps 12 \
  --capture-trajectory --export json
```

**PowerShell**
```powershell
New-Item -ItemType Directory -Force diligence-pack | Out-Null
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

### 4. Review the pack

Open `diligence-pack/valuation-memo.md` and `risk-memo.md`. Check the
arithmetic against `inputs/contracts-register.csv` yourself.

### 5. Run the checker (optional)

The checker recomputes ARR from the contract list. It then compares the
result with `diligence-pack/arr-register.json`, and flags any MOU or verbal
commitment counted as authoritative.

**bash**
```bash
python check_evidence.py diligence-pack
```

**PowerShell**
```powershell
python check_evidence.py diligence-pack
```

Exit code `0` means the register matches the source. Exit code `1` means it
does not. Exit code `0` with a "No arr-register.json yet" message means the
run has not finished.

## Expected outcomes

Expected, not a recorded run. These are the figures the synthetic inputs are
designed to produce.

| Measure | Expected value |
|---|---|
| Management stated ARR | $84.0M |
| Authoritative ARR (executed + auto-renewed) | $60.1M ($52.3M + $7.8M) |
| Quarantined (MOUs $18.9M + verbal $5.0M) | $23.9M |
| Implied multiple of the ask on stated ARR | about 7.1x |
| Grounded value at that multiple on authoritative ARR | about $429M |
| Gap to the $600M ask | about $171M |
| Top-2 customers as share of executed ARR | 41.1%, both with change-of-control rights |
| Contingent liabilities (modeled reserve $0) | $20M to $39M (midpoint $29.5M) |

## What to look for

- The pack should refuse to count the MOUs or the verbal commitment as ARR,
  even though management's headline includes them.
- Concentration and change-of-control rights belong in the risk memo, not
  buried in an appendix.
- A $0 reserve against a $20M to $39M range is a gap to call out, not a
  number to accept.
- If the memo's figures disagree with the checker, trust the checker and find
  the row that differs.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tokn: command not found` | Put the `tokn` binary on your PATH, or run `./tokn` from its folder |
| `tokn version` shows an older build | Download v0.3.57 or later from the distribution repo |
| Model or key error at step 3 | Re-check step 2; see [SETUP.md](../../SETUP.md) |
| `No diligence-pack\arr-register.json yet` | The run did not finish. Re-run step 3 and check its output |
| Checker reports `FAIL` on a register figure | Expected if the agent counted an MOU or verbal commitment. Review the register |
| `FileNotFoundError` for the CSV | Run the checker from the `diligence-pack` folder |
