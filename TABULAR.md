# Local classifiers and regressors

`tokn tabular` is available in Community, with no trial or model API key.
It uses labeled examples to predict outcomes for new rows. This is not chat
completion and not a replacement for business policy or human authorization.

## A complete first run

Install Python 3.11+ if absent; `inspect` and `scaffold` do not need it.

```sh
tokn tabular scaffold --dir delivery-demo --example delivery
tokn tabular inspect --root delivery-demo
tokn tabular doctor --root delivery-demo
tokn tabular evaluate --root delivery-demo
tokn tabular predict --root delivery-demo
```

All commands emit JSON on stdout. Inspection validates the problem/data;
doctor reports runtime prerequisites; evaluation reports held-out performance;
prediction returns two synthetic query-row predictions. `doctor` exits nonzero
if dependencies are missing. A failure never becomes an LLM-guessed prediction.

`maintenance` provides another classifier; `repair-cost` provides a regressor.
The generated `run.py` and `test_pipeline.py` wrap the same TOKN executor.
These deliberately simple teaching datasets do not demonstrate real-world
accuracy or certify Kumo quality.

## Your problem

Edit `problem.json` to select the task, explicit feature names and
numerical/categorical types, target, context/query CSV paths, and evaluation
split. Paths stay inside `--root`. Do not put target labels into query files.
Use time splits for prospective outcomes, group splits for repeated entities,
and never leak post-outcome features into the prediction context.

The default `baseline` is deterministic mixed-feature kNN using Python's
standard library. Classification outputs a class distribution. Regression
reports median and quantiles. Evaluation compares with a trivial prior/median
reference; intervals and probabilities remain uncalibrated until measured on
representative data.

## Optional Kumo-Tabular

Prepare SDM/PyTorch dependencies and the appropriate local checkpoint first.
The scaffold includes `requirements-kumo.txt` for connected wheel preparation;
the baseline does not need these packages.
Change the backend to `kumo` and add this **model configuration template**:

```json
{
  "id": "nvidia/Kumo-Tabular",
  "revision": "v1.0.0",
  "size": "small",
  "checkpoint": "models/small/classifier.pt",
  "sha256": "REPLACE_WITH_VERIFIED_CHECKPOINT_SHA256",
  "device": "cpu",
  "estimators": 1
}
```

The placeholder is intentionally invalid until replaced. For regression use
`regressor.pt`. Keep the checkpoint inside the explicit project root.
Run `tokn tabular doctor --root delivery-demo` for all missing prerequisites,
installation and offline preparation guidance. Choose `cuda` only on a
compatible, verified NVIDIA runtime; CPU availability/performance also depends
on the installed dependencies and workload. No Apple Silicon acceleration is
claimed.

Small-checkpoint CPU classification/regression was exercised on Windows x64
with Python 3.11 using synthetic data, including the generated application.
This is functional evidence, not a production accuracy benchmark. CUDA and
medium/large-checkpoint inference have not yet been validated by TOKN.

Weights: [nvidia/Kumo-Tabular](https://huggingface.co/nvidia/Kumo-Tabular),
OpenMDW-1.1. Runtime:
[structured-data-models](https://github.com/NVIDIA/structured-data-models),
Apache-2.0. TOKN pins the supported SDM source revision; prepare that revision
rather than silently upgrading to `main`.

## Air-gapped setup

Use a connected preparation machine matching the offline OS/architecture.
Prepare a reviewed Python environment or wheelhouse, licenses, and checkpoint
files with SHA256 manifests. Transfer them explicitly, install only from the
local wheelhouse with `pip --no-index --find-links`, then run doctor offline.
`--python` can select the absolute path to that trusted interpreter.

From the generated project, inside a trusted virtual environment:

```sh
# Connected preparation only:
python -m pip wheel --wheel-dir wheelhouse -r requirements-kumo.txt
# Offline target, after transferring the wheelhouse:
python -m pip install --no-index --find-links wheelhouse structured-data-models
```

The requirements file includes a pinned Git source URL, so do not install it
directly offline. Git is needed only on the preparation machine, not at inference.

Each large classifier/regressor file is below 1 GB (~855 MB/~863 MB). This is
not the total download, combined weight size, or RAM/VRAM requirement; context
rows and inference caches consume additional memory.

Inference never downloads missing weights or packages. For unrelated TOKN
startup behavior, set `TOKN_NO_REGISTER=1` and `TOKN_NO_UPDATE_CHECK=1`.
Agent-driven use additionally needs a local agent model and `--air-gap`.
Use OS/container network isolation if a hard no-egress guarantee is required.

## Let the agent help

The shared agent tool catalog includes `tabular_scaffold`, `tabular_inspect`,
`tabular_doctor`, `tabular_evaluate` and `tabular_predict`. They retain normal
permissions/hooks and do not let a model select arbitrary interpreters.

```sh
tokn plugin install tabular-prediction
```

The bundled skill teaches label definition, leakage avoidance, reproducibility
and evaluation. `/learn tabular` is available in the REPL.

Text embeddings/Jev-derived features, remote endpoints and native
judgment-policy adapters are deferred. A continuous regression value is not
System One's ordered Score. Existing domain gates and licensing are unchanged.
