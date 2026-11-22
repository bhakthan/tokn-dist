# Example: move one grid-engineering task between model rungs step by step

This walkthrough runs one deep-domain task, a 6-bus N-1 transmission screen, with
TOKN's opt-in `--auto-route` flag. Instead of paying frontier price for every step,
TOKN picks a model rung for each step: a faster rung for read-only work, the
configured model for ordinary work and planning, and a higher rung only when
steps keep failing. The agent solves the power flow, runs the contingency study and
writes a report. The model names and costs below are from a historical observed run;
they are not current defaults.

The network in `workspace/` is **synthetic**: six buses and eight lines,
invented for this example. It is not a real grid.

| Rung | Model | Used for |
|---|---|---|
| fast | A faster configured model | Read-only steps: listing files, reading CSVs and notes |
| standard | Your configured model | The default for ordinary work steps |
| frontier | A higher-capability configured model | Planning and hard steps |
| apex | An optional ceiling model | Reached only after repeated failed steps |

Routing is opt-in. Without `--auto-route` (or `TOKN_AUTO_ROUTE=1`) every step uses
the one model you name.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.102 or newer** | Release with `--auto-route` | `tokn version` |
| A configured model provider and endpoint | Per-request model routing needs a provider that supports the selected models and routing endpoint. | `tokn doctor --provider <id>` checks static configuration only |
| Provider authentication | Use the provider's supported credential source. | Use a provider-specific authenticated probe only when you choose to verify live access |
| **14-day trial** (`tokn license trial`) | `--mode grideng` is a domain mode | `tokn license features` |
| **Python 3** on PATH | The agent writes and runs a solver script | `python --version` |

On Windows, `python` may be the Microsoft Store alias, which prints nothing useful.
If so, use `py -3` in its place: `py -3 --version`. The solver uses only the
standard library, so no packages are installed.

> **What the model endpoint receives.** The task text and the files the agent reads
> or writes (the two CSVs, the solver and the report). The data is small and
> synthetic. See the [examples index](../README.md) for notes on startup traffic.

## 1. Configure the endpoint

Use `.env.example` as a reference template only; do not copy, source or import
it. Set endpoint, deployment and credential values directly in a trusted shell
for the provider you selected. Never commit a populated `.env`.

## 2. Load the settings into your shell

Set only the values for your selected provider in your interactive shell. For
example, use your provider's documented endpoint and deployment alias, and
enter any secret through a trusted secret store or hidden prompt. Do not copy
placeholders such as `YOUR_TRUSTED_HOST` unchanged.

## 3. Run the agent with auto-route

Run from inside `workspace/`, so the agent sees only the study files:

macOS / Linux:

```bash
cd workspace
tokn agent-run --mode grideng --auto-route \
  --model-provider YOUR_PROVIDER --model-name 'YOUR_CONFIGURED_MODEL' \
  --prompt-file TASK.md --max-steps 40 \
  --output-format json --repo-root .
```

Windows PowerShell:

```powershell
Set-Location workspace
tokn agent-run --mode grideng --auto-route `
  --model-provider YOUR_PROVIDER --model-name 'YOUR_CONFIGURED_MODEL' `
  --prompt-file TASK.md --max-steps 40 `
  --output-format json --repo-root .
