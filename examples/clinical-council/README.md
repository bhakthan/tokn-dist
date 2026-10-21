# Example: Clinical Council Convergence and Infographics

> "Three reviewers look at a synthetic precision-medicine case. Do they agree that an uncertain variant may not be listed as actionable?"

Several reviewers answer one question independently. TOKN's `council chair` then reads their verdicts and reports whether they converge, and whether the result is grounded and specified enough to use. A second, optional step renders two infographics about the case. The data here is fully synthetic, and the framing follows the safety gates of the `precmed` domain.

For the precision-medicine mode itself, including the trial, the case lifecycle and the gate runs, see [../precmed-variant/README.md](../precmed-variant/README.md). This example does not repeat that walkthrough.

| Capability | What it shows |
|---|---|
| `tokn council chair` | Convergence over blind, grounded peer verdicts. Reads local files only. |
| `--require-spec` (default on) | A verdict without a consumed spec is barred from the consensus. |
| `council-verdict/1.1` bundles | One verdict per file, each with a peer, a disposition, and provenance. |
| `tokn docs illustrate` (optional) | Renders infographics from a spec. Skipped cleanly when no image endpoint is set. |
| `precmed` safety framing | Variants of uncertain significance are not actionable. Research and decision support only. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The `council` and `docs illustrate` commands ship in this version. | `tokn version` |
| 14-day trial (`tokn license trial`) | The case follows the `precmed` domain mode, which needs the trial. The `council` command itself was not checked for a licence gate. | `tokn license` |
| Image endpoint (optional) | Needed only for the infographic step. Without it the step is skipped. | See step 5 |
| An LLM provider | Not needed for the convergence step. Only needed if you produce new verdicts. | See [../../SETUP.md](../../SETUP.md) |

Activate the trial once per machine:

```bash
tokn license trial
```

```powershell
tokn license trial
```

Starting the trial sends a one-time anonymous install registration, as described in [../precmed-variant/README.md](../precmed-variant/README.md).

**What leaves your machine:** the convergence step reads local JSON and makes no model call. The image step, if you run it, sends the prompts in `illustrate-spec.json` to the image endpoint you configure. Those prompts contain only synthetic text.

## 1. Copy the example to a scratch folder

Run the example outside this repo. TOKN writes `.nospace/` state and any image output into the working folder.

```bash
cp -r examples/clinical-council ~/council-run   # any scratch folder you own
cd ~/council-run
```

```powershell
Copy-Item -Recurse examples\clinical-council $HOME\council-run
Set-Location $HOME\council-run
```

## 2. Read the question and the three verdicts

The question is `SYN-Q-0001`: may the summary list an uncertain variant as actionable? Each verdict is a separate file under `verdicts/`. Each one is synthetic and names a placeholder peer.

| Peer | Role | Disposition | Convergence |
|---|---|---|---|
| `reviewer-alpha` | clinical-genomics reviewer | approve | 0.82 |
| `reviewer-beta` | research-methods reviewer | approve_with_notes | 0.78 |
| `reviewer-gamma` | data-governance reviewer | approve_with_notes | 0.70 |

## 3. Check the bundles offline

This check reads local files only. It confirms the schema tag, the disposition values, the convergence range, and that each bundle names a `consumesSpec`.

```bash
python check_council.py verdicts/peer-alpha.json verdicts/peer-beta.json verdicts/peer-gamma.json illustrate-spec.json
```

```powershell
python check_council.py verdicts\peer-alpha.json verdicts\peer-beta.json verdicts\peer-gamma.json illustrate-spec.json
```

Expected, not a recorded run: one `ok` line per file.

## 4. Run the convergence chair

```bash
tokn council chair verdicts/peer-alpha.json verdicts/peer-beta.json verdicts/peer-gamma.json
```

```powershell
tokn council chair verdicts\peer-alpha.json verdicts\peer-beta.json verdicts\peer-gamma.json
```

The defaults are a convergence threshold of 0.75 and a minimum of 2 grounded verdicts. Add `--json` for a machine-readable consensus. The chair does not call a model.

Expected, not a recorded run: a consensus with three verdicts and a majority disposition of approval. The exact printed layout was not checked against a live run.

## 5. Optional: render the infographics

This step needs an image endpoint. First, run a preflight with no endpoint set. TOKN reports what is missing and exits without an error. That is the graceful no-image path.

```bash
tokn docs illustrate --spec illustrate-spec.json --dry-run
```

```powershell
tokn docs illustrate --spec illustrate-spec.json --dry-run
```

To render for real, set two placeholders. Replace them with your own values. Do not commit them.

```bash
export AZURE_OPENAI_ENDPOINT=<your image endpoint URL>
export AZURE_OPENAI_IMAGE_DEPLOYMENT=<your image deployment name>
tokn docs illustrate --spec illustrate-spec.json --out-dir images --format png --limit 2
```

```powershell
$env:AZURE_OPENAI_ENDPOINT = "<your image endpoint URL>"
$env:AZURE_OPENAI_IMAGE_DEPLOYMENT = "<your image deployment name>"
tokn docs illustrate --spec illustrate-spec.json --out-dir images --format png --limit 2
```

Check how the command authenticates to the endpoint with `tokn docs illustrate --help` before the real run. The authentication method was not verified for this walkthrough.

To check the provenance of a rendered image:

```bash
tokn docs watermark images/synthetic-case-functional.png
```

```powershell
tokn docs watermark images\synthetic-case-functional.png
```

Skip this step if you have no endpoint. Steps 3 and 4 do not depend on it.

## What to look for

- All three verdicts name the same question ID, `SYN-Q-0001`. A mismatch means the bundles answer different questions.
- Every verdict says the variant is not actionable. The disagreement is only about wording and risk, not the outcome.
- The `consumesSpec` is present in each verdict. Remove it from one file and rerun step 4 to see `--require-spec` bar that verdict.
- The infographic prompts use only synthetic text and placeholder labels.

## Safety framing

The `precmed` domain enforces these gates. Their names are the ones in the domain code. This example demonstrates the reasoning they require. The gates themselves run inside an agent session, covered by the precmed walkthrough.

| Gate | What it requires |
|---|---|
| `acmg_vus_gate` | A variant of uncertain significance is not treated as actionable. |
| `pgx_critical_contraindication` | A critical pharmacogenomic contraindication blocks the output. |
| `somatic_germline` | Somatic and germline findings are kept separate. |
| `consent` | Clinical use requires recorded consent. |
| `research_phi` | Research output must not contain identifiers. |

This is research and decision support. It is not clinical advice, and nothing in this example should guide patient care.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tokn: command not found` | Install TOKN v0.3.57 or newer and open a new terminal. |
| Verdict rejected as missing `consumesSpec` | Add the spec reference to the verdict, or pass `--require-spec=false` only for a dry run. |
| Consensus does not reach the threshold | Expected for weak verdicts. Check each `convergenceMetric`. |
| `docs illustrate` prints guidance and exits | No image endpoint is set. This is the graceful path. Steps 3 and 4 still work. |
| `docs illustrate` fails after setting the endpoint | Check the endpoint and deployment placeholders, then see the authentication note in step 5. |
| `precmed` mode refused | Run `tokn license trial` (once per machine), then `tokn license` to confirm. |
