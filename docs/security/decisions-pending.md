# Release status and limitations

Use this as a short checklist of evidence to request, not a promise that
unconfirmed controls are live.
The [security overview](README.md) records observations for v0.3.100.

| Question | Current guidance |
|---|---|
| Can I authenticate a public download? | Verify both the signed manifest and the matching binary checksum |
| Is this release immutable on GitHub? | Check the particular release; v0.3.100 reports `immutable: false` |
| Does the download include an SBOM? | No SBOM assets are listed on v0.3.100 |
| Can I assume a public build attestation exists? | No; request evidence matching the exact downloaded artifact |
| Is a macOS download notarized? | Do not infer this from TOKN's release signature; inspect the asset and release-specific evidence |
| Is Developer licensing ready on Apple Silicon? | No; Community use and licence readiness are separate |
| Has an independent audit report been published here? | No report is published in these guides |

Newer releases may change individual answers. Verify their actual assets and
metadata rather than carrying a status forward from an older page.

For evaluation, use synthetic inputs and least-privilege permissions.
For a deployment with additional compliance requirements, obtain the required
evidence before relying on a capability. A model's answer, a successful command
or a licence does not constitute that evidence.

- [Download verification](../../README.md#2-verify-what-you-downloaded)
- [Supply-chain evidence](supply-chain.md)
- [macOS checks](macos-code-signing.md)
- [Threat model](threat-model.md)
- [Private vulnerability reporting](../../SECURITY.md)
