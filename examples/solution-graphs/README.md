# Example: Solution graphs — plan, validate, generate and run a guarded graph

> "Build me a small app that predicts late deliveries, and prove it works
> before anything touches the network."

`tokn solution` turns a requirement into a **solution graph**: a JSON plan of
typed stages (tabular models, text models, file tools) with measured
acceptance checks. You can write the plan by hand or have a model propose it.
TOKN checks the plan against what is actually installed, and runs it only
when you say so:

| Step | Command | What it does |
|---|---|---|
| See what exists | `catalog` | Lists the typed capabilities this machine can run, and the ones it cannot |
| Propose | `plan` | Asks a model for a plan (or questions) from your requirement. Never runs nodes |
| Check | `validate` | Checks a plan's shape, targets, inputs and egress policy. Never runs nodes |
| Package | `generate` | Writes a new app directory (`solution.json`, `run.py`, tests). Never runs nodes |
| Execute | `run` | Runs a plan and its measured checks. Requires `--execute` |
| All in one | `solve` | Plan, generate and run. Requires `--execute` |

The safety rules are flags you pass, not settings the plan can change:

| Flag | Effect |
|---|---|
| `--execute` | Required by `run` and `solve`. Without it they refuse |
| `--allow-external` | Required for any external stage (a remote model, a judgment service) |
| `--air-gap` | Forbids every external stage, even with `--allow-external` |
| `--allow-code` | Adds trusted host Python executors. Not sandboxed. Needs `--allow-external`, forbids `--air-gap` |

Steps 1–8 run offline, with no model.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.68 or later | Ships `tokn solution` | `tokn solution --help` |
| Python 3.11+ on `PATH` (`python` or `python3`) | The tabular baseline model runs in Python. It needs only the standard library | `python --version` |
| The JSON files in this folder | The plans used below | — |
| A model provider (steps 9–10 only) | A text-model stage, and `plan` / `solve` | see [SETUP.md](../../SETUP.md) |

It runs on every tier, including the free Community tier. Nothing in this
walkthrough was gated.

### What leaves your machine

Nothing, in steps 1–8. They read and write files inside one folder you
choose (the **root**), and run a local Python model on synthetic data. Steps
9 and 10 send the requirement, the context file and the metrics to the model
provider you configure — and only when you pass `--allow-external`.

## 1. Make a root folder

Every command takes `--root`: an existing folder that holds the plans, the
data and anything the graph writes. Nothing outside it is read into a plan.
From a clone of this repository, copy this folder's JSON files into it.

bash:

```bash
mkdir -p "$HOME/tokn-solution"
cp examples/solution-graphs/*.json "$HOME/tokn-solution/"
cd "$HOME/tokn-solution"
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\tokn-solution" | Out-Null
Copy-Item examples\solution-graphs\*.json "$HOME\tokn-solution\"
Set-Location "$HOME\tokn-solution"
```

| File | What it is |
|---|---|
| `plan.json` | The working plan: scaffold a synthetic delivery dataset, then evaluate a baseline model |
| `plan-broken.json` | The same plan with a check that measures nothing |
| `plan-strict.json` | A plan whose acceptance check the model cannot meet |
| `plan-explain.json` | Adds an external text-model stage that explains the metrics |
| `context.json` | Extra facts for `plan` and `solve` (steps 9–10) |

TOKN writes its session log to `.tokn/logs/` in the current folder.

## 2. Catalog: what can a plan use?

```bash
tokn solution catalog --root .
```

Expected (shortened; the full output is about 100 KB of JSON schemas):

```text
{
  "capabilities": [
    {
      "id": "edit_file",
      "kind": "tool",
      ...
      "local": true,
      "parameters": { ... },
      "result_schema": { ... }
    },
    ...
  ],
  "unavailable": [
    ...
    { "id": "judgment", "reason": "no visible, configured typed capability; no substitute will be selected" },
    { "id": "llm", "reason": "no visible, configured typed capability; no substitute will be selected" },
    ...
  ],
  "constraints": {
    "domain": "general",
    "air_gap": false,
    "allow_external": false,
    "max_steps": 0,
    "timeout_seconds": 0
  }
}
```

