# Telemetry and Network Connections

Complete inventory of every outbound network connection TOKN makes, ordered by data sensitivity.

## 1. Model Provider Requests (Highest Sensitivity)

**This is by far the largest and most sensitive data flow in TOKN.**

| Aspect | Detail |
|--------|--------|
| **Destination** | Whichever model provider the user configures (see table below) |
| **Trigger** | Every agent turn — whenever the LLM is consulted |
| **Payload** | The full conversation context: system prompt, user messages, file contents, tool outputs, and any other content the agent has gathered |
| **On by default** | Yes — TOKN cannot function without a model provider |
| **How to disable** | Use a fully local provider (Ollama, GGUF, ONNX) to keep all data on-machine |

### Supported providers and their endpoints

| Provider | Default base URL | Auth |
|----------|-----------------|------|
| OpenAI | `https://api.openai.com/v1` | Bearer token (`OPENAI_API_KEY`) |
| Azure OpenAI | User-configured endpoint (e.g., `https://<resource>.openai.azure.com`) | API key or Azure AD token |
| Anthropic | `https://api.anthropic.com` | `x-api-key` header |
| Google Gemini | `https://generativelanguage.googleapis.com` | API key |
| OpenRouter | `https://openrouter.ai/api/v1` | Bearer token |
| Fireworks | `https://api.fireworks.ai/inference/v1` | Bearer token |
| AWS Bedrock | User-configured endpoint | AWS SigV4 |
| Google Vertex AI | User-configured endpoint | Google OAuth |
| HuggingFace Inference | `https://router.huggingface.co/hf-inference/models/...` | Bearer token (`HF_TOKEN`) |
| Groq | `https://api.groq.com/openai/v1` | Bearer token |
| Ollama (local) | `http://localhost:11434` | None |
| GGUF (local) | Local llama.cpp server | None |
| 15+ additional API-key providers | See `config/apikey_providers.go` | Bearer token |

Source: `environment-manager/internal/agent/provider/provider.go` (function `New`, lines 197–550); `environment-manager/internal/agent/config/apikey_providers.go`.

**What TOKN does NOT do:** TOKN does not filter, redact, or inspect content before sending it to the model provider. If you paste a secret into a prompt or the agent reads a file containing credentials, that content goes to the provider.

## 2. Self-Update Channel

| Aspect | Detail |
|--------|--------|
| **Destination** | `https://api.github.com/repos/bhakthan/tokn-dist/releases/latest` (and `/tags/<tag>` for pinned updates) |
| **Trigger** | `tokn update` command; throttled background check on CLI startup |
| **Payload** | HTTP GET with `User-Agent: tokn-self-update`. If `GITHUB_TOKEN` / `GH_TOKEN` is set, it is sent as a Bearer token for private-repo access. |
| **On by default** | The background check runs on startup (throttled). Manual update requires explicit invocation. |
| **How to disable** | Do not run `tokn update`. The startup check is throttled and read-only. |

Source: `environment-manager/internal/agent/commands/update_cmds.go` lines 24, 29, 370–400.

## 3. Install Registration (Anonymous)

| Aspect | Detail |
|--------|--------|
| **Destination** | `https://tokn-registration-892151559760.us-central1.run.app/api/tokn/register` |
| **Trigger** | First run (`first_run` event); trial activation (`trial_start` event). Each event fires at most once per machine. |
| **Payload** | `{ schema, install_id, machine_hash, event, version, os, arch, ts }` — see below |
| **On by default** | Yes, in release builds (the endpoint is compiled in via `-ldflags`). Dev builds have no endpoint and are a silent no-op. |
| **How to disable** | Set any of: `TOKN_NO_TELEMETRY=1`, `TOKN_NO_REGISTER=1`, or `DO_NOT_TRACK=1` |

### Exact payload fields

| Field | Description |
|-------|-------------|
| `install_id` | Random UUIDv4 generated locally on first run. Stable per machine. |
| `machine_hash` | One-way SHA-256 of `hostname+OS+arch+MACs`. Raw identifiers are never sent. |
| `event` | `"first_run"` or `"trial_start"` |
| `version` | TOKN version string (e.g., `"0.3.2"`) |
| `os` | `runtime.GOOS` (e.g., `"darwin"`) |
| `arch` | `runtime.GOARCH` (e.g., `"arm64"`) |
| `ts` | UTC RFC3339 timestamp of the genuine first-run moment |

### What is NOT sent

Names, emails, file contents, prompts, source code, model API keys, directory paths, raw hostnames, or raw MAC addresses. No raw IP is stored by the endpoint (coarse country is derived server-side and discarded from the request).

### Behavior details

