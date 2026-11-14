# TOKN security documentation

Use these guides to decide what to trust, what to configure and what to verify.
They apply to the **public distribution**, not a source-code build.

## Start here

```text
Download -> verify checksum AND signature -> configure data access -> run
                     |
                     +-> failure: stop; do not bypass verification
```

| Guide | What it helps you do |
|---|---|
| [Security policy](../../SECURITY.md) | Report a vulnerability privately |
| [Threat model](threat-model.md) | Understand tool, model and host boundaries |
| [Network activity](telemetry-and-network.md) | Choose endpoints and disable unrelated startup checks |
| [Update process](update-process.md) | Verify a download and recover from an update problem |
| [Release-key verification](key-management.md) | Understand the public key and signature trust |
| [macOS checks](macos-code-signing.md) | Distinguish release verification from Apple platform approval |
| [Supply-chain evidence](supply-chain.md) | Check what evidence actually accompanies an artifact |
| [Release status and limitations](decisions-pending.md) | Separate available evidence from unconfirmed properties |

## Current public-release evidence

Checked against **v0.3.100**:

| Item | Observed status |
|---|---|
| Platform binaries | Five assets listed on the public release |
| Checksum manifest | `SHA256SUMS` listed |
| Manifest signature | `SHA256SUMS.sig` listed |
| GitHub release immutability | The release API reports `immutable: false` for this tag |
| SBOM downloads | No SBOM assets listed on this release |
| Independent audit report | No report published in these guides |

An asset being listed does not establish that it was verified. Follow the
[verification procedure](../../README.md#2-verify-what-you-downloaded) for the
file you actually downloaded. A signature is not a code audit, a malware scan
or a guarantee that a model's answer is correct.

Do not infer notarization, attestation or certification from the presence of
a checksum. See the relevant guide for what to check.