With no flags, the capabilities are all local:

| id | kind |
|---|---|
| `read_file`, `write_file`, `edit_file`, `list_directory`, `file_search`, `grep_search` | `tool` |
| `tabular_scaffold`, `tabular_inspect`, `tabular_doctor`, `tabular_evaluate`, `tabular_predict` | `tabular` |

`llm`, `slm`, `judgment` and `specialist` are listed as **unavailable**.
TOKN never swaps in a substitute: a plan that names `llm` fails until you
configure one (step 9). Each capability's `parameters` is the input schema a
node must match, and `result_schema` tells you what a check can reference.
For example, `read_file` returns the file text as a string, so a check or
`$ref` uses `node#` for the whole result.

`catalog` reads only `--root` and the capability flags (`--provider`,
`--model`, `--slm-provider`, `--slm-model`, `--python`, `--allow-external`,
`--allow-code`, `--air-gap`, `--system-one`). `tokn solution catalog --help`
says so; other inherited flags are accepted and ignored.

## 3. Read the plan

`plan.json` is a two-node graph:

```json
{
  "schema": "tokn.solution/1",
  "requirement": "Create the synthetic delivery example and measure how well the baseline model predicts late deliveries.",
  "domain": "general",
  "nodes": [
    { "id": "scaffold", "kind": "tabular", "target": "tabular_scaffold",
      "input": { "directory": "delivery", "example": "delivery" } },
    { "id": "evaluate", "kind": "tabular", "target": "tabular_evaluate",
      "input": { "spec": "delivery/problem.json" },
      "depends_on": ["scaffold"],
      "checks": [ { "ref": "evaluate#/backend", "operator": "eq", "expected": "baseline" } ] }
  ],
  "checks": [
    { "ref": "evaluate#/metrics/accuracy", "operator": "gte", "expected": 0.8 },
    { "ref": "evaluate#/metrics/log_loss", "operator": "lte", "expected": 0.2 }
  ]
}
```

| Field | Rule |
|---|---|
| `schema` | Must be `tokn.solution/1` |
| `requirement` | Must not be empty |
| `nodes[].kind` + `target` | Must match a catalog capability of that kind |
| `nodes[].input` | Must match the capability's `parameters` |
| `depends_on` | Earlier nodes only; no cycles |
| `{"$ref": "node#/json/pointer"}` | Passes part of a dependency's result into an input (see `plan-explain.json`) |
| `checks[].ref` | `node#/json/pointer` into a node's result. `node#` is the whole result |
| `checks[].operator` | `exists`, `eq`, `gt`, `gte`, `lt`, `lte` |
| top-level `checks` | Required. At least one must be something other than `exists` |

## 4. Validate: a broken plan, then the fixed one

`plan-broken.json` only checks that the metrics exist:

```json
"checks": [ { "ref": "evaluate#/metrics", "operator": "exists" } ]
```

```bash
tokn solution validate --root . --plan plan-broken.json
```

Expected (exit status 1):

```text
Error: hybrid: acceptance requires at least one non-exists check
```

A plan must *measure* something. "The model produced output" is not
acceptance. Now validate the working plan:

```bash
tokn solution validate --root . --plan plan.json
```

Expected:

```text
{
  "plan_hash": "b76dc33e25a8ad72b6a48c929121dea8a2300510b83f2911455d3c153d869253",
  "valid": true
}
```

Validation ran no nodes: there is still no `delivery/` folder. Other errors you
may meet while writing a plan by hand:

| Mistake | Error |
|---|---|
| `"dependsOn"` instead of `"depends_on"` | `plan.nodes[1]: unknown field "dependsOn"` |
| `"kind": "tool"` for `tabular_evaluate` | `hybrid: node "evaluate" target "tabular_evaluate" is absent or has a different kind` |
| `"specification"` instead of `"spec"` | `hybrid: node "evaluate": input missing required parameter "spec"` |

## 5. Generate an application directory

```bash
tokn solution generate --root . --plan plan.json --dir app
```

Expected:

