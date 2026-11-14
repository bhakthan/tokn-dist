# Example: local tabular prediction next to the LLM

TOKN can predict from a labelled table without a model call. A small local
kNN baseline runs with Python only. Optional foundation-model backends (NVIDIA
Kumo-Tabular and Google TabFM) run offline once their weights are staged. The
LLM does not predict; it only reads the typed result.

> *Given 60 past deliveries, predict whether four new ones will be late.*

| Feature | What it does here |
|---|---|
| **`tokn tabular`** | Typed predictions from labelled CSV context, printed as JSON. |
| **`baseline` backend** | Deterministic stdlib kNN. Needs Python only. |
| **`kumo` / `tabfm` backends** | Local foundation models with pinned, hash-checked weights. Optional. |
| **Problem spec** (`problem.json`) | The explicit schema, target and features. Nothing is inferred. |

The prediction backends do not download weights at run time or call an LLM.
This does not disable TOKN's separate startup registration or update checks;
set `TOKN_NO_REGISTER=1` and `TOKN_NO_UPDATE_CHECK=1` for an offline session.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | `tokn tabular` subcommands | `tokn version` |
| Python 3 on `PATH` | The `baseline` worker runs under Python | `python --version` |
| Licence tier | `tokn tabular` is **Community** | `tokn license features` |

**Optional, for `kumo` or `tabfm` only:**

| Requirement | Why | Size | Check |
|---|---|---|---|
| Python **3.11+** in a venv | Pinned runtime for the model backends | small | `python --version` |
| Model runtime packages | Kumo (SDM, torch, pyarrow, pandas, scikit-learn, huggingface_hub) and TabFM (torch, safetensors) | several GB with torch | `tokn tabular doctor` |
| Kumo weights | Task `.pt` checkpoint, sha256-pinned | 0.86 GB per task (large) | `tokn tabular doctor` |
| TabFM weights | `classification/` and `regression/` folders | 820 MB per task (default 1.1.0); about 6.6 GB per task for 1.0.0 | `tokn tabular doctor` |
| RAM / VRAM | Model inference | Not measured in this walkthrough. Larger weights need much more. | watch the process |

**Licence note for the weights.** Kumo-Tabular weights are OpenMDW-1.1. TabFM
weights are `tabfm-non-commercial-v1.0`, which permits non-commercial use only.
TOKN refuses to run TabFM until you acknowledge that exact string.

> **What leaves your machine.** These tabular operations use local files and
> local prediction runtimes. Optional package and weight staging needs
> connectivity on a preparation machine. Predictions are uncalibrated
> model output, not authorization to take an action.

## 1. Preflight: check the tools

Run this from the `tokn-dist` root. `--root` must be an **absolute** path.
Set it once for the rest of the walkthrough:

macOS / Linux:

```bash
TABULAR_ROOT="$PWD/examples/tabular-prediction"
```

PowerShell:

```powershell
$TABULAR_ROOT = (Resolve-Path examples\tabular-prediction).Path
```

bash or PowerShell (same command):

```bash
tokn tabular doctor --root "$TABULAR_ROOT"
```

`doctor` lists every local prerequisite it finds, and installs nothing. For
`baseline` it needs only Python. If it reports a missing item, install it with
the command for your OS below.

| Piece | Windows | macOS | Linux (Debian/Ubuntu) |
|---|---|---|---|
| Python 3 | `winget install Python.Python.3.12` | `brew install python@3.12` | `sudo apt-get install -y python3 python3-venv` |

The baseline needs no pip packages or weights. For `kumo` or `tabfm`, create
a venv and use the requirement files generated in section 6. Creating the
venv alone does not install a foundation-model runtime.

Windows PowerShell:

