# Local llama.cpp example

Run TOKN against a GGUF model on your own machine. TOKN talks to a
[llama.cpp](https://github.com/ggml-org/llama.cpp) server through its
OpenAI-compatible API, using the `gguf` provider. Once the model weights are
downloaded, everything runs offline.

This example includes a small, deterministic task: read a CSV inventory file
and write a markdown table of the items that need reordering. A checker then
confirms the result.

## What is in this folder

| File | Purpose |
|---|---|
| `task.md` | The task TOKN is asked to perform |
| `workspace/inventory.csv` | Input data for the task |
| `expected-reorder.md` | The expected item list |
| `check.py` / `check.ps1` | Read-only checker (stdlib only, no network) |
| `run-local.ps1` / `run-local.sh` | Preflight checks, then the run |
| `.env.example` | Settings template (placeholders only) |

## 1. Prerequisites

| Dependency | Why | Install |
|---|---|---|
| `tokn` binary | Runs the agent loop | Download from the [latest release](https://github.com/bhakthan/tokn-dist/releases/latest) and put it on your `PATH` |
| llama.cpp (`llama-server`) | Serves the model over HTTP | See the install commands in section 2 |
| A GGUF model | The local model TOKN talks to | Any GGUF from Hugging Face, for example `<hf-repo>:<quant>` |
| curl | Health checks in the scripts | Included on Windows 10 1803+ and macOS; `sudo apt install curl` on Debian/Ubuntu |
| Python 3 | Runs `check.py` (Linux/macOS script path) | Included on most systems; optional on Windows if you use `check.ps1` |

**Hardware notes**

- A model of 4B parameters with a quantization such as Q4_K_M runs on a laptop
  with 8 GB of RAM, but slowly.
- A 14B to 32B model needs a GPU with enough VRAM for the weights plus the
  context. More capable models handle multi-step domain tasks more reliably.
- CPU-only inference works. It is just slower, so use `--run-timeout 0` (set
  in the scripts).

## 2. Install llama.cpp

Pick the command for your OS.

**Windows**

```powershell
winget install ggml.llamacpp
```

**macOS (Apple Silicon or Intel)**

```bash
brew install llama.cpp
```

**Linux**

Build from source (see [the llama.cpp build guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)):

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release -j
```

Or download a prebuilt binary from the [llama.cpp releases page](https://github.com/ggml-org/llama.cpp/releases).

Confirm the binary is available:

```bash
llama-server --version
```

## 3. Start the llama.cpp server

Start the server on loopback only. Replace `<hf-repo>:<quant>` with the model
you want. llama.cpp downloads it on first use.

```bash
llama-server -hf <hf-repo>:<quant> --host 127.0.0.1 --port 8080 -c 32768
```

`-c 32768` sets the context size. If the server runs out of GPU memory, lower
this value (see Troubleshooting).

Keep this terminal open. The server must stay running while TOKN works.

## 4. Verify the server is healthy

In a second terminal:

```bash
curl http://127.0.0.1:8080/health
```

Expected output:

```json
{"status":"ok"}
```

To find the model id the server reports, run:

```bash
curl http://127.0.0.1:8080/v1/models
```

## 5. Install and configure this example

Copy the settings template and edit it:

```bash
cp .env.example .env
```

Set `TOKN_MODEL` in `.env` to the model id from the previous step. The other
values can stay as they are:

```
GGUF_SERVER_URL=http://127.0.0.1:8080/v1
TOKN_MODEL=<your-model-id>
```

`.env` is git-ignored. The scripts load it without overriding variables you
have already set in your shell.

## 6. Run the sample task

**Windows (PowerShell 7 or Windows PowerShell 5.1)**

```powershell
cd examples\local-llamacpp
.\run-local.ps1
```

**macOS / Linux**

```bash
cd examples/local-llamacpp
chmod +x run-local.sh
./run-local.sh
```

The script runs preflight checks first. It then runs:

```
tokn agent-run --model-provider gguf --model-name <TOKN_MODEL> \
  --prompt-file task.md --repo-root ./workspace \
  --max-steps 15 --run-timeout 0 --output-format text
```

The full agent output is saved to `run-output.txt`. When the run finishes, the
script calls the checker automatically.

You can also check the result on its own:

```bash
python3 check.py          # macOS / Linux
python check.py           # Windows
.\check.ps1               # PowerShell
```

A passing run prints `PASS: 3 items match.` and writes `workspace/reorder.md`.

### Preflight checks

Before anything runs, the scripts check each dependency and report every
problem together. For each one they print what is missing, why it is needed,
and the install command. They then exit with status 1. The checks cover:

- the `tokn` binary (on `PATH`, or set with `TOKN_BIN`)
- `TOKN_MODEL` is set to a real value, not the placeholder
- `curl` is available
- the llama.cpp server responds at `/health`
- with `--system-one` / `-SystemOne`: the `SYSTEMONE_*` shell variables are set
  and the decision server responds

## 7. Limited-capability mode

When a local model's id includes a size of 8B or smaller (for example
`Qwen3.5-4B`), TOKN switches to limited-capability mode automatically. In this
mode TOKN:

- sends a compact tool set: the core file and command tools, plus the tools of
  the active domain
- skips skill composition
- caps each reply at 8192 output tokens

The run log prints a line starting with `⚡ Limited-capability mode:` when
this mode is active. The run script also reports it.

**Override it**

| Setting | Effect |
|---|---|
| `NOSPACE_LIMITED_MODEL=1` | Force limited mode on. Use this when the model id has no size in it. |
| `NOSPACE_LIMITED_MODEL=0` | Force limited mode off. |
| `TOKN_MAX_OUTPUT_TOKENS=<n>` | Change the reply cap |

Set these in `.env` or in your shell.

## 8. Optional: local decision model (System One)

System One is a decision layer that can run on a second local model. It needs
its own llama.cpp server on a different loopback port.

**Step 1: start a second server** (use a smaller model if you have limited
memory):

```bash
llama-server -hf <decision-hf-repo>:<quant> --host 127.0.0.1 --port 8081 -c 8192
```

**Step 2: set the variables in your shell, not in `.env`.** TOKN deliberately
does not load `SYSTEMONE_ALLOW_LOCAL` from a file.

PowerShell:

```powershell
$env:SYSTEMONE_BACKEND = "compatible"
$env:SYSTEMONE_ALLOW_LOCAL = "1"
$env:SYSTEMONE_BASE_URL = "http://127.0.0.1:8081/v1"
$env:SYSTEMONE_MODEL = "<decision-model-id>"
```

bash / zsh:

```bash
export SYSTEMONE_BACKEND=compatible
export SYSTEMONE_ALLOW_LOCAL=1
export SYSTEMONE_BASE_URL=http://127.0.0.1:8081/v1
export SYSTEMONE_MODEL=<decision-model-id>
```

Only loopback hosts (`127.x`, `::1`, `localhost`) are accepted for local
decision servers. No API key is needed. The default timeout for a local
decision is 30 seconds. Set `SYSTEMONE_TIMEOUT_MS` to change it.

**Step 3: check the decision layer:**

```bash
tokn system-one status
```

**Step 4: run with the flag:**

```powershell
.\run-local.ps1 -SystemOne
```

```bash
./run-local.sh --system-one
```

Tip: running the agent model and the decision model on one GPU slows both. If
you can, put the decision model on a second GPU or on the CPU.

## 9. Tips for small models

- Keep tasks small and well scoped. Name the exact files and the expected
  output, as `task.md` does.
- Write step-by-step task files with a numbered list.
- Allow more steps (`--max-steps`) and leave the run timeout at `0`.
- Tell the model which commands exist on your machine. Small models may assume
  tools such as `python3` are available.
- Use a larger model (14B to 32B) for multi-step domain tasks.
- Ask for a short, fixed reply format, such as "reply with one line: DONE".

## 10. Troubleshooting

**The server is not reachable (`Missing: llama.cpp server is not responding`)**

- Confirm the server is running in its own terminal.
- Check the port matches `GGUF_SERVER_URL` in `.env`.
- Run `curl http://127.0.0.1:8080/health` by hand. If it fails, look at the
  server's terminal output for the reason.

**Responses are slow**

- Expected on CPU or small GPUs. Leave `--run-timeout 0` in place.
- Use a smaller quantization (for example Q4 rather than Q8) if the model fits
  your hardware poorly.
- Avoid running System One on the same GPU as the agent model.

**The model writes long replies or repeats itself**

- Limited mode already caps replies at 8192 tokens. Lower the cap further with
  `TOKN_MAX_OUTPUT_TOKENS=2048`.
- Make the task shorter and ask for one fixed output format.

**The connection is reset, or the server crashes mid-run (GPU memory is full)**

- Restart `llama-server`.
- Reduce the context size: `-c 32768` (or lower, e.g. `-c 16384`).
- Use a smaller model or a lower-bit quantization.
- Close other GPU-heavy programs.

**`check.py` reports missing or unexpected items**

- Open `workspace/reorder.md` and compare it with `expected-reorder.md`.
- Re-run the task. Smaller models sometimes skip a row, so the output may
  need another attempt.
- Use `python check.py --help` to confirm the checker's options.

## 11. Air-gapped use

After the GGUF weights are downloaded, every step runs offline. The only
network traffic is the first model download. Run `llama-server` without
`-hf` and point it at a local `.gguf` file with `-m <path-to-model.gguf>` to
avoid any network use.

## 12. Cleanup

```bash
# Stop the llama.cpp servers: press Ctrl+C in each server terminal.

# Remove generated output (keeps the inputs)
rm -f run-output.txt workspace/reorder.md   # macOS / Linux
del run-output.txt workspace\reorder.md     # Windows
```

Remove `.env` as well if you do not want to keep your settings.
