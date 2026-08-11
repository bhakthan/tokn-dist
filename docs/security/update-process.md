# Update Process

How `tokn update` works and what it verifies before replacing the running binary.

## Overview

`tokn update` replaces the running executable with a newer build fetched from the GitHub release on `bhakthan/tokn-dist`. The process is designed to be fail-closed: any verification failure aborts the update and leaves the current binary untouched.

## Discovery

1. TOKN queries the GitHub Releases API:
   ```
   GET https://api.github.com/repos/bhakthan/tokn-dist/releases/latest
   ```
   Or, for a pinned version: `.../releases/tags/<tag>`.

2. The response is parsed for three assets matching the current platform:
   - `tokn_{os}_{arch}[.exe]` — the binary
   - `SHA256SUMS` — the checksum manifest
   - `SHA256SUMS.sig` — the ed25519 signature over the manifest

3. If the release tag matches the running version AND the binary is byte-identical (checksum comparison), the update is a no-op. TOKN detects re-published releases (same tag, different bytes) and updates in that case.

Source: `environment-manager/internal/agent/commands/update_cmds.go` lines 24, 29, 340–420.

## Verification Layers

Two layers, both fail-closed:

### Layer 1: SHA-256 Checksum (always on)

- The `SHA256SUMS` asset is downloaded from the release.
- If absent → `ErrNoChecksums` → update refused.
- The binary is downloaded through a `hashingWriter` that computes SHA-256 in a single streaming pass.
- The computed hash is compared to the expected hash from the manifest.
- Mismatch → `ErrChecksumMismatch` → update refused. "Treat as hostile, never as a transient failure" (source comment).

**What this buys:** Protection against corruption and against replacement of a *single asset* when the manifest itself is unmodified.

**What this does NOT buy:** If the attacker can write *all* assets (including `SHA256SUMS`), a matching checksum proves nothing. The manifest is trusted only because of Layer 2.

### Layer 2: Ed25519 Signature (on when release key is compiled in)

- `SHA256SUMS.sig` is downloaded and verified against the ed25519 public key compiled into the binary (`releaseSigPubKeyB64`, injected at build time via `-ldflags`).
- If the key is absent (dev builds) → signature check is skipped; only Layer 1 applies.
- If the key is present but `SHA256SUMS.sig` is missing → `ErrBadSignature` → update refused.
- If the signature does not verify → `ErrBadSignature` → update refused.

**What this buys:** Even if the attacker controls the entire release (all assets, including `SHA256SUMS`), they cannot produce a valid signature without the private key. This is the layer that defends against a compromised GitHub token.

**There is deliberately no bypass.** No environment variable, no `--force` flag overrides a signature failure. The doc comment in `update_verify.go` states: "a silent downgrade to 'trust whatever GitHub served' is exactly the outcome this code exists to prevent."

Source: `environment-manager/internal/agent/commands/update_verify.go` (full file, especially the doc comment block and `resolveExpectedDigest`).

## Installation

After verification passes:

1. The current binary is saved as an N-1 fallback in a versions directory alongside the executable.
2. The new binary is written to a temporary path and atomically renamed over the current executable.
3. Old backups beyond N-1 are pruned (only the immediate previous version is retained).

## N-1 Rollback

`tokn update --rollback` swaps the running binary with the single retained fallback. A second rollback toggles back (the version rolled back *from* becomes the new fallback). This provides a single-step recovery when an update introduces a regression.

`tokn update --list` shows the current version and the retained rollback target.

Source: `update_cmds.go` lines 60–78, 276–318, 583–706.

## Re-publish Detection

TOKN's release policy is to rebuild and re-upload to the *current* tag rather than bump a version for every fix. The updater detects this by comparing the SHA-256 of the running binary against the published checksum — not by comparing version tags. Same tag + different checksum = re-published build → update proceeds.

The full (wiki-embedded) variant cannot be compared against the public asset (they differ by design), so it returns "unknown" and defers to `--force`.

Source: `update_verify.go`, function `detectRepublish`.

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| No network | Update fails cleanly; current binary untouched |
| `SHA256SUMS` absent | `ErrNoChecksums` — refused |
| Checksum mismatch | `ErrChecksumMismatch` — refused |
| `SHA256SUMS.sig` absent (release build) | `ErrBadSignature` — refused |
| Signature invalid | `ErrBadSignature` — refused |
| GitHub API 404 | Error with guidance ("repo may be private; set GITHUB_TOKEN") |
| Asset > 1 MiB (meta-assets) | Capped by `maxMetaAssetBytes`; prevents memory exhaustion |

## Manual Verification Recipe

If you do not want to trust the updater, you can verify a release manually:

```bash
# 1. Download the binary and metadata
curl -LO https://github.com/bhakthan/tokn-dist/releases/latest/download/tokn_linux_amd64
curl -LO https://github.com/bhakthan/tokn-dist/releases/latest/download/SHA256SUMS
curl -LO https://github.com/bhakthan/tokn-dist/releases/latest/download/SHA256SUMS.sig

# 2. Verify the checksum
sha256sum -c SHA256SUMS --ignore-missing

# 3. Verify the signature (requires the public key)
# Public key (base64): 3O2DznsYRy+OU2gTIbpvOfw0O6tUIIRQfiOUDbfoHxo=
# Use the releasesign tool or any ed25519 verifier:
go run ./environment-manager/cmd/releasesign \
  -verify \
  -pub "3O2DznsYRy+OU2gTIbpvOfw0O6tUIIRQfiOUDbfoHxo=" \
  -in SHA256SUMS \
  -sig SHA256SUMS.sig
```

For additional verification via build provenance attestation (SLSA), see [supply-chain.md](supply-chain.md).

For macOS Gatekeeper verification, see [macos-code-signing.md](macos-code-signing.md).

## What the Updater Tells You

Before installing, the updater prints one of:

- `Verified: SHA-256 checksum + ed25519 release signature.` — full verification (release build with compiled-in key)
- `Verified: SHA-256 checksum (this build has no release signing key compiled in).` — integrity only, no authenticity (dev builds)

Source: `update_verify.go`, function `updateVerificationNotice`.
