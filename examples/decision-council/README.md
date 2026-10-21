# Example: a council of decision models triages a wind fleet

This walkthrough runs one real domain task from start to finish:

> *A wind operator has a two-week maintenance window, one crane, two inspection
> crews and 24 turbines. Decide for each turbine whether to defer, inspect or
> replace it, flag imminent risk, set a priority, and build the crew plan.*

It shows three TOKN capabilities working together:

| Tier | What it does here | TOKN command |
|---|---|---|
| **Decision models** | Several typed decision models answer the same three questions for every turbine, in parallel. Each takes milliseconds. | `tokn system-one batch` |
| **Council** | A deterministic vote merges their answers. Rows where the models disagree, or are unsure, are **escalated**. | `python council.py merge` |
| **Reasoning model** | A frontier LLM settles **only the escalated rows**, checks the rest against the policy, and builds the crew plan. | `tokn agent-run` |

The rules are in `workspace/POLICY.md`. The grader computes the correct answer
in code from that policy; it never asks a model. All data in
`workspace/data/turbines.csv` is synthetic.

The table includes traps. One turbine has a replace-level gearbox reading but a
note that says *"sounds fine, recommends deferring"*. Another has a 34 mm blade
crack that the note calls *"cosmetic"*. Several readings sit just below a
threshold. There are also more replace-level turbines than the crane can handle.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Earlier builds hid `POLICY.md` from the agent (see [Troubleshooting](#troubleshooting)) | `tokn version` |
| Python **3.9 or newer** | Runs `council.py`. It uses the standard library only and makes no network call | `python --version` |
| **Two or more** decision-model backends | One backend works, but a council needs at least two voters to find disagreements | see [step 2](#2-pick-your-decision-models) |
| One LLM provider and key | Runs the reasoning step | see [SETUP.md](../../SETUP.md) |

Trial and Community tiers both run this example. System One decision models are
not license-gated. Model calls are billed by your own providers, not by TOKN.

> **What leaves your machine.** Each decision backend receives the measured
> values and note for each turbine, plus the three questions in `batch.json`.
> The LLM receives the prompt and the files the agent reads in `workspace/`.
> `council.py` sends nothing anywhere.

## 1. Copy the example

macOS / Linux:

```bash
cp -r examples/decision-council ~/tokn-council && cd ~/tokn-council && mkdir -p votes
```

Windows PowerShell:

```powershell
Copy-Item examples\decision-council $HOME\tokn-council -Recurse
Set-Location $HOME\tokn-council; New-Item -ItemType Directory votes | Out-Null
```

You now have:

```text
tokn-council/
  batch.json            # 24 typed requests, one per turbine (same for every backend)
  council.py            # merges votes and grades the result (answer key lives here)
  prompt.md             # instructions for the reasoning step
  votes/                # you will put one <backend>.json per decision model here
  workspace/POLICY.md   # the maintenance policy
  workspace/data/turbines.csv
```

The answer key is in `council.py`, **outside** `workspace/`, so the agent never
sees it.

## 2. Pick your decision models

List the supported models and the settings for each. This works offline:

```bash
tokn system-one models
```

These are the three backends we used. Use any two or more you have access to.

| Backend | Settings |
|---|---|
| TypeSafe **Jev** | `SYSTEMONE_BACKEND=jev`, `JEV_API_KEY=<key>` |
| Bespoke Labs **Nimble** (hosted) | `SYSTEMONE_BACKEND=compatible`, `SYSTEMONE_BASE_URL=https://api.bespokelabs.ai/v1`, `SYSTEMONE_API_KEY=<key>`, `SYSTEMONE_MODEL=nimble-latest` |
| Microsoft **decision-1** | `SYSTEMONE_BACKEND=microsoft`, `DECISION_API_ENDPOINT=https://<resource>.cognitiveservices.azure.com`, `DECISION_API_KEY=<key>` (or Entra ID via `az login`) |
| OpenAI Decisions API | `SYSTEMONE_BACKEND=openai`, `OPENAI_API_KEY=<key>` |

Set these in your shell. Destinations such as `SYSTEMONE_BACKEND`,
`SYSTEMONE_BASE_URL` and `DECISION_API_ENDPOINT` are **never** read from a
repository `.env`. Never paste a key into a file you might commit or share.

## 3. Ask every decision model (in parallel)

Run one batch per backend. Each command sends the 24 requests eight at a time
and writes the answers as JSON to stdout. Use a separate shell for each backend
so the settings do not leak between them. Running them side by side is what
makes this tier fast.

macOS / Linux, Jev for example:

```bash
export SYSTEMONE_BACKEND=jev JEV_API_KEY=<your key>
tokn system-one batch --file batch.json --concurrency 8 --run-timeout 120s --mcp-disabled > votes/jev.json
```

Windows PowerShell, Nimble for example:

```powershell
$env:SYSTEMONE_BACKEND  = "compatible"
$env:SYSTEMONE_BASE_URL = "https://api.bespokelabs.ai/v1"
$env:SYSTEMONE_API_KEY  = "<your key>"
$env:SYSTEMONE_MODEL    = "nimble-latest"
tokn system-one batch --file batch.json --concurrency 8 --run-timeout 120s --mcp-disabled > votes\nimble.json
```

Repeat with your other backend(s), writing `votes/<name>.json` each time. The
file name becomes the voter's name. Before spending a call, `tokn system-one
status` confirms which backend a shell is set to.

Each request asks three typed questions:

| Question | Type | Answer |
|---|---|---|
| `action` | `choice` | `defer`, `inspect` or `replace`, with the policy thresholds as criteria |
| `imminent_risk` | `noul` | a probability that failure is imminent |
| `priority` | `score` | one of five priority levels |

Typed answers from different vendors can be compared directly. No free-text
parsing is involved.

## 4. Form the council (offline)

```bash
python council.py merge votes
```

The output looks like this (from our run):

```text
provider       rows  action  in/out tokens
decision1      24/24     96%  11848/72
jev            24/24     96%  20075/1759
nimble         24/24    100%  14320/96

council action accuracy 100%; 3 of 24 row(s) escalated: ['T11', 'T18', 'T24']
wrote workspace/council/consensus.csv and workspace/council/disputes.json
```

How the council works:

- **Majority vote** per field. On an action tie, the most severe action wins.
- A row is **escalated** when the models split on action or risk, their
  priorities differ by 2 or more, the winning answer has low confidence, or a
  model gave no answer.
- `consensus.csv` holds one line per turbine. `disputes.json` holds each
  model's vote for the escalated rows only. Small evidence files keep the next
  step cheap.

Two models each made one mistake here, but on different turbines, so the vote
corrected both. That is the reason to use more than one decision model.

## 5. Let the reasoning model settle the disputes

Configure your LLM as in [SETUP.md](../../SETUP.md). For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a Claude model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

Then run:

```bash
tokn agent-run --repo-root workspace --prompt-file prompt.md --max-steps 20 --no-confirm --no-stream
```

`prompt.md` tells the agent to:

1. accept the undisputed rows as they are;
2. decide each escalated row from the measured values and `POLICY.md`;
3. spot-check the undisputed rows, and override one only when a measured value
   plainly contradicts the consensus;
4. build the crew plan within capacity: 4 replacements and 8 inspections.

It writes `workspace/triage.json` with only the escalated and overridden rows
plus the plan. Expect 1–3 minutes.

## 6. Grade it

```bash
python council.py grade workspace/triage.json
```

```text
action 100%  risk 100%  priority 100%
wrong rows: none; replace-level under-calls: none
crew plan: valid
PASS
```

The grader overlays the agent's rows on the council's consensus, then checks:

| Check | Why it matters |
|---|---|
| Action accuracy is 95% or higher | Matches the written policy |
| No replace-level turbine is under-called | The costly error is calling a failing gearbox "inspect" |
| Every escalated row was settled | A skipped dispute is reported, never silently filled in |
| The crew plan is valid | Within capacity, highest priority first, nothing dropped |

It exits `0` on PASS and `1` on FAIL.

## What one of our runs looked like

Three decision models and three reasoning models (two OpenAI, one Anthropic).
Your numbers will differ.

| Measure | Result |
|---|---|
| Decision tier | 72 typed decisions in about **2 seconds**, about 48k small-model tokens |
| Council | 100% action accuracy; **3 of 24** rows escalated |
| Reasoning tier | All three reasoning models scored 100%, with a valid crew plan |
| Replace-level turbines under-called | none |

The efficiency comes from the decision tier. The council reached the right
answer for 21 of 24 turbines in about two seconds, with no frontier-model call.
The reasoning model's job became settling three disputes and planning the crew.
Every row also has an independent, explainable vote behind it.

No model fell for the T02 and T03 notes. The two individual mistakes (T11 and
T24) were inspect-level turbines called `defer`. Each was a different model's
miss, so both rows were escalated and settled correctly.

## Try this next

- **Remove a voter.** Delete one file from `votes/` and run `merge` again.
  Watch the escalations and accuracy change.
- **Break the data.** Edit a reading in `workspace/data/turbines.csv` so it sits
  on a threshold, re-run steps 3–6, and see whether the council escalates it.
  `council.py` recomputes the answer key from the edited data.
- **Compare without the council.** Delete `workspace/council/` and run step 5
  with your own prompt that asks for all 24 rows. Compare the tokens the agent
  reports at the end.

This is decision support for a human maintenance planner, not an autonomous
work order.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The agent says it cannot read `POLICY.md`, or sees `[OUTPUT BLOCKED BY SCANNER ...]` | Upgrade to v0.3.57 or newer. Earlier builds treated the sentence "A model judgment never overrides a measured threshold" as a prompt injection and blocked the file. v0.3.57 delivers the file with a visible `[scanner review: ...]` notice instead. |
| `merge` reports fewer than 24 rows for a backend | Look in that `votes/<name>.json` for `"error"` entries. A `401` means a wrong key; a timeout means you should raise `--run-timeout` |
| `no JSON object found` | The batch failed before it produced output. Re-run the command without `>` to see the message |
| `tokn system-one status` shows the wrong backend | A setting from another shell or from `~/.tokn/config/credentials.env` is taking effect. Open a fresh shell |
| `disputed row(s) not adjudicated` | The agent skipped an escalated row. Run step 5 again, or raise `--max-steps` |
| Rate-limit (`429`) messages | TOKN retries automatically. Lower `--concurrency` or try again later |
