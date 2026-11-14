# Supply-chain evidence for public downloads

**Check evidence for the exact artifact you downloaded.** A workflow badge,
source scan or document about future tooling is not proof about that binary.

## What is available

The **v0.3.100** public release lists five platform binaries,
`SHA256SUMS` and `SHA256SUMS.sig`. It lists **no SBOM assets**.
This guide does not claim public build-provenance coverage for those downloads.

Start with the [checksum and signature procedure](../../README.md#2-verify-what-you-downloaded).
That verifies the actual downloaded bytes against the signed manifest.

## Different evidence answers different questions

| Evidence | What it helps establish | What it does not establish |
|---|---|---|
| Checksum | Bytes match a stated digest | Who published those bytes |
| Release signature | The manifest was signed by the trusted release key | A code audit or a safe result for every task |
| SBOM, if provided | A declared component inventory for an artifact | Complete vulnerability coverage or correct behaviour |
| Build attestation, if provided | A verifiable relationship between an artifact and its build | That the source or dependencies are defect-free |
| Independent audit report, if provided | Findings for the stated scope and date | A permanent guarantee for later releases |

Only claim an SBOM or attestation applies when it identifies the same binary
and its verification material is accessible to you. A source-only workflow
does not establish provenance for the public binary you downloaded.

## Inspect a release

With GitHub CLI installed:

```sh
gh release view v0.3.100 --repo bhakthan/tokn-dist --json tagName,assets
gh api repos/bhakthan/tokn-dist/releases/tags/v0.3.100 --jq '{tag: .tag_name, immutable: .immutable}'
```

Alternatively, open the
[release page](https://github.com/bhakthan/tokn-dist/releases/tag/v0.3.100).
For this tag, the release API reports `immutable: false`.
A new version tag is useful identification, but is not itself an immutability
or authenticity guarantee. Retain the verified digest with your installation
record.

## Operational use

Inventory the version, platform and verified checksum you deploy. Reassess
updates against your environment, restrict executable permissions and keep a
recovery path. Where a procurement policy requires an SBOM, attestation or
independent audit, request that evidence rather than treating this guide as
an equivalent certification.

See [update behaviour](update-process.md), [release-key verification](key-management.md)
and [private vulnerability reporting](../../SECURITY.md).
