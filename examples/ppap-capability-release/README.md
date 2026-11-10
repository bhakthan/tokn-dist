# Example: Capability Release Decision

> Assign a release status to each of seven characteristics of synthetic supplier lot LOT-2401 from raw SPC subgroups, MSA evidence and the PFMEA, before the lot is released to production.

A general-purpose LLM reads the records and gives a confident verdict. The `mfgquality` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `mfgq_control_chart` | Control chart with limits computed from PROCESS data (never from spec limits). |
| `mfgq_capability_study` | Process capability after a statistical-control check. |
| `mfgq_msa_grr` | Crossed gage R&R. |
| `mfgq_pfmea_score` | Score PFMEA rows. |
| `mfgq_release_decision` | Per-characteristic release decision running every gate. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.83 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:mfgquality` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/ppap-capability-release ~/ppap-capability-release-run
cd ~/ppap-capability-release-run
```

```powershell
Copy-Item -Recurse examples\ppap-capability-release $HOME\ppap-capability-release-run
Set-Location $HOME\ppap-capability-release-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`msa.json`, `pfmea.json`, `spc_data.json`, `supplier_submission.json`), then assign a status to each item yourself: `CH-01`, `CH-02`, `CH-03`, `CH-04`, `CH-05`, `CH-06`, `CH-07`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode mfgquality --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

7 items with 5 tools each can take 35 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `mfgq_control_chart`, `mfgq_capability_study`, `mfgq_msa_grr`, `mfgq_pfmea_score`, `mfgq_release_decision` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any characteristic with a run-rule signal on its X-bar or R chart receive a Cpk-based status (release, release_with_caveats or reject) instead of hold? |
| 3 | Trap avoided | Answer is no: Does the result accept CH-04's supplier control limits, which equal the drawing tolerance, as process control limits? |
| 4 | Trap avoided | Answer is no: Does CH-06 pass because its RPN (54) is low, despite severity 9 with no recorded action? |
| 5 | Trap avoided | Answer is no: Is CH-05's capability used for release even though its gauge study shows %GRR above 30%? |
| 6 | Evidence is cited | `RESULT.md` mentions `Cpk`, `Ppk`, `statistical control`, `%GRR`, `ndc`, `severity`, `action priority` |
| 7 | Calibrated language | Nothing says "zero defects guaranteed", "guaranteed capable", "100% defect-free", "root cause confirmed", "no risk of escape" |
| 8 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `CH-01` | `release` | No trap: the status follows directly from the tool results. |
| `CH-02` | `release_with_caveats` | The raw 10x3x3 gauge study gives a %GRR between 10% and 30% with ndc of at least 5: conditionally acceptable, so the status is release_with_caveats, not release and not blocked. |
| `CH-03` | `hold` | The supplier claims Cpk 2.6 and the within-subgroup estimate is indeed above 2, but the mean shifts upward from subgroup 14 onward: the X-bar chart (limits from all 25 subgroups) shows points beyond 3 sigma (subgroups 15 and 20) plus 2-of-3, 4-of-5 and 8-on-one-side signals. The process is not in statistical control, so capability is not assessable and the status is hold, not release. |
| `CH-04` | `blocked` | The supplier's control limits (UCL 8.040, LCL 7.960, source 'drawing tolerance') are the specification limits. The control_limits_from_process gate blocks: control limits must be computed from the process data, never from the spec. The raw data are actually capable, which tempts a release. |
| `CH-05` | `blocked` | One-sided flatness specification with in-control, capable-looking data, but the raw gauge R&R study gives %GRR above 30% (and ndc below 5): the measurement system is unacceptable, so the data cannot support a release. |
| `CH-06` | `blocked` | Excellent capability (Cpk about 2.6) and RPN 54 (S9 O2 D3, action priority L) look harmless, but severity 9 with no recorded action triggers the severity_requires_action gate regardless of RPN. |
| `CH-07` | `reject` | In control and normal, so capability is assessable, but Cpk and Ppk are about 1.2, below the 1.33 policy minimum: reject, not hold. |

All 7 correct counts as PASS. Missing any trap item (`CH-02`, `CH-03`, `CH-04`, `CH-05`, `CH-06`, `CH-07`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:mfgquality` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode mfgquality`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
