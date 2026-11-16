# Example: route one RNA-seq case across the Claude 5.5 family step by step

This example uses TOKN's opt-in `--auto-route` flag on one biomolecular task: a
bulk RNA-seq differential expression study. TOKN wrote the case study in a first
run, then a second, separate TOKN run solved it. In the solve run, TOKN picks a
model for each step by its capability: a fast rung for read-only work, a standard
rung for writing and running analysis code, and the frontier model for planning.

The case is **synthetic**. TOKN generated 4,000 genes and 12 samples with a seed,
so the answer key is known exactly and the solution can be graded.

## The rungs

| Rung | Model | Used for |
|---|---|---|
| fast | `claude-haiku-5-5` | Read-only steps: listing files, reading data and notes, small follow-ups |
| standard | `claude-sonnet-5-5` | Writing and running analysis code, the default for ordinary work |
| frontier | `claude-opus-5-5` | Planning at step 0, and hard steps; also the configured model (`--model-name`) |
| apex | `claude-fable-5-2` | The ceiling, reached only after repeated failed steps |

Deploy any subset of these models. In the absence of a rung, its work moves one
rung up. The run in this example never needed the apex rung.

Routing is opt-in. Without `--auto-route` (or `TOKN_AUTO_ROUTE=1`), every step
uses the one model you name.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.102 or newer** | Release with `--auto-route` | `tokn version` |
| **14-day trial** (`tokn license trial`) | `--mode transcriptomics` is a domain mode | `tokn license features` |
| An **Anthropic API key**, or an **Anthropic-compatible gateway** (`ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY`) | Authentication and model access. Azure API Management gateways are detected automatically and use the `api-key` header; set `ANTHROPIC_AUTH_HEADER` to override. | A short test run |
| **Python 3** with **numpy** | The agent writes and runs the analysis scripts. The grader uses only the standard library. | `python --version` |

> **What the model endpoint receives.** The task text and the files the agent reads
> or writes: the counts and sample tables, the analysis scripts and the report. The
> data is small and synthetic. See the [examples index](../README.md) for notes on
> startup traffic.

## 1. Configure the endpoint

From the example folder, copy the template and fill in your own values. Never commit `.env`; the folder's
`.gitignore` already excludes it.

PowerShell:

```powershell
Copy-Item .env.example .env
Get-Content .env | Where-Object { $_ -match '^\s*[^#\s][^=]*=' } | ForEach-Object {
  $k, $v = $_ -split '=', 2
  Set-Item -Path "env:$($k.Trim())" -Value $v.Trim()
}
```

bash:

```bash
cp .env.example .env
set -a; source .env; set +a
```

## 2. Two phases, both run by TOKN

### Phase 1: author the case

TOKN receives the brief in `author/AUTHOR.md`. The brief fixes the deliverables and
constraints but not the science: TOKN designs the study itself. It writes
`make_case.py`, the solver brief `case/TASK.md`, the data, the answer key and the
grader. It also tests its own grader with an oracle file (must pass), a deliberately
bad file (must fail), a solver that ignores batch (must fail) and a solver that skips
filtering (must fail).

Run it in an empty folder that holds the brief as `AUTHOR.md`:

PowerShell:

```powershell
New-Item -ItemType Directory -Path author-run | Out-Null
Copy-Item author\AUTHOR.md author-run\AUTHOR.md
Set-Location author-run
tokn agent-run --mode transcriptomics --auto-route `
  --model-provider anthropic --model-name claude-opus-5-5 `
  --repo-root . --prompt-file AUTHOR.md --max-steps 40 --no-confirm
```

bash:

```bash
mkdir author-run && cp author/AUTHOR.md author-run/AUTHOR.md
cd author-run
tokn agent-run --mode transcriptomics --auto-route \
  --model-provider anthropic --model-name claude-opus-5-5 \
  --repo-root . --prompt-file AUTHOR.md --max-steps 40 --no-confirm
```

The run writes `make_case.py`, `case/` and `answer_key/` into `author-run/`. The
script writes its outputs next to itself, so it can be run from any folder. The
grader expects `case/` and `answer_key/` as siblings. The seed is fixed (20240607),
so re-running `make_case.py` regenerates the same case.

**The shipped `case/` and `answer_key/` are exactly what phase 1 produced.** You can
skip phase 1 and go straight to phase 2.

### Phase 2: solve the case

The solver gets only `case/`. The answer key must stay outside its workspace, so
do not copy `answer_key/` into the solve folder.

PowerShell:

```powershell
New-Item -ItemType Directory -Path solve-run | Out-Null
Copy-Item -Recurse case solve-run\case
Set-Location solve-run
tokn agent-run --mode transcriptomics --auto-route `
  --model-provider anthropic --model-name claude-opus-5-5 `
  --repo-root . --prompt-file case/TASK.md --max-steps 50 --no-confirm
```

bash:

```bash
mkdir solve-run && cp -r case solve-run/case
cd solve-run
tokn agent-run --mode transcriptomics --auto-route \
  --model-provider anthropic --model-name claude-opus-5-5 \
  --repo-root . --prompt-file case/TASK.md --max-steps 50 --no-confirm
```

The solver writes `solution/results.tsv`, `solution/report.md` and its code into
`solve-run/solution/`.

## 3. What happened in our run

**Phase 1, author.** 28 steps, $1.31, 371k tokens. Step 0 ran on Opus for planning.
Steps 1 to 27 ran on Sonnet while TOKN wrote the generator, the grader, reference
solvers and the thresholds. The case it produced:

