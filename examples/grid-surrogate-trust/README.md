# Example: Grid Foundation-Model Trust

> Independently verify six GridSFM surrogate AC-OPF predictions and assign each a fail-closed trust disposition before it reaches the operator desk.

A general-purpose LLM reads the records and gives a confident verdict. The `gridfm` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `verify_surrogate_solution` | Independently verify a GridSFM surrogate AC-OPF prediction against power-flow physics (voltage bounds, generator limits, thermal limits, power balance, flow-voltage consistency). |
| `evaluate_warm_start` | Quantify the warm-start speedup of seeding a classical AC-OPF solver with a surrogate prediction. |
| `select_model_tier` | Select the GridSFM model tier validated for a given grid size. |
| `assess_ood` | Assess whether a grid is out-of-distribution / over-scale for a GridSFM tier and return the implied confidence cap. |
| `list_verification_checks` | List the independent physics checks the harness runs on a surrogate solution, the lifecycle phases, and the current tolerances. |

This is the single-agent version of the [gridfm relay walkthrough](../domain-relay/walkthroughs/gridfm/README.md). It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:gridfm` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/grid-surrogate-trust ~/grid-surrogate-trust-run
cd ~/grid-surrogate-trust-run
```

```powershell
Copy-Item -Recurse examples\grid-surrogate-trust $HOME\grid-surrogate-trust-run
Set-Location $HOME\grid-surrogate-trust-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`deployment_context.json`, `predictions.json`, `warm_start_timings.json`), then assign a status to each item yourself: `PRED-A`, `PRED-B`, `PRED-C`, `PRED-D`, `PRED-E`, `PRED-F`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode gridfm --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

6 items with 5 tools each can take 30 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `verify_surrogate_solution`, `evaluate_warm_start`, `select_model_tier`, `assess_ood`, `list_verification_checks` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any prediction receive operational_advisory or warm_start_only because of the surrogate's own feasibility flag or confidence rather than the independent verifier's result? |
| 3 | Trap avoided | Answer is no: Does the result describe any prediction with confidence above the 0.30 out-of-distribution cap implied by the 3,700-bus full network on the GridSFM-Open tier? |
| 4 | Evidence is cited | `RESULT.md` mentions `surrogate`, `disposition`, `residual`, `confidence cap` |
| 5 | Calibrated language | Nothing says "proven optimal", "100% reliable", "physically guaranteed", "trusted unconditionally", "no verification needed" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `PRED-A` | `operational_advisory` | No trap: the status follows directly from the tool results. |
| `PRED-B` | `hold_for_review` | Physics is identical to PRED-A and passes, but the surrogate self-reports 'infeasible' — REVIEW, not operational. |
| `PRED-C` | `reject` | Highest self-reported confidence (0.97, 'feasible') and every voltage, limit and flow is inside bounds, but generation 1.88 pu vs load 2.00 + losses 0.03 leaves a -0.15 pu power-balance residual — REJECTED. |
| `PRED-D` | `operational_advisory` | Boundary item: G2 exactly at Pmax 1.00, B1 exactly at Vmax 1.05, L23 exactly at its 0.40 pu rating and L13 at 0.40 — all limits are strict, so it is OPERATIONAL. |
| `PRED-E` | `reject` | Disposition is WARM_START (B3 voltage 0.93 < 0.95, L13 1.06 > 1.00), which looks salvageable, but the seeded solve took 4.6 s vs 4.2 s cold (speedup 0.91 < 1.0) — reject. |
| `PRED-F` | `warm_start_only` | Only violation is G2 reactive output 0.62 > Qmax 0.50; speedup 1.75 >= 1.0 — warm_start_only, not operational. |

All 6 correct counts as PASS. Missing any trap item (`PRED-B`, `PRED-C`, `PRED-D`, `PRED-E`, `PRED-F`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:gridfm` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode gridfm`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
