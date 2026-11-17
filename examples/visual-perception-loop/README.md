# Visual perception loop

TOKN has typed vision tools (`tokn vision ...`). They let an agent look at a
rendered page, measure what it sees, and check its own work. This example walks
through each tool on a small landing page, then runs a full agent loop that
rebuilds the page from a screenshot.

## Why typed vision tools

- **Seeing and coding are separate steps.** The vision tools turn a picture into
  typed results: text, boxes, colours, and a list of differences. A coding agent
  can use these results even if it cannot see images itself.
- **Vision-capable coders get measurements.** Pixel scores such as SSIM are
  computed from the images, not guessed by the model.
- **Each check is small.** You can ask one question, get one answer, and fix one
  thing.

## Evidence

In the maintainer's 5-seed benchmark, a vision-capable coder (Claude Haiku 5.5)
used these tools on two tasks: an HTML card and an SVG badge.

| Task | Average SSIM with vision tools | Average SSIM without |
|------|-------------------------------|----------------------|
| HTML card | 0.974 | 0.957 |
| SVG badge | 0.970 | 0.942 |

Runs with the tools were slower: 38 to 98 seconds, compared with 8 to 30 seconds
without them.

## Files

| File | What it is |
|------|------------|
| `target.html` | The page to match. Think of it as the design you were given. |
| `draft.html` | A copy of the page with three faults (see below). |
| `brief.md` | The task brief for the agent run in step 9. |
| `.env.example` | Placeholder settings. Copy it to `.env` and add your key. |

The draft has three faults:

1. The main button is blue (`#2b7bd6`) instead of orange (`#e36414`).
2. The button says "Start trial" instead of "Start free trial".
3. The "Share" card is missing.

## Setup

You need:

- TOKN v0.3.105 or newer on your `PATH`.
- Google Chrome or Chromium. The render step uses headless Chromium.
  `tokn vision doctor` shows whether it was found.
- An Anthropic API key, or an Anthropic-compatible gateway.

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

The commands below are the same on every system. Run them from this folder,
where `out\` is created by the render step. The commands below show PowerShell
paths (`out\`). On macOS or Linux, use `out/` instead.

## Walkthrough

### 1. Check the setup

```powershell
tokn vision doctor
```

This lists the vision provider, the model, and the headless browser.

### 2. Render both pages

```powershell
tokn vision render --kind html --source target.html --out out\target.png
tokn vision render --kind html --source draft.html --out out\render_1.png
```

Each command writes a 1280x720 PNG.

### 3. Read the layout

```powershell
tokn vision transcribe out\target.png --focus layout
```

The output is a list of regions. Each region has a `role`, a `box`, and
`children`. Boxes are fractions of the page, from 0 to 1. Here is the logo entry,
shortened:

```json
{"box": [0.05, 0.035, 0.105, 0.065], "label": "Logo", "role": "text", "text": "Lumen"}
```

### 4. Find an element

```powershell
tokn vision grep out\target.png --query "primary call-to-action button"
```

The result for this page is "Start free trial orange button", with confidence
0.95 and box `[0.428,0.345,0.572,0.416]`.

### 5. Inspect the colour and shape

```powershell
tokn vision inspect out\target.png --element "Start free trial button" --attr "background color,text color,border radius"
```

Each attribute comes with a `source` field:

- `"model"` means the vision model read the value.
- `"measured"` means TOKN measured the value from the pixels.

For this button:

- Background: `#e36414` (source `model`, confidence 0.95).
- Border radius: `8` (source `model`, confidence 0.6).
- Text colour: `#feffff` (source `measured`, `model_value` `#feffff`, confidence 0.85).

Trust the `measured` values most. Treat `model` values as a second opinion.

### 6. Check a layout claim

Each `--assert` is a plain-language claim. TOKN returns `pass` and a confidence.

```powershell
tokn vision align out\target.png --assert "exactly three feature cards sit side by side below the headline"
tokn vision align out\target.png --assert "the navigation bar has five links"
```

- The first claim passes (`true`, confidence 0.97). The page has three cards.
- The second fails (`false`, confidence 0.95). The navigation bar has four links.

### 7. Compare the draft with the target

```powershell
tokn vision diff out\target.png out\render_1.png
```

On the draft, the result is:

- `ssim`: 0.9378182570672562 (measured from pixels).
- `high_severity`: 2.
- `converged`: false.

The discrepancies:

- **High:** a row is misplaced.
- **High:** the "Share" card is missing.
- **Medium:** the call-to-action button has the wrong colour (blue instead of
  orange).
- **Low:** the button label is wrong.

Fix the high-severity items first. Then render again and diff again.

`tokn vision route` lists every vision operation, if you want to see what else
is available.

### 8. Turn on the typed tools for the agent

The next step lets an agent call the same tools. Set these two variables first.

PowerShell:

```powershell
$env:TOKN_VISION_TOOLS='typed'
$env:TOKN_HOST_VISION='1'
```

macOS or Linux:

```bash
export TOKN_VISION_TOOLS=typed
export TOKN_HOST_VISION=1
```

### 9. Let an agent rebuild the page

Make a working folder with three things:

- `target.png`: copy `out\target.png` here.
- `brief.md`: the task brief, included in this example.
- An empty `out\` folder.

Then run:

```powershell
tokn agent-run --repo-root . --prompt-file brief.md --image target.png --model-provider anthropic --model-name claude-haiku-5-5 --max-steps 30 --headless --no-confirm
```

The agent writes `index.html`, renders it, diffs it against the target, and
fixes what it finds.

Result from the maintainer's run:

- Exit code 0, in 94 seconds.
- 9 steps, 11 tool calls, 0 tool errors.
- 4 vision calls: render, diff, render, diff.
- The second diff reported `converged` true.

Score the result yourself:

```powershell
tokn vision render --kind html --source index.html --out out\final.png
tokn vision diff target.png out\final.png
```

The maintainer's score:

- `ssim`: 0.9794324783309369.
- `high_severity`: 0.
- `converged`: true.
- Remaining: 1 medium and 2 low items, all about style and placement.

## About these outputs

These outputs come from one maintainer run with Claude Haiku 5.5 as the vision
model on TOKN v0.3.105. Requires TOKN v0.3.105 or newer.

Model-written fields, such as descriptions and labels, will vary from run to
run. Pixel-measured fields, such as SSIM and colour values, are deterministic
for the same images.
