# Threat Model

This document describes the threat model for TOKN — an AI agent CLI that executes tools (shell commands, file edits, web fetches) on the user's machine and communicates with external model providers.

## Assets

| Asset | Where it lives | Compromise impact |
|-------|---------------|-------------------|
| **Release signing private key** (ed25519) | `~/.tokn-release/signing.key` on the release engineer's workstation | Attacker can sign arbitrary binaries that every TOKN user will accept via `tokn update` — remote code execution at scale |
| **Trial HMAC seed** | `~/.tokn-release/trial-seed.txt` on the release engineer's workstation | Attacker can forge valid trial licenses; existing trials may stop verifying if seed changes |
| **User source code and prompts** | User's machine; transmitted to configured model provider | Exfiltration via model provider compromise or prompt injection |
| **User's model-provider API keys** | User's environment / `~/.nospace/config.toml` | Unauthorized model usage; billing fraud; data exfiltration through the provider |
| **The update channel** | GitHub release assets on `bhakthan/tokn-dist` | Supply-chain attack: distribute malicious binaries to all users who run `tokn update` |
| **Domain safety gates** | Compiled into the binary; configuration in the user's workspace | Disabling a gate (e.g., `synbio/` biosecurity screening) could allow the agent to assist with dangerous actions it was designed to refuse |

## Trust Boundaries

### User's machine ↔ Model providers

Every prompt, file excerpt, and tool output sent to the model leaves the user's machine over HTTPS to the configured provider (OpenAI, Anthropic, Azure OpenAI, Gemini, HuggingFace, Ollama/local, OpenRouter, Fireworks, Bedrock, Vertex, or any of 15+ API-key providers). **This is the largest data flow in the product.** TOKN does not filter or redact content before sending it to the provider. The user's trust in TOKN includes implicit trust in their chosen model provider's data handling.

Source: `environment-manager/internal/agent/provider/provider.go` (the `New()` function, lines ~197–550).

### User's machine ↔ Release channel

`tokn update` fetches release metadata and binaries from `https://api.github.com/repos/bhakthan/tokn-dist/releases/latest`. Trust depends on: (1) TLS to GitHub, (2) SHA-256 checksum of the binary, and (3) ed25519 signature of the checksum manifest.

Source: `environment-manager/internal/agent/commands/update_verify.go`, `update_cmds.go` line 24.

### Agent ↔ Tool execution

TOKN executes shell commands and file edits on the user's machine with the user's full permissions. **There is no sandbox, no privilege separation, and no capability restriction beyond what the model chooses not to do.** Content from repositories, fetched web pages, and MCP tool outputs is presented to the model in the same context that drives tool calls. This means:

- **Prompt injection from repository content** (e.g., a malicious `AGENTS.md`, `README.md`, or comment in source code) can influence the agent to execute arbitrary commands.
- **Prompt injection from web fetches** can achieve the same.
- **Malicious MCP servers** the user connects to can return tool outputs designed to manipulate the agent.

No mitigation exists today for prompt injection into an agent with shell access. This is a fundamental architectural limitation shared with all tool-using LLM agents.

### User's machine ↔ TOKN telemetry infrastructure

A single anonymous registration event (install UUID, one-way machine hash, version, OS, arch, timestamp). The URL policy layer (`urlpolicy.go`) enforces HTTPS for non-loopback endpoints. Opt-out with `DO_NOT_TRACK=1`.

### User's machine ↔ MCP servers

User-configured MCP servers are spawned as subprocesses (stdio) or connected via HTTP/SSE. TOKN validates that stdio servers do not escape the plugin root directory and rejects reserved environment variable names. However, once launched, an MCP server runs with the user's full permissions.

Source: `environment-manager/internal/agent/plugins/agentplugin.go` (path traversal checks, lines ~450–510).

## Adversaries

| Adversary | Capability | Primary target |
|-----------|-----------|----------------|
| **Compromised GitHub token** | Write access to `bhakthan/tokn-dist` releases | Update channel — publish malicious binaries |
| **Compromised release workstation** | Access to signing key, trial seed, release scripts | All assets — sign malicious releases, forge trials |
| **Malicious repository content** | Control of files the agent reads (cloned repo, fetched URL) | Prompt injection → arbitrary tool execution |
| **Compromised model provider** | Full visibility into prompts and responses; ability to inject tool calls | User source code; arbitrary command execution via manipulated responses |
| **Network attacker (MITM)** | Intercept/modify traffic to non-HTTPS endpoints | Telemetry data; update payloads (mitigated by HTTPS enforcement) |

## Threat → Mitigation → Residual Risk

### 1. Supply-chain attack via release asset replacement

**Threat:** Attacker with a stolen GitHub PAT (or compromised CI) replaces release binaries on `bhakthan/tokn-dist`.

**Mitigation:**
- SHA-256 checksum verification is mandatory (`update_verify.go`: `ErrNoChecksums` if `SHA256SUMS` is absent).
- Ed25519 signature verification when the public key is compiled in (`releaseSigPubKeyB64` injected via ldflags). The signature covers the `SHA256SUMS` manifest, so replacing individual assets is not enough — the attacker must also produce a valid signature.
- `scripts/release.ps1` refuses to upload a `.sig` file older than the manifest it covers, preventing stale-signature publication.
- The release script verifies the signature against the embedded public key before uploading, catching key mismatch at build time.

