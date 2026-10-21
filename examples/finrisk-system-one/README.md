# Example: Synthetic Financial-Risk Briefing with System One

> "Call the deterministic materiality tool, draft a qualified briefing, ask System One one structured review request, then deliver the briefing with its signals."

This example runs TOKN's **finrisk** domain on a synthetic case. The model calls a deterministic
materiality tool, drafts a briefing, sends one `system_one_evaluate` request with three typed
questions, and then writes a final briefing that reflects the returned signals. A grader checks
the run trace: order, arithmetic, and that the model made one review request instead of several.

Everything is synthetic. The company, figures, and jurisdiction are made up, and nothing here is
investment advice.

| Capability | How this example uses it |
|---|---|
| Domain mode (`finrisk`) | `assess_materiality` computes the ratio and level deterministically |
| System One (`tokn system-one`) | One `system_one_evaluate` request with three typed questions |
| Agent run (`tokn agent-run`) | Runs the prompt against the case workspace |
| Local grader (`check.py`) | Reads the local run log and checks the trace (standard library only) |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | `system-one` and `--output-format stream-json` are in this version | `tokn version` |
| Finrisk tier (14-day trial) | The finrisk domain needs a trial or licence. Community grants only `domains:basic` | `tokn license trial` (one per machine) |
| An LLM provider | The model runs the agent loop | See step 2 |
| A System One backend | The review request goes to the decision backend you configure | See step 3 |
| Python 3.8+ | Runs `check.py` (standard library only) | `python --version` |

The trial also sends an anonymous install registration. To opt out, set `TOKN_NO_TELEMETRY=1`
before running `tokn license trial`.

**What leaves your machine:** the synthetic case JSON, your draft text, and the three
questions go to the System One backend you choose, because `--system-one` is opt-in. The LLM
provider also receives the prompt and tool results. Nothing else is sent. Use only synthetic data
in this example.

## 1. Set up the workspace

Run these from this folder (`examples/finrisk-system-one`).

**bash**
```bash
tokn license trial
tokn system-one status
```

**PowerShell**
```powershell
tokn license trial
tokn system-one status
```

`tokn system-one status` shows which backend is configured. If `tokn license trial` reports the
trial is already used or expired, you need a licence to continue. Contact your TOKN administrator.

## 2. Configure the LLM

Configure the LLM with placeholders. Replace each `<...>` with your own value. See [SETUP.md](../../SETUP.md)
for provider details. Any supported LLM provider works. This example was run with a frontier
OpenAI model.

**bash**
```bash
export NOSPACE_MODEL_PROVIDER=<your provider, for example openai>
export NOSPACE_MODEL_NAME=<your model name>
export ANTHROPIC_API_KEY=<your key>   # use the key variable for your provider
```

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "<your provider, for example openai>"
$env:NOSPACE_MODEL_NAME = "<your model name>"
$env:ANTHROPIC_API_KEY = "<your key>"   # use the key variable for your provider
```

## 3. Choose the System One backend

Set `SYSTEMONE_BACKEND` and the matching key. Use placeholders only; never commit keys.

| Backend | `SYSTEMONE_BACKEND` | Set these variables |
|---|---|---|
| Jev (default) | `jev` | `JEV_API_KEY=<your key>` |
| Bespoke hosted Nimble, via a compatible backend | `compatible` | `DECISION_API_ENDPOINT=<your endpoint>`, `DECISION_API_KEY=<your key>` |
| Microsoft decision-1 | `microsoft` | `<see your Microsoft deployment>` |
| OpenAI Decisions | `openai` | `OPENAI_API_KEY=<your key>` |

**PowerShell example (Jev):**
```powershell
$env:SYSTEMONE_BACKEND = "jev"
$env:JEV_API_KEY = "<your key>"
tokn system-one status
```

## 4. Run the agent

Run the prompt against the case workspace. Stream the events to a file so `check.py` can read them.

**bash**
```bash
tokn agent-run --mode finrisk --system-one --repo-root workspace \
  --prompt-file prompt.md --max-steps 12 --no-confirm \
  --output-format stream-json > events.ndjson
AGENT_EXIT=$?
echo "agent exit code: $AGENT_EXIT"
```

**PowerShell**
```powershell
tokn agent-run --mode finrisk --system-one --repo-root workspace `
  --prompt-file prompt.md --max-steps 12 --no-confirm `
  --output-format stream-json > events.ndjson
$AgentExit = $LASTEXITCODE
Write-Host "agent exit code: $AgentExit"
```

Flags used (checked with `tokn agent-run --help`):

- `--mode finrisk` selects the domain. `--system-one` enables the review request.
- `--repo-root workspace` is where the run log is written (`workspace/.nospace/runs/`).
- `--prompt-file prompt.md` loads the prompt. `--max-steps 12` caps the loop.
- `--no-confirm` skips interactive prompts. `--output-format stream-json` writes events to stdout.

Each executed tool adds a governance cooldown, so one run takes around a minute and a half.

## 5. Grade the run

`check.py` reads only the local run log under the repo root. It makes no network call.

**bash**
```bash
python check.py workspace --exit-code $AGENT_EXIT
```

**PowerShell**
```powershell
python check.py workspace --exit-code $AgentExit
```

`check.py` prints JSON with a `verdict` (`PASS` or `FAIL_CHAIN`) and the list of failed checks.
Its own exit status is 0 for PASS and 1 for FAIL.

## 6. How to check the result

Open `events.ndjson` and find the `final` event. Then confirm:

- `assess_materiality` ran before `system_one_evaluate`.
- The domain result reports `material` with a ratio of 0.06.
- The `system_one_evaluate` request has three questions: `grounded` (noul), `qualified` (noul),
  and `disposition` (choice).
- The final JSON includes `jev_answers` and a `revision_reason`.

## What to look for

- **Deterministic before generative.** The level and ratio come from the tool, not the model's arithmetic.
- **One review request.** Three questions go in one call. Extra calls are a failed check.
- **Qualified wording.** The briefing says it is synthetic, not investment advice, and that thresholds alone do not establish a regulatory conclusion.
- **Honest revision.** The model keeps or revises its draft based on what System One actually returned, and says why.

## What one of our runs looked like (your numbers will differ)

On our test runs the trace passed every check across repeated successful runs. Each run took
roughly 85 to 96 seconds, with most of that time spent in governance cooldowns. The
backend latency was under a second. In one run the model added a citation it could not verify,
and it disclosed that in its answer. Check your own output rather than relying on this summary.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `tokn: command not found` | Binary not on `PATH` | Run it by full path, or add its folder to `PATH` |
| Finrisk mode refused | No trial or licence | Run `tokn license trial`, or obtain a licence |
| `tokn license trial` says already used | Trial is one per machine | Obtain a licence |
| `system-one status` shows no backend | `SYSTEMONE_BACKEND` or key not set | Set the variables in step 3 |
| `check.py` reports `exactly_one_runlog` failed | No run log, or more than one | Delete old files in `workspace/.nospace/runs/` and re-run |
| `check.py` reports `process_completed` failed | The agent run exited non-zero | Check the agent run output, then re-run step 4 |
| `system_one_evaluate` failed | Backend unreachable or key rejected | Re-check the key and backend, then re-run |
| Run is slow | Governance cooldown per tool call | Expected. Do not reduce the cooldown |
