# Example: two reviewers, one dashboard, handoff notes between peers

> *Two reviewers read the same synthetic status dashboard. Each leaves the other a
> note with an action to take. An agent drafts a review of the dashboard, and the
> two people exchange the result.*

The dashboard is fictional. It describes an imaginary research reactor with
illustrative numbers. It is a review exercise only. Nothing here operates, tunes, or
monitors a real plant, and the numbers are not real limits.

This example shows two things TOKN does for collaboration:

| Capability | What it shows here |
|---|---|
| **Peer exchange** (`tokn peer`) | Two identities write messages to a shared folder. Each side acts on what the other sends, with a trust grade. |
| **Watch and acknowledge** (`tokn peer watch --once`) | A peer picks up new messages and acknowledges them. It runs once and exits, so you control when it runs. |
| **Agent drafts a review** (`tokn agent-run`) | An agent reads the dashboard file and writes a review for the humans to discuss. |
| **Agent peer messaging** (`--peers`, optional) | Agents can message each other through a control plane. This is an advanced path, covered at the end. |

Steps 1–4 are the same-machine path: two terminals, one folder. The cross-machine
path, where the two people are on different computers, is in step 6.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Current release with `tokn peer` and `--peers` | `tokn version` |
| **Two terminals** on one machine | Each terminal is one peer identity | — |
| Licence tier: **Community** for steps 1–4 | No peer gate was found in the licence policy. Confirm on your machine. | `tokn license features` |
| An LLM provider and key (step 5 only) | Runs the agent that drafts the review | see [SETUP.md](../../SETUP.md) |
| **14-day trial** (`tokn license trial`) only if you switch step 5 to a domain mode such as `nucsci` | Domain modes need `domains:<name>`. Community grants only `domains:basic`. The default mode used here does not need it. | `tokn license features` |

> **What leaves your machine.** Steps 1–4 write only local files to the exchange
> folder, and make no model call. Step 5 sends the review prompt and the dashboard file
> to the model provider you configure. Step 6 changes only where the folder lives.

## 1. Create a scratch folder and the synthetic dashboard

macOS / Linux:

```bash
mkdir -p ~/tokn-peers/exchange && cd ~/tokn-peers
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-peers\exchange | Out-Null
Set-Location $HOME\tokn-peers
```

Save the following as `dashboard.json` in that folder. All values are invented for this
exercise.

```json
{
  "reactor": "FICTIONAL-R7",
  "note": "Synthetic, illustrative values. Not real limits.",
  "panels": {
    "A": { "coolant_outlet_c": 301.0, "trend_7d": "flat", "sample_rate_hz": 1.0 },
    "B": { "coolant_outlet_c": 318.0, "trend_7d": "rising", "sample_rate_hz": 0.5 },
    "C": { "coolant_outlet_c": 297.0, "trend_7d": "flat", "sample_rate_hz": 1.0 }
  },
  "alarm_threshold_c": 330.0
}
```

You now have:

```text
tokn-peers/
  dashboard.json      # synthetic, fictional dashboard
  exchange/           # shared folder that both peers write to
```

## 2. Check the exchange folder

Each peer identity needs the same exchange folder. Start with `ana`, the first reviewer.

```bash
tokn peer status --exchange ./exchange --identity ana
```

```powershell
tokn peer status --exchange .\exchange --identity ana
```

`status` reads the folder and prints this peer's state. Add `--check-write` to confirm
the folder is writable before you rely on it.

## 3. Ana sends a review note to Ben

Preview the message first. `--dry-run` computes and prints the message, and writes nothing.

```bash
tokn peer send --exchange ./exchange --identity ana --consumer ben \
  --type review-note --subject "Panel B trend" \
  --note "Panel B coolant reading is rising over 7 days. Please check its sample rate." \
  --action "Confirm why panel B samples at 0.5 Hz while A and C sample at 1.0 Hz" \
  --dry-run
```

```powershell
tokn peer send --exchange .\exchange --identity ana --consumer ben `
  --type review-note --subject "Panel B trend" `
  --note "Panel B coolant reading is rising over 7 days. Please check its sample rate." `
  --action "Confirm why panel B samples at 0.5 Hz while A and C sample at 1.0 Hz" `
  --dry-run
```

