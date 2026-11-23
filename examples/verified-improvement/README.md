# Example: prove a prompt improvement before you trust it

This walkthrough improves a **pharmacovigilance triage prompt**, then proves the
improvement with evidence that would survive a sceptical reviewer:

> *An ICSR (Individual Case Safety Report) arrives from a clinical trial. Is it
> serious? Is it expected under the Reference Safety Information? Is it related?
> Is it a SUSAR, and is the reporting clock 7 days, 15 days or none?*

A wrong answer here has consequences. A missed 7-day SUSAR is a late regulatory
report. An over-called one wastes medical-review time. So "the new prompt scored
higher" is not enough. You want to know **whether it is better on cases it has
never seen**, **whether the gain is larger than run-to-run noise**, and
**whether anything other than the prompt changed**.

| Feature | What it does here |
|---|---|
| **Prompt optimizer** (`tokn prompt-optimize`) | Mutates the prompt using failures from a *visible* eval set and picks the best variant. |
| **Held-out confirmation** (`--confirm-set`) | Installs the winner only if it also beats the live prompt on cases the mutator never saw. |
| **Leak check** | Refuses a confirmation set that shares any case with the eval set. |
| **Flywheel receipts** (`--harness-path`, `--model-ref`) | Fingerprints the exact prompt, script, dataset, split, grader and model behind every score. |
| **Noise band** (`--noise-reports`) | Measures how much the *unchanged* system moves between runs; a gain must beat it. |
| **Strict gate** (`--strict`) | Refuses to compare two runs unless only the model or harness differs. |
| **Identity diff** (`flywheel compare --explain-identity`) | Shows axis by axis what changed between two runs. |

Everything is synthetic. No patient data, no real product, no real trial.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.122 or newer** | Ships `--confirm-set`, receipts, noise bands and `--strict` | `tokn version` |
| An LLM provider and key (from step 5) | Every case is one model call. A full walkthrough is roughly 150 calls with a small, fast model. | `tokn doctor --provider anthropic` |
| `python3` (macOS / Linux only) | `candidate.sh` parses the JSON result | `python3 --version` |

Steps 3 and 4 need **no model and no key**: they show TOKN refusing unsafe
promotions before any compute is spent.

> **What leaves your machine.** Each case's text plus the prompt being tested
> is sent to your provider. During optimization, failing cases (input, output,
> expected pattern) are also sent to the mutator model. Grading is local regex
> and exact-match checks; no model grades anything.

## 1. Open the folder

```bash
cd examples/verified-improvement
```

```powershell
Set-Location examples\verified-improvement
```

```text
verified-improvement/
  starting-prompt.md      # the department SOP prompt, with realistic flaws
  eval-visible.jsonl      # 10 cases the optimizer learns from
  confirm-heldout.jsonl   # 8 different cases, never shown to the optimizer
  confirm-leaky.jsonl     # a deliberately broken confirm set (2 cases copied from eval)
  test-dataset.json       # 10 more different cases, for the flywheel
  candidate.sh / .ps1     # runs one case through `tokn agent-run` with the LIVE prompt
  .env.example            # placeholders only
```

### Three splits, three jobs

| File | Cases | Seen by the mutator? | Used for |
|---|---:|---|---|
| `eval-visible.jsonl` | 10 | **yes**: its failures are pasted into the rewrite request | choosing a winner |
| `confirm-heldout.jsonl` | 8 | never | deciding whether the winner may be installed |
| `test-dataset.json` | 10 | never | the before/after flywheel measurement |

The visible set cannot judge the winner. The winner was *chosen* there, from
variants written *while looking at* its failures, so a high visible score can
just mean the prompt memorised those ten cases. That is why the other two
splits exist and why TOKN checks they do not overlap.

## 2. Read the starting prompt (and spot the flaws)

`starting-prompt.md` reads like a reasonable SOP. It contains five errors that
real triage teams make:

| SOP says | The actual rule | Case that exposes it |
|---|---|---|
| Life-threatening = "could have resulted in death" | **Actual** risk of death at the time of the event, not hypothetical | hyponatraemia that *could* have progressed: hospitalization, not life-threatening |
| Hospitalization includes "attended hospital" | **Inpatient admission** or prolonged stay; an ED visit with same-day discharge is not | urticaria treated in ED, sent home: non-serious |
| Expected if the term is in the RSI | Expected only if listed **with the same nature, severity and outcome**. A fatal case of a listed event is unexpected. | fatal interstitial lung disease when ILD is listed: 7-day SUSAR |
| Use the investigator's causality | Related if the investigator **or** the sponsor considers it related | sponsor upgrades optic neuritis to related: 15-day SUSAR |
| (no rule) | Report the **most severe** criterion when several apply | anaphylactic shock with admission: life-threatening, 7-day |

Answer key used by every case:

- **Serious** if death, life-threatening, hospitalization, disability, congenital anomaly or medically important (in that order of precedence).
- **SUSAR** = serious + unexpected + related.
- **Clock**: fatal or life-threatening SUSAR = `7-day`; other SUSAR = `15-day`; otherwise `none`.

The answer is one line, so it can be graded exactly:

```text
SERIOUS=yes CRITERION=hospitalization EXPECTED=no RELATED=yes CLOCK=15-day
```

## 3. Configure the model and install the live prompt

Set the variables in your shell (see `.env.example`; never commit a filled-in
`.env`). Use any provider TOKN supports, such as a hosted Anthropic or OpenAI
model or a local Ollama model.

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=YOUR_MODEL_ID
export ANTHROPIC_API_KEY=...            # your own key
mkdir -p .nospace/prompts
cp starting-prompt.md .nospace/prompts/pv-icsr-triage.md
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = 'anthropic'
$env:NOSPACE_MODEL_NAME     = 'YOUR_MODEL_ID'
$env:ANTHROPIC_API_KEY      = '...'     # your own key
New-Item -ItemType Directory -Force .nospace\prompts | Out-Null
Copy-Item starting-prompt.md .nospace\prompts\pv-icsr-triage.md
```

`.nospace/prompts/pv-icsr-triage.md` is the **live** prompt for template key
`pv/icsr-triage`. The optimizer replaces it, and the flywheel candidate reads it,
so both always measure the same file.

A project prompt override can replace TOKN's own behaviour, so TOKN ignores it
until you trust the folder. Grant only the prompts capability:

```bash
tokn trust . --capability prompts --yes
```

If you skip this, `prompt-optimize` stops with a message naming the file it
refused and the exact `tokn trust` command to run.

## 4. Watch TOKN refuse two unsafe promotions (no model needed)

**4a. `--apply` without confirmation.**

```bash
tokn prompt-optimize --repo-root . --key pv/icsr-triage \
  --eval-set eval-visible.jsonl --apply
```

Observed (exit 1, nothing evaluated):

```text
Error: prompt-optimize: --apply needs held-out confirmation.
The winner is chosen on the same --eval-set whose failures were fed to the mutator, so installing it
unconfirmed can overfit that set and silently change every later session that uses this prompt.
Fix it one of two ways:
  --confirm-set FILE                 a JSONL eval set (same schema as --eval-set) never shown to the mutator;
                                     the winner is installed only if it also beats the live prompt there
  --apply-unconfirmed "<your name>"  install without confirmation; your name is recorded as the approver
```

**4b. A leaky confirmation set.** `confirm-leaky.jsonl` contains two cases
copied from the eval set.

```bash
tokn prompt-optimize --repo-root . --key pv/icsr-triage \
  --eval-set eval-visible.jsonl --confirm-set confirm-leaky.jsonl --apply
```

Observed (exit 1, in 0.2 s, before any model call):

```text
Error: prompt-optimize: --confirm-set shares cases with --eval-set; a confirmation split must never be
shown to the mutator: improveproof: confirmation used the visible split (2 overlapping case(s))
```

## 5. Measure the starting prompt (flywheel cycle 1)

The flywheel runs `test-dataset.json` through the candidate script and grades
each answer with `expect_equals`. These arguments are shared by every run in
steps 5, 6 and 8:

```bash
FW="--dataset test-dataset.json --candidate-cmd 'bash candidate.sh' \
  --model-ref anthropic/YOUR_MODEL_ID \
  --harness-path candidate.sh --harness-path .nospace/prompts/pv-icsr-triage.md \
  --split test --run-timeout 0 --yes"
eval tokn flywheel run $FW --out-dir cycles --cycle 1
```

```powershell
$FW = @('--dataset','test-dataset.json',
  '--candidate-cmd','powershell -NoProfile -ExecutionPolicy Bypass -File candidate.ps1',
  '--model-ref',"anthropic/$env:NOSPACE_MODEL_NAME",
  '--harness-path','candidate.ps1','--harness-path','.nospace/prompts/pv-icsr-triage.md',
  '--split','test','--run-timeout','0','--yes')
tokn flywheel run @FW --out-dir cycles --cycle 1
```

The plan prints a **receipt** before anything runs. Read it:

```text
  receipt   model: declared:anthropic/claude-haiku-5-5
  receipt   harness: verified-bytes:sha256:80368af4…
  receipt   corpus: verified-bytes:sha256:3b03c0d6…
  receipt   split: test
  receipt   grader: passrate-v1;trials=1,k=1
  receipt   not identified: none
```

- `harness` hashes the bytes of the script **and** the live prompt, so a changed prompt is a changed harness.
- `corpus` hashes the dataset. Editing one case changes it.
- `model` is `declared`. TOKN records what you said, and it cannot verify which weights the provider served. The receipt states that limit rather than hiding it.

Observed with claude-haiku-5-5:

```text
inference: ran   cases: 7/10 passed
  pass_rate          0.7000 (target)