- 4,000 genes by 12 samples, with a balanced design: 3 replicates per condition in
  each batch cell (batches A and B).
- 280 planted differentially expressed genes with |log2FC| between 0.75 and 3.5.
- 1,007 lowly expressed genes that should be filtered.
- A strong batch shift on 60% of genes.
- Nine numeric acceptance criteria in `case/TASK.md`.

**Phase 2, solve (routed).** The routing trace for the solve run:

| Step | Model | Rung | What the step did |
|---|---|---|---|
| 0 | `claude-opus-5-5` | frontier (configured) | Read the brief and wrote the plan. |
| 1 | `claude-sonnet-5-5` | standard | Listed the workspace and read the sample and count tables. |
| 2 | `claude-haiku-5-5` | fast | Step 1 only read files, so this step went to the fast rung: it checked the Python environment and read `case/TASK.md`. |
| 3 | `claude-sonnet-5-5` | standard | Settled on the Python interpreter for the analysis. |
| 4–11 | `claude-sonnet-5-5` | standard | Explored the data. Wrote `analysis.py` (size factors, filtering, batch-aware model, Benjamini-Hochberg), `verify.py` and the report. |
| 12 | `claude-haiku-5-5` | fast | Step 11 only read `report.md`, so this step went to the fast rung: a small exploratory script and run. |
| 13–15 | `claude-sonnet-5-5` | standard | Fixed the remaining issues and ran the final verification. |

**Outcome:** 16 steps, $0.59, 209k tokens, about 3 minutes. The grade is PASS on all
13 checks: 280 calls, precision 0.929, empirical FDR 0.071, recall 0.929 (260 of 280).
The log2 fold-change Pearson r on true DE genes is 0.989, with 100% sign agreement.
0 of 816 near-zero genes were tested. The report has a QC section and runs to 1,121 words.

**Comparison.** The same phase 2 brief, run on Opus alone with `--auto-route` off:

| Run | Routing | Steps | Cost | Tokens | Time | Grade |
|---|---|---|---|---|---|---|
| Routed (above) | on | 16 | $0.59 | 209k | about 3 min | PASS: precision 0.929, recall 0.929, r 0.989 |
| Opus only | off | stopped at step 21 by the token-budget guard, results already written | $3.21 | 594k | 7m 42s | PASS: precision 0.919, recall 0.936, r 0.989 |

Routing reached the same grade at about 5.4 times lower cost. This is one run of
each, and the two runs took different paths, so treat the numbers as indicative.

## 4. Check it yourself

Run the grader from the example root, where `answer_key/` and `case/` sit side by
side. Point it at the solve run's output:

PowerShell:

```powershell
python answer_key\grade.py solve-run\solution\results.tsv --report solve-run\solution\report.md
```

bash:

```bash
python answer_key/grade.py solve-run/solution/results.tsv --report solve-run/solution/report.md
```

The grader checks the schema and integrity of `results.tsv`, the accuracy against
the hidden truth, the low-count filtering, and the report's QC heading and length.

## 5. Read the routing trace

Each step's routing decision is logged as an `auto_route` event, and a rung handover
as an `auto_route_fallback` event, in `.nospace/runs/*.jsonl` inside the run folder.

PowerShell:

```powershell
Select-String -Path solve-run\.nospace\runs\*.jsonl -Pattern 'auto_route' | ForEach-Object { $_.Line }
```

bash:

```bash
grep -h -E 'auto_route' solve-run/.nospace/runs/*.jsonl
```

## How routing decides

- **Step 0** is classified from the task prompt. Planning goes to the frontier rung.
- **Later steps** are classified from recent tool use. If only read-only tools were
  used, the next step goes to the fast rung. Otherwise it goes to the standard rung.
- **A step where every tool call fails** first raises reasoning effort on the same
  model (Anthropic: `xhigh`). Repeated failures climb one rung at a time. Apex is the
  ceiling. A successful step resets the count.
- **Safety-critical modes** such as `structbio`, `compbio`, `genomics` and `drugdisc`
  keep a frontier floor. This example uses `transcriptomics`, where all rungs are
  eligible.
- **Opt-in only.** Routing needs `--auto-route` or `TOKN_AUTO_ROUTE=1`.

## Try it differently

- **Compare the cost.** Run phase 2 without `--auto-route`, and compare the cost in the
  run's output with the figures above. Compare several runs before drawing a conclusion.
- **Use the environment variable instead of the flag.** Set `TOKN_AUTO_ROUTE=1` and
  drop `--auto-route` from the command.

## Cleanup

The runs leave state and generated files in the run folders. Remove them before you
share the folder:

PowerShell:

```powershell
Remove-Item -Recurse -Force author-run, solve-run -ErrorAction SilentlyContinue
Remove-Item -Force .env -ErrorAction SilentlyContinue
```

bash:

```bash
rm -rf author-run solve-run .env
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `--auto-route` not recognised | Upgrade to TOKN v0.3.102 or newer: `tokn version` |
| `transcriptomics` mode refused | Start the trial (`tokn license trial`) and check `tokn license features` |
| Authentication fails | Check `ANTHROPIC_API_KEY`. For a compatible gateway, check `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_HEADER`. |
| The endpoint does not recognise the model name | Use a model name your endpoint serves in `--model-name` |
| No `auto_route` lines in the trace | Routing is off. Check for `--auto-route` or `TOKN_AUTO_ROUTE=1`. |
| The grader reports a FAIL row | Read the detail on that row, then re-run phase 2 or check `solution/report.md` against `results.tsv` |
