# Example: Autodesign landing page

> "Improve this landing page for a fictional offline note app. Make it readable, accessible, well structured, and concise. Keep the story and the call to action."

This example runs TOKN's autodesign mode on a small synthetic landing page. Each experiment changes the page, the evaluator scores it on four weighted dimensions, and seven binary gates decide whether the change is allowed to count. Kept designs form a Pareto frontier, and you can read both the frontier and the gate results to see what the run did.

The product, the copy, and the scores are all invented. There are no real customers, brands, or data.

| Capability | How this example uses it |
|---|---|
| Autodesign mode | `tokn agent-run --mode autodesign` runs the experiment loop |
| Weighted dimensions | Four dimensions in `design_brief.md`, normalised to sum to 1 |
| Binary gates | Seven gates in `design_brief.md`; a failing gate rejects the experiment |
| Pareto frontier | Written to `.nospace/autodesign/` in the run folder |
| Synthetic evaluator | `eval/score_landing.py` (stdlib Python) prints the scores and gates |
| Read-only checker | `check_results.py` (stdlib Python) summarises the recorded results |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Autodesign mode and `--output-format` | `tokn version` |
| The 14-day trial (`tokn license trial`) or a paid license | AutoDesign is a premium mode; Community does not include `mode:autodesign` | `tokn license features` |
| Python 3 on PATH | The evaluator is a Python script | `python --version` (Windows) or `python3 --version` (macOS/Linux) |
| A model provider and API key | The agent that edits the page is an LLM | See [SETUP.md](../../SETUP.md) |

## What leaves your machine

- **The LLM provider you configure** receives the prompt, the design brief, and the contents of the files the agent reads or edits (`landing/index.html`, `landing/style.css`, and the evaluator output). Nothing else from your machine is sent.
- **The evaluator runs locally.** `eval/score_landing.py` reads two local files and makes no network calls.
- **`check_results.py` runs locally.** It reads files under `.nospace/autodesign/` and writes nothing.
- **Starting a trial** (`tokn license trial`) sends a one-time anonymous install registration (a machine hash and the TOKN version). Set `TOKN_NO_TELEMETRY=1` before running it to opt out.

Run the experiment in a copy of this folder, not in the cloned repo. TOKN writes run artifacts to `.nospace/autodesign/` in the repo root, and you should not commit them.

## 1. Copy the example to a working folder

**bash**
```bash
cp -r examples/autodesign ~/autodesign-run
cd ~/autodesign-run
```

**PowerShell**
```powershell
Copy-Item -Recurse examples\autodesign $HOME\autodesign-run
Set-Location $HOME\autodesign-run
```

## 2. Configure the LLM

Follow [SETUP.md](../../SETUP.md) and set your provider. The shape is:

**bash**
```bash
export NOSPACE_MODEL_PROVIDER=<your provider, e.g. anthropic>
export NOSPACE_MODEL_NAME=<your model name>
export ANTHROPIC_API_KEY=<your key>
```

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "<your provider, e.g. anthropic>"
$env:NOSPACE_MODEL_NAME = "<your model name>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

## 3. Run the autodesign experiment

The prompt is in `prompt.md`. The brief, the gates, and the budget are in `design_brief.md`.

**bash**
```bash
tokn agent-run --mode autodesign --repo-root . --prompt-file prompt.md --max-steps 25 --no-confirm
```

**PowerShell**
```powershell
tokn agent-run --mode autodesign --repo-root . --prompt-file prompt.md --max-steps 25 --no-confirm
```

`--no-confirm` skips the per-tool approval prompts. Remove it if you want to approve each edit by hand.

## 4. Read the results

The run writes its results to `.nospace/autodesign/`:

| File | What it holds |
|---|---|
| `results.json` | One entry per experiment: id, status (kept, discarded, or rejected), score, decision |
| `results.tsv` | The same results as a tab-separated table |
| `run-<timestamp>/timeline.tsv` | One row per iteration: type, score, decision, duration |
| `run-<timestamp>/pareto-frontier.json` | The frontier entries and the best score so far |
| `run-<timestamp>/report.md` | The Pareto table for the run |

