# Change tracking

`tokn vision track` compares two frames and lists what changed. TOKN measures
where the pixels changed; the vision model names each change (moved, appeared,
disappeared) and boxes the objects; TOKN then measures each named change from
the pixels. The frames are synthetic. Run only from a scratch copy; generated
images and model results must not be written into the distribution checkout.

## Files

| File | What it is |
|------|------------|
| `make_frames.py` | Draws the worked pair and an unseen synthetic pair with Pillow. |
| `.env.example` | Reference settings; supply credentials through a trusted shell or secret store. |
| `grading/` | Sanitized expected counts and a historical observed receipt; keep outside model input. |

## Setup

Make a scratch copy outside the distribution checkout before generating images.
All commands below run from that copy:

PowerShell:

```powershell
Copy-Item -Recurse examples\change-tracking $HOME\change-tracking-run
Set-Location $HOME\change-tracking-run
```

macOS / Linux:

```bash
cp -r examples/change-tracking ~/change-tracking-run
cd ~/change-tracking-run
```

You need:

- TOKN v0.3.105 or newer on your `PATH`.
- Python 3.9 or newer, with Pillow (for `make_frames.py`).
- A configured vision provider and model.

Install Pillow:

```powershell
python -m pip install Pillow
```

Set your key for this session.

PowerShell:

```powershell
$secure = Read-Host 'Provider API key' -AsSecureString
$env:ANTHROPIC_API_KEY = [System.Net.NetworkCredential]::new('', $secure).Password
$env:TOKN_VISION_PROVIDER='anthropic'
$env:TOKN_VISION_MODEL='YOUR_CONFIGURED_VISION_MODEL'
```

macOS or Linux:

```bash
read -rs -p 'Provider API key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
export TOKN_VISION_PROVIDER=anthropic
export TOKN_VISION_MODEL='YOUR_CONFIGURED_VISION_MODEL'
```

The remaining commands run from the scratch copy. Only the
environment-variable syntax above differs.

## Walkthrough

### 1. Make the two frames

```powershell
python make_frames.py
```

This writes `before.png`, `after.png`, `unseen-before.png` and
`unseen-after.png`:

- In `before.png`, there is a red disc, a blue disc, and no green square.
- In `after.png`, the blue disc has moved right, and a green square has appeared.
- The red disc stays where it is.
- The unseen pair has one moved square, one disappeared disc and one unchanged disc.

### 2. Track the changes

```powershell
tokn vision track before.png after.png --query "coloured shapes"
```

The `--query` text tells TOKN what kind of objects to look for.

### 3. Read the result

Historical observed output for the first pair (TOKN v0.3.105, one vision-model
run; not a current guarantee):

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

The first pair is the worked case. `grading/first-pair-receipt.json` records its
synthetic expected counts separately from the historical measured counts. The
receipt labels the run and its limitations; model-written names and boxes are
not expected to repeat exactly. Positions are fractions of the frame, from 0 to 1.

| Object | What the script drew | What TOKN reported |
|--------|----------------------|--------------------|
| Blue disc | Moved right by 150 px, which is 0.1875 of the frame width | Moved, `dx` 0.1872 |
| Green square | Appeared, at `[0.75,0.12,0.875,0.32]` | Appeared, region `[0.75,0.12,0.876,0.322]` |
| Red disc | Unchanged, at `[0.15,0.36,0.275,0.56]` | Not listed as a change (`dx` 0) |

The measured positions in that historical run matched the drawn ones to within
about 0.002. This is one observation, not a general accuracy claim.

Now score the unseen pair without reading `grading/` first:

```powershell
tokn vision track unseen-before.png unseen-after.png --query "shapes"
```

Compare the returned moved/appeared/disappeared counts and the unchanged-object
count with `grading/unseen-expected.json` from outside the model input. This
held-out synthetic pair is for independent scoring; it is not biological or
real-world validation.

## About these outputs

The receipt describes one historical maintainer observation with a vision model
on TOKN v0.3.105. Requires TOKN v0.3.105 or newer.

Model-written fields can vary from run to run: the object names, the wording of
each change, and the boxes (so `region` and `dx` too). Pixel-measured fields are
deterministic for the same images: `ssim`, `mean_abs_diff`, the measured change
regions, and the `magnitude` of each change inside its region.
