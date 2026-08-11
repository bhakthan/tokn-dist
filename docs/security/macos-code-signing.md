# macOS Code Signing & Notarization

> **Current status (as of writing):** TOKN's macOS binaries are **ad-hoc signed only** (`codesign -s -`, Go's default). They are NOT notarized. Gatekeeper rejects them on a clean Mac with _"cannot be opened because the developer cannot be verified"_. The tooling described below exists and is correct, but it becomes effective **only once** an Apple Developer Program enrolment is active and the signing credentials are configured.

## Overview

Apple's Gatekeeper requires that all distributed macOS software be:

1. **Code-signed** with a Developer ID certificate (not ad-hoc).
2. **Notarized** — submitted to Apple's automated security scan and approved.
3. Ideally **stapled** — the notarization ticket embedded in the distributable so Gatekeeper can verify it offline.

Without these, users must manually override Gatekeeper (`xattr -d com.apple.quarantine`), which is unacceptable for a professional tool.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/macos-sign-notarize.sh` | Signs darwin binaries, optionally packages as .pkg/.dmg, notarizes, staples |
| `scripts/macos-verify.sh` | User-facing verification of a downloaded binary or package |

Both scripts run **only on macOS** and enforce the repo's external dependency preflight policy.

## Prerequisites

### Apple Developer Program Enrolment

- **Individual or Organisation** — either works. Organisation enrolment requires a D-U-N-S number; allow 2–4 weeks for Dun & Bradstreet processing.
- URL: <https://developer.apple.com/programs/>

### Certificates Required

| Certificate | Usage |
|-------------|-------|
| Developer ID Application | Signs the binary itself (`codesign`) |
| Developer ID Installer | Signs `.pkg` installers (`productbuild --sign`) |

Create both in [Certificates, Identifiers & Profiles](https://developer.apple.com/account/resources/certificates/list). Download the `.cer` files and import them (with their private keys as `.p12`) into your keychain.

### App Store Connect API Key (for CI)

Create under [Users and Access → Keys](https://appstoreconnect.apple.com/access/api). Download the `.p8` file. Note the Key ID and Issuer ID.

## Credential Configuration

### Environment Variables

```bash
# Always required for signing
export APPLE_SIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export APPLE_TEAM_ID="XXXXXXXXXX"

# Required for .pkg packaging
export APPLE_INSTALLER_IDENTITY="Developer ID Installer: Your Name (TEAMID)"

# Notarization — API key (preferred for CI)
export APPLE_API_KEY_ID="XXXXXXXXXX"
export APPLE_API_ISSUER_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export APPLE_API_KEY_PATH="/path/to/AuthKey_XXXXXXXXXX.p8"

# OR — Apple ID (laptop fallback)
export APPLE_ID="you@example.com"
export APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"  # app-specific password
```

### GitHub Actions Secrets

For CI, store the signing certificate as a base64-encoded `.p12`:

```bash
# On your Mac, export the cert + key:
security export -t identities -f pkcs12 -o certs.p12 -k login.keychain
base64 -i certs.p12 | pbcopy
```

Set these GitHub Actions secrets:

| Secret | Value |
|--------|-------|
| `APPLE_CERTIFICATE_P12_BASE64` | base64 of the .p12 file |
| `APPLE_CERTIFICATE_PASSWORD` | Password for the .p12 |
| `APPLE_SIGN_IDENTITY` | Full identity string |
| `APPLE_INSTALLER_IDENTITY` | Full installer identity string |
| `APPLE_TEAM_ID` | Team ID |
| `APPLE_API_KEY_ID` | API key ID |
| `APPLE_API_ISSUER_ID` | Issuer ID |
| `APPLE_API_KEY_BASE64` | base64 of the .p8 file |

In your CI workflow, import into a **temporary keychain** (never the login keychain):

```yaml
- name: Import signing certificate
  run: |
    KEYCHAIN="build.keychain"
    KEYCHAIN_PASSWORD=$(openssl rand -base64 32)
    security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN"
    security set-keychain-settings -lut 3600 "$KEYCHAIN"
    security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN"
    echo "${{ secrets.APPLE_CERTIFICATE_P12_BASE64 }}" | base64 -d > cert.p12
    security import cert.p12 -k "$KEYCHAIN" -P "${{ secrets.APPLE_CERTIFICATE_PASSWORD }}" -T /usr/bin/codesign
    security set-key-partition-list -S apple-tool:,apple: -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN"
    security list-keychains -d user -s "$KEYCHAIN" $(security list-keychains -d user | tr -d '"')
    rm cert.p12
