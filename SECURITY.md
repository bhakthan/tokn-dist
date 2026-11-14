# Security policy

## Supported versions

Use the [latest official release](https://github.com/bhakthan/tokn-dist/releases/latest).
TOKN does not maintain backport branches. Check your version with `tokn version`;
`tokn update --check` contacts the release channel without installing an update.

## Reporting a vulnerability

**Use [GitHub Private Vulnerability Reporting](https://github.com/bhakthan/tokn-dist/security/advisories/new)
in this public distribution repository.** The report itself is private.
Do not post exploit details, credentials or sensitive files in a public issue.

Include the affected version, OS/architecture, a minimal synthetic reproduction
and the impact you observed. Redact logs and configuration before attaching them.
If the private form is unavailable, open an issue requesting a private reporting
channel **without describing the vulnerability**.

We aim to acknowledge reports within 72 hours and triage within seven days.
For critical or high-impact issues, the target is a fix or mitigation within
30 days. These are targets, not contractual guarantees.
Please allow coordinated disclosure before publishing details.

## Scope

In scope are TOKN's update verification, credential handling, tool permissions,
workspace boundaries, integrations and domain safeguards. A flaw in TOKN's
handling of an external tool is still relevant even if that tool is third-party.

Provider-side defects should also be reported to the provider.
TOKN cannot protect a machine or account that an attacker already controls.

## What users should rely on—and what they should not

| Area | Practical boundary |
|---|---|
| Download verification | Official releases publish a checksum manifest and signature; follow the [verification instructions](README.md#2-verify-what-you-downloaded) |
| Tool execution | Permissions and trust settings restrict workflows; ordinary execution is not an OS sandbox |
| Untrusted content | Repository files, web pages and tool results can influence a model; do not assume prompt-injection immunity |
| Model data | Hosted models receive the context sent to them; choose approved providers and inputs |
| Local models | Preparing local inference does not by itself disable every external tool or startup connection |
| Domain safeguards | Checks support review; they are not professional approval or regulatory certification |
| Licensing | Feature entitlement is not a security or data-isolation boundary |

Use least privilege, review approvals and use host/container isolation when the
task requires it. Never bypass a failed signature check to make an update work.

## Additional documentation

- [Security overview](docs/security/README.md)
- [Threat model](docs/security/threat-model.md)
- [Network activity and opt-outs](docs/security/telemetry-and-network.md)
- [Update process](docs/security/update-process.md)
- [Release-key verification](docs/security/key-management.md)
- [macOS checks](docs/security/macos-code-signing.md)
- [Supply-chain evidence](docs/security/supply-chain.md)

No independent third-party audit report is published here. These guides describe
user-facing controls and limitations, not a security certification.