**Residual risk:** If the attacker also has the signing private key (see threat #2), all verification is defeated. Checksum-only builds (dev builds without a compiled-in key) have no authenticity guarantee — only integrity against corruption/partial replacement.

### 2. Signing key compromise

**Threat:** The ed25519 private key (`~/.tokn-release/signing.key`) is exfiltrated from the release engineer's workstation.

**Mitigation:** No mitigation exists today beyond file permissions (0600) and the key never being committed to the repository.

**Residual risk:** **This is the weakest link in the current supply chain.** A signing key on a general-purpose workstation is vulnerable to malware, credential theft, and physical access. See [key-management.md](key-management.md) for the hardening roadmap.

### 3. Stale signature / mismatched trial seed in release

**Threat:** A release is published with a `SHA256SUMS.sig` that was generated for a previous manifest, or with a trial seed that differs from prior releases (invalidating existing trials).

**Mitigation (already implemented):**
- `scripts/release.ps1` deletes any `.sig` file older than the manifest when no signing key is available, preventing accidental stale-signature publication.
- The script's timestamp check (`LastWriteTimeUtc`) refuses to upload a signature that predates the manifest.
- The script prints explicit warnings when secrets are missing, naming the exact consequence ("TRIALS ISSUED BY PREVIOUS RELEASES WILL STOP VERIFYING").
- Post-sign verification confirms the signature matches the embedded public key.

**Residual risk:** The warnings are advisory. An operator who ignores them (or passes `-AllowNoEndpoint`) can still produce a broken release. This is a human-process risk, not a code defect.

### 4. Prompt injection → arbitrary code execution

**Threat:** Attacker places crafted content in a repository file, URL, or MCP tool output that causes the LLM to execute attacker-chosen shell commands.

**Mitigation:** No mitigation today. The agent has unrestricted shell access by design. Domain safety gates block specific *domain-level* dangerous actions (e.g., synthesizing a pathogen sequence in `synbio/`) but do not defend against arbitrary prompt injection.

**Residual risk:** **Critical.** Any user who points TOKN at untrusted content (cloned repos, web URLs, third-party MCP servers) is exposed to arbitrary code execution. This is inherent to the tool-using agent architecture and is shared with all similar products (Claude Code, Cursor Agent, GitHub Copilot Workspace, etc.).

### 5. Safety gate bypass

**Threat:** An attacker (or a prompt injection) disables or circumvents a domain safety gate — e.g., the biosecurity screening in `synbio/` or the clinical safety gates in `precmed/`.

**Mitigation:**
- Gates are compiled into the binary and fire based on the active domain mode. They cannot be disabled via configuration alone.
- Domain hooks only fire when their domain mode is active (workspace instructions enforce this as a trust invariant).
- Gate bypass requires modifying the binary, the Go source, or the domain mode selection logic.

**Residual risk:** A local attacker who can replace the binary or build from modified source can remove any gate. The gates defend against the *model* being manipulated into dangerous actions, not against a determined local attacker. Additionally, a sufficiently sophisticated prompt injection could potentially convince the model to switch domain modes or invoke tools in an unexpected order — gates mitigate but do not eliminate this.

### 6. Model-provider-side data access

**Threat:** The configured model provider logs, trains on, or is compelled to disclose the user's prompts and source code.

**Mitigation:** TOKN does not add its own data retention. Users who need strict data residency can use Ollama (fully local) or Azure OpenAI with a private endpoint. Provider selection is the user's responsibility.

**Residual risk:** Most users send their code to a third-party API. This is a privacy exposure that TOKN enables by design.

### 7. Credential leakage via environment/config

**Threat:** Model-provider API keys stored in environment variables or `~/.nospace/config.toml` are exfiltrated (via prompt injection instructing the agent to `echo $OPENAI_API_KEY`, via a malicious MCP server reading the environment, etc.).

**Mitigation:**
- The `credentials/` package has a sensitive-access guard that flags tool invocations accessing known credential paths.
- TOKN refuses to load API keys from repository-local `.env` files for security reasons (see `commands/provider_selection_lesson.go` — "AZURE_OPENAI_ENDPOINT in a repo .env is refused by design").

**Residual risk:** The agent has full access to the user's environment. A successful prompt injection can trivially exfiltrate any environment variable. The sensitive-access guard is a detection/alerting layer, not a prevention layer.

## Residual Risk Summary

| Risk | Severity | Status |
|------|----------|--------|
| Signing key on general-purpose workstation | High | No mitigation today; hardening roadmap in [key-management.md](key-management.md) |
| Prompt injection → arbitrary execution | Critical | No mitigation; architectural limitation |
| Source code sent to third-party providers | Medium | User choice; local models available |
| Credential exfiltration via agent | Medium | Detection only (sensitive-access guard) |
| Safety gate bypass via binary modification | Low | Requires local attacker with write access to the binary |
| MCP server escape after launch | Low | Subprocess runs as user; pre-launch path validation only |