- Best-effort: a failed POST is never marked sent; it retries silently on later runs.
- Never blocks the CLI or returns a fatal error.
- Air-gap safe: the install UUID and first-run timestamp are captured locally even with no network, and flushed with the original timestamp when connectivity is restored.
- A no-op unless an endpoint was compiled in (`var EndpointURL = ""` in source; release builds inject it).

Source: `environment-manager/internal/registration/registration.go` (full package doc comment and `Event` struct).

## 4. Feedback Submission (Opt-in)

| Aspect | Detail |
|--------|--------|
| **Destination** | Derived from the registration endpoint: `.../feedback` (i.e., `https://tokn-registration-892151559760.us-central1.run.app/api/tokn/feedback`) |
| **Trigger** | Explicit user action: `tokn feedback` command or `/feedback` slash command |
| **Payload** | User-authored message (max 8000 chars), category, sentiment, anonymous install_id + machine_hash (unless telemetry is opted out), version, OS, arch, timestamp. Hostname is included ONLY if `--identify` flag or `TOKN_FEEDBACK_IDENTIFY=1` is set. |
| **On by default** | No — requires explicit invocation per submission |
| **How to disable** | Don't invoke it. Correlation IDs are suppressed by `TOKN_NO_TELEMETRY=1`. |

### Offline behavior

If the endpoint is unreachable, feedback is queued to `~/.tokn/feedback-outbox.jsonl` and flushed on a later run. Feedback is never lost.

Source: `environment-manager/internal/feedback/feedback.go`.

## 5. MCP Server Connections (User-configured)

| Aspect | Detail |
|--------|--------|
| **Destination** | Whatever MCP servers the user has configured (local stdio subprocesses or remote HTTP/SSE endpoints) |
| **Trigger** | Agent tool calls routed to MCP servers |
| **Payload** | JSON-RPC tool invocations; content depends on what the agent sends |
| **On by default** | Only if the user configures MCP servers |
| **How to disable** | Remove MCP server configuration |

Source: `environment-manager/internal/agent/plugins/`, `config/settings.go` line 214.

## 6. GitHub API (for updates and local model downloads)

| Aspect | Detail |
|--------|--------|
| **Destination** | `https://api.github.com` |
| **Trigger** | Self-update; llama.cpp release discovery for local model server |
| **Payload** | GET requests with optional auth token |
| **On by default** | Yes (update check); local model server download is explicit |
| **How to disable** | Do not run `tokn update` or local model commands |

Source: `update_cmds.go` line 24; `models/server.go` line 161.

## 7. Specialist Model Endpoints (Codegen)

| Aspect | Detail |
|--------|--------|
| **Destination** | HuggingFace Inference Router (`https://router.huggingface.co/hf-inference/models/...`) for 15 specialist models |
| **Trigger** | Codegen specialist model invocation (domain-specific tasks) |
| **Payload** | Model-specific inference requests |
| **On by default** | Only when explicitly invoked via codegen tools |
| **How to disable** | Do not use codegen specialist tools |

Source: `environment-manager/internal/agent/codegen/specialist.go` lines 32–115.

## Transport Security

All remote endpoints are subject to the URL policy in `environment-manager/internal/urlpolicy/urlpolicy.go`:
- HTTPS is required for all non-loopback destinations.
- Plaintext HTTP is allowed only to loopback addresses (`localhost`, `127.0.0.0/8`, `[::1]`) for local development.
- Non-HTTP schemes are refused.

This applies to the registration and feedback endpoints. Model provider URLs are configured by the user and not subject to this policy (the user may legitimately use `http://localhost:11434` for Ollama).

## How to Verify This Yourself

You do not need to trust this document. Here is how to independently verify TOKN's network behavior:

1. **Network monitoring**: Run `tcpdump`, Wireshark, or Little Snitch while using TOKN. All connections are standard HTTPS — no obfuscation, no custom protocols.

2. **Source inspection**: Every outbound call originates from the files cited in this document. Search the Go tree:
   ```
   grep -r "http.NewRequest\|http.Post\|http.Get" environment-manager/
   ```

3. **Opt-out verification**: Set `DO_NOT_TRACK=1` and confirm via network monitoring that no registration/feedback traffic occurs. Model provider traffic still flows (it must, for the tool to function) unless you switch to a local provider.

4. **Build-time endpoint injection**: In a dev build (`go build` without ldflags), registration is a silent no-op because `EndpointURL` is empty. You can verify this by inspecting the binary: `strings tokn | grep tokn-registration` — it will be absent in a dev build and present in a release build.

5. **Endpoint in release builds**: The registration URL compiled into release builds is:
   ```
   https://tokn-registration-892151559760.us-central1.run.app/api/tokn/register
   ```
   This is the `-RegistrationURL` default in `scripts/release.ps1` line 37.
