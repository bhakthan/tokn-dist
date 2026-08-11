# Supply Chain Security

Status: **Effective from the next release after this workflow merges.** Already-published assets pre-dating this workflow carry ed25519 signatures but NOT Sigstore attestations.

---

## Overview

TOKN ships via two channels:

| Channel | Repository | Audience |
|---------|-----------|----------|
| Public  | `bhakthan/tokn-dist` | General users |
| Private | `bhakthan/tokn` | Source-access users (includes embedded wiki) |

Both channels receive identical supply-chain protections.

---

## Current Limitation: CI-Built vs. Production Binaries

> **The artifacts users download today are NOT covered by build provenance.**

Production releases are currently built on the release engineer's Windows workstation via `scripts/release.ps1`, which injects secrets (registration URL, trial HMAC seed, ed25519 signing key, release public key) that are not available in CI. The supply-chain workflow builds binaries **in CI** and attests those — proving the source→binary mapping is reproducible — but these CI-built artifacts are not byte-identical to the production binaries because:

1. Production binaries carry `registration.EndpointURL`, `licensing.TrialSeed`, and `updater.ReleaseSigPubKey` via ldflags. CI binaries may have these empty unless the corresponding GitHub secrets are configured.
2. Build timestamps differ (Go embeds `main.buildDate`).

**What this means for users:** If you run `gh attestation verify` on a binary downloaded from `bhakthan/tokn-dist`, it will **not** match — because that binary was built locally, not by this workflow. Attestation applies only to CI-built artifacts uploaded as workflow artifacts.

**Path to full coverage:** When releases are cut entirely from CI (with all secrets wired via GitHub encrypted secrets), the CI-built artifacts become the production artifacts, and provenance covers what users actually download. Until then, rely on the ed25519 `SHA256SUMS.sig` for download verification.

---

## Known Blockers: Why Attestation Is Not Effective Yet

Three independent issues combine to make attestation unverifiable by public users today. Each alone would be survivable; together they mean **`gh attestation verify` cannot succeed for any user downloading from the public channel.**

### 1. Private repository requires GitHub Enterprise Cloud

