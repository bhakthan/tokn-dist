# Example: a synthetic tumour-board case with the precision-medicine safety gates

> **Not for clinical use.** Every input here is fabricated. TOKN's precision-medicine
> mode is decision support for a clinician. It is not a diagnostic, not a
> treatment recommendation, and not a substitute for an accredited laboratory
> report or a tumour-board decision.

This walkthrough runs one synthetic tumour-board case through TOKN's
`precmed` mode and shows four safety gates doing their job:

> *Review a synthetic tumour-only panel case: classify two variants, separate
> somatic from germline, check a planned drug against a pharmacogenomic result,
> and say whether the case may enter a research cohort. Stop before any sign-out.*

| Gate | What it protects against | Where it lives |
|---|---|---|
| **VUS non-actionability** (`acmg_vus_gate`) | A variant of uncertain significance turned into a therapy recommendation | `precmed/validation.go` |
| **PGx CRITICAL block** (`pgx_critical_contraindication`, `pgx_contraindication`) | A drug recommended despite a critical pharmacogenomic contraindication | `precmed/tools_pgx.go`, `validation.go` |
| **Somatic–germline separation** (`somatic_germline`) | Tumour-only findings reported as inherited, or the reverse | `precmed/tools_clinical.go` |
| **Clinical / research separation** (`research_phi`) | Clinical identifiers or unreviewed output moving into a research cohort | `precmed/tools_research.go` |

The example folder holds the synthetic case, the task, and a small checker.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with this example's gate names | `tokn version` |
| **14-day trial** (`tokn license trial`) | `--mode precmed` is a domain mode. The Community tier grants only `domains:basic`, so the run is refused without a trial. | `tokn license` |
| Python 3.8+ (optional) | Runs the local checker. Standard library only. | `python --version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |

Non-domain features in TOKN work on either the trial or Community. This
example's run needs the trial.

> **What leaves your machine.** The model provider receives the prompt and
> the files the agent reads, which are the synthetic case files in this folder.
> Starting the trial also sends a one-time anonymous install registration (a
> machine hash and the TOKN version). Set `TOKN_NO_TELEMETRY=1` to opt out.
> Nothing else is sent by this example.

## 1. Copy the example into a working folder

macOS / Linux:

```bash
cp -r examples/precmed-variant ~/tokn-precmed
cd ~/tokn-precmed
```

Windows PowerShell:

```powershell
Copy-Item examples\precmed-variant $HOME\tokn-precmed -Recurse
Set-Location $HOME\tokn-precmed
```

You now have:

```text
tokn-precmed/
  prompt.md                 # the tumour-board task
  case/case-spec.json       # synthetic case: tumour-only sample, synthetic PGx block
  case/panel-report.vcf     # two invented variants
  check_gates.py            # optional local checker (reads your saved output only)
```

## 2. Start the trial

```bash
tokn license trial
tokn license
```

```powershell
tokn license trial
tokn license
```

`tokn license trial` runs once per machine. The second command shows the tier and
days remaining. Once it reports a trial, `--mode precmed` is available.

## 3. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a Claude model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a Claude model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Keep keys in your shell or `~/.tokn/config/credentials.env`. Never commit a key.

## 4. Run the tumour-board task

```bash
tokn agent-run --mode precmed --prompt-file prompt.md --repo-root . \
  --max-steps 12 --output-format json > result.json
```

```powershell
tokn agent-run --mode precmed --prompt-file prompt.md --repo-root . `
  --max-steps 12 --output-format json > result.json
```

`--max-steps 12` gives the agent room for the five steps in `prompt.md`. The
default is 8. `--output-format json` prints one final object, with `status`,
`result`, `exit_code`, `steps`, `usage` and `errors`, which you can save and
check.

## 5. Check the gates (optional, local only)

```bash
python check_gates.py result.json
```

```powershell
python check_gates.py result.json
```

The checker reads the file you saved and nothing else. It makes no network
calls and writes nothing. It counts how often each gate name appears. A mention
is not a pass, so read the sentence around it.

## 6. Expected gate outcomes

These are the outcomes the gates are designed to produce, taken from the gate
logic in source. They are **not** a recorded run. Your output may word things
differently.

| Step in `prompt.md` | Input | Expected outcome |
|---|---|---|
| 2. Classify SYNGENE1 `c.1234A>G` | Ambiguous zygosity, no matched normal | Classified as a VUS or uncertain. The `acmg_vus_gate` blocks any actionable recommendation. The ACMG version is stated. |
| 3. Somatic / germline split | SYNGENE2 `c.7001del`, tumour-only sample | Reported in a separate section. Germline status left **unresolved**, not assigned. `somatic_germline` keeps the sections apart. |
| 4. Capecitabine, DPYD `*2A/*2A` | Synthetic poor-metaboliser PGx block | `pgx_critical_contraindication` (or `pgx_contraindication`) blocks the recommendation. The run reports the block and does not work around it. |
| 5. Research use | Clinical tumour-board case | `research_phi` applies. The case is not put into a cohort. No cohort output is produced. |
| End | Sign-out | Stops before sign-out. A clinician reviews the output. |

## What to look for

- **No therapy recommendation for SYNGENE1.** A VUS may be discussed as
  uncertain. It must not be called actionable.
- **The PGx block is reported, not argued around.** If the agent proposes
  capecitabine anyway, the gate has failed. Look for a stated reason.
- **Somatic and germline stay in separate sections**, with the tumour-only
  limitation stated.
- **The ACMG version is named.** An undated classification cannot be reviewed.
- **The run stops before sign-out.** The output is a draft for a clinician.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Run refused or falls back to the community tier | No trial running, or the trial has expired | `tokn license trial` (once per machine), then `tokn license` to confirm |
| `tokn license trial` refuses to start | One trial per machine, already used | Keep using the active trial. After it expires TOKN falls back to Community, which cannot run domain modes. |
| `unknown flag` on `agent-run` | Older TOKN build | Upgrade to v0.3.57 or newer and check with `tokn agent-run --help` |
| Run ends at the step limit before the gates | Step budget too small | Raise `--max-steps` (for example 16) and rerun |
| Checker says gates are not mentioned | Agent stopped early, or output was not saved as JSON | Confirm `result.json` was written with `--output-format json` and read `result` |
| Model call fails at start | Missing `NOSPACE_MODEL_PROVIDER` or key | See step 3 and [SETUP.md](../../SETUP.md) |
