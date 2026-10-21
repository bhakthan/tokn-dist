# Example: a loop that wins the wrong game (Graph of Loops)

This walkthrough shows why one optimizing loop cannot be trusted to grade itself:

> *A loop told to minimize training error will keep making its model more complex
> until training error looks excellent, even though the model is now worse at the
> real goal. A governed graph of loops must refuse that "win" unless an independent
> held-out computation agrees.*

The task is curve fitting. The data are synthetic, from a quadratic with a little
noise. The optimizer only sees the training set, and a guard loop and an independent
check both look at data the optimizer never sees.

| Feature | What it does here |
|---|---|
| **Optimizing loop** | Tries to minimize training error. Its primary metric is gameable. |
| **Counter-metric guard** | Refuses a win when held-out error gets worse. |
| **Frozen-rule anchor** | An independent held-out check the optimizer never sees. A win must agree with it. |
| **GraphRecord** (`tokn loopgraph run --json`) | An audit receipt: was the win accepted, was it grounded, and why. |
| **Cross-check** (`crosscheck.py`) | Recomputes both errors in plain Python and compares them with the record. |

No LLM is involved. Every check is a local command.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Ships `tokn loopgraph` | `tokn version` |
| Python 3 (standard library only) | Runs the oracle and the cross-check. No packages to install. | `python --version` |

Trial and Community tiers both run this example. The `loopgraph` commands are not
license-gated in the source. The CLI prints `running the free community tier` when
the trial has ended, which is expected. If a command refuses to run, start the
14-day trial with `tokn license trial`.

> **What leaves your machine.** Nothing. This example makes no model call and no
> network request. Every file it reads is in this folder.

## 1. Open the example folder

macOS / Linux:

```bash
cd examples/loop-graph
```

Windows PowerShell:

```powershell
Set-Location examples\loop-graph
```

You now have:

```text
loop-graph/
  graph.json          # the governed graph: two loops, two anchors, a stop rule
  model.json          # the one knob the optimizer turns: {"degree": N}
  oracle.py           # the grading oracle: fits on train, scores on a given set
  crosscheck.py       # recomputes both errors and compares them with the record
  data/train.csv      # the optimizer's data (13 synthetic points)
  custodian/heldout.csv  # held-out data the optimizer never sees (12 points)
```

> **Shell note.** The graph's check commands use `python`. On macOS and Linux, if
> `python` is not found but `python3` is, replace `python` with `python3` in
> `graph.json`. Keep the paths relative and free of spaces.

## 2. Check the graph refuses to run without an anchor

`validate` checks the spec and refuses a graph that has no held-out anchor:

macOS / Linux / Windows PowerShell (same command):

```bash
tokn loopgraph validate --spec graph.json
```

A valid spec should pass without a refusal. The `--cheap-win` and `--ungrounded`
flags, listed in `tokn loopgraph validate --help`, are for demonstrating refusals.
(Not yet run against this copy of the example.)

## 3. Start where the optimizer starts

With `model.json` at degree 1, a straight line cannot follow a curve. Both
errors should be high. Check this with the oracle directly:

macOS / Linux / Windows PowerShell (same command):

```bash
python oracle.py --model model.json --train data/train.csv --eval custodian/heldout.csv --max-mse 0.10 --emit exit
```

Expected: a line that ends `pass=false` and exit code 1.

## 4. Play the optimizer: chase the training score

Set the model to degree 12. A polynomial that complex can pass through nearly
every training point. This is the move a loop makes when it only looks at its
primary metric.

macOS / Linux:

```bash
echo '{ "degree": 12 }' > model.json
```

Windows PowerShell:

```powershell
Set-Content -Path model.json -Value '{ "degree": 12 }'
```

Run the graph and save its record:

macOS / Linux:

```bash
tokn loopgraph run --spec graph.json --json --timeout 60s > graph-record.json
```

Windows PowerShell:

```powershell
tokn loopgraph run --spec graph.json --json --timeout 60s | Out-File -Encoding utf8 graph-record.json
```

Then cross-check the record:

macOS / Linux / Windows PowerShell (same command):

```bash
python crosscheck.py graph-record.json
```

Expected for degree 12: the training check passes, the held-out check fails, and
the graph does **not** accept the win. The cross-check prints `CONSISTENT`.

## 5. Play the optimizer again: a fit that generalizes

Now set the model to degree 2, which matches the curve the data came from.

macOS / Linux:

```bash
echo '{ "degree": 2 }' > model.json
```

Windows PowerShell:

```powershell
Set-Content -Path model.json -Value '{ "degree": 2 }'
```

Run the graph, record it and cross-check it, using the same commands as in step 4.

Expected for degree 2: both checks pass, and the graph accepts the win as grounded.

## 6. Read the result

Open `graph-record.json`. These are the fields to look at:

| Field | What it tells you |
|---|---|
| `accepted` | `true` only when the graph accepted the optimizer's win |
| `grounded` | `true` only when the held-out anchors agreed with the claim |
| `stop_reason` | Why the graph stopped |
| `cycles[].anchor_verdicts[].agrees` | Whether each anchor agreed with the optimizer's claim |

`crosscheck.py` exits 0 when the record agrees with the independent computation,
1 when a win was accepted that the held-out check refutes, and 2 when an input
is missing.

### What we expect (not yet observed in this port)

These expectations follow from the source's test design. They have not been
run against this copy of the example, so check them on your machine.

| `model.json` | Training check | Held-out check | Expected graph result |
|---|---|---|---|
| `degree 1` | fails | fails | no win claimed |
| `degree 12` | passes (interpolates) | fails | win vetoed, `accepted` false |
| `degree 2` | passes | passes | win accepted, `grounded` true |

## What to look for

- **The primary metric can be gamed.** Degree 12 wins on training error and
  still loses on held-out error. The graph must not report that as a win.
- **The guard sees data the optimizer does not.** The held-out file is in
  `custodian/` and the optimizer's loop never reads it.
- **Refusal is a result, not a failure.** A graph that refuses a fake win is
  doing its job. A graph that accepts one is the bug.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python` not found (macOS / Linux) | Replace `python` with `python3` in `graph.json` |
| `oracle: singular normal-equations matrix` | Expected for some high degrees. The check fails closed, so the graph refuses. |
| Graph run hits the overall timeout | Add `--run-timeout 2m` to the `tokn loopgraph run` command. The default is 30s. |
| `tokn loopgraph` shows the trial banner | Expected on the community tier. Start a trial with `tokn license trial` if you want the full feature set. |
| `unknown flag` | Upgrade to v0.3.57 or newer, then run `tokn loopgraph run --help` |