```

`--model-name` is your configured model. Review and approve tool calls interactively.
The agent should finish with `dcflow.py`, `GRID_REPORT.md` and a summary in the output.

## 4. Read the routing trace

Each step's routing decision is logged as an `auto_route` event, and a rung handover (for example to the next rung up)
as an `auto_route_fallback` event, in `.nospace/runs/*.jsonl`.

PowerShell:

```powershell
Select-String -Path .nospace\runs\*.jsonl -Pattern 'auto_route' | ForEach-Object { $_.Line }
```

bash:

```bash
grep -h -E 'auto_route' .nospace/runs/*.jsonl
```

## What happened in our run

The following is a historical observed run, not a current default or a promise
of routing, model availability, or cost.

The historical run used Azure OpenAI GPT-6 deployments. Its observed routing trace
and deployment names are examples only, not current defaults:

| Step | Model | Rung | What the step did |
|---|---|---|---|
| 0 | `gpt-6.1-sol` | frontier (configured) | Weighed the task once. Its plan signal kept the configured model. Wrote a plan and listed the folder. |
| 1 | `gpt-6-luna` | fast | Read `buses.csv`, `lines.csv` and `TASK.md`. |
| 2 | `gpt-6-luna` | fast | Checked the data: generation is 300 MW against 380 MW of load, so the slack bus supplies the 80 MW residual. Wrote the first `dcflow.py`. |
| 3 | `gpt-6.1-sol` | standard → frontier | Our resource runs without `gpt-6.1-terra`, so standard-rung work moved up to `gpt-6.1-sol` for the rest of the run. |
| 4–13 | `gpt-6.1-sol` | standard → frontier | Ran the solver, fixed an exact-at-limit floating-point case, ran the N-1 study and the balance check, and wrote `GRID_REPORT.md`. |

**Outcome:** success, 14 steps, 15 tool calls, no tool errors, about 3 minutes.
No step had all of its tool calls fail, so the run never moved to `gpt-6-astra`.

**Observed cost:** about **$0.099** with `--auto-route`, against about **$0.202** for the same
task with every step on `gpt-6.1-sol`. This is one run each. The two runs took
different paths, so treat the numbers as indicative, not as a benchmark.

**Engineering result** (re-solved independently, matches exactly):

- Base case (N-0) passes. The highest loading is line L24 at 103.8 MW of 120 MW, or 86.5%.
- The N-1 screen **fails**. Three of eight single-line outages overload a line,
  giving five overloaded-line instances. No outage islands the network.
- The worst contingency is the outage of L24. It loads L26 to 109.5 MW of 80 MW,
  or 136.9%. L13 is also overloaded, at 108.8%.
- Outage of L13 loads L24 to 131.4% and L26 to 102.9%. Outage of L26 loads L24 to 120.0%.
- The base-case nodal balance residual is 5.7e-14 MW, against a 0.1 MW requirement.

The point of the example is the routing, not the grid result. A DC screen is an
approximation, and the report's limitations section says so.

## How the router decides

- **Step 0** is classified from the task text. Later steps are classified from their
  own signals: the tools just used, the size of the context, and the remaining budget.
  Read-only steps go to the fast rung. Other steps go to the standard rung.
- **A failed step** (every tool call failed) first raises reasoning effort on the same
  model. Repeated failures climb one rung at a time. Apex is the ceiling. A successful
  step resets the count.
- **In the absence of a rung**, its work moves one rung up (never into apex unless
  apex was the choice); if that rung is also absent, one rung down.
- **Safety-critical domains** (for example synbio, precision medicine and nuclear
  science) never route below the frontier rung.
- **Local providers** (Ollama, llama.cpp, ONNX) always keep the configured model.
- **Opt-in only.** Routing needs `--auto-route` or `TOKN_AUTO_ROUTE=1`.

## Try it differently

- **Compare the cost.** Run the same command without `--auto-route`. Every step then
  uses your configured model. Compare your run's output with the historical figures above.
  Expect different trajectories, so compare several runs before drawing a conclusion.
- **Use the environment variable instead of the flag.** Set `TOKN_AUTO_ROUTE=1` in
  your shell (`$env:TOKN_AUTO_ROUTE = "1"` in PowerShell, `export TOKN_AUTO_ROUTE=1`
  in bash) and drop `--auto-route` from the command.
- **Use the v1 endpoint.** Routing needs an endpoint ending in `/openai/v1`. A classic
  per-deployment Azure endpoint disables auto-route and logs a line saying so.

## Cleanup

The run leaves generated files and state in `workspace/`. Remove them before you
share the folder:

PowerShell:

```powershell
Remove-Item -Recurse -Force workspace\.nospace, workspace\.tokn, workspace\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Force workspace\dcflow.py, workspace\GRID_REPORT.md, workspace\dcflow_results.json -ErrorAction SilentlyContinue
```

bash:

```bash
rm -rf workspace/.nospace workspace/.tokn workspace/__pycache__
rm -f workspace/dcflow.py workspace/GRID_REPORT.md workspace/dcflow_results.json
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `--auto-route` not recognised | Upgrade to TOKN v0.3.102 or newer: `tokn version` |
| `grideng` mode missing or refused | Start the trial (`tokn license trial`) and check `tokn license features` |
| The configured model fails with "not found" | The deployment name in `--model-name` does not match a deployment on your Foundry resource |
| No `auto_route` lines in the trace | Routing is off. Check for `--auto-route` or `TOKN_AUTO_ROUTE=1`, and that the endpoint ends in `/openai/v1` (a classic endpoint disables routing) |
| `python` opens the Microsoft Store | Use `py -3` on Windows, or install Python 3 |
