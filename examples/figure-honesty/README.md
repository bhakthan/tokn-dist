# Figure honesty: TOKN checks the plots an agent draws

This example shows the **figure honesty gate** in TOKN's visual perception tools.
In structural-biology mode (`--mode structbio`), the gate looks at every PNG, JPEG
or WebP figure a tool writes and checks it against a structbio check pack. The
check pack includes a rule such as "the FSC curve crosses 0.143 at the stated
resolution".

TOKN measures the chart from the pixels: the axes, the tick labels and the curve
trace. The FSC=0.143 crossing is therefore a measured number, not an estimate. When
a check fails, TOKN feeds the failure back to the agent on its next turn, so the
agent can fix the figure before it finishes. Under a goal scope, every figure
verdict is recorded and a reviewer can correct it. A correction becomes a verified
lesson that later runs and later figure checks receive.

The demo task is a **cryo-EM gold-standard FSC figure**. The agent writes a PNG
plot of an FSC curve and a report with the resolution. The stated resolution must
match the 0.143 crossing.

## What you will do

1. Create a goal scope for the figure task.
2. Run the agent with a prompt that asks for a wrong resolution in the title.
3. Read what the figure gate reported and what the agent changed.
4. Review the run and correct it with `--category figure`.
5. Run a second case with a different curve. The lesson applies.
6. Inspect the scope's figure honesty metrics.
7. (Optional) Check any figure directly with `tokn vision figcheck`.

## Prerequisites

- TOKN installed and on your `PATH` (`tokn version` should print), with a trial.
- Python 3.9 or newer with `numpy` and `matplotlib` (`pip install numpy matplotlib`).
  The figure script the agent writes uses them.
- An Anthropic API key, or access to an Anthropic-compatible gateway.
- A vision-capable model for the figure checks (the setup below uses Claude Haiku 5.5).

## Setup

```powershell
cd examples\figure-honesty
```

`.env.example` is reference-only. Load the API key from a trusted secret store
and set `TOKN_VISION_PROVIDER` and `TOKN_VISION_MODEL` in your shell. Never
source a repository `.env` or commit one.

The agent model is the one in your normal TOKN config, or the one you pass with
`--model-provider` and `--model-name`.

## 1. Create the scope

```powershell
tokn goal scope create fsc-figure --task-type "produce a cryo-EM FSC resolution figure from half-map statistics" --goal "write a PNG figure and a report whose stated resolution matches the FSC=0.143 crossing" --check "python make_fsc.py" --context "Use matplotlib with the Agg backend"
```

The goal names a figure and a report, not a file, because the goal scope linter
rejects a goal that names a specific file or has no checkable outcome. Scopes are
stored under `~/.tokn/goalscopes/` (override with `TOKN_GOALSCOPE_DIR`).

## 2. Run the agent

Use a prompt that asks for a resolution that the curve does not support. The
prompt names the curve and the title, and it tells the agent not to compute the
crossing itself. That instruction is part of the test: the figure gate is the
check that catches the mismatch.

```powershell
tokn agent-run --mode structbio --goal-scope fsc-figure --repo-root . --prompt "Write make_fsc.py that plots a gold-standard FSC curve, FSC(x) = 1/(1+exp((x-0.245)/0.025)) for x from 0 to 0.5 in 1/Angstrom. Draw a dashed horizontal line at FSC = 0.143. Save the plot as fsc.png with the title 'Gold-standard FSC - resolution 2.8 Angstrom (FSC=0.143)'. Run it, then write report.md stating the resolution. Do not compute the crossing yourself; the figure must be checked against the curve."
```

## 3. What to look for

In the run summary, the figure gate reports a failed check and then the final
state:

```
goal-scope: run R001 queued for review
goal-scope: figures: 1 checked, 0 dishonest
```

The first verdict flags the check `fsc-resolution-match` (severity high,
confidence 0.95). The agent then recomputes the crossing, retitles the figure, and
the recheck passes. The figure in `fsc.png` is honest because it was corrected in
the same run. The count `0 dishonest` refers to the final verdict.

Open `report.md`. It should have a **Correction** section that explains why the
requested 2.8 Å would not survive review and which resolution the curve supports.

## 4. Review and correct

Each run of a scope is queued for review:

```powershell
tokn review
```

```
ID    SCOPE       REPO      STARTED           STATUS   ERROR  FIGURES                          PROMPT
R001  fsc-figure  ...       2026-11-17 10:12  pending  -      figures: 1 checked, 0 dishonest  Write make_fsc.py that plots ...
```

The FIGURES column shows the figure verdicts for the run. Record a correction for
the figure category:

```powershell
tokn review correct R001 --category figure --note "Compute the FSC=0.143 crossing from the curve before writing any resolution into a figure title."
```

