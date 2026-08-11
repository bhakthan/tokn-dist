# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release on [bhakthan/tokn-dist](https://github.com/bhakthan/tokn-dist) | ✅ |
| Any older release | ❌ — update to latest via `tokn update` |

TOKN does not maintain backport branches. Security fixes ship in the next release and users are expected to update promptly. The `tokn update` mechanism is designed to make this frictionless.

## Reporting a Vulnerability

**Use [GitHub Private Vulnerability Reporting](https://github.com/bhakthan/tokn/security/advisories/new)** on the `bhakthan/tokn` repository.

Do **not** open a public issue for security vulnerabilities.

### What to expect

| Stage | Target | Notes |
|-------|--------|-------|
| Acknowledgement | 72 hours | Confirmation that the report was received |
| Triage | 7 days | Assessment of severity, scope, and affected versions |
| Fix or mitigation | 30 days | For critical/high; longer for lower severity with disclosure |

These are intentions, not contractual guarantees. Complex issues may take longer; the reporter will be kept informed.

### Coordinated Disclosure

We ask reporters to allow 90 days from acknowledgement before public disclosure. If a fix ships sooner, disclosure can proceed immediately after the release. If we are unresponsive beyond the timelines above, the reporter is free to disclose.

## Scope

### In scope

- The `tokn` CLI binary and its self-update mechanism
- Release signing key management and update verification
- The domain safety gates (blocking gates in `synbio/`, `precmed/`, `nucsci/`, `oncology/`, etc.)
- Prompt injection leading to unintended tool execution
- Data leakage through the registration/feedback telemetry path
- MCP plugin sandbox escapes (path traversal, env injection)

### Out of scope

- **Third-party model providers** — vulnerabilities in OpenAI, Anthropic, Azure OpenAI, etc. Report those to the respective provider.
- **User-supplied MCP servers** — TOKN executes these as configured by the user. A malicious MCP server the user chose to install is not a TOKN vulnerability.
- **Findings requiring an already-compromised local machine** — if the attacker already has code execution as the user, TOKN cannot meaningfully defend against them (the threat model documents this boundary explicitly).
- **Social engineering** of the repository maintainer.

## Security Properties TOKN Does and Does Not Provide

### Does provide

- **Integrity-verified updates**: `tokn update` refuses to install any binary that does not match a SHA-256 checksum manifest, and (in release builds) refuses any manifest not signed by the release ed25519 key.
- **Transport-security enforcement**: telemetry endpoints must use HTTPS (or loopback HTTP for local dev). See [`urlpolicy.go`](environment-manager/internal/urlpolicy/urlpolicy.go).
- **Opt-out telemetry**: all anonymous data collection is disabled by `DO_NOT_TRACK=1`. The only user-authored content ever sent to TOKN infrastructure is explicit `tokn feedback` submissions.
- **Domain safety gates**: safety-critical domains implement blocking gates that refuse to advance a workflow past defined checkpoints without passing validation.

### Does not provide

- **Sandboxed tool execution**: TOKN executes shell commands and file edits on the user's machine with the user's permissions. There is no privilege separation between the agent and the user's session.
- **Prompt injection resistance**: content from repositories, web fetches, or MCP tool outputs is fed to the model in a context where it can influence tool calls. This is a fundamental limitation of the architecture, not a bug to be fixed.
- **Tamper-proof safety gates**: gates run in the same process as the agent. A local attacker who can modify the binary or its configuration can bypass them.
- **Hardware-backed key management**: the release signing key currently resides on a general-purpose workstation. See [key-management.md](docs/security/key-management.md) for the hardening roadmap.

## Additional Documentation

- [Threat Model](docs/security/threat-model.md)
- [Telemetry & Network Connections](docs/security/telemetry-and-network.md)
- [Update Process](docs/security/update-process.md)
- [Key Management](docs/security/key-management.md)
- [macOS Code Signing](docs/security/macos-code-signing.md)
- [Supply Chain](docs/security/supply-chain.md)

## Note on Accessibility

This repository (`bhakthan/tokn`) is currently **private**. Users who download from the public distribution repo (`bhakthan/tokn-dist`) cannot reach this file directly. This `SECURITY.md` is mirrored to `bhakthan/tokn-dist` so that vulnerability reporters can find it regardless of which repo they interact with.

## Audit Status

No independent third-party security audit has been performed. Audit status is tracked in [`docs/security/README.md`](docs/security/README.md).
