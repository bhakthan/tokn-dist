# Example: Computational Biology Gates

> "Merge the two cohort VCFs and run differential expression on the counts table, then report the top genes."

This prompt looks routine. A general-purpose LLM will often just run the merge and the test. The `compbio` domain mode stops the silent errors first: mixed genome builds, unnormalized indels, missing ploidy, and uncorrected p-values.

| Capability | What the gate does |
|---|---|
| `genome_build_gate` | Blocks coordinate-aware tools when builds are missing or mismatched. |
| `vcf_normalization_gate` | Blocks `merge_vcfs` until inputs are left-aligned and contig-consistent. |
| `ploidy_gate` | Blocks variant callers that have no explicit ploidy. |
| MTC gate | Requires a named correction method and an adjusted-p output column. |
| `reproducibility_attestation` | Writes a provenance record when a provenance path is set. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The `compbio` mode and its gates ship in this version. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. Community grants only `domains:basic`. | `tokn license features` shows `domains:compbio` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

Activate the trial once per machine:

```bash
tokn license trial
```

```powershell
tokn license trial
```

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

Run the demo outside this repo. TOKN writes `.nospace/` state and output files into the working folder.

```bash
cp -r examples/compbio-gates ~/compbio-run   # any scratch folder you own
cd ~/compbio-run
```

```powershell
Copy-Item -Recurse examples\compbio-gates $HOME\compbio-run
Set-Location $HOME\compbio-run
```

## 2. Configure the LLM

Use the same placeholders as [grid-screening](../grid-screening/README.md#2-configure-the-llm). Replace them with your own values.

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<your model name>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<your model name>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

For other providers, see [../../SETUP.md](../../SETUP.md).

## 3. Optional: check the reference builds yourself

The two VCFs declare different genome builds on purpose. You can confirm this before TOKN runs.

```bash
grep -m1 "reference=" demo-input/cohort_chr1.vcf demo-input/cohort_chr2.vcf
```

```powershell
Select-String -Path demo-input\cohort_chr1.vcf, demo-input\cohort_chr2.vcf -Pattern "reference=" | Select-Object -First 2
```

## 4. Run the task

```bash
tokn agent-run --mode compbio --repo-root . --prompt-file prompt.md --max-steps 25 --no-confirm
```

```powershell
tokn agent-run --mode compbio --repo-root . --prompt-file prompt.md --max-steps 25 --no-confirm
```

If the run stops early, raise `--max-steps`.

## 5. Check the result

Good behavior looks like this:

| # | Expectation | Pass signal |
|---|---|---|
| 1 | Both VCFs are inspected | `inspect_vcf` runs on each file |
| 2 | The genome-build gate fires | A build-mismatch block or a declared-build request appears |
| 3 | Normalization comes before merge | `normalize_vcf` runs first, or the gate explains why |
| 4 | No silent merge | The merge does not happen on mismatched builds |
| 5 | Multiple-testing correction is explicit | The method and adjusted-p column are named |
| 6 | Reproducibility tooling is used | `pin_environment` or `attest_reproducibility` runs |

Score it by hand. Six passes count as PASS. Four or five count as a partial pass. Fewer than four, or any gate that is wrongly bypassed, is FAIL.

## What to look for

- The model stops at the build gate and asks which build to use, instead of guessing.
- The merge is delayed until normalization is done.
- The DE summary names the correction method, such as BH.
- Soft points: a batch-effect caveat for `counts.csv` (it has no batch column), and an FDR threshold stated in the answer.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:compbio` is missing | Run `tokn license trial`, then `tokn license features`. |
| `tokn: command not found` | Install TOKN v0.3.57 or newer and open a new terminal. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME`, and your key. See [../../SETUP.md](../../SETUP.md). |
| The run stops at the step limit | Increase `--max-steps`. |
| The model merges without a gate | Confirm `--mode compbio` is set. Other modes do not load this gate. |