From the [`actions/attest` README](https://github.com/actions/attest):

> Artifact attestations are available in public repositories for all current GitHub plans.  
> To use artifact attestations in private or internal repositories, you must be on a GitHub Enterprise Cloud plan.

`bhakthan/tokn` is private. Unless the account is on GHEC, the attestation steps will fail at runtime with an error that does not mention plan limitations — it will look like an API permission error, not a billing issue.

**If the account IS on GHEC:** Attestation creation succeeds, but points 2 and 3 below still apply.

### 2. Attestations are stored against `bhakthan/tokn` (private)

`actions/attest` records attestations against the repository where the workflow runs. This workflow runs in `bhakthan/tokn`. Therefore all attestations — for both public and private variant binaries — are stored there.

### 3. Public users cannot verify against a private repo

Users download from `bhakthan/tokn-dist` (public). To verify, they must run:

```bash
gh attestation verify tokn_darwin_arm64 --repo bhakthan/tokn
```

But `bhakthan/tokn` is private. A user without read access to that repository **cannot query its attestation store.** The verify command will fail with a 404 or permission error — indistinguishable from "this binary has no attestation" or "this binary was tampered with."

This is the worst outcome: a user following correct verification procedure gets a failure that looks like evidence of compromise, when it is actually an access control issue.

### Resolution path

Provenance must be produced by a workflow running in the **public** repository that users actually download from. Specifically:

1. **Move the release build to a workflow in `bhakthan/tokn-dist`** (or a public repo the user can read). Public-good Sigstore applies automatically to public repos (no GHEC needed), and `gh attestation verify --repo bhakthan/tokn-dist` is runnable by anyone.
2. **Alternatively**, if releases remain in the private repo: make `bhakthan/tokn-dist` a mirror that runs its own attestation workflow, or publish attestation bundles as release assets that can be verified offline.

This is a **maintainer decision** about where release builds live. It is not solved by this workflow and cannot be solved without changing the release architecture.

### What to do today

Until these blockers are resolved:

- **Do not tell users to run `gh attestation verify`.** It will fail and cause alarm.
- **Rely on the ed25519 `SHA256SUMS.sig`** for download verification — it works offline, requires no GitHub access, and covers the actual production binaries.
- The supply-chain workflow still provides value: it proves source→binary reproducibility in CI, runs vulnerability scanning, and generates SBOMs. These functions work regardless of the attestation storage issue.

---

## What Provenance Proves (and Does Not)

SLSA build provenance attestations prove:

- **This artifact was produced by this workflow, at this commit, in this repository.**
- The build was not tampered with after it left GitHub Actions.

Provenance does **not** prove:

- The source code is free of backdoors or logic bombs.
- The build environment itself was not compromised (though GitHub's hosted runners are ephemeral and isolated).
- The artifact is fit for any particular purpose.

Provenance is a chain-of-custody record, not a code audit.

---

## Verification Commands

Attestations are stored against the repository where the workflow runs (`bhakthan/tokn`). Both variant attestations (public and private) are stored there.

```bash
# Verify provenance of a CI-built artifact (both variants attest to bhakthan/tokn)
gh attestation verify tokn_darwin_arm64 --repo bhakthan/tokn
```

> **Note:** This will NOT succeed for production binaries downloaded from releases (see "Current Limitation" above). It only verifies CI-built artifacts from this workflow.

### Verify SBOM attestation

```bash
gh attestation verify tokn_linux_amd64 --repo bhakthan/tokn \
  --predicate-type https://spdx.dev/Document
```

---

## Software Bill of Materials (SBOM)

Each release publishes two SBOM formats per variant:

- **SPDX** (`sbom-{public,private}.spdx.json`) — broad ecosystem compatibility.
- **CycloneDX** (`sbom-{public,private}.cdx.json`) — VEX and dependency-track integration.

### Why Syft over cyclonedx-gomod?

Both are valid choices. We use [Anchore Syft](https://github.com/anchore/syft) because:

1. It scans the **built binary** (reads Go's embedded build info), not just `go.mod`. The SBOM describes what shipped, not what was in the repo.
2. It emits both SPDX and CycloneDX from a single tool invocation.
3. It would detect non-Go dependencies if any were bundled (the private variant embeds a ~64 MB MkDocs site).

`cyclonedx-gomod` reads the Go module graph (accurate for Go deps, blind to everything else). For a pure-Go binary the two overlap heavily, but Syft's broader lens is the right default for supply-chain transparency.

### Both variants are covered

The private variant embeds the MkDocs documentation site; its binary composition differs from public. Both get independent SBOMs.

### Reading the SBOM

```bash
# Download from workflow artifacts or release
# Pretty-print with jq
jq '.components[] | {name, version}' sbom-public.cdx.json

# Feed to vulnerability scanner
grype sbom:sbom-public.cdx.json
```

---

## Vulnerability Response Policy

### govulncheck — reachability-aware (enforced gate)

[govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) performs call-graph analysis: it reports a CVE only if the vulnerable function is actually reachable from TOKN's code. A finding here means the vulnerability is genuinely exploitable in this binary.

**Policy: The pipeline fails if govulncheck reports any reachable vulnerability.**

### Grype — version-match breadth scan (informational)

[Grype](https://github.com/anchore/grype) scans the SBOM for all known CVEs by version number. Most findings are in unreachable code paths of transitive dependencies.

**Policy: Grype results are published to GitHub Code Scanning (SARIF) and as workflow artifacts. They do NOT block the pipeline.**

**Rationale:** A hard fail on any transitive-dep CVE makes releases hostage to unrelated upstreams. Teams respond by disabling the gate — which is strictly worse than an informational report that is always visible. The reachability gate (govulncheck) is the load-bearing control; grype provides defense-in-depth visibility.

### Scheduled re-scanning

A weekly cron run (`0 7 * * 1` UTC) re-scans the source against fresh vulnerability databases. A CVE disclosed after release still matters — the scheduled run catches it.

---

## Layering With ed25519 Signatures

TOKN releases carry **both** Sigstore attestations (CI-built) and an ed25519 `SHA256SUMS.sig` (production):

| Property | ed25519 `SHA256SUMS.sig` | Sigstore attestation |
|----------|--------------------------|---------------------|
| Covers production binaries | ✅ Yes | ❌ CI-built only (until releases move to CI) |
| Verifiable offline | ✅ Yes | ❌ Requires network + Sigstore infrastructure |
| Trust anchor | Key controlled by TOKN maintainer | GitHub's OIDC + Sigstore CA |
| Proves | Integrity + authenticity (if you trust the key) | Provenance (workflow → commit → artifact) |
| Survives GitHub outage | ✅ | ❌ |
| Survives key compromise | ❌ | ✅ (key is ephemeral per-signing) |

They are **complementary, not redundant**:

- The ed25519 signature lets `tokn update` verify downloads fully offline with a key compiled into the binary.
- The Sigstore attestation lets third parties (and future auditors) verify provenance without trusting a single long-lived key.

---

## Required GitHub Secrets

The workflow uses `${{ github.token }}` (automatic) for all operations within the `bhakthan/tokn` repository. No PAT is required because the workflow runs in and attests against the same repository.

For full production-equivalent builds, configure these **optional** repository secrets:

| Secret | Purpose | Impact if absent |
|--------|---------|-----------------|
| `REGISTRATION_URL` | Compiled into binary for install registration | Binary registration is a no-op |
| `FEEDBACK_URL` | Compiled into binary for feedback delivery | Feedback queues to local outbox |
| `RELEASE_SIG_PUBKEY` | Embedded for `tokn update` signature verification | Updater cannot verify authenticity |
| `TRIAL_SEED` | HMAC seed for trial license validation | Trials from other builds won't verify |
| `RELEASE_PUB_KEY` | Public key for paid license verification | Community-only build |

The workflow emits a warning annotation when secrets are absent but does not fail — the CI-built binary is still a valid attestation subject for proving source→binary reproducibility.

---

## Action Pinning

Third-party actions are pinned to major version tags (e.g. `@v4`, `@v6`). Pinning to full commit SHAs is the stronger practice because tags are mutable — a compromised action maintainer can retag a SHA. However, we do not pin to SHAs we cannot independently verify at authoring time. The workflow documents this trade-off.

---

## Build Reproducibility Note

The CI build uses `-trimpath` to avoid embedding absolute runner paths into the binary. Without `-trimpath`, builds embed paths like `/home/runner/work/tokn/tokn/...` which:
- Leak CI infrastructure details
- Make byte-for-byte reproducibility impossible across different build environments

Full reproducibility (identical bytes from identical source) is not yet achieved because Go embeds build timestamps. This is a known limitation.

---

## Divergence Note: GoReleaser in `release.yml`

The existing `.github/workflows/release.yml` runs GoReleaser (`goreleaser/goreleaser-action@v6`) as an additional, **divergent** build path alongside the authoritative `scripts/release.ps1`. The two paths produce binaries with different ldflags (GoReleaser omits the registration/feedback endpoints). This supply-chain workflow's CI build mirrors `release.ps1`'s structure, not GoReleaser. Reconciling or removing the GoReleaser path is outside scope but noted here for transparency.

---

## What Is Not Yet Covered

- **Production binary attestation**: Until releases are cut from CI, downloaded binaries are not provenance-covered (see "Current Limitation").
- **Container images**: TOKN does not currently publish container images. If added, they should receive both provenance and SBOM attestation.
- **SLSA Level 3+**: Achieving SLSA L3 requires a hermetic build environment. GitHub-hosted runners satisfy L2 but not L3.
- **Cross-repo attestation for `tokn-dist`**: Attestations are stored in `bhakthan/tokn`. Users who download from `bhakthan/tokn-dist` must verify against `bhakthan/tokn`. A future improvement could run a mirrored workflow in `tokn-dist` or use `gh attestation verify --owner bhakthan`.