```text
{
  "executed": false,
  "files": [
    ".../tokn-solution/app/solution.json",
    ".../tokn-solution/app/README.md",
    ".../tokn-solution/app/run.py",
    ".../tokn-solution/app/test_contract.py",
    ".../tokn-solution/app/.gitignore"
  ]
}
```

| File | What it is |
|---|---|
| `solution.json` | The validated plan |
| `run.py` | A Python wrapper (standard library only) that calls `tokn solution run` and passes on its exit code |
| `test_contract.py` | Offline tests of the wrapper itself |
| `README.md` | How to run it, and what the guards do and do not cover |

`--dir` must be a **new** folder inside `--root`. Run `generate` again with
the same `--dir` and it refuses: `hybrid: destination already exists; choose a
new directory`.

Check the wrapper offline:

bash:

```bash
cd app && python3 -B test_contract.py && cd ..
```

PowerShell:

```powershell
Push-Location app; python -B test_contract.py; Pop-Location
```

Expected:

```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.016s

OK
```

These tests check the wrapper, not your solution. Only a real run (next step)
can pass the acceptance checks.

## 6. Run: refused without `--execute`, measured with it

```bash
tokn solution run --root . --plan plan.json
```

Expected (exit status 1):

```text
Error: run requires --execute; use plan or validate for nonexecuting work
```

The generated wrapper behaves the same, because it only forwards the flags
you give it. Run the app with `--execute`. `--root` must be an absolute path
here, and `tokn` must be on `PATH`:

bash:

```bash
python3 app/run.py --root "$PWD" --execute
```

PowerShell:

```powershell
python app/run.py --root "$PWD" --execute
```

(`tokn solution run --root . --plan plan.json --execute` does the same thing.)

Expected (shortened):

```text
{
  "schema": "tokn.solution/1",
  "status": "succeeded",
  "plan_hash": "b76dc33e25a8ad72b6a48c929121dea8a2300510b83f2911455d3c153d869253",
  "results": [
    {
      "id": "scaffold",
      "status": "succeeded",
      "output": {
        "files": [ "delivery/.gitignore", "delivery/README.md", "delivery/context.csv", ... ],
        "notes": [ "problem.json uses the baseline backend and runs with Python only.", ... ],
        "synthetic": true
      }
    },
    {
      "id": "evaluate",
      "status": "succeeded",
      "output": {
        "backend": "baseline",
        "metrics": { "accuracy": 1, "brier": 0.026666666666666672, "ece": 0.03333333333333333, "log_loss": 0.04256880198050014, "rows": 12 },
        "model": "baseline-knn",
        ...
        "trivial_baseline_metrics": { "accuracy": 0.3333333333333333, ..., "log_loss": 0.7365490324449256, "rows": 12 },
        "uncalibrated": true,
        "warnings": [
          "query file is not used by evaluate; metrics come from the context holdout.",
          "Uncalibrated model output; not authorization.",
          "Deterministic mixed-feature kNN; k=min(5, context rows)."
        ]
      },
      "checks": [
        { "ref": "evaluate#/backend", "operator": "eq", "expected": "baseline", "actual": "baseline", "passed": true }
      ]
    }
  ],
  "checks": [
    { "ref": "evaluate#/metrics/accuracy", "operator": "gte", "expected": 0.8, "actual": 1, "passed": true },
    { "ref": "evaluate#/metrics/log_loss", "operator": "lte", "expected": 0.2, "actual": 0.04256880198050014, "passed": true }
  ]
}
```

Every check records `expected`, `actual` and `passed`. The plan hash matches
the one `validate` printed, so you know this is the plan you reviewed. The
data is synthetic (48 rows, 12 held out), so a perfect accuracy here says
nothing about real deliveries. Compare it with `trivial_baseline_metrics`,
the score of a trivial predictor on the same rows.

Run the same plan a second time and it fails, because `tabular_scaffold`
never overwrites:

```text
{
  "schema": "tokn.solution/1",
  "status": "failed",
  ...
  "results": [
    { "id": "scaffold", "status": "failed", "error": "create new tabular project (parent must exist; existing paths are not overwritten): mkdirat delivery: file exists" },
    { "id": "evaluate", "status": "skipped", "error": "not executed" }
  ],
  ...
}
```