```

**Critical:** Delete the temporary keychain in a `post` step or `always()` block:

```yaml
- name: Cleanup keychain
  if: always()
  run: security delete-keychain build.keychain
```

This prevents credential leakage to subsequent jobs on shared runners.

## The Ordering Constraint

**This is the single most important correctness point for macOS releases.**

> **Two-manifest interaction:** `scripts/release.ps1` produces `SHA256SUMS` covering the 5 platform binaries. `scripts/macos-sign-notarize.sh` **rewrites that file** after codesigning (which changes the darwin binary bytes) and after packaging (which adds `.pkg`/`.dmg` assets). The resulting manifest covers both binaries and packages, in deterministic order. Anyone reading `release.ps1` alone would not discover that its `SHA256SUMS` is legitimately overwritten by a downstream script — this is that documentation.

```
┌─────────────────────────────────────────────────────────────────┐
│  1. scripts/release.ps1        → builds binaries, SHA256SUMS    │
│  2. scripts/macos-sign-notarize.sh → codesigns darwin binaries  │
│                                      (CHANGES THEIR BYTES)      │
│  3.                            → recomputes SHA256SUMS           │
│  4.                            → DELETES stale SHA256SUMS.sig   │
│  5. re-sign manifest:                                           │
│       go run ./environment-manager/cmd/releasesign \             │
│         -key <signing.key> -in SHA256SUMS -out SHA256SUMS.sig   │
│  6. Upload                                                      │
└─────────────────────────────────────────────────────────────────┘
```

**If you upload with the pre-signing checksums,** `tokn update` will reject every macOS download because the SHA-256 hashes won't match the code-signed binaries. This looks like a working release but is a self-inflicted outage for all macOS users.

The signing script handles steps 2–4 automatically and prints a prominent warning with the exact re-sign command.

## Bare Binary vs. Stapled Package

| Form | Notarizable | Stapleable | Offline Gatekeeper |
|------|:-----------:|:----------:|:------------------:|
| Raw Mach-O binary | ✓ (via zip) | ✗ | ✗ — ticket fetched online |
| `.pkg` installer | ✓ | ✓ | ✓ |
| `.dmg` disk image | ✓ | ✓ | ✓ |

**Recommendation:** Distribute a signed+stapled `.pkg` for users on locked-down or offline Macs. The bare binary works for users with internet access (Gatekeeper queries Apple's servers for the notarization ticket).

The raw binary cannot be stapled because stapling requires a container format that can hold the ticket (an `__CodeSignature` directory for bundles, or package/DMG metadata). This is an Apple platform limitation, not a TOKN choice.

## User Verification

Users can verify what they downloaded:

```bash
# Quick check — should print "valid on disk" and show the Team ID
codesign --verify --deep --strict --verbose=2 ./tokn
codesign -dv --verbose=4 ./tokn 2>&1 | grep -E '(Authority|TeamIdentifier)'

# Gatekeeper check — should print "accepted"
spctl --assess --type exec -v ./tokn

# For .pkg: check installer approval and staple
spctl --assess --type install -v ./tokn.pkg
xcrun stapler validate ./tokn.pkg
```

Or use the provided verification script:

```bash
./scripts/macos-verify.sh ./tokn_darwin_arm64
./scripts/macos-verify.sh ./tokn_darwin_arm64-1.2.0.pkg
```

## Certificate Expiry & Renewal

Developer ID certificates are valid for **5 years**. Key facts:

- A **notarized** build continues working after the signing certificate expires, because the notarization ticket is timestamped by Apple's servers. This is precisely why `--timestamp` is required during signing — it proves the signature was made while the certificate was valid.
- A non-notarized but timestamped signature also survives certificate expiry (Gatekeeper trusts the timestamp).
- Without `--timestamp`, the signature becomes invalid the moment the certificate expires, and Gatekeeper blocks the binary.
- **Renewal:** Generate a new certificate before expiry. Future builds use the new cert; past notarized builds remain valid indefinitely.

## What This Does NOT Cover

- **Windows Authenticode signing** — separate concern, separate tooling.
- **Linux binary signing** — Linux does not have an equivalent Gatekeeper; the ed25519 SHA256SUMS.sig serves this purpose.
- **Automatic CI integration** — the workflow file (`.github/workflows/release.yml`) is owned separately. This doc covers the credentials and scripts it would invoke.