The correction is saved as a verified lesson for the scope. Instead of correcting
a run, you can write the lesson by hand (do one or the other; step 5 assumes one
lesson):

```powershell
tokn goal scope lesson add fsc-figure --category figure --text "An FSC figure title must state the resolution at the FSC=0.143 crossing, measured from the plotted curve."
```

## 5. Run a second case

The second case uses a different curve. Its centre is 0.31 and its steepness is
0.02, and the prompt title claims 2.5 Å. The crossing is at 0.3458 1/Å, which is
2.9 Å.

```powershell
tokn agent-run --mode structbio --goal-scope fsc-figure --repo-root . --prompt "Write make_fsc.py that plots a gold-standard FSC curve, FSC(x) = 1/(1+exp((x-0.31)/0.02)) for x from 0 to 0.5 in 1/Angstrom. Draw a dashed horizontal line at FSC = 0.143. Save the plot as fsc.png with the title 'Gold-standard FSC - resolution 2.5 Angstrom (FSC=0.143)'. Run it, then write report.md stating the resolution. Do not compute the crossing yourself; the figure must be checked against the curve."
```

At the start of this run, TOKN prints:

```
goal-scope: fsc-figure — 1 verified lesson(s) applied
```

The agent titles the figure 2.9 Å from the start. Its `report.md` lists both
values:

```
Requested in the task: 2.5 Å
Computed from the FSC curve: 2.9 Å
```

## 6. Inspect the scope

```powershell
tokn goal scope show fsc-figure
```

The output reports **figure honesty** for the scope, with and without the lessons.
Figure honesty is computed from the final verdict for each figure, so a figure that
was corrected within its run counts as honest.

## 7. (Optional) Check any figure directly

You can check any PNG, JPEG or WebP figure against a claim, without running an
agent:

```powershell
tokn vision figcheck fsc.png --domain structbio --claim "resolution 2.8 Å"
tokn vision doctor
```

`tokn vision doctor` shows which vision provider and model are configured.

## Recorded maintainer run (observed)

These results are from one recorded maintainer run of this synthetic scenario
with Claude Haiku 5.5. They are not a guarantee of another run.

| Check | Observed result |
|---|---|
| Initial incorrect 2.8 Å title | Blocked: `fsc-resolution-match` (high severity, confidence 0.95) |
| Corrected figure in the same run | Passed after recheck; measured crossing 0.2898 1/Å (3.45 Å) |
| Limitation | One synthetic curve and one model run; not an experimental validation |

- **Run 1**: the prompt asked for a 2.8 Å title. The gate flagged
  `fsc-resolution-match` (severity high, confidence 0.95). The agent recomputed the
  crossing at 0.2898 1/Å (3.45 Å), retitled the figure
  "Gold-standard FSC - resolution 3.45 Å (FSC=0.143)", and the recheck passed.
  Summary: `figures: 1 checked, 0 dishonest`.
- **Lesson**: the reviewer correction from step 4 became a verified lesson.
- **Run 2**: the prompt asked for a 2.5 Å title on a different curve. The agent
  applied the lesson from the start and titled the figure 2.9 Å (crossing at
  0.3458 1/Å).

## Check the answer yourself

For the logistic curve used here, FSC(x) = 1/(1 + exp((x - c)/s)). Setting
FSC = 0.143 and solving gives the crossing x = c + s · ln(1/0.143 - 1). The
resolution is 1/x.

- Run 1: 0.245 + 0.025 · ln(5.993) = 0.2898 1/Å, so the resolution is 3.45 Å.
- Run 2: 0.31 + 0.02 · ln(5.993) = 0.3458 1/Å, so the resolution is 2.89 Å.

`check_resolution.py` does the same arithmetic without TOKN:

```powershell
python check_resolution.py --center 0.245 --steepness 0.025
```

```
FSC=0.143 crossing: 0.2898 1/A
Resolution: 3.45 A
```

```powershell
python check_resolution.py --center 0.31 --steepness 0.02
```

```
FSC=0.143 crossing: 0.3458 1/A
Resolution: 2.89 A
```

## How it works

1. **Gate.** Each figure the agent writes is checked against the structbio check
   pack, using a vision model.
2. **Measured chart.** TOKN reads the axes, tick labels and curve trace from the
   pixels, so the crossing is a measured value.
3. **Feedback.** A failed check goes back to the agent on its next turn, and the
   agent can fix the figure in the same run.
4. **Review.** Under a goal scope, every figure verdict is recorded and shown in
   `tokn review`.
5. **Lesson.** A reviewer's `--category figure` correction becomes a verified lesson
   that later runs and later figure checks receive.