gate: BASELINE — baseline established (first cycle — no prior to compare against)
```

## 6. Measure the noise: run the *unchanged* system again

Same prompt, same model, same cases. Any difference is noise.

```bash
eval tokn flywheel run $FW --out-dir noise --cycle 1
eval tokn flywheel run $FW --out-dir noise --cycle 2
```

```powershell
tokn flywheel run @FW --out-dir noise --cycle 1
tokn flywheel run @FW --out-dir noise --cycle 2
```

Observed: **0.60 and 0.60**, against 0.70 in cycle 1. Nothing changed, yet the
score moved by 0.10. A 0.10 "gain" from a prompt edit would therefore prove
nothing.

## 7. Optimize, with held-out confirmation

```bash
tokn prompt-optimize --repo-root . --key pv/icsr-triage \
  --eval-set eval-visible.jsonl \
  --confirm-set confirm-heldout.jsonl --confirm-repeats 2 \
  --generations 2 --variants 3 \
  --provider "$NOSPACE_MODEL_PROVIDER" --model-name "$NOSPACE_MODEL_NAME" \
  --apply --run-timeout 0
```

```powershell
tokn prompt-optimize --repo-root . --key pv/icsr-triage `
  --eval-set eval-visible.jsonl `
  --confirm-set confirm-heldout.jsonl --confirm-repeats 2 `
  --generations 2 --variants 3 `
  --provider $env:NOSPACE_MODEL_PROVIDER --model-name $env:NOSPACE_MODEL_NAME `
  --apply --run-timeout 0
```

Observed (2 min 46 s):

```text
Template: `pv/icsr-triage` · baseline: **0.7000** (7/10)

| candidate | generation | score | passed |
| g1-v1 | 1 | 1.0000 | 10/10 |
| g1-v2 | 1 | 1.0000 | 10/10 |
| g1-v3 | 1 | 1.0000 | 10/10 |
| g2-v1 | 2 | 1.0000 | 10/10 |
| g2-v2 | 2 | 1.0000 | 10/10 |
| g2-v3 | 2 | 0.9000 | 9/10  |

**Winner: g1-v1** — score 1.0000, gain +0.3000.

## Confirmation
| incumbent (mean of 2) | 0.5625 |
| nominee               | 1.0000 (8/8) |

- Noise band: 0.2500 (repeated-evaluations, 2 repeat(s))
- Claim: `demonstrated_gain` (Δ +0.4375, margin 0.2500)
- Contamination (embedded_task_material): `not_found`
- Status: **confirmed**
- Transaction state: `applied`
- Live override changed: yes
```

How to read it:

1. **Visible 10/10 means nothing on its own.** Five of six variants scored 10/10 on the set the mutator was looking at.
2. **The held-out split decides.** The live prompt was evaluated twice on the 8 unseen cases (0.5625 mean, with a noise band of 0.25 from the two repeats). The nominee scored 8/8. The gain of +0.4375 is larger than the band, so the claim is `demonstrated_gain`.
3. **Contamination check.** TOKN looked for held-out case text inside the winning prompt and found none. A prompt that pasted the answers in would be rejected here.
4. **Transaction.** Before installing, TOKN records the live file's digest and re-checks it, then verifies the install or rolls it back. A prompt edited by someone else mid-run is not silently overwritten.

Everything is in `.nospace/promptopt/`: `REPORT.md`, `report.json`, and every
candidate under `candidates/`.

**What changed in the prompt.** Diff the live file against `starting-prompt.md`.
In our run the winner had fixed all five flaws from step 2. It changed "could
have resulted in death" to *immediate risk at the time of the event*. It said
that an ED visit ending in same-day discharge is *not* hospitalization,
"however long the visit". It added the precedence order, required severity and
outcome to match for expectedness, and accepted investigator **or** sponsor
causality. Read the diff yourself: an optimizer that scores well can still
encode a rule your SOP does not allow.

## 8. Re-measure, gated on noise and identity (flywheel cycle 2)

```bash
eval tokn flywheel run $FW --out-dir cycles --cycle 2 \
  --baseline cycles/cycle-1.json --strict --noise-reports noise
```

```powershell
tokn flywheel run @FW --out-dir cycles --cycle 2 `
  --baseline cycles/cycle-1.json --strict --noise-reports noise
```

Observed:

```text
  receipt   harness: verified-bytes:sha256:e6da04c2…     <- new prompt, new hash
  receipt   corpus: verified-bytes:sha256:3b03c0d6…      <- same cases
  noise:    band ±0.1633 from 3 frozen run(s) incl. the baseline (repeated-evaluations, z=2); target must beat max(0.005, band)
  strict:   baseline must carry a comparable receipt (only model/harness may differ); missing metrics regress

