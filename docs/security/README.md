# TOKN Security Documentation

This directory is the index for TOKN's security posture. Every document here is
written to one rule, which is the same rule the rest of this repository runs on:

> **State what is true today. Mark everything else as not yet done.**

A security document that describes an aspiration in the present tense is worse
than no document, because it converts an unmitigated risk into a mitigated-looking
one. Where a control is planned but not live, this directory says so in the same
sentence that describes it.

## Contents

| Document | Covers |
|---|---|
| [`../../SECURITY.md`](../../SECURITY.md) | Vulnerability reporting, supported versions, scope |
| [`threat-model.md`](threat-model.md) | Assets, trust boundaries, adversaries, mitigations, residual risk |
| [`telemetry-and-network.md`](telemetry-and-network.md) | Every outbound connection, what it carries, how to disable it |
| [`update-process.md`](update-process.md) | What `tokn update` verifies, and manual verification recipes |
| [`key-management.md`](key-management.md) | Release signing key, trial seed, fingerprints, rotation |
| [`macos-code-signing.md`](macos-code-signing.md) | Developer ID signing, hardened runtime, notarization, Gatekeeper |
| [`supply-chain.md`](supply-chain.md) | Build provenance attestation, SBOMs, vulnerability scanning |

## Control status

This table is the honest summary. It is deliberately the first thing a reader
sees, because the individual documents describe mechanisms in detail and it is
easy to come away believing a mechanism is active when only its tooling exists.

| Control | Status | Notes |
|---|---|---|
| SHA-256 manifest per release | **Live** | `SHA256SUMS` published for both variants |
| ed25519 signature over the manifest | **Live** | `SHA256SUMS.sig`; public key compiled into the binary, so `tokn update` verifies authenticity offline |
| Update refuses unverified downloads | **Live** | See [`update-process.md`](update-process.md) |
| Signing-key fingerprint published | **Live** | Below, and mirrored out-of-band — see [`key-management.md`](key-management.md) |
| Signing key held offline / in hardware | **Not done** | Currently a file on the release engineer's workstation. This is the weakest link in the chain today; hardening path in [`key-management.md`](key-management.md) |
| macOS Developer ID signing + notarization | **Tooling ready, not active** | Requires Apple Developer Program enrolment. macOS binaries are currently **ad-hoc signed and Gatekeeper rejects them** |
| Build provenance attestation | **Tooling ready, blocked on plan + build location** | Two independent gaps: releases are built on a workstation rather than in CI, and artifact attestations in a **private** repo require GitHub Enterprise Cloud. See [`supply-chain.md`](supply-chain.md) |
| SBOM (SPDX + CycloneDX) | **Tooling ready** | Effective from the first release cut through the workflow |
| Vulnerability scanning published | **Tooling ready** | `govulncheck` gates on reachable findings; `grype` informational |
| GitHub immutable releases | **Not enabled** | See below — enabling it is a deliberate process change, not just a switch |
| Independent third-party security audit | **Not performed** | See below |

## Release signing key fingerprint

TOKN signs each release's `SHA256SUMS` manifest with an ed25519 key. The
corresponding public key is compiled into every released binary so that
`tokn update` can verify authenticity without contacting anything.

```
Algorithm:  ed25519
Public key: 3O2DznsYRy+OU2gTIbpvOfw0O6tUIIRQfiOUDbfoHxo=
SHA-256 fingerprint of the raw 32-byte public key:
            364e425ec887eb4b13e0c83927679f603608eab679c893fd3f8e508a22c7d14a
```

**Why the fingerprint is also published elsewhere.** Comparing a signature
against a key you obtained from the same repository that served you the binary
proves very little: an attacker who can replace the binary can usually also
replace the key you would check it against. The fingerprint is therefore
mirrored on at least one channel that an attacker would have to compromise
*separately*. See [`key-management.md`](key-management.md) for the current list
of publication channels and for how to verify a key you have in hand.

If a fingerprint you find anywhere disagrees with the value above, **do not
install the binary** — report it via the process in
[`../../SECURITY.md`](../../SECURITY.md).

## Independent security audit

**No independent third-party security audit of TOKN has been performed.**

Nothing in this directory should be read as implying otherwise. When an audit is
commissioned, this section will carry the auditor, the scope, the date, the
report or its summary, and the disposition of each finding — including findings
that were accepted rather than fixed.

Scope that an audit should cover, in rough priority order:

1. **The release and update path** — signature verification in
   `environment-manager/internal/agent/commands/update_verify.go`, the signer in
   `environment-manager/cmd/releasesign`, and the key handling in
   `scripts/release.ps1`. A flaw here is remotely exploitable against every
   installed copy, which makes it the highest-value target in the product.
2. **Agent tool execution** — TOKN edits files and runs commands on the user's
   machine. Prompt injection reaching a tool-using agent is the most likely path
   from "untrusted content" to "code execution", and it is a design-level
   exposure rather than a bug to be patched.
3. **Domain safety gates** — several domain plugs (`synbio`, `precmed`,
   `nucsci`, `oncology`, `edagent`) exist specifically to *block* unsafe
   operations. A bypass is a safety failure, not merely a security one, so the
   gates deserve adversarial review rather than functional testing.
4. **Credential handling** — model-provider API keys, license material, and the
   trial HMAC seed.

## GitHub immutable releases

Immutable releases freeze a release's assets and tag at publish time. This is a
genuine supply-chain improvement: it removes the "the tag moved under me" class
of attack entirely.

It is **not enabled yet**, and enabling it is a process change rather than a
setting change. Two things must be understood first:

1. **There is no REST API for it.** As of 2026-08 it is UI-only:
   *Settings → General → Releases → "Enable release immutability"*. It must be
   set on **both** `bhakthan/tokn` and `bhakthan/tokn-dist`. An API `PATCH` of
   `immutable_releases` is silently ignored — it returns success and changes
   nothing, which is a trap worth knowing about. The per-release `immutable`
   field *is* readable via the API, and `scripts/release.ps1` uses it.

2. **It is incompatible with the current "upload to the current tag" habit.**
   TOKN's standing release rule has been to rebuild and re-upload assets to the
   existing tag with `gh release upload --clobber`. Under immutability that is
   permanently rejected once a release is published — and deleting the release
   does **not** free the tag for reuse. Every shipment then requires a new
   version tag.

`scripts/release.ps1` has been made immutability-aware ahead of the switch:

- It reads the release's `immutable` field and **refuses to upload** to a
  published immutable release, explaining that a new tag is required. This check
  runs *before* any asset is transferred, because the failure it prevents is a
  partial upload — under immutability, a release that got three of five binaries
  cannot be repaired, only abandoned.
- `-Draft` creates the release as a draft, so all assets are attached before
  anything is visible or frozen; `-Publish` then publishes it. Draft-first is the
  only correct order under immutability, and is an improvement without it.
- After upload it verifies every expected asset is actually present on the
  release before publishing, because `gh release upload` has been observed to
  exit zero having skipped a file.

Recommended flow once immutability is on:

```powershell
git tag vX.Y.Z && git push origin vX.Y.Z
./scripts/release.ps1 -Version X.Y.Z -Upload -Draft -Publish
```

## Reporting a problem with these documents

If a control described here does not behave as written, that is itself a
security defect — the documentation is part of the trust chain. Report it the
same way as a vulnerability, via [`../../SECURITY.md`](../../SECURITY.md).
