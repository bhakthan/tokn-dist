# Configuring a model provider & API key

TOKN is **bring-your-own-model**. It does not ship or proxy any hosted model — you
point it at a provider you already have access to (OpenAI, Azure OpenAI, Anthropic,
Google Gemini) or a local runtime (Ollama, llama.cpp/GGUF, ONNX). Your keys stay
on your machine; TOKN never phones home with them.

> Out of the box TOKN starts in a **mock** provider so `--help`, `license`, and
> `update` all work with no key. To actually run the agent (`tokn agent-run`,
> `tokn agent-repl`, modes, domains) you must select a real provider below.

---

## 1. Two ways to supply configuration

**A. Real environment variables** (recommended for CI, servers, secrets managers):

```bash
# macOS / Linux
export NOSPACE_MODEL_PROVIDER=openai
export NOSPACE_MODEL_NAME=gpt-4o
export OPENAI_API_KEY=sk-...
```

```powershell
# Windows PowerShell
$env:NOSPACE_MODEL_PROVIDER = "openai"
$env:NOSPACE_MODEL_NAME     = "gpt-4o"
$env:OPENAI_API_KEY         = "sk-..."
```

**B. A `.env` file in your working directory** (convenient for local use). TOKN
auto-loads `.env` from the directory you run it in (or the `--repo-root` you pass).
Loading is **non-overriding** (a real env var always wins), quiet when the file is
absent, and skips malformed lines:

```dotenv
# .env  — keep this file out of git
NOSPACE_MODEL_PROVIDER=openai
NOSPACE_MODEL_NAME=gpt-4o
OPENAI_API_KEY=sk-...
```

> 🔒 **Never commit `.env`.** Add it to `.gitignore`. For safety, TOKN will **not**
> auto-load Azure credential variables (`AZURE_TENANT_ID`, `AZURE_CLIENT_ID`,
> `AZURE_CLIENT_SECRET`) from a `.env` — supply those as real env vars or use
> `az login` (see Azure below), so a stale file can't poison your credential chain.

---

## 2. The two selectors

Every setup sets these two, then adds provider-specific keys:

| Variable | Purpose | Example |
|----------|---------|---------|
| `NOSPACE_MODEL_PROVIDER` | Which backend to use | `openai`, `azure-openai`, `anthropic`, `gemini`, `ollama`, `gguf`, `onnx`, `mock` |
| `NOSPACE_MODEL_NAME` | Model / deployment name | `gpt-4o`, `claude-...`, `gemini-2.5-pro`, a local model id |

---

## 3. Per-provider settings

### OpenAI
```dotenv
NOSPACE_MODEL_PROVIDER=openai
NOSPACE_MODEL_NAME=gpt-4o
OPENAI_API_KEY=sk-...
# optional — for Azure-compatible / proxy / gateway endpoints:
OPENAI_BASE_URL=https://api.openai.com/v1
```

### Azure OpenAI
```dotenv
NOSPACE_MODEL_PROVIDER=azure-openai
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_VERSION=2024-10-21           # optional; this is the default
# authenticate with ONE of:
AZURE_OPENAI_API_KEY=<key>                     # 1) API key
# AZURE_OPENAI_AD_TOKEN=<aad-token>            # 2) a pre-fetched Entra token
# AZURE_OPENAI_USE_DEFAULT_CREDENTIAL=true     # 3) DefaultAzureCredential (az login / MSI)
```
With option 3, run `az login` first — TOKN uses the Azure Default Credential chain,
so no secret is stored in a file.

### Anthropic (Claude API)
```dotenv
NOSPACE_MODEL_PROVIDER=anthropic
NOSPACE_MODEL_NAME=claude-3-5-sonnet-latest
ANTHROPIC_API_KEY=sk-ant-...
# optional:
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_VERSION=2023-06-01                   # optional; default shown
```

### Google Gemini
```dotenv
NOSPACE_MODEL_PROVIDER=gemini
NOSPACE_MODEL_NAME=gemini-2.5-pro
GEMINI_API_KEY=...
# optional:
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
```

### Local — Ollama (no key)
```dotenv
NOSPACE_MODEL_PROVIDER=ollama
NOSPACE_MODEL_NAME=llama3.1        # any model you've pulled in Ollama
```

### Local — llama.cpp / GGUF server (no key)
```dotenv
NOSPACE_MODEL_PROVIDER=gguf
NOSPACE_MODEL_NAME=<model name loaded in your llama.cpp server>
GGUF_SERVER_URL=http://127.0.0.1:8080
# or run fully in-process with a local file:
# GGUF_MODEL_PATH=/path/to/model.gguf
```

### Local — ONNX Runtime GenAI (no key)
```dotenv
NOSPACE_MODEL_PROVIDER=onnx
NOSPACE_MODEL_NAME=<model id from your ONNX Runtime GenAI server>
ONNX_SERVER_URL=http://127.0.0.1:8080
# ONNX_MODEL_PATH=/path/to/onnx-model
```

### Mock (default — no key, for smoke tests only)
```dotenv
NOSPACE_MODEL_PROVIDER=mock
```

---

## 4. Verify it's wired up

```bash
tokn auth status          # shows which provider is configured & ready
tokn agent-run --prompt "say hello in one word" --max-steps 1
```

If a required variable is missing, TOKN fails fast with an explicit message naming
the exact variable it needs (e.g. `OPENAI_API_KEY is required when
NOSPACE_MODEL_PROVIDER=openai`).

---

## 5. Optional keys for specific features

Some features use their own keys **only if you enable them** — none are required to
run the core agent:

| Feature | Variable | Notes |
|---------|----------|-------|
| Web search (WebIQ) | `WEB-IQ-KEY` | enables the `web_search` tool |
| Specialist HuggingFace models | `HUGGINGFACE_API_KEY` | domain specialist model calls |

Keep all of these in your local `.env` or real env — never in this repo.
