# Example: recover from a malformed tool call instead of failing

Models sometimes call a tool with an argument that does not match the tool's
schema. This walkthrough gives TOKN a file-reading task where the natural
wording leaves one range end open, and shows what TOKN does with it.

> *Show lines 60 to the end of a Go file, then the top of the file up to line 12,
> and explain what `Push` does when the buffer is full.*

The request says "to the end" and "up to line 12", so the model naturally
leaves out `end_line` on the first read and `start_line` on the second. The
file-read tool's contract says what a missing end means. TOKN fills in the
missing field, records that it did, and tells the model what it did, rather
than returning an error.

| Feature | What it does here |
|---|---|
| **Relational defaulting** | An omitted `start_line` becomes `1`. An omitted `end_line` becomes `0`, which means end of file. The result says so. |
| **Repair telemetry** | TOKN prints a summary line to stderr when it repaired or blocked a call, and can accumulate counts across runs in a JSON file. |
| **Off switch** (`--no-tool-contract`) | Turns the layer off, so you can see the raw failure for comparison. |

All data in `fixture/` is synthetic and written for this example.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with the tool-contract flags used here | `tokn version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |
| Tier: **trial or Community** | `tokn license features` on the Community tier lists `core:*` and `workflow:*`, which cover the agent loop used here. Community is enough. The 14-day trial (`tokn license trial`) is not required. | `tokn license` |

> **What leaves your machine.** The model provider receives the task and the
> files the agent reads. The fixture is synthetic. Telemetry stays in the local
> JSON file you choose in step 4.

## 1. Make a scratch repo

macOS / Linux:

```bash
mkdir -p ~/tokn-contract && cd ~/tokn-contract
cp -r path/to/examples/tool-contract/fixture . 
cp path/to/examples/tool-contract/prompt.md .
git init -q && git add -A && git commit -qm "tool contract example"
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-contract | Out-Null
Set-Location $HOME\tokn-contract
Copy-Item path\to\examples\tool-contract\fixture -Recurse .
Copy-Item path\to\examples\tool-contract\prompt.md .
git init -q; git add -A; git commit -qm "tool contract example"
```

Replace `path/to` with the location of your `tokn-dist` checkout.

## 2. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For example:

```bash
export NOSPACE_MODEL_PROVIDER=<your provider>
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "<your provider>"
$env:NOSPACE_MODEL_NAME     = "<a model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Keep keys out of the repo. Do not commit them.

## 3. Run the task

Repair is on by default, so this run needs no extra flags for recovery. It
writes cross-session telemetry to a JSON file. The path must be absolute, so
the command uses your home folder.

macOS / Linux:

```bash
tokn agent-run --prompt-file prompt.md --no-confirm --headless \
  --max-steps 10 --log-file contract-run.log \
  --tool-contract-stats "$HOME/tokn-tool-contract.json" \
  --output-format json > result.json 2> contract-stderr.txt
```

Windows PowerShell:

```powershell
tokn agent-run --prompt-file prompt.md --no-confirm --headless `
  --max-steps 10 --log-file contract-run.log `
  --tool-contract-stats "$HOME\tokn-tool-contract.json" `
  --output-format json > result.json 2> contract-stderr.txt
```

## 4. Check for the repair

When a run repaired or blocked anything, TOKN prints a summary line to the
terminal's error stream (stderr). It is not written to `--log-file`, so keep
stderr visible or redirect it to a file:

macOS / Linux:

```bash
tokn agent-run ... 2> contract-stderr.txt
grep "tool-contract" contract-stderr.txt
```

Windows PowerShell:

```powershell
tokn agent-run ... 2> contract-stderr.txt
Select-String "tool-contract" contract-stderr.txt
```

A repaired run prints a summary such as:

```text
tool-contract: repaired 2 tool call(s), blocked 0 with retry guidance
```

The repair also adds a `notes` entry to the tool result, saying which field was
filled in and with what value. That is the transparency the model receives. A
clean run with both line numbers prints no summary line.

The file given to `--tool-contract-stats` keeps counts across runs, per model
and tool. Open it to compare repairs and blocks between runs.

## 5. Compare with the raw failure (optional)

Turn the layer off and run the same task:

macOS / Linux:

```bash
tokn agent-run --prompt-file prompt.md --no-confirm --headless \
  --max-steps 10 --no-tool-contract --log-file raw-run.log --output-format json > raw.json
```

Windows PowerShell:

```powershell
tokn agent-run --prompt-file prompt.md --no-confirm --headless `
  --max-steps 10 --no-tool-contract --log-file raw-run.log --output-format json > raw.json
```

Without the layer, a read with the missing field is not repaired. The model
sees the raw result and has to work out the fix itself. Compare the step
counts in `result.json` and `raw.json`. Models do not always make the same
mistake, so the raw run may succeed anyway. That is also worth noting.

## 6. Read the result

| File | Read it for |
|---|---|
| `result.json` | Final status, answer and step count |
| `contract-run.log` | The session log |
| `contract-stderr.txt` | The `tool-contract:` summary line (only when a repair or block happened) |
| `tokn-tool-contract.json` | Cross-session totals by model and tool |

### What to look for

- **Two reads, both correct.** The first read should show lines 60 to the last
  line. The second should show lines 1 to 12.
- **A repair, not a failure.** The run should finish without an error. The
  summary line should count the repairs.
- **The disclosure.** The read result's `notes` should say which field was
  filled in. The model should not present the defaulted range as if the user
  had asked for it.
- **The explanation.** `Push` returns `ErrFull` when `b.count == len(b.items)`.
  The answer should quote that check, not guess.

Sometimes a model puts the range into the `path` string instead of the
argument. The read then returns "not found", the model retries with the range
in the right place, and the run still completes. That is also a recovery
worth recognising in the log.

### What one of our runs looked like (your numbers will differ)

Our committed matrix ran this task with three models from two providers. All
three passed. One model sometimes put the range into the path string, and
recovered after a not-found result.

## Troubleshooting

| Symptom | Fix |
|---|---|
| No `tool-contract:` line in stderr | The model passed both line numbers, so nothing needed repair. That is fine. Check the read results instead. |
| `--tool-contract-stats` rejected | The path must be absolute. Use `$HOME/...` or `$HOME\...`. |
| The read returns "not found" | The model may have put the range in the path. Check the log for the retry, and check that `fixture/ring_buffer.go` exists in the folder you run from. |
| The run stops at the step limit | Raise `--max-steps`, or check the LLM configuration in step 2. |
| `Unknown flag` error | Run `tokn agent-run --help` and check the flag name. |
