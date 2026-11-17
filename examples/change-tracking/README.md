# Change tracking

`tokn vision track` compares two frames and lists what changed. TOKN measures
where the pixels changed; the vision model names each change (moved, appeared,
disappeared) and boxes the objects; TOKN then measures each named change from
the pixels. This example uses two synthetic frames, so you can check the
result against the known answer.

## Files

| File | What it is |
|------|------------|
| `make_frames.py` | Draws `before.png` and `after.png` with Pillow. |
| `.env.example` | Placeholder settings. Copy it to `.env` and add your key. |

## Setup

You need:

- TOKN v0.3.105 or newer on your `PATH`.
- Python 3.9 or newer, with Pillow (for `make_frames.py`).
- An Anthropic API key, or an Anthropic-compatible gateway.

Install Pillow:

```powershell
python -m pip install Pillow
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

The commands below work the same on every system. Only the environment-variable
syntax above differs. Run them from this folder.

## Walkthrough

### 1. Make the two frames

```powershell
python make_frames.py
```

This writes `before.png` and `after.png`:

- In `before.png`, there is a red disc, a blue disc, and no green square.
- In `after.png`, the blue disc has moved right, and a green square has appeared.
- The red disc stays where it is.

### 2. Track the changes

```powershell
tokn vision track before.png after.png --query "coloured shapes"
```

The `--query` text tells TOKN what kind of objects to look for.

### 3. Read the result

The result for this pair of frames:

- `changes`:
  - One **moved** change: the blue circle. `magnitude` 0.3818, `dx` 0.1872,
    region `[0.5875,0.4,0.701,0.582]`.
  - One **appeared** change: the green square. `magnitude` 0.5776, region
    `[0.75,0.12,0.876,0.322]`.
- `dropped_unchanged`: 0.
- `unexplained_regions`: `[]`.
- `mode`: `"change"`.
- `ssim`: 0.9558 (measured from pixels).
- `mean_abs_diff`: 0.0313.

The `objects` list shows each shape in both frames. The red circle has `dx` 0,
so it did not move. The blue circle has `dx` 0.1872. The green square has no
box in the first frame, because it was not there yet.

If the model describes a change that the pixels do not show, TOKN drops it.
Dropped changes are counted in `dropped_unchanged`. A 0 there means every change
the model listed was confirmed by the pixels.

### 4. Compare with the known answer

The script draws every shape at a known position. Here is how the result
compares. Positions are fractions of the frame, from 0 to 1.

| Object | What the script drew | What TOKN reported |
|--------|----------------------|--------------------|
| Blue disc | Moved right by 150 px, which is 0.1875 of the frame width | Moved, `dx` 0.1872 |
| Green square | Appeared, at `[0.75,0.12,0.875,0.32]` | Appeared, region `[0.75,0.12,0.876,0.322]` |
| Red disc | Unchanged, at `[0.15,0.36,0.275,0.56]` | Not listed as a change (`dx` 0) |

The measured positions match the drawn ones to within about 0.002.

## About these outputs

These outputs come from one maintainer run with Claude Haiku 5.5 as the vision
model on TOKN v0.3.105. Requires TOKN v0.3.105 or newer.

Model-written fields can vary from run to run: the object names, the wording of
each change, and the boxes (so `region` and `dx` too). Pixel-measured fields are
deterministic for the same images: `ssim`, `mean_abs_diff`, the measured change
regions, and the `magnitude` of each change inside its region.
