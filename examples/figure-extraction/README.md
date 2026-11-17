# Figure extraction

TOKN can read a picture of a figure and turn it back into data. This example
covers three cases:

- A line chart becomes a series of numbers, with axis fits and reference lines.
- A circuit diagram becomes OpenQASM code.
- A flow diagram becomes Mermaid code.

Each conversion is checked with a round trip. TOKN rebuilds the model from the
extracted text, renders it, and compares the result with the original picture.
The score is measured from the two images, so it is not the model's own opinion.

## Files

| File | What it is |
|------|------------|
| `make_chart.py` | Draws a synthetic FSC curve (a cryo-EM resolution plot) as `fsc.png`. |
| `bell.svg` | A two-qubit circuit: a Hadamard gate, a CNOT, and two measurements. |
| `pipeline.svg` | A four-step flow: raw reads, trim and QC, align, count matrix. |
| `crossing.py` | Reads the chart JSON and finds where the curve crosses a level. |
| `.env.example` | Placeholder settings. Copy it to `.env` and add your key. |

All data is synthetic. No real measurements are included.

## Setup

You need:

- TOKN v0.3.105 or newer on your `PATH`.
- Python 3.9 or newer, with `matplotlib` and `numpy` (for `make_chart.py`).
- Google Chrome or Chromium. The render step uses headless Chromium.
  `tokn vision doctor` shows whether it was found.
- An Anthropic API key, or an Anthropic-compatible gateway.

Install the Python packages:

```powershell
python -m pip install matplotlib numpy
```

Set your key for this session.

PowerShell:

```powershell
$env:ANTHROPIC_API_KEY='your-anthropic-api-key'
$env:TOKN_VISION_PROVIDER='anthropic'
$env:TOKN_VISION_MODEL='claude-haiku-5-5'
```

macOS or Linux:

```bash
export ANTHROPIC_API_KEY=your-anthropic-api-key
export TOKN_VISION_PROVIDER=anthropic
export TOKN_VISION_MODEL=claude-haiku-5-5
```

The commands below are the same on every system. Only the environment-variable
syntax above differs. Run them from this folder.

## Walkthrough

### 1. Render the two SVG figures

```powershell
New-Item -ItemType Directory -Force out | Out-Null
tokn vision render --kind svg --source bell.svg --out out\bell.png --width 900 --height 300
tokn vision render --kind svg --source pipeline.svg --out out\pipeline.png --width 1000 --height 260
```

On macOS or Linux, use `mkdir -p out` and `out/` instead.

### 2. Make the chart

```powershell
python make_chart.py
```

This writes `fsc.png`, a curve with a dashed reference line at 0.143. The curve
falls from near 1 to near 0 as spatial frequency rises.

### 3. Extract the chart data

```powershell
tokn vision extract fsc.png --kind chart --hint "cryo-EM FSC curve; resolution where FSC crosses 0.143" > chart.json
```

The `> chart.json` part saves the result to a file. Use it in step 4.

The result, shortened:

- `measured`: true. The points come from the pixels.
- `approximate`: false.
- `chart_type`: `"line"`.
- `reference_lines`: one dashed line at `y` 0.14321.
- `x_axis`: label `"Spatial frequency (1/A)"`, scale `"linear"`, `fit_r2` 0.999999.
- `y_axis`: label `"FSC"`, `fit_r2` 1.
- `series`: one series, named `"series 1"`, with `measured` true.
- `csv`: 500 points, one row each, with `series,x,y` columns.

Here is the top of the `csv` field:

```text
series,x,y
series 1,0.000639125,0.997531
...
```

The `x_ticks` and `y_ticks` fields hold the detected tick values. The `...` marks
parts left out for length.

### 4. Find the 0.143 crossing

```powershell
python crossing.py chart.json
```

The script reads the JSON file, interpolates between the two points where the
curve crosses the level, and prints the crossing in 1/Å and the resolution in
Å (one divided by the crossing).

The maintainer's run gave a crossing at 0.2895 1/Å, which is 3.45 Å. The true
crossing of this synthetic curve is 0.2898 1/Å, also 3.45 Å.

The script expects UTF-8 with or without a byte-order mark. PowerShell's `>`
redirect can add one, and the script handles it.

### 5. Convert the circuit to OpenQASM

```powershell
tokn vision extract out\bell.png --kind circuit --verify
```

The result, shortened:

- `gates`: `H` on q0, `CNOT` on q0→q1, `measure` on q0, `measure` on q1, each with
  a box.
- `qubits`: 2. `clbits`: 2.
- `qasm`:

```text
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
```

With `--verify`, TOKN also reports the round trip:

- `fidelity`: 0.9927.
- `verified`: true.
- `semantic` score: 1. `structural` score: 1.

### 6. Convert the flow diagram to Mermaid

```powershell
tokn vision extract out\pipeline.png --kind graph --hint "RNA-seq processing pipeline" --verify
```

The result:

- `mermaid`:

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

- With `--verify`: `fidelity` 0.9942, `verified` true, `edge_f1` 1, `node_f1` 1.

## Why the round trip matters

A round trip is TOKN's check on its own output. It does these steps:

1. Rebuilds the model (the QASM or Mermaid text) from what it read.
2. Renders the rebuilt model.
3. Reads the render again and compares it with the original, both by structure
   (same gates or nodes and edges) and by pixels.

The fidelity score comes from that comparison, so it is measured. It is not the
model saying "this looks right". A low fidelity means the extracted text does
not reproduce the figure, even if it looks plausible on the page.

## About these outputs

These outputs come from one maintainer run with Claude Haiku 5.5 as the vision
model on TOKN v0.3.105. Requires TOKN v0.3.105 or newer.

Model-written fields, such as the QASM text, the Mermaid labels, and the gate
and node boxes, can vary from run to run. Chart values and axis fits are measured
from the pixels, so they are deterministic for the same image. The fidelity score
is measured too, but it scores whatever the model extracted on that run, so a
weaker extraction gets a lower score.