## 7. A check that fails

`plan-strict.json` scaffolds a second copy (`delivery-strict/`) and demands a
log loss of at most 0.01:

```bash
tokn solution run --root . --plan plan-strict.json --execute
```

Expected (shortened, exit status 1):

```text
{
  "schema": "tokn.solution/1",
  "status": "failed",
  ...
  "checks": [
    {
      "ref": "evaluate#/metrics/log_loss",
      "operator": "lte",
      "expected": 0.01,
      "actual": 0.04256880198050014,
      "passed": false
    }
  ],
  "error": "hybrid: acceptance check \"evaluate#/metrics/log_loss\" lte failed"
}
```

Both nodes succeeded, but the solution did not: the result was measured and
it fell short. The exit status is non-zero, so a script or CI job stops here.

## 8. External stages and the air gap

`plan-explain.json` adds two nodes after `evaluate`: an `llm` node that
explains the metrics, and a `write_file` node that saves the explanation.
The metrics go to the model through a reference:

```json
"input": {
  "prompt": "Explain these holdout metrics in three short sentences for a delivery manager.",
  "data": { "$ref": "evaluate#/metrics" }
}
```

With no model configured, the plan names a capability that does not exist:

```bash
tokn solution validate --root . --plan plan-explain.json
```

Expected:

```text
Error: hybrid: node "explain" target "llm" is absent or has a different kind; capability "llm" unavailable: no visible, configured typed capability; no substitute will be selected
```

The next commands need a remote provider's credentials in your environment
(here `OPENAI_API_KEY` for `--provider openai`; use your own provider and
model). They make **no model call**: `validate` never runs nodes, and the
blocked run stops before the first node.

```bash
tokn solution validate --root . --plan plan-explain.json --provider openai --model gpt-4.1-mini
```

Expected:

```text
Error: hybrid: node "explain" requires external capability "llm"; operator egress policy forbids it
```

A remote model is an external capability, so it needs `--allow-external`.
Now add both `--allow-external` and `--air-gap`, and try to run it:

```bash
tokn solution run --root . --plan plan-explain.json --provider openai --model gpt-4.1-mini \
  --allow-external --air-gap --execute
```

PowerShell:

```powershell
tokn solution run --root . --plan plan-explain.json --provider openai --model gpt-4.1-mini `
  --allow-external --air-gap --execute
```

Expected (exit status 1):

```text
{
  "schema": "tokn.solution/1",
  "status": "blocked",
  "plan_hash": "878b762a98f5512aa35a9e111909a5d0354848e0c62bf895f34c35b2996155a6",
  "results": [
    { "id": "scaffold", "status": "skipped", "error": "not executed" },
    { "id": "evaluate", "status": "skipped", "error": "not executed" },
    { "id": "explain", "status": "skipped", "error": "not executed" },
    { "id": "save", "status": "skipped", "error": "not executed" }
  ],
  "error": "hybrid: node \"explain\" requires external capability \"llm\"; operator egress policy forbids it"
}
```

`--air-gap` wins. The whole graph is blocked before anything runs: no
`delivery-explained/` folder is created, even though the first two stages are
local. With `--allow-external` and no `--air-gap`, `validate` prints
`"valid": true`.

A local model server is not external. With `--provider ollama --model
llama3.2 --air-gap`, the catalog lists `llm` with `"local": true`, and the
air gap allows it. Locality is decided by the endpoint (localhost), not by
the model's name.

### `--allow-code`

`--allow-code` adds code executors (`execute_domain_script`, `validate_code`,
`run_incremental_tests`) to the catalog as external `tool` capabilities. It
needs `--allow-external` and refuses `--air-gap`:

```bash
tokn solution run --root . --plan plan.json --execute --allow-code
```

Expected (exit status 1):

```text
Error: --allow-code requires --allow-external and no --air-gap; generated code is not OS-sandboxed
```

A refused run prints no warning. Once every check passes (for example
`--allow-code --allow-external`), `run` and `solve` print this warning to
stderr before the first node runs:

```text
WARNING: --allow-code executes trusted host Python. Python file, network and child-process operations DO NOT inherit TOKN guards. Environment filtering is not an OS, filesystem or network sandbox and does not prevent code from reading accessible credential files. Enable only for trusted code; existing execution consent and approvals still apply.
```

Take the warning literally. Code run this way can read and write anything
your user account can, including credential files. Use it only for code you
trust, or inside your own sandbox. `--system-one` (configured judgment tools)
also needs `--allow-external` and no `--air-gap`.

## 9. Optional: let a model propose the plan

This needs a model provider. The output depends on the model, so none is
shown here.

```bash
tokn solution plan --root . \
  --requirement "Predict which open deliveries will be late, and report holdout accuracy." \
  --context context.json \
  --provider openai --model gpt-4.1-mini --allow-external
