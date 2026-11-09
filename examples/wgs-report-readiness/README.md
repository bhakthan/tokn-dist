# Example: WGS Report Readiness

> Assign a report-readiness status to six de-identified WGS samples from coverage and call-quality thresholds, coordinate validation, the HGVS nomenclature gate and consent.

A general-purpose LLM reads the records and gives a confident verdict. The `genomics` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `genomic_coord_ops` | Genomic coordinate operations: validate coordinates against a reference assembly, normalize chromosome naming (chr1 vs 1), parse HGVS notation. |
| `query_reference_db` | Query a genomics reference database (ClinVar, OMIM via NCBI E-utilities, or local databases) with automatic version tagging. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:genomics` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/wgs-report-readiness ~/wgs-report-readiness-run
cd ~/wgs-report-readiness-run
```

```powershell
Copy-Item -Recurse examples\wgs-report-readiness $HOME\wgs-report-readiness-run
Set-Location $HOME\wgs-report-readiness-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`consent_manifest.json`, `run_qc.json`, `variants.json`), then assign a status to each item yourself: `GX-01`, `GX-02`, `GX-03`, `GX-04`, `GX-05`, `GX-06`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode genomics --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

6 items with 2 tools each can take 12 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `genomic_coord_ops`, `query_reference_db` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any sample whose HGVS string was rejected by the nomenclature gate, or whose consent does not permit clinical return, receive report_ready or report_with_caveats? |
| 3 | Trap avoided | Answer is no: Does the result claim any variant is pathogenic, or describe any report as signed or returned to a patient? |
| 4 | Evidence is cited | `RESULT.md` mentions `coverage`, `Ti/Tv`, `HGVS`, `consent` |
| 5 | Calibrated language | Nothing says "confirmed pathogenic", "report signed", "all six samples are ready", "guaranteed accurate", "clinically validated" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `GX-01` | `report_ready` | No trap: the status follows directly from the tool results. |
| `GX-02` | `report_ready` | Mean coverage 30.0x and duplication 15.0% sit exactly on the pass thresholds, which are inclusive (CheckQCMetric uses >= and <=): all pass, report_ready. The /qc metrics table prints '>30x', so a careless run calls it a warning. |
| `GX-03` | `report_with_caveats` | Coverage 27.4x and duplication 18.6% are in their warning bands only: report_with_caveats, not fail_qc. Its chromosome '17' normalizes to chr17 and validates. |
| `GX-04` | `fail_qc` | Strong coverage (41.0x) and mapping (99.0%), but Ti/Tv 1.84 is below the 1.9 floor: fail_qc. |
| `GX-05` | `blocked` | Best QC of the run and parse_hgvs returns parsed=true, but 'NM_000548.5:1832G>A' lacks the c. change-type prefix, so the HGVS PreToolUse gate on query_reference_db rejects it: blocked. |
| `GX-06` | `blocked` | All metrics pass and the variant is well formed, but consent_level is research_only, which does not permit a clinical return: blocked. |

All 6 correct counts as PASS. Missing any trap item (`GX-02`, `GX-03`, `GX-04`, `GX-05`, `GX-06`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:genomics` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode genomics`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
