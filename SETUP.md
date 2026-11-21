# Configuring a model provider and API key

TOKN is **bring-your-own-model**. Choose a hosted provider or prepare a local
runtime and model. The Community previews and rules-based judgments need
neither; start with [GETTING_STARTED.md](GETTING_STARTED.md) for that path.

Updated for **v0.3.100**. Replace every uppercase placeholder below.
Use model IDs available to your account or installed runtime rather than
assuming an old example model is still offered.

```text
Your task
   |
   v
TOKN -- chosen provider --+--> hosted API (your credentials; data leaves host)
                         |
                         +--> local runtime (prepared model; local endpoint)

Tools and external connections have their own permissions and data flows.
Choosing a local model alone does not isolate the whole machine.
```

## Before you configure anything

| Path | What you need |
|---|---|
| Hosted API | TOKN, network access, access to the selected model and the provider's credentials |
| Azure with Entra sign-in | The above, plus an authorised Azure identity; Azure CLI is needed if you choose `az login` |
| Ollama | An installed, running Ollama and a downloaded model suitable for the task |
| llama.cpp/GGUF | An installed llama.cpp server and compatible model files |
| ONNX | A compatible ONNX Runtime GenAI setup and locally prepared model |

These are alternatives, not a list of things everyone must install.
Model downloads, optional packages and toolchains are separate from TOKN.
For local tool-using agents, choose a model with appropriate tool support;
images additionally require a compatible vision model and runtime.

## 1. Two ways to supply configuration

### A. Real environment variables — recommended

Set the provider, model and credentials in the terminal that will run TOKN.
These settings affect that terminal and child processes; a new terminal may
need them again.

**PowerShell**
```powershell
$env:NOSPACE_MODEL_PROVIDER = "openai"
$env:NOSPACE_MODEL_NAME = "YOUR_MODEL_ID"
$env:OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
```

**Bash**
```bash
export NOSPACE_MODEL_PROVIDER="openai"
export NOSPACE_MODEL_NAME="YOUR_MODEL_ID"
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

Keep credentials out of source control, screenshots and shared shell history.
Use your organisation's approved secret-management process where available.
Credentials are used to authenticate to the provider you select.

### B. A local `.env` — limited convenience, not arbitrary configuration

TOKN can load supported model preferences and API keys from a `.env` in the
working directory or explicit `--repo-root`. Existing process variables win.
For example:

```dotenv
NOSPACE_MODEL_PROVIDER=openai
NOSPACE_MODEL_NAME=YOUR_MODEL_ID
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

**Never commit this file.** Ignore `.env` before putting a key in it.
Do not use a repository's `.env` to set network destinations, Azure identity
credentials or authentication-scheme switches. In particular,
`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_USE_DEFAULT_CREDENTIAL`,
`GGUF_SERVER_URL` and `ONNX_SERVER_URL` belong in your real environment,
not an auto-loaded repository file.

If TOKN says a value was refused from `.env`, export it explicitly rather than
repeatedly editing the same file. Use `tokn config doctor` to inspect active
configuration with secrets redacted.

## 2. The two selectors

| Variable | Purpose | Example |
|---|---|---|
| `NOSPACE_MODEL_PROVIDER` | Provider ID | `openai`, `azure-openai`, `anthropic`, `gemini`, `ollama`, `gguf`, `onnx` |
| `NOSPACE_MODEL_NAME` | API model ID, deployment name or installed model ID | `YOUR_MODEL_ID` |

For a one-off agent run, `--model-provider` and `--model-name` select the
provider and model explicitly. They do not supply credentials:

```sh
tokn agent-run --model-provider openai --model-name "YOUR_MODEL_ID" --prompt "Say hello in one word." --max-steps 1 --headless --mcp-disabled
```

This makes a model call and may incur charges. Use the diagnostic steps below
before trying it.

Shortcut: `tokn -p "Say hello in one word."` runs the same one-shot prompt with
the provider and model already set in your environment. The explicit form above
stays useful for scripts and for trying a different provider or model. `-m
<model>` sets the model name for a single run.

## 3. Per-provider settings

The Bash examples use real environment variables. In PowerShell, translate
`export NAME="value"` to `$env:NAME = "value"`, as in section 1.
Choose one provider path.

### OpenAI