Summarise the results from the working folder:

**bash**
```bash
python3 check_results.py
```

**PowerShell**
```powershell
python check_results.py
```

### What the evaluator checks

`eval/score_landing.py` prints one JSON object. The brief sets the weights and the gate order.

| Dimension (weight) | What it measures |
|---|---|
| readability (0.30) | Body text contrast and line height |
| accessibility (0.30) | Page language, image alt text, and contrast |
| structure (0.25) | Exactly one `<h1>`, at least two sections, and a title |
| concision (0.15) | Body copy length, between 40 and 120 words |

| Gate (checked in this order) | Passes when |
|---|---|
| `has_title` | The page has a non-empty `<title>` |
| `has_h1` | The page has exactly one `<h1>` |
| `lang_set` | The `<html>` element has a `lang` attribute |
| `img_alt` | Every `<img>` has an `alt` attribute |
| `contrast_ok` | Body text contrast is at least 4.5:1 |
| `no_external` | No `<link>` or `<script>` loads from `http(s)` |
| `cta_present` | An element has the class `cta` |

Contrast is computed from hex colours on the `body` rule only. The brief sets `# Strict Gates` to true, so a gate the harness does not report counts as failed.

### Expected gate outcomes

These values come from reading the harness logic and the starting page. They were **not run**. Treat them as what the evaluator should report, and check your own run.

| Design | Gates | Result |
|---|---|---|
| Starting page (`landing/`) | `has_title` pass; **`has_h1` fail** (two `<h1>`); **`lang_set` fail**; **`img_alt` fail**; **`contrast_ok` fail** (`#777` on `#fff` is about 4.48:1); `no_external` pass; `cta_present` pass | Rejected. The scorer reports `has_h1` as the rejection gate, because it is the first failing gate in brief order. A rejected experiment's total score is 0. |
| A design that fixes the gates (one `<h1>`, `lang="en"`, alt text, body colour `#505050` on white, about 8:1) | All seven pass | Kept, with dimension scores near 100 in each dimension |

The frontier is the set of kept designs that no other kept design beats on every dimension. A design that is better on one dimension and worse on another stays on the frontier. Check `report.md` for the exact entries.

## What to look for

- **The baseline is rejected, and that is the point.** A design that fails a gate cannot win on the weighted score, however good its other dimensions are.
- **Gates are ordered.** The rejection reason is the first failing gate in the brief, not every failing gate. Fix `has_h1` first and the next failing gate becomes visible.
- **Dimension scores are in the iteration logs, not in `results.json`.** Open `run-*/iterations/iter-N.json` to inspect one experiment's per-dimension and per-gate detail. (Check the file in your run; this layout comes from the source, not from a recorded run.)
- **The frontier is a trade-off, not a winner.** Read `report.md` to see which designs trade readability against concision, for example.
- **Intent themes are not confirmed here.** TOKN's source includes intent-aware strategies (reframe, fix, expand, and others), but this walkthrough does not verify that they change the run. Do not rely on them for the outcome.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `autodesign` is not a recognised mode | TOKN is older than v0.3.57 | Update TOKN, then run `tokn version` |
| Every experiment is rejected on `has_h1` | Expected for the starting page. The agent has not yet removed the second `<h1>` | Let the run continue, or check `report.md` for progress |
| Dimension scores are all 0 | The evaluator printed no JSON, or it failed | Run `python eval/score_landing.py` in the working folder to see the error (`python3` on macOS/Linux) |
| `python` is not found | Python 3 is not on PATH | Install Python 3 and open a new terminal |
| `No results yet` from `check_results.py` | The run has not written results, or you ran the checker in the wrong folder | Run the checker from the working copy, after step 3 |
| The run stops with no experiments | The LLM provider is not configured | Re-check step 2 and [SETUP.md](../../SETUP.md) |
| Run artifacts appear in your repo | You ran the experiment in the cloned repo | Delete `.nospace/` from the repo and run from a copy |