inference: ran   cases: 10/10 passed
  pass_rate          1.0000  Δ+0.3000 (better) (target)
  mean_latency_ms    12124.5650  Δ+3241.8060 (better)
gate: PASSED — target "pass_rate": demonstrated_gain (Δ=+0.3000 beyond margin 0.1633 incl. noise band 0.1633)
      and no other metric regressed
```

- The band comes from **three** runs of the unchanged system: 0.70, 0.60 and 0.60. The cycle-1 baseline counts as a frozen run because its receipt is identical to the noise runs.
- The gain of +0.30 is larger than ±0.163, so it is **demonstrated**. A +0.10 gain would have been reported as `no_demonstrated_gain`.
- Deltas are oriented so that positive always means *better*. For latency, `+3241` means about 3.2 s **faster** per case.
- `--strict` would have refused the comparison if the dataset, split or grader had changed between cycles.

## 9. Explain the identity of the comparison

```bash
tokn flywheel compare --reports cycles/cycle-1.json,cycles/cycle-2.json --explain-identity
```

Observed:

```text
identity: cycles/cycle-1.json -> cycles/cycle-2.json (model and harness may differ)
comparable: yes
axis             status   allowed  base -> candidate
model            same     yes      declared:anthropic/claude-haiku-5-5 -> declared:anthropic/claude-haiku-5-5
harness          changed  yes      verified-bytes:sha256:80368af4… -> verified-bytes:sha256:e6da04c2…
corpus           same     no       verified-bytes:sha256:3b03c0d6… -> verified-bytes:sha256:3b03c0d6…
split            same     no       test -> test
grader_epoch     same     no       passrate-v1;trials=1,k=1 -> passrate-v1;trials=1,k=1
metric_contract  same     no       target=pass_rate;dir=higher -> target=pass_rate;dir=higher
budget_policy    same     no       timeout=2m0s -> timeout=2m0s
cases            same     no       10 -> 10
changed: harness
not identified: none
incompatible: none
note: model is declared, not verified
```

Exactly one thing changed, the harness, which here means the prompt. That is the
whole claim: *this prompt, with everything else held fixed, gains 0.30 on unseen
cases, beyond the measured noise*.

**Try breaking it.** Edit one `expect_equals` in `test-dataset.json` and re-run
step 8. `corpus` now shows `changed` with `allowed: no`, and `--strict`
refuses to gate.

## What to look for

| Question a reviewer asks | Where the evidence is |
|---|---|
| Was the winner judged on data it was tuned on? | Step 7 confirmation table: held-out 8/8 vs 0.5625 |
| Could the confirm set have leaked? | Step 4b refusal; step 7 contamination `not_found` |
| Is the gain bigger than run-to-run noise? | Step 6 noise runs; step 8 band ±0.163 vs Δ +0.30 |
| Did anything besides the prompt change? | Step 9 identity table |
| Who approved the install? | `.nospace/promptopt/report.json` transaction (confirmed, not a named override) |

## Results will vary

These numbers come from one run with claude-haiku-5-5. Different models, and
repeat runs of the same model, give different scores. That is the point of
steps 6 and 8. With a stronger model the baseline may already be high, which
leaves little room for a demonstrated gain. With a weaker model the optimizer
may not find a variant that survives confirmation. In that case TOKN keeps the
live prompt and says why, which is the correct outcome.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `template key "pv/icsr-triage" has a project override at …, but it was refused because this workspace is not trusted` | Run `tokn trust . --capability prompts --yes` (step 3). |
| Every case fails instantly, `run status 'failed'` in `scratch/*/result.json` | Provider auth or model id. Run `tokn doctor --provider <name>`. |
| `400 … tools.N.custom.name` or `input_schema.type` from the provider | An MCP server in your config exposes a tool name or schema the provider rejects. Upgrade to v0.3.122+, or pass `--mcp-disabled` in the candidate script. |
| Cases time out at 30 s | Add `--run-timeout 0` (the global default is 30 s). |
| Windows PowerShell 5.1 stops on a red stderr line | Use the shipped `candidate.ps1`, which relaxes `$ErrorActionPreference` around the native call. |
| `noise: UNCALIBRATED` | You need at least two frozen reports under `noise/`. |
| Don't run step 7 while step 5, 6 or 8 is running | The optimizer rewrites the live prompt that the candidate reads. |

## Clean up

```bash
rm -rf scratch cycles noise .nospace .tokn && tokn trust revoke .
```

```powershell
Remove-Item -Recurse -Force scratch, cycles, noise, .nospace, .tokn -ErrorAction SilentlyContinue; tokn trust revoke .
```

Observed on TOKN v0.3.122, Windows 11, claude-haiku-5-5.
