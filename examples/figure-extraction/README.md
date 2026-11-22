# Figure extraction

This guided example has one worked figure and one new synthetic figure:

1. The worked FSC chart demonstrates extracting measured data and checking its
   crossing against the synthetic source.
2. The new pipeline diagram is the guided round-trip exercise. Its expected
   Mermaid structure is checked by a small offline script.

The model infers content from pixels. A round trip checks whether TOKN's
extracted representation can reproduce the input; it is not independent
verification of what the figure means.

## Files

| File | What it is |
|------|------------|
| `make_chart.py` | Draws the synthetic FSC curve as `fsc.png`. |
| `crossing.py` | Finds where the extracted curve crosses the 0.143 level. |
| `pipeline.svg` | A synthetic four-step flow diagram for the guided exercise. |
| `check_pipeline.py` | Checks the extracted Mermaid nodes and edges. |
| `.env.example` | Reference settings template. Do not source it or put secrets in it. |

No real measurements or project data are included.

## Setup

- TOKN v0.3.105 or newer on your `PATH`.
- Python 3.9 or newer, with `matplotlib` and `numpy`.
- Google Chrome or Chromium. `tokn vision doctor` checks whether it was found.
- An Anthropic API key, or an Anthropic-compatible gateway.

Install the Python packages:

```powershell
python -m pip install matplotlib numpy
```

Set the key for this session without placing it in shell history.

PowerShell: load the key from your approved secret store into this session; do
not place the secret in a command or repository file.

```powershell
$env:TOKN_VISION_PROVIDER='anthropic'
$env:TOKN_VISION_MODEL='YOUR_MODEL_ID'
```

macOS or Linux:

```bash
read -rs -p 'Anthropic API key: ' ANTHROPIC_API_KEY; echo
export ANTHROPIC_API_KEY
export TOKN_VISION_PROVIDER='anthropic'
export TOKN_VISION_MODEL='YOUR_MODEL_ID'
```

Run the commands below from this folder. `fsc.png` is generated here; the
pipeline image and JSON go under `out/`. Keep generated files out of source
control.

## Walkthrough

### 1. Worked figure: extract and check the FSC chart

Generate the synthetic chart and extract its data:

<a id="1-render-the-two-svg-figures"></a>

<a id="2-make-the-chart"></a>

```powershell
New-Item -ItemType Directory -Force out | Out-Null
python make_chart.py
```

<a id="3-extract-the-chart-data"></a>

```powershell
tokn vision extract fsc.png --kind chart --hint "cryo-EM FSC curve; resolution where FSC crosses 0.143" > out\chart.json
```

<a id="4-find-the-0143-crossing"></a>

```powershell
python crossing.py out\chart.json
```

On macOS or Linux, run `mkdir -p out` first and use `out/chart.json` instead of
`out\chart.json`.

The maintainer's run measured a crossing at about `0.2895 1/Å`, corresponding
to `3.45 Å`. The synthetic source's known crossing is `0.2898 1/Å`, also
`3.45 Å`. The small difference is extraction error, not proof that the
measurement is exact. The curve values are measured from pixels; labels and
interpretation may be inferred by the model.

<a id="5-convert-the-circuit-to-openqasm"></a>

The older circuit-conversion section has been removed to keep this walkthrough
to one worked figure and one guided figure.

<a id="6-convert-the-flow-diagram-to-mermaid"></a>

### 2. New synthetic figure: extract the pipeline

Render the new figure, extract it, and request a round trip:

```powershell
New-Item -ItemType Directory -Force out | Out-Null
tokn vision render --kind svg --source pipeline.svg --out out\pipeline.png --width 1000 --height 260
tokn vision extract out\pipeline.png --kind graph --hint "RNA-seq processing pipeline" --verify > out\pipeline.json
python check_pipeline.py out\pipeline.json
```

On macOS or Linux, use `mkdir -p out`, `out/pipeline.png`, and
`out/pipeline.json`.

The machine-checkable expected structure is:

```text
flowchart LR
    n0["Raw reads"]
    n1["Trim + QC"]
    n2["Align"]
    n3["Count matrix"]
    n0 --> n1
    n1 --> n2
    n2 --> n3
```

`check_pipeline.py` checks the direction, four labels, and three connections;
node IDs and whitespace may vary. Inspect `pipeline.json` to compare TOKN's
extraction with the source SVG.

## Why the round trip matters

`--verify` rebuilds and re-renders the extracted graph, then compares it with
the original pixels. That is a round-trip self-check, not an independent source
of truth.

## About these outputs

These are synthetic figures. Model-written labels and graph structure can vary
between runs. The checker only validates the expected pipeline structure; a
passing result does not establish that the same interpretation is valid for a
real scientific figure.

The FSC extraction value above came from a prior maintainer run with Claude
Haiku 5.5 on TOKN v0.3.105; it is one observed run, not a current validation.
The pipeline check is an expected result, not a recorded run.

If extraction fails, check `tokn vision doctor`, the configured provider and
model, and that Chrome or Chromium is available. Model calls may incur provider
charges.