```bash
export NOSPACE_MODEL_PROVIDER="openai"
export NOSPACE_MODEL_NAME="YOUR_MODEL_ID"
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

Custom or OpenAI-compatible endpoints require the provider's documented
configuration. Set any endpoint override in the real environment; review the
destination before sending data.

### Azure OpenAI

```bash
export NOSPACE_MODEL_PROVIDER="azure-openai"
export NOSPACE_MODEL_NAME="YOUR_DEPLOYMENT_NAME"
export AZURE_OPENAI_ENDPOINT="https://YOUR_RESOURCE.openai.azure.com/openai/v1"
export AZURE_OPENAI_DEPLOYMENT="YOUR_DEPLOYMENT_NAME"
export AZURE_OPENAI_API_KEY="YOUR_AZURE_OPENAI_API_KEY"
```

Use your **deployment name**, which may differ from the underlying model ID.
Use the endpoint supplied for your resource; the example is only a placeholder.

**Alternative: Entra sign-in instead of an API key.** If your identity has the
required access, sign in with `az login` and set
`AZURE_OPENAI_USE_DEFAULT_CREDENTIAL=true` in the real environment. Keep the
endpoint and deployment settings, but choose one authentication method rather
than combining keys and sign-in switches.

For the Azure CLI path, check `az --version` first. If absent:

| OS | Install Azure CLI |
|---|---|
| Windows | `winget install Microsoft.AzureCLI` |
| macOS | `brew install azure-cli` |
| Linux | Follow the [distribution-specific installation guide](https://learn.microsoft.com/cli/azure/install-azure-cli-linux) |

Installing Azure CLI does not grant model access. Your Azure administrator
must authorise the identity for the resource.

### Anthropic (Claude API)

```bash
export NOSPACE_MODEL_PROVIDER="anthropic"
export NOSPACE_MODEL_NAME="YOUR_CLAUDE_API_MODEL_ID"
export ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
```

Use a Claude **API** model ID available to your account. Access to a consumer
chat subscription does not by itself establish API credentials.

### Google Gemini

```bash
export NOSPACE_MODEL_PROVIDER="gemini"
export NOSPACE_MODEL_NAME="YOUR_GEMINI_MODEL_ID"
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

### Local — Ollama (no key)

Check the runtime and available models before selecting one:

```sh
ollama --version
ollama list
```

If missing, install Ollama with `winget install Ollama.Ollama` on Windows,
`brew install ollama` on macOS, or follow the
[Linux installation guide](https://docs.ollama.com/linux).
Start the runtime, choose an appropriate model and download it while connected:

```sh
ollama pull "MODEL_ID_YOU_SELECTED"
```

Replace that placeholder. Model weights can be large; check storage and memory
requirements first. Then select the exact name shown by `ollama list`:

```bash
export NOSPACE_MODEL_PROVIDER="ollama"
export NOSPACE_MODEL_NAME="YOUR_INSTALLED_MODEL"
```

These instructions use Ollama's default local endpoint. A remote server is a
different data boundary; do not describe it as on-machine execution.

### Local — llama.cpp / GGUF server (no key)

Prepare llama.cpp, compatible weights and a running server using the
[local llama.cpp walkthrough](examples/local-llamacpp/README.md).
Then set its endpoint in your real environment:

```bash
export NOSPACE_MODEL_PROVIDER="gguf"
export NOSPACE_MODEL_NAME="YOUR_SERVED_MODEL_ID"
export GGUF_SERVER_URL="http://127.0.0.1:8080"
```

The port must match your server. It is not created by setting these variables.

### Local — ONNX Runtime GenAI (no key)

With a compatible server and model already prepared:

```bash
export NOSPACE_MODEL_PROVIDER="onnx"
export NOSPACE_MODEL_NAME="YOUR_SERVED_MODEL_ID"
export ONNX_SERVER_URL="http://127.0.0.1:8080"
```

Runtime compatibility, model format and available memory must be checked
separately. Do not assume a GGUF file can be used as an ONNX model.

### Mock — smoke tests only

`mock` is not a real assistant. A canned response does not demonstrate that
your hosted credentials, local model or tool-use path works.
Select a real provider before evaluating model behaviour.

## 4. Verify it's wired up

Start without a task:

```sh
tokn auth status
tokn doctor --list
tokn doctor --provider ollama
```

Replace `ollama` with the provider you selected. `auth status` reports
credential readiness, not a successful inference. `doctor` checks the selected
provider and can contact its endpoint. Review its findings before running an
agent; missing dependencies are not successful checks.

Then follow the [first-ten-minutes task](examples/first-ten-minutes/README.md#4-ask-the-agent-to-read-one-file).
It uses a synthetic file in a temporary directory, limits the run and explains
the expected result. A larger run may cost more than this small exercise.

| Problem | Check |
|---|---|
| Missing variable despite `.env` | Was it refused from a repository file? Export it in the real environment |
| Authentication fails | Key, account access, deployment and chosen auth method |
| Local connection refused | Server running, correct port, model loaded |
| Tool calls fail | Model/runtime tool support; do not bypass permissions to hide the failure |
| Unexpected provider or model | Current terminal variables and explicit command flags; use `tokn config doctor` |

## 5. Optional services and offline preparation

Only configure search, specialist services or external tools when the chosen
workflow needs them. Their own credentials, dependencies and data transfers
are separate from the main model.

For offline use, stage the runtime, model and workflow dependencies before
disconnecting. Set `TOKN_NO_REGISTER=1` and `TOKN_NO_UPDATE_CHECK=1` to disable
the unrelated startup checks, and use the workflow's documented air-gap flag.
Use host-level network controls when no egress must be enforced; a local model
selection is not a sandbox.
