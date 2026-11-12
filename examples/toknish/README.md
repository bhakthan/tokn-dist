# toknish: trusted federation and compact model answers

> Walkthrough: `tokn` leader and worker sessions, the toknish wire profile, and the toknish-M benchmark.

toknish is a set of optional features in TOKN that make multi-machine work and model answers easier to trust. There are four parts. Each can be used on its own.

| Feature | What it does for you | How it is enabled |
|---|---|---|
| **Blob refs** (`blobs/1`) | Large repositories and patches are sent as content-addressed references, so repos bigger than the 1 MiB request cap can still be seeded to workers. | Automatic when leader and worker both support it. |
| **Long polling** (`longpoll/1`) | The leader waits for results instead of polling in a loop. It falls back to polling when a worker does not support it. | Automatic. Tune the wait with `--longpoll-wait`. |
| **Trust profile** (`toknish/0.2`) | Every message is hash-chained and authenticated. Each claim carries an evidence class and a confidence level, and an audit log records the run so you can verify it afterwards. | Opt in with `--wire toknish` or `--wire auto`. |
| **toknish-M** (pilot) | A model answers with a short JSON frame of claims instead of prose. Only the answer is compressed, never the model's reasoning. Works with local models, so it runs offline. | `tokn tkm bench` measures it against prose answers. |

Everything below runs on your own machine. Nothing is sent to a remote service unless you choose a cloud provider.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN (`tokn`) on your PATH, v0.3.90 or later | Ships `agent-worker`, `agent-leader`, `toknish` and `tkm` | `tokn version` |
| Ollama with a model pulled (recommended, offline) | Runs the bench and the worker's model locally | `ollama list` |
| *or* a cloud provider key in `.env` (optional) | Use a hosted model instead of Ollama | see `.env.example` |
| A shared token, `TOKN_WORKER_TOKEN` | Authenticates leader and worker | set by the scripts for the session |

### Install Ollama and pull a model

Pick the command for your system, then pull the model:

- **Windows:** `winget install Ollama.Ollama`, or download the installer from https://ollama.com/download
- **macOS:** `brew install ollama`, or download the app from https://ollama.com/download
- **Linux:** `curl -fsSL https://ollama.com/install.sh | sh`

Then, on every system:

```bash
ollama pull qwen3:8b
ollama list
```

The model name is only an example. Any model you have pulled works. Pass it with `--model`.

### Install TOKN

Follow the TOKN install instructions for your OS, then open a new terminal and run `tokn version`. If `tokn` is not found, the run scripts stop with a message telling you what to fix.

## 1. Try it: a two-terminal loopback federation

This runs one worker and one leader on the same machine, talking over `127.0.0.1`. Both sides share one token.

### Step 1: set the shared token (both terminals)

bash:

```bash
export TOKN_WORKER_TOKEN="$(openssl rand -base64 32)"
```

PowerShell:

```powershell
$b = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
$env:TOKN_WORKER_TOKEN = [Convert]::ToBase64String($b)
```

Run the same export in the second terminal, using the same value. Never write the token into a file you commit.

### Step 2: start the worker (terminal A)

The worker keeps its toknish chain and audit log in `--federation-dir`, which must be an absolute path. Create the directories first.

bash:

```bash
mkdir -p "$PWD/scratch/worker-state" "$PWD/scratch/repo"
tokn agent-worker --listen 127.0.0.1:8099 --worker-id w1 \
  --repo-root "$PWD/scratch/repo" \
  --provider ollama --model qwen3:8b \
  --federation-dir "$PWD/scratch/worker-state"
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$PWD\scratch\worker-state", "$PWD\scratch\repo" | Out-Null
tokn agent-worker --listen 127.0.0.1:8099 --worker-id w1 `
  --repo-root "$PWD\scratch\repo" `
  --provider ollama --model qwen3:8b `
  --federation-dir "$PWD\scratch\worker-state"
```

The worker offers the toknish profile by default. Add `--no-toknish` to turn it off and serve plain JSON only.

### Step 3: run the leader (terminal B)

Use `--wire auto`. The leader uses toknish with every worker that offers it, and plain JSON with the others.

bash:

```bash
tokn agent-leader \
  --worker w1=http://127.0.0.1:8099 \
  --wire auto \
  --federation-dir "$PWD/scratch/leader-state" \
  --prompt "List the files in the repository root and say which one looks like a README." \
  --out "$PWD/scratch/results.json"
```

PowerShell:

```powershell
tokn agent-leader `
  --worker w1=http://127.0.0.1:8099 `
  --wire auto `
  --federation-dir "$PWD\scratch\leader-state" `
  --prompt "List the files in the repository root and say which one looks like a README." `
  --out "$PWD\scratch\results.json"
```

`--prompt` runs one ad-hoc task. For several dependent tasks, write a plan with `tokn workplan` and pass it with `--plan`. See the [federation walkthrough](../federation/README.md).

### Step 4: confirm the wire that was negotiated

- **Session folder.** With `--wire auto`, a worker that does not offer the profile is served over plain JSON. A session subdirectory under the leader's `--federation-dir` appears only when toknish was used.
- **Strict check.** Run with `--wire toknish` instead. The leader refuses to use any worker that does not offer toknish, so a successful run confirms that every worker negotiated it.
- **Audit log.** The leader writes one subdirectory per session under `--federation-dir`. Its name is the session ID. Verify the chain offline:

```bash
tokn toknish audit <session-id> --dir "$PWD/scratch/leader-state"
```

PowerShell:

```powershell
tokn toknish audit <session-id> --dir "$PWD\scratch\leader-state"
```

The exit code tells you the result: `0` clean, `2` chain broken, `3` authentication (MAC) failure, `4` incomplete. Add `--gloss` for a plain-English reading of each claim. Add `--json` for the full report.

### Step 5: clean up

Press Ctrl+C in terminal A to stop the worker. The `scratch/` folder is git-ignored. Delete it when you are done.

## 2. Try it: benchmark compact model answers (toknish-M)

toknish-M asks the model to answer as a short JSON frame of claims. The bench runs the same questions twice, once as prose and once as frames, and compares them.

Two rules the frame follows:

- The model compresses its **answer**, never its **thinking**.
- The model may use only the evidence classes RET, INF, GSS, UNK, REP and FRM. It may not use OBS or CMP, because those classes need evidence it cannot supply.

### (a) Smoke test with the built-in sample

```bash
tokn tkm bench --provider ollama --model qwen3:8b --sample
```

PowerShell:

```powershell
tokn tkm bench --provider ollama --model qwen3:8b --sample
```

The sample is a small embedded set. It is a smoke test that shows the pipeline works. It is far below the sample size needed for a decision, so it never passes the gate.

### (b) A dataset run

`dataset.json` in this folder has 12 synthetic cases. Four of them include `context` entries, which are tool output or file content the model may cite. Run it and save the full report:

```bash
tokn tkm bench --provider ollama --model qwen3:8b \
  --dataset dataset.json --out bench-report.json
```

PowerShell:

```powershell
tokn tkm bench --provider ollama --model qwen3:8b `
  --dataset dataset.json --out bench-report.json
```

Add `--n` to cap how many cases run, `--retries` to set re-asks, and `--seed` to make the bootstrap repeatable. Use `--json` to print the whole report instead of the summary.

To bench a cloud model, set `--provider` and `--model` to your provider's values and put its key in `.env`. The scripts read `.env` for you.

### Reading the bench report

The summary prints one row per arm, `prose` and `tkm` (the frame), with these columns:

| Field | What to look at |
|---|---|
| `pass` | Share of cases whose answer contains the expected text. Compare `tkm` with `prose`. |
| `mean-out` | Mean output tokens per answer. This is what the frame is meant to reduce. |
| `mean-answer` | Mean tokens in the answer alone, excluding the frame scaffolding. |
| `p50` | Median latency. |
| `errors` | Requests that failed outright. |
| Answer ratio | Frame answer size relative to prose. |
| Violations | Frame answers that broke a rule, on the first attempt and after a re-ask, plus the counts of fallbacks, free-text answers and alias hits. A high number means the model is not following the frame. |
| Calibration (`n`, `ECE`, `Brier`) | How well the stated confidence matches reality. Lower `ECE` and `Brier` are better. |
| Gate | Change in pass rate in percentage points (Δ pass pp), its bootstrap lower bound, the seed, and `N` against the minimum (`--min-n`, default 200). |

The gate passes only when **both** conditions hold: `N` is at least 200 paired cases, and the bootstrap lower bound of the pass-rate change is at least −1.0 percentage points. In other words, the frame must not be measurably worse than prose. The other fields are reported for you to judge; they do not decide the gate.

The JSON report written by `--out` contains every row. Use it for the exact definitions of each field.

## Preflight and run scripts

`run-local.ps1` (PowerShell) and `run-local.sh` (bash) do the whole loopback run and the bench in one go. Before doing anything, they check for:

1. `tokn` on your PATH.
2. The provider: Ollama installed and reachable, with the model pulled. For a cloud provider, they remind you to set its key in `.env`.
3. A shared token. If `TOKN_WORKER_TOKEN` is not set, they create one for the run only and do not write it to disk.

If something is missing, they stop with a message naming the problem and the command that fixes it.

```bash
./run-local.sh                       # uses qwen3:8b on Ollama
./run-local.sh --model llama3.2      # any model you have pulled
```

PowerShell:

```powershell
./run-local.ps1                      # uses qwen3:8b on Ollama
./run-local.ps1 -Model llama3.2
```

## Files

| File | What it is |
|---|---|
| `README.md` | This walkthrough |
| `dataset.json` | 12 synthetic cases for the bench, with `context` on four |
| `run-local.ps1`, `run-local.sh` | Preflight and the full local run |
| `.env.example` | Placeholders for a cloud provider key. Copy to `.env`. |
| `.gitignore` | Keeps `scratch/`, `.env` and bench reports out of git |

## Troubleshooting

- **`tokn` not found.** Open a new terminal after installing, then run `tokn version`.
- **Worker unreachable.** Check that the worker is still running in terminal A and that `--listen` and `--worker` use the same port.
- **`--wire toknish` fails.** The worker does not offer the profile. Remove `--no-toknish` from the worker, or use `--wire auto`.
- **`toknish audit` exits `3`.** The token in your audit command is not the token the run used. Check `TOKN_WORKER_TOKEN`.
- **Bench gate says "not enough cases".** That is expected with `--sample` or a small dataset. Only a dataset of 200 or more cases can pass the gate.
- **Ollama model missing.** Run `ollama pull <model>` with the same name you pass to `--model`.

## Related

- [federation](../federation/README.md): the leader and worker basics, with two workers and a work plan
- [quality-flywheel](../quality-flywheel/README.md): grading a dataset against a baseline
- [evidence-earned-prompting](../evidence-earned-prompting/README.md): evidence-cited prompt patches
