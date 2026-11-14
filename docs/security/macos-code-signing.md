# macOS download checks

**TOKN's release signature and Apple's platform checks are different things.**
Verifying `SHA256SUMS.sig` does not prove Developer ID signing or notarization.
Do not assume those properties unless the particular release documents them
and the relevant checks succeed.

The public channel supplies raw macOS binaries. Choose `tokn_darwin_arm64`
for Apple Silicon or `tokn_darwin_amd64` for Intel.
First follow the [download verification procedure](../../README.md#2-verify-what-you-downloaded).

## Inspect the downloaded artifact

These are **macOS-only** commands using Apple's system tools. Run them in the
directory holding the verified download; substitute your asset name:

```bash
command -v codesign
command -v spctl
codesign --verify --strict --verbose=2 ./tokn_darwin_arm64
codesign -dv --verbose=4 ./tokn_darwin_arm64 2>&1
spctl --assess --type exec --verbose=2 ./tokn_darwin_arm64
```

| Check | How to read it |
|---|---|
| Release checksum/signature | Checks the download against the signed TOKN manifest |
| `codesign --verify` | Tests the artifact's code-signature validity; success alone does not establish a named Developer ID |
| `codesign -dv` | Shows signature details; an ad-hoc signature is not a Developer ID identity |
| `spctl --assess` | Reports the local platform's assessment; a rejection is not an accepted check |

Results depend on the artifact and macOS policy. These are inspection commands,
not a recorded successful assessment of v0.3.100. Do not disable system policy
or remove quarantine merely to silence an unexplained verification failure.
If your organisation requires notarized software, obtain confirmed evidence
before deployment.

## Apple Silicon licensing is a separate limitation

Community use is available on Apple Silicon. **Developer-license support is
not ready on macOS arm64**, as stated in the current
[platform-support table](../../README.md#platform-support).
Passing a code-signing check does not change licence readiness.
Do not spend the one-per-machine trial there to test licensed workflows.

Report a platform problem with the release tag, asset name, macOS version and
sanitized error text. Use the [private reporting route](../../SECURITY.md)
if the report includes a security issue.