```

PowerShell:

```powershell
tokn solution plan --root . `
  --requirement "Predict which open deliveries will be late, and report holdout accuracy." `
  --context context.json `
  --provider openai --model gpt-4.1-mini --allow-external
```

The prompt gets the requirement, `context.json` and the catalog; no other
files are read into it. The model
returns either a plan or a list of questions. A plan with questions cannot be
validated or run until you answer them. Save the plan to a file, review it,
then `validate` and `run` it as in steps 4–6.

For a local model server, use `--provider ollama --model <model>` and leave
out `--allow-external`. Without `--allow-external`, a remote planner is
refused before any call:

```text
Error: hybrid: configured planner is external; operator egress policy forbids it
```

A failed `plan` prints nothing to stdout; the error goes to stderr. A script
that saves stdout to a file never gets a plan from a failed run.

## 10. Optional: solve in one step

```bash
tokn solution solve --root . --dir delivery-app \
  --requirement "Predict which open deliveries will be late, and report holdout accuracy." \
  --context context.json \
  --provider openai --model gpt-4.1-mini --allow-external --execute
```

`solve` plans, generates `delivery-app/` and runs the plan in one command. It
needs `--requirement`, a new `--dir` and `--execute`. The output depends on
the model. Prefer steps 4–6 when you want to review the plan before it runs.

## What to look for

- **Nothing runs by accident.** `catalog`, `plan`, `validate` and `generate`
  never execute a node. `run` and `solve` refuse without `--execute`.
- **The plan cannot grant itself permission.** Egress comes only from your
  flags. `--air-gap` blocks the whole graph before the first node.
- **No substitutes.** A missing capability is an error, not a quiet fallback
  to some other model.
- **Success is measured.** Each check reports `expected`, `actual` and
  `passed`. One failed check fails the run, with a non-zero exit status.
- **The plan hash** ties a run to the plan you validated.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `--root is required; ...` | Every subcommand, including `catalog`, needs `--root`. Use `--root .` |
| `run requires --execute; ...` | Intended. Add `--execute` once you have reviewed the plan |
| `mkdirat delivery: file exists` | `tabular_scaffold` never overwrites. Delete the folder, or change `directory` (and `spec`) in the plan |
| `destination already exists; choose a new directory` | `generate` and `solve` need a new `--dir` |
| `configured python interpreter does not exist` | Install Python 3.11+, or pass `--python <absolute path>` |
| `requires external capability "llm"; operator egress policy forbids it` | Add `--allow-external`, and remove `--air-gap` — or use a local model server |
| `configure both --provider and --model; ...` | Pass both, or neither (catalog and tabular-only plans need neither) |
| `no configured planner; ...` | `plan` and `solve` need `--provider` and `--model` |
| `--context must contain one JSON object` | The context file must be a single `{ ... }` object, not an array |
| `OPENAI_API_KEY is required ...` | Set your provider's credentials in the environment. See [SETUP.md](../../SETUP.md) |
| `local model server is unavailable` | Start your local server (for example Ollama) and pull the model first. TOKN installs and downloads nothing |

To go further with the tabular models themselves, see
[tabular-prediction](../tabular-prediction/README.md).