```powershell
python -m venv $HOME\tokn-tabular-venv
& $HOME\tokn-tabular-venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

macOS / Linux:

```bash
python3 -m venv ~/tokn-tabular-venv
source ~/tokn-tabular-venv/bin/activate
python -m pip install --upgrade pip
```

## 2. Look at the data

The folder holds a fresh synthetic table. Nothing in it comes from a real
system.

| File | Rows | Columns |
|---|---|---|
| `context.csv` | 60 labelled past deliveries | `distance_km`, `service`, `delayed` (`yes`/`no`) |
| `query.csv` | 4 new deliveries to predict | `distance_km`, `service` |
| `problem.json` | — | The explicit problem specification |

`problem.json` names the target, types each feature, and sets a random 25%
holdout for `evaluate`. Every field is explicit, so `inspect` can reject a
malformed spec before anything runs.

## 3. Inspect the problem (no Python)

bash or PowerShell (same command):

```bash
tokn tabular inspect --root "$TABULAR_ROOT"
```

`inspect` checks the spec, the CSV columns, the target classes and the row
limits. It never starts Python.

Expected: a JSON report with `"operation": "inspect"`,
`"task": "classification"` and `"backend": "baseline"`. Readiness is
reported by `doctor`, not `inspect`.

## 4. Predict the four query rows

bash or PowerShell (same command):

```bash
tokn tabular predict --root "$TABULAR_ROOT"
```

Expected, not a recorded run: a JSON object on stdout with `"operation": "predict"`,
`"backend": "baseline"` and one prediction per row of `query.csv`. Each
prediction is a class label (`yes` or `no`).

## 5. Check how good it is

Cross-validation runs on the context rows only. The query rows are never used.

bash or PowerShell (same command):

```bash
tokn tabular evaluate --root "$TABULAR_ROOT" --folds 3
```

Expected, not a recorded run: accuracy, log-loss, Brier and calibration metrics,
compared with a trivial "always the majority class" baseline. On 60 rows,
treat the numbers as a demonstration of the pipeline, not a claim about
delivery performance.

With `--folds 3`, cross-validation replaces the problem file's single
holdout split. Omit `--folds` to use that holdout instead. Neither evaluation
is a substitute for testing on representative, independently held-out data.

## 6. (Optional) Add a foundation-model backend

`tokn tabular scaffold` creates a **new** starter directory, with a working
baseline specification, an optional TabFM template and runtime requirement
files. Use a separate scratch root, not the checked-in example.

```bash
tokn tabular scaffold --root "<absolute existing scratch root>" --dir delivery-demo --example delivery
```

Replace the placeholder with a directory you own; `delivery-demo` must not
already exist. The output names the generated files and gives weight-staging
guidance. Read those notes and the generated `requirements-tabfm.txt` or
`requirements-kumo.txt` before installing anything. The scaffold does not
install packages or fetch weights.

### How TOKN stages weights for offline use

TOKN never downloads a model at run time. Staging happens once, on a machine
you control:

1. **Build the wheelhouse online.** Download the pinned packages once:
   `python -m pip wheel --wheel-dir wheelhouse -r requirements-tabfm.txt`
   from the generated directory, using the target OS, architecture and
   Python version. For Kumo, use `requirements-kumo.txt`.
2. **Install offline.** Copy `wheelhouse` to the air-gapped machine and run
   `python -m pip install --no-index --find-links wheelhouse -r requirements-tabfm.txt`.
   Do not move a venv between machines; rebuild it.
3. **Fetch the weights once** with the stage commands from `scaffold`. Verify
   each file's sha256 against the value in the spec.
4. **Point TOKN at the local files.** For TabFM, use
   `--tabfm-weights <dir>` (relative to `--root`, or absolute), or the
   checkpoint setting in its generated spec. The folder holds the
   classification and regression weights. Kumo uses its own specification
   pointing to the task's `.pt` checkpoint, not `--tabfm-weights`.

TabFM variants:

| Variant | Size per task | Flag |
|---|---|---|
| 1.1.0 (default) | 820 MB classification, 825 MB regression | `--tabfm-variant 1.1.0` |
| 1.0.0 (large) | about 6.6 GB per task | `--tabfm-variant 1.0.0` |

Kumo-Tabular v1.0.0 has small, medium and large sizes. The large classifier is
855 MB and the regressor 863 MB. All six checkpoints total 2.44 GB. TOKN loads
only the task you ask for.

To run TabFM, acknowledge the licence exactly:

```bash
tokn tabular doctor --root "<absolute scratch root>/delivery-demo" --spec problem-tabfm.json --tabfm-license-ack tabfm-non-commercial-v1.0
tokn tabular predict --root "<absolute scratch root>/delivery-demo" --spec problem-tabfm.json --tabfm-license-ack tabfm-non-commercial-v1.0
```

The `--tabfm-license-ack` value must match `tabfm-non-commercial-v1.0` exactly.
Use it only for non-commercial work.

Passing the acknowledgement with the original `problem.json` does **not**
select TabFM: that file still requests `baseline`. Explicitly select
`problem-tabfm.json` and finish its local weights setup first.

## 7. Where this sits next to the LLM

The LLM reads the typed JSON from `predict` and explains it. It never
produces the numbers. Keep the two steps separate in your own pipeline, so
the prediction can be checked without a model call.

## What to look for

- **The spec is the contract.** Unknown fields are rejected. Change the target
  or a feature type in `problem.json` and `inspect` will catch it.
- **Predictions are typed.** Every row has a class label and class
  probabilities, not free text. Probabilities are not guaranteed calibrated
  confidence.
- **Evaluation uses only context rows.** The query rows never leak into the
  metrics.
- **Weights are pinned.** A changed file fails the sha256 check. TOKN does not
  silently swap in another checkpoint.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `python: not found` | Python is not on `PATH` | Install it (step 1) or pass `--python <path>` |
| `root must be an absolute path` | A relative `--root` was passed | Set `TABULAR_ROOT` as in step 1 |
| `inspect` says a column is missing | The feature or target name does not match the CSV header | Compare `problem.json` with the first line of `context.csv` |
| `tokn tabular predict` refuses TabFM | The licence string is missing or not exact | Pass `--tabfm-license-ack tabfm-non-commercial-v1.0` exactly |
| `doctor` reports a checkpoint hash mismatch | The weights file differs from the pinned sha256 | Re-stage the file from the source. Do not edit the spec's hash to match. |
| Out of memory on TabFM 1.0.0 | Large variant needs far more RAM or VRAM | Use the default 1.1.0 variant |
| `evaluate` fails with a fold error | `--folds` is outside the allowed range | Use a value the error message gives |

Expected, not a recorded run. Outputs are shown as shape only, because the exact
numbers depend on your TOKN build.