When the printed message looks right, run the same command without `--dry-run`. `--type`
is required. `--action` can be repeated for more than one request.

## 4. Ben picks up the note

In a second terminal, as Ben, run the watcher once. `--once` runs a single tick and exits,
so you decide when it runs.

```bash
tokn peer watch --once --exchange ./exchange --identity ben
```

```powershell
tokn peer watch --once --exchange .\exchange --identity ben
```

By default the acknowledgement is deterministic and makes no model call. `--min-grade`
(default `internal`) sets the lowest trust grade the watcher will act on. Ben can check
the folder with `tokn peer status --exchange ./exchange --identity ben`.

Ben replies with his own note:

```bash
tokn peer send --exchange ./exchange --identity ben --consumer ana \
  --type review-reply --subject "Panel B trend" \
  --note "Sampling was reduced on purpose during a calibration window. I will confirm the dates."
```

```powershell
tokn peer send --exchange .\exchange --identity ben --consumer ana `
  --type review-reply --subject "Panel B trend" `
  --note "Sampling was reduced on purpose during a calibration window. I will confirm the dates."
```

Ana runs `tokn peer watch --once --exchange ./exchange --identity ana` to pick it up.

## 5. Agent drafts the dashboard review

Configure the LLM. Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Save this prompt as `review-prompt.txt`:

```text
Read dashboard.json. It is a fictional, synthetic status dashboard for a training
exercise. Write a short review: which panel needs attention, why, and one question
for each reviewer. Do not give operating instructions and do not propose setpoint
changes. Keep it under 150 words.
```

Run the agent in the default mode, with tool confirmation on:

```bash
tokn agent-run --repo-root . --prompt-file review-prompt.txt --max-steps 8
```

```powershell
tokn agent-run --repo-root . --prompt-file review-prompt.txt --max-steps 8
```

Paste the review into a note to the other reviewer with `tokn peer send`, as in step 3.

## 6. Cross-machine: the same folder on a shared path

When the two people are on different computers, both point at one shared folder. Replace
the placeholder with a path your team already has access to.

```bash
tokn peer status --exchange <exchange-share-path> --identity ana
```

```powershell
tokn peer status --exchange <exchange-share-path> --identity ana
```

Each person runs the same `send` and `watch --once` commands from steps 3–4 with their own
`--identity`. The only change is the `--exchange` path. Do not put a relay URL, tunnel,
or host address into the example files. Keep the path in your own shell or config.

### Optional: agents messaging each other

The `--peers` flag lets agents exchange messages through a control plane.

```bash
tokn agent-repl --peers --control-plane-url <control-plane-url> --control-plane-token <your token>
```

```powershell
tokn agent-repl --peers --control-plane-url <control-plane-url> --control-plane-token <your token>
```

Inside the REPL, `/peers list`, `/peers inbox`, `/peers send`, and `/peers thread` work
once peers are enabled. Without `--peers`, the REPL prints `Peers are not enabled. Restart
with --peers.` The control plane is a separate server. This release was not verified to
ship one, so run this path only if your team has a control plane running.

### What to look for

- **The message trail.** Each `send` writes a message to the folder. Each `watch --once`
  picks it up and acknowledges it. Both sides can see the same thread.
- **The trust grade.** Messages below `--min-grade` are not acted on. Check that a
  message with a lower grade is held back.
- **No writes outside the folder.** `status`, `send`, and `watch` should change only the
  exchange folder and the per-identity state file.
- **The review stays a review.** The agent's review should describe the dashboard, ask
  questions, and avoid operating instructions.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `--type` is required | Add `--type review-note` (or another type) to `send` |
| `status --check-write` fails | The exchange folder is not writable, or the path is wrong. Check the path and permissions. |
| `watch --once` acts on nothing | The message may be below `--min-grade`. Check the sender identity and the grade. |
| `Peers are not enabled. Restart with --peers.` | Start the REPL with `tokn agent-repl --peers ...` |
| Control-plane connection refused | The control plane is not running at the URL you gave. This is a separate server. |
| Agent step fails with no tool calls | The LLM is not configured. Re-check step 5 |
