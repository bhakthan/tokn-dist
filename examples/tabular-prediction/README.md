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

No network call is made by TOKN. Weights are never downloaded at run time.

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

> **What leaves your machine.** Nothing. The baseline backend, `inspect`,
> `doctor`, `evaluate` and `predict` make no network calls.

## 1. Preflight: check the tools

Run this from the `tokn-dist` root. It only reads your environment.

bash or PowerShell (same command):

```bash
tokn tabular doctor --root examples/tabular-prediction
```

`doctor` lists every local prerequisite it finds, and installs nothing. For
`baseline` it needs only Python. If it reports a missing item, install it with
the command for your OS below.

| Piece | Windows | macOS | Linux (Debian/Ubuntu) |
|---|---|---|---|
| Python 3 | `winget install Python.Python.3.12` | `brew install python@3.12` | `sudo apt-get install -y python3 python3-venv` |

For `kumo` or `tabfm`, create a venv and install the pinned runtime. The pins
are embedded in the TOKN binary. Install the versions they pin, not the latest
releases. (The exact requirement file is not reproduced in this example.)

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
| `problem.json` | — | The explicit problem spec (`tokn.tabular/1`) |

`problem.json` names the target, types each feature, and sets a random 25%
holdout for `evaluate`. Every field is explicit, so `inspect` can reject a
malformed spec before anything runs.

## 3. Inspect the problem (no Python)

bash or PowerShell (same command):

```bash
tokn tabular inspect --root examples/tabular-prediction
```

`inspect` checks the spec, the CSV columns, the target classes and the row
limits. It never starts Python.

Expected, not a recorded run: a JSON report with `"task": "classification"`,
`"backend": "baseline"`, and `"ready": true`.

## 4. Predict the four query rows

bash or PowerShell (same command):

```bash
tokn tabular predict --root examples/tabular-prediction
```

Expected, not a recorded run: a JSON object on stdout with `"operation": "predict"`,
`"backend": "baseline"` and one prediction per row of `query.csv`. Each
prediction is a class label (`yes` or `no`).

## 5. Check how good it is

Cross-validation runs on the context rows only. The query rows are never used.

bash or PowerShell (same command):

```bash
tokn tabular evaluate --root examples/tabular-prediction --folds 3
```

Expected, not a recorded run: accuracy, log-loss, Brier and calibration metrics,
compared with a trivial "always the majority class" baseline. On 60 rows,
treat the numbers as a demonstration of the pipeline, not a claim about
delivery performance.

## 6. (Optional) Add a foundation-model backend

Change `"backend"` in a copy of `problem.json` to `kumo` or `tabfm`, then add a
`model` block. `tokn tabular scaffold` writes a complete template for each
backend, so you do not need to write the block by hand:

```bash
tokn tabular scaffold --dir scratch-tabfm --example delivery
```

Run that in a scratch folder under your `--root`, not inside this example. It
writes `problem.json` (baseline) and `problem-tabfm.json` (TabFM). The JSON
output's `notes` field carries the exact stage commands for the weights.

### How TOKN stages weights for offline use

TOKN never downloads a model at run time. Staging happens once, on a machine
you control:

1. **Build the wheelhouse online.** Download the pinned packages once:
   `python -m pip download -d wheelhouse -r <pinned requirements file>`.
2. **Install offline.** Copy `wheelhouse` to the air-gapped machine and run
   `python -m pip install --no-index --find-links wheelhouse -r <pinned requirements file>`.
   Do not move a venv between machines; rebuild it.
3. **Fetch the weights once** with the stage commands from `scaffold`. Verify
   each file's sha256 against the value in the spec.
4. **Point TOKN at the local folder.** Use `--tabfm-weights <dir>` (relative to
   `--root`, or absolute), or set `model.checkpoint` in the spec. The folder
   must hold `classification/` and `regression/` (TabFM) or the task's `.pt`
   file (Kumo).

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
tokn tabular predict --root examples/tabular-prediction --tabfm-license-ack tabfm-non-commercial-v1.0
```

The `--tabfm-license-ack` value must match `tabfm-non-commercial-v1.0` exactly.
Use it only for non-commercial work.

## 7. Where this sits next to the LLM

The LLM reads the typed JSON from `predict` and explains it. It never
produces the numbers. Keep the two steps separate in your own pipeline, so
the prediction can be checked without a model call.

## What to look for

- **The spec is the contract.** Unknown fields are rejected. Change the target
  or a feature type in `problem.json` and `inspect` will catch it.
- **Predictions are typed.** Every row has a class label and the count behind
  it, not free text.
- **Evaluation uses only context rows.** The query rows never leak into the
  metrics.
- **Weights are pinned.** A changed file fails the sha256 check. TOKN does not
  silently swap in another checkpoint.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `python: not found` | Python is not on `PATH` | Install it (step 1) or pass `--python <path>` |
| `inspect` says a column is missing | The feature or target name does not match the CSV header | Compare `problem.json` with the first line of `context.csv` |
| `tokn tabular predict` refuses TabFM | The licence string is missing or not exact | Pass `--tabfm-license-ack tabfm-non-commercial-v1.0` exactly |
| `doctor` reports a checkpoint hash mismatch | The weights file differs from the pinned sha256 | Re-stage the file from the source. Do not edit the spec's hash to match. |
| Out of memory on TabFM 1.0.0 | Large variant needs far more RAM or VRAM | Use the default 1.1.0 variant |
| `evaluate` fails with a fold error | `--folds` is outside the allowed range | Use a value the error message gives |

Expected, not a recorded run. Outputs are shown as shape only, because the exact
numbers depend on your TOKN build.
