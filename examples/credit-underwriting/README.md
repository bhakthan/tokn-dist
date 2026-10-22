# Example: Credit Covenant Review with Finrisk Gates

> "Recompute the covenants, check the dates, draft the memo, and let the gates say when it is not ready."

This example runs a finance-domain review of a synthetic small-business loan file. The applicant,
figures, and covenant limits are invented. You will recompute three covenant ratios, compare them
with proposed limits, and have the agent draft an underwriting memo. TOKN's finrisk mode enforces
gates on the report as it moves through its stages, so a memo that makes an unsupported claim or
skips the disclaimer does not get marked complete.

This is a training exercise. It is not financial advice and does not produce a credit decision.

For the domain background, see [finrisk-system-one](../finrisk-system-one/README.md), which covers
the risk-analysis workflow in more depth. This example focuses on the underwriting review and the
gates it passes through.

| Capability | How this example uses it | Command or check |
|---|---|---|
| Finrisk domain mode | Runs the review under the finrisk workflow | `tokn agent-run --mode finrisk` |
| Temporal consistency gate | Confirms the interim and annual dates are ordered correctly | Gate `temporal_consistency` |
| Citation validation gate | Requires drafted claims to point to a source | Gate `citation_validation` |
| Materiality language gate | Requires materiality wording to be tied to figures | Gate `materiality_language` |
| Disclaimer gate | Requires the standard disclaimer before distribution | Gate `disclaimer` |
| Offline ratio check | Recomputes ratios with no model call | `check_ratios.py` |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | Finrisk mode and these gates are in this version | `tokn version` |
| Trial tier (or a licence with the finrisk feature) | Domain modes are not in the free tier | `tokn license status` |
| Python 3.9 or newer | Runs the offline ratio checker | `python --version` |
| An LLM provider (step 4 only) | The agent drafts the memo | See step 4 and [SETUP.md](../../SETUP.md) |

**Licence tier:** domain modes such as finrisk need a trial or a licence that includes the domain.
The community tier does not include them. Step 1 starts a trial. A trial sends one anonymous install
registration. To opt out, set `TOKN_NO_TELEMETRY=1` before you run it.

**What leaves your machine:** steps 1–3 send nothing beyond the trial registration. Step 4 sends the
prompt, the applicant file, and tool output to the LLM provider you configure. The file is synthetic.

## 1. Start the trial and confirm the features

**bash**
```bash
tokn license status
tokn license trial
tokn license features
```

**PowerShell**
```powershell
tokn license status
tokn license trial
tokn license features
```

Expected, not a recorded run: `license features` lists the domain features, including finrisk, once
the trial is active. If finrisk is missing, the trial did not start. Run `tokn license status` and
read the message.

## 2. Create a separate work folder

Copy the applicant file into a work folder. Do not run the agent inside this example folder.

**bash**
```bash
mkdir -p credit-review-work/applicant
cp applicant/synthetic-file-0042.md credit-review-work/applicant/
cp prompt.md credit-review-work/
```

**PowerShell**
```powershell
New-Item -ItemType Directory -Force -Path credit-review-work\applicant | Out-Null
Copy-Item applicant\synthetic-file-0042.md credit-review-work\applicant\
Copy-Item prompt.md credit-review-work\
```

## 3. Recompute the covenants offline (no model)

`check_ratios.py` reads the applicant file and recomputes the three ratios. It makes no network call
and writes nothing.

**bash**
```bash
python check_ratios.py applicant/synthetic-file-0042.md
echo "exit code: $?"
```

**PowerShell**
```powershell
python check_ratios.py applicant\synthetic-file-0042.md
"exit code: $LASTEXITCODE"
```

Expected, not a recorded run: three `PASS` lines, with the computed values near 2.27 for debt service
coverage, 3.04 for leverage, and 1.29 for the current ratio, against the proposed limits of 1.25,
3.50, and 1.20. Exit code 0. A `BREACH` line exits with code 3.

Check the arithmetic by hand before you read the agent's memo. The agent's answer should match these
figures, and any difference is something to investigate.

## 4. Optional: draft the memo with the finrisk workflow

Configure the LLM with placeholders. Replace each `<...>` with your own value.

**bash**
```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<your model name>
export ANTHROPIC_API_KEY=<your key>
tokn agent-run --prompt-file credit-review-work/prompt.md \
  --repo-root ./credit-review-work --mode finrisk \
  --max-steps 30 --no-confirm --output-format json > credit-review-result.json
echo "exit code: $?"
```

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<your model name>"
$env:ANTHROPIC_API_KEY = "<your key>"
tokn agent-run --prompt-file credit-review-work\prompt.md `
  --repo-root .\credit-review-work --mode finrisk `
  --max-steps 30 --no-confirm --output-format json | Out-File -Encoding utf8 credit-review-result.json
"exit code: $LASTEXITCODE"
```

The agent should write `credit-review-work/memo.md`.

## 5. Read the gate results

The finrisk workflow moves a review through stages, and each stage has a gate. Read the gate status
for the memo.

| Gate | What it checks in this review | What a failure looks like |
|---|---|---|
| `temporal_consistency` | Interim period end falls before the annual reference date | The memo treats interim figures as annual, or the dates are reversed |
| `citation_validation` | Each factual claim points to a source in the file | The memo cites a rule or number that the file does not contain |
| `materiality_language` | Materiality statements are tied to a figure | "Material" appears with no number behind it |
| `disclaimer` | The memo ends with the standard disclaimer | The memo is missing the not-advice statement |

Each gate passes or stays open. A memo with an open gate is not ready for distribution, even if the
text reads well.

## What to look for

- The three recomputed ratios in the memo match `check_ratios.py`.
- The memo does not invent any figure that is absent from the applicant file.
- The memo says the interim statement is earlier than the annual reference date, and says why that
  is correct.
- The memo ends with the disclaimer, and it says the review is a synthetic training exercise.
- Any gate that stays open is named in the result. Treat that as the finding, not as noise.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `finrisk` is not accepted as a mode | No trial or licence with the finrisk feature | Run `tokn license trial`, then `tokn license features` |
| `check_ratios.py` prints `FAIL: missing fields` | The applicant file was edited and a key was removed | Restore the key from the original file |
| Ratios differ from the expected values | A figure was edited | Recompute by hand and compare with the file |
| Memo is missing | The agent did not reach the drafting stage in the step budget | Raise `--max-steps` and re-run in the work folder |
| No model response | LLM variables are not set in this shell | Set them again |
| Trial message about registration | Anonymous install registration | Set `TOKN_NO_TELEMETRY=1` before `tokn license trial` to opt out |
