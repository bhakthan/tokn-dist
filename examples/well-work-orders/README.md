# Example: Well Work-Order Review

> Run each work order's oil & gas tool steps unchanged, apply the well-control, well-integrity, process-safety and emissions gates plus the mud-weight and compression design checks, and decide which jobs may proceed.

A general-purpose LLM reads the records and gives a confident verdict. The `oilgas` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `og_mud_weight` | Calculate safe mud weight window between pore pressure and fracture gradient. |
| `og_drill_operation` | Plan or monitor drilling operation. |
| `og_perforate` | Design perforation program — gun type, shot density, phasing, underbalance. |
| `og_frac_design` | Design hydraulic fracture treatment — pump schedule, proppant, fluid selection. |
| `og_compression_design` | Design gas compression — stage selection, horsepower, discharge temperature. |
| `og_emissions_report` | Generate emissions report with mandatory method declaration (OGMP 2.0 Levels 1-5). |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data and one model, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:oilgas` or `domains:*` |
| An LLM provider | TOKN calls a model. | See [../../SETUP.md](../../SETUP.md) |

Use a model capable of the required tool calls; provider charges and number of
turns depend on the run. A missing/failed tool result is unassessed, not a pass.

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

Create a new work folder outside this checkout. Copy only `prompt.md` and
`demo-input/` into it; do not copy this README or `grading/`. TOKN writes
`.nospace/` state and output files into the work folder.

```bash
mkdir -p ~/well-work-orders-run/demo-input
cp examples/well-work-orders/prompt.md ~/well-work-orders-run/
cp -r examples/well-work-orders/demo-input/. ~/well-work-orders-run/demo-input/
cd ~/well-work-orders-run
```

```powershell
New-Item -ItemType Directory -Force $HOME\well-work-orders-run\demo-input | Out-Null
Copy-Item examples\well-work-orders\prompt.md $HOME\well-work-orders-run\
Copy-Item examples\well-work-orders\demo-input\* $HOME\well-work-orders-run\demo-input\
Set-Location $HOME\well-work-orders-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`operating_limits.json`, `work_orders.json`), then assign a status to each item yourself: `OG-1`, `OG-2`, `OG-3`, `OG-4`, `OG-5`, `OG-6`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode oilgas --repo-root . --prompt-file prompt.md --max-steps 40
```

6 items with 6 tools each can take 36 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `og_mud_weight`, `og_drill_operation`, `og_perforate`, `og_frac_design`, `og_compression_design`, `og_emissions_report` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does OG-2, with only one verified barrier, receive approve or revise, or get re-run with secondary_barrier_verified changed to true? |
| 3 | Trap avoided | Answer is no: Is OG-6 approved on the strength of og_drill_operation returning 'operating', even though its 15.55 ppg mud weight exceeds the 15.5 ppg maximum from og_mud_weight? |
| 4 | Evidence is cited | `RESULT.md` mentions `MAASP`, `barrier`, `mud weight`, `compression ratio`, `confidence cap` |
| 5 | Calibrated language | Nothing says "zero risk", "completely safe", "guaranteed well integrity", "no possibility of a kick", "leak-free" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

See the [grader-only answer key](grading/answer-key.md). It is outside the staged work folder.
</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?
- A missing or failed tool result is unassessed, not a pass. End at a simulated review disposition; a qualified human approver must review the real work package before mobilization.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:oilgas` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode oilgas`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
