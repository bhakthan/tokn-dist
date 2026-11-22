# Visual perception loop

TOKN has typed vision tools (`tokn vision ...`). They let an agent inspect a
rendered page and compare visual evidence. Steps 1–7 render and inspect the
provided synthetic pages; they do not ask an agent to edit HTML. The optional
build in step 9 is a separate, model-backed exercise with file writes.

## Why typed vision tools

- **Seeing and coding are separate steps.** The vision tools turn a picture into
  typed results: text, boxes, colours, and a list of differences. A coding agent
  can use these results even if it cannot see images itself.
- **Vision-capable coders get measurements.** Pixel scores such as SSIM are
  computed from the images, not guessed by the model.
- **Each check is small.** You can ask one question, get one answer, and fix one
  thing.

## Evidence

In a historical maintainer 5-seed benchmark, a vision-capable coder used these
tools on two tasks: an HTML card and an SVG badge. This is an observed result
from that benchmark, not a guarantee or a result reproduced by this walkthrough.

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
| `.env.example` | Reference-only settings; configure values in your trusted shell. |

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
$secret = Read-Host 'Anthropic API key' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try { $env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
$env:TOKN_VISION_PROVIDER='anthropic'
$env:TOKN_VISION_MODEL='YOUR_MODEL_ID'
```

macOS or Linux:

```bash
read -rs -p 'Anthropic API key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
export TOKN_VISION_PROVIDER='anthropic'
export TOKN_VISION_MODEL='YOUR_MODEL_ID'
```

Use a protected shell/session secret source for PowerShell rather than copying
a key into a command or file.

## Scratch workspace

From the `tokn-dist` root, copy only the three inputs into a unique folder
outside the checkout. Run the walkthrough there; its rendered images and
`.tokn/` state will stay out of the repository.

PowerShell:

```powershell
$WORK = Join-Path $env:TEMP "tokn-vision-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $WORK | Out-Null
Copy-Item examples\visual-perception-loop\target.html, examples\visual-perception-loop\draft.html, examples\visual-perception-loop\brief.md $WORK
Set-Location $WORK
```

macOS or Linux:

```bash
WORK="$HOME/tokn-vision-$(date +%Y%m%d%H%M%S)-$$"
mkdir "$WORK"
cp examples/visual-perception-loop/target.html examples/visual-perception-loop/draft.html examples/visual-perception-loop/brief.md "$WORK/"
cd "$WORK"
```

The commands below use PowerShell paths (`out\`). On macOS or Linux, use
`out/` instead.

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

The image-inspection steps are read-only with respect to the HTML sources, but
model-backed vision calls may send the selected image and query to your
configured provider and may incur charges. Rendering writes PNGs under `out/`.

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

Historical observed output for the supplied draft (results can vary by version
and provider):

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

This is optional and may incur provider charges. Keep normal interactive
tool approvals enabled; do not use `--no-confirm`. Work only in a fresh scratch
folder outside the example checkout. Make a working folder with three things:

- `target.png`: copy `out\target.png` here.
- `brief.md`: the task brief, included in this example.
- An empty `out\` folder.

Then run:

```powershell
tokn agent-run --repo-root . --prompt-file brief.md --image target.png --model-provider anthropic --model-name $env:TOKN_VISION_MODEL --max-steps 30 --permission-mode default --headless
```

The agent writes `index.html`, renders it, diffs it against the target, and
fixes what it finds, subject to the approvals you grant. Stop if it requests
writes outside `index.html` or `out/`.

Historical observed result from one maintainer run; it is not an expected
score or a recorded result from this walkthrough:

- Exit code 0, in 94 seconds.
- 9 steps, 11 tool calls, 0 tool errors.
- 4 vision calls: render, diff, render, diff.
- The second diff reported `converged` true.

Score the result yourself, and inspect both the rendered pixels and the HTML
structure. A visual score does not establish semantic or accessibility
correctness:

```powershell
tokn vision render --kind html --source index.html --out out\final.png
tokn vision diff target.png out\final.png
```

The maintainer's score:

- `ssim`: 0.9794324783309369.
- `high_severity`: 0.
- `converged`: true.
- Remaining: 1 medium and 2 low items, all about style and placement.

## Held-out layout check

To test a change the rebuild has not seen, create a grader-only copy of
`target.html` outside the agent's work folder, add one layout change (for
example, a fifth navigation link), and render it to a new target PNG. Give the
agent only that PNG, `brief.md`, and an empty `out/` directory in a fresh work
folder. Keep the changed HTML outside its read scope. After the approved build,
compare the new PNG with `tokn vision diff`; separately inspect the generated
HTML or browser DOM to confirm the new navigation structure. The visual
comparison is pixel evidence; the DOM check is a separate structural check.

## About these outputs

The historical outputs above come from a maintainer run on TOKN v0.3.105 using
that operator's configured vision model. The minimum version for this
walkthrough is TOKN v0.3.105 or newer.

Model-written fields, such as descriptions and labels, will vary from run to
run. Pixel-measured fields, such as SSIM and colour values, are deterministic
for the same images.
