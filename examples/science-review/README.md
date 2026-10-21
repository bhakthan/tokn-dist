# Example: Reviewing a Figure Caption with `review_artifact`

> "Here is a figure caption with three planted defects. Use TOKN's review tool to surface them, then check what it reported."

A reviewer agent receives a scientific figure caption that contains three planted defects. The
model must call TOKN's `review_artifact` tool, which checks the caption against the numbers,
citations, and code the author declared. A small checker then reads the streamed output and
confirms the tool reported each defect with the expected severity.

Everything here is synthetic. The figure, numbers, citation keys, and code are made up.

| Capability | How this example uses it |
|---|---|
| `review_artifact` tool | Checks declared numbers, citations, and code provenance for an artifact |
| Agent run (`tokn agent-run`) | Runs the reviewer prompt and streams events |
| Local checker (`check.py`) | Reads the streamed output file only (standard library) |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | `--output-format stream-json` is in this version | `tokn version` |
| Tier | `review_artifact` is registered in every mode, so no domain licence is expected. This is from source; we have not confirmed it on the public binary. If the tool is missing, see Troubleshooting | `tokn agent-run --help` |
| An LLM provider | The model calls the review tool | See step 2 |
| Python 3.8+ | Runs `check.py` (standard library only) | `python --version` |

**What leaves your machine:** the caption text and the review inputs in `prompt.md` go to the LLM
provider you configure, because the model reads them. Nothing else is sent by this example. Use
only synthetic or public content.

## 1. Set up

Run these from this folder (`examples/science-review`).

**bash**
```bash
tokn version
```

**PowerShell**
```powershell
tokn version
```

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

## 3. Run the reviewer

Stream the events to a file so `check.py` can read them.

**bash**
```bash
tokn agent-run --prompt-file prompt.md --max-steps 8 --no-confirm \
  --output-format stream-json > events.ndjson
AGENT_EXIT=$?
echo "agent exit code: $AGENT_EXIT"
```

**PowerShell**
```powershell
tokn agent-run --prompt-file prompt.md --max-steps 8 --no-confirm `
  --output-format stream-json > events.ndjson
$AgentExit = $LASTEXITCODE
Write-Host "agent exit code: $AgentExit"
```

Flags used (checked with `tokn agent-run --help`):

- `--prompt-file prompt.md` loads the reviewer prompt. `--max-steps 8` caps the loop.
- `--no-confirm` skips interactive prompts.
- `--output-format stream-json` writes newline-delimited events to stdout, which the redirect saves.
  Logs go to stderr, so they do not end up in `events.ndjson`.

## 4. Check the output

Before grading, open `events.ndjson` and look at one line that mentions `review_artifact`. The
checker expects either a `progress` line whose `text` is a JSON event, or a plain event line. It
looks for the tool name under `ToolName` or `tool_name`, and the result under `Output` or
`output`. If your output uses other key names, the checker will report `called` as failed. In that
case, update the two key names in `check.py` to match your line.

**bash**
```bash
python check.py events.ndjson
```

**PowerShell**
```powershell
python check.py events.ndjson
```

`check.py` reads only `events.ndjson`. It makes no network call. It prints JSON with a `verdict`
(`PASS` or `FAIL`) and the list of failed checks. Its exit status is 0 for PASS, 1 for FAIL, and 2
if the file cannot be read.

## What the checker expects

| Check | Expected |
|---|---|
| `called` | `review_artifact` was called and returned a result |
| `report_present` | The result contains a report with `findings` and `passed` |
| `reports_untraceable_number_high` | A `untraceable_number` finding at `high` severity (the 47% claim) |
| `reports_unresolved_citation_high` | An `unresolved_citation` finding at `high` severity (the [4] reference) |
| `reports_code_artifact_drift_critical` | A `code_artifact_drift` finding at `critical` severity (0.42 vs 0.47 in the plot code) |
| `no_incomplete_provenance` | No `incomplete_provenance` finding (the provenance fields are present) |
| `not_passed` | `passed` is `false` |
| `three_findings` | Exactly three findings |

## What to look for

- **Three defects, found by the tool.** The model should report what `review_artifact` returned,
  not invent findings of its own.
- **Known false positives.** The number checks compare numbers in prose against the declared
  values. A number such as the `4` inside `IC50` can be flagged as untraceable. If you see one,
  treat it as a known limit of the check and note it in your review rather than hiding it.
- **Drift is critical.** The producing code and current code disagree on the reduction value, so
  the figure no longer matches what the code produces.

## What one of our runs looked like (your numbers will differ)

On our test runs, each model we tried flagged all three planted defects, and none raised a false
provenance finding. Check your own output rather than relying on this summary.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `review_artifact` is not called | The model did not follow the prompt | Re-run. If it persists, try a different model |
| Tool not available | Your TOKN build does not register it | Run `tokn version`, then update to v0.3.57 or newer |
| `check.py` reports `called` failed | Key names differ from the checker's assumption | Look at one line of `events.ndjson` and update the key names in `check.py` |
| `check.py` reports `report_present` failed | The tool returned an error, or the result is not JSON | Search `events.ndjson` for `review_artifact` and read the result line |
| `could not read` | `events.ndjson` is missing | Re-run step 3 with the redirect |
