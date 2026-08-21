# Key Management

This document covers the cryptographic keys used in TOKN's release and licensing infrastructure: their purpose, current storage, risks, and hardening path.

## Keys in Use

| Key | Algorithm | Purpose | Location |
|-----|-----------|---------|----------|
| **Release signing key** | Ed25519 | Signs `SHA256SUMS` manifests so `tokn update` can verify authenticity | `~/.tokn-release/signing.key` (private), `signing.key.pub` (public) |
| **Trial HMAC seed** | HMAC-SHA256 seed | Derives trial license tokens; ships inside every binary by design, so it is a stability requirement rather than a secret — it must be identical across releases or existing trials stop verifying | `~/.tokn-release/trial-seed.txt` |
| **License signing key** | Ed25519 | Signs paid (`pro` / `enterprise`) licenses. The private half is never distributed and never enters a build; only the public half is compiled in. **Not yet active** — no released binary embeds a license public key, so paid tiers are unreachable on published builds | private half offline; public half at `~/.tokn-release/release-key.pub` |
| **Apple Developer ID** (forward-looking) | RSA 2048 (Apple-issued) | macOS code signing, notarization, Gatekeeper | Apple Developer account; see [macos-code-signing.md](macos-code-signing.md) |

## Release Signing Key

### What it protects

The ed25519 release signing key is the **single credential that determines whether `tokn update` trusts a binary**. Every release build has the corresponding public key compiled in (`releaseSigPubKeyB64` via `-ldflags`). The updater:

1. Downloads `SHA256SUMS` and `SHA256SUMS.sig` from the release.
2. Verifies the signature over `SHA256SUMS` using the compiled-in public key.
3. Refuses to install if verification fails (no bypass exists).

Source: `environment-manager/internal/agent/commands/update_verify.go`.

### Current public key

```
Public key (base64, ed25519): 3O2DznsYRy+OU2gTIbpvOfw0O6tUIIRQfiOUDbfoHxo=

SHA-256 fingerprint of the raw 32-byte public key:
  364e425ec887eb4b13e0c83927679f603608eab679c893fd3f8e508a22c7d14a
```

### Current storage model

The private key resides at `~/.tokn-release/signing.key` on the release engineer's workstation, with file permissions `0600`. It is never committed to the repository. The release script (`scripts/release.ps1`) reads it from this path (or a `-ReleaseSignKey` parameter) at build time.

**This is the weakest link in the current supply chain.** A signing key on a general-purpose workstation is exposed to:

- Malware or infostealer on the workstation
- Credential theft (e.g., if the home directory is backed up to a compromised cloud service)
- Physical access
- Any process running as the same user

There is no passphrase protection, no hardware binding, and no access logging today.

### Hardening roadmap

Three options, in order of increasing security:

#### Option A: Hardware token (YubiKey)

| Aspect | Detail |
|--------|--------|
| **How** | Store the ed25519 private key on a YubiKey (FIDO2/PIV applet) or similar hardware token. Signing requires physical touch. |
| **Tradeoff** | Low cost (~$50); key is non-exportable after generation; physical presence required for every release. |
| **Limitation** | YubiKey PIV supports RSA and P-256/P-384 but not raw ed25519. Would require either: (a) switching to ed25519-sk (SSH-format, supported by YubiKey 5+), or (b) using the YubiKey as a passphrase-unlocking mechanism for a software key. |
| **Residual risk** | Lost/stolen token + no backup = permanently lost key. Mitigate with a second enrolled token in a secure location. |

#### Option B: Cloud HSM / KMS

| Aspect | Detail |
|--------|--------|
| **How** | Generate the key inside Azure Key Vault, GCP KMS, or AWS KMS. The private key is non-exportable; signing is an API call authenticated by the release engineer's cloud identity. |
| **Tradeoff** | Key never exists in extractable form. Full audit trail. Access controlled by IAM policies. Monthly cost ~$1–5. |
| **Limitation** | Azure Key Vault supports ed25519 (as of 2024). GCP/AWS KMS do not natively support ed25519 — would require P-256 + signature scheme change, or a custom CloudHSM partition. Adds a cloud dependency to the release process. |
| **Residual risk** | Cloud account compromise → signing access (but not key extraction). Mitigate with MFA, conditional access, and approval workflows. |

#### Option C: GitHub Actions OIDC-based signing

| Aspect | Detail |
|--------|--------|
| **How** | Move signing into a GitHub Actions workflow. The workflow authenticates to a KMS via OIDC (no long-lived secret). The private key never leaves the KMS. |
| **Tradeoff** | Removes the workstation from the trust path entirely. Signing is tied to a specific repo/branch/workflow via OIDC claims. Full audit trail in Actions logs. |
| **Limitation** | Requires restructuring the release process from local `scripts/release.ps1` to a CI/CD pipeline. Increases complexity and adds GitHub Actions as a trust dependency. |
| **Residual risk** | Workflow injection (compromised action, malicious PR modifying the workflow file). Mitigate with branch protection, required reviews on workflow changes, and pinned action SHAs. |

### Recommendation

Option B (Cloud KMS) or Option C (Actions OIDC + KMS) are the strongest choices. Option A is a meaningful improvement over the status quo with minimal infrastructure change. Any of the three is strictly better than the current model.

## Fingerprint Publication

The release signing public key is compiled into every shipped binary. However, if the repository itself is compromised, the attacker controls the copy of the public key that users would compare against. **Out-of-band publication of the fingerprint is what makes independent verification meaningful.**

Current fingerprint:
```
364e425ec887eb4b13e0c83927679f603608eab679c893fd3f8e508a22c7d14a
```

### Recommended publication channels

At minimum two independent channels that an attacker would need to compromise separately:

1. **This document** (committed to source control) — compromised if the repo is compromised.
2. **A signed Git tag annotation** — survives force-push if the verifier has a local clone from before the compromise.
3. **A pinned post / about section on a social media account** controlled by the maintainer — independent of GitHub.
4. **DNS TXT record** on a domain controlled by the maintainer — requires domain registrar compromise to alter.

The current fingerprint is published in this document and is embedded in the `docs/security/README.md` (umbrella-owned). Additional out-of-band channels are recommended but not yet established.

## Trial HMAC Seed

The trial seed (`~/.tokn-release/trial-seed.txt`) is used to derive trial license tokens. It must be **identical across all releases** — if it changes, every trial issued by a prior release stops verifying, which appears to users as "my trial expired for no reason."

`scripts/release.ps1` prints an explicit warning when this occurs: "TRIALS ISSUED BY PREVIOUS RELEASES WILL STOP VERIFYING".

### Risk

The seed is **compiled into every released binary** and is therefore recoverable
by anyone holding a copy of the software. This is not a storage weakness to be
fixed; it is a direct consequence of TOKN verifying licenses fully offline, with
no phone-home. A symmetric seed that must verify signatures inside the user's
own process cannot also be secret from that user.

The correct conclusion is not "protect the seed harder" but "do not rely on it
for anything that matters". Trial signing resists accident and casual tampering;
it is not an anti-piracy control. See
[threat-model.md](threat-model.md#trial-licensing-is-not-a-security-control).

Two properties do **not** depend on the seed staying secret, and both are
enforced at verification time:

- an `hmac-sha256` signature may authorize **only** the `trial` tier — paid
  tiers require an ed25519 signature from an offline key that is never
  distributed;
- the maximum trial term is checked when a license is verified, not only when it
  is issued.

### Mitigation

- Treat the seed as a **build input that must stay stable**, not as a
  confidentiality boundary. Its real operational risk is *changing* it, which
  silently invalidates trials issued by prior releases.
- Because it must be available to the build, it cannot move to a non-exportable
  HSM — and there is no security benefit in trying, since the value ships anyway.
- Do not co-locate it with the release signing key in tooling or in reasoning:
  the signing key is genuinely secret and genuinely high-impact, and grouping a
  non-secret alongside it erodes the handling discipline the signing key needs.
- The seed is never sent over the network by the built binary; it is used purely
  for local HMAC computation.
- If TOKN later requires trials that resist a determined user, the fix is
  server-side issuance, not a better hiding place.

## Key Rotation

### Why rotation is painful

The ed25519 public key is compiled into every shipped binary. Already-shipped binaries embed the *old* public key and will **reject any release signed by a new key**. This means:

1. Users on the old binary cannot `tokn update` to a release signed by the new key — the signature verification fails.
2. There is no automatic migration path: the user must manually download the new binary (which embeds the new key).

Source: `update_verify.go` — `releaseSigPubKeyB64` is a var set by the linker; the verification logic has no concept of key rotation, key lists, or trust-on-first-use.

### Rotation procedure (if needed)

1. Generate a new keypair: `go run ./environment-manager/cmd/releasesign -genkey -out new-release-key`
2. Build a **transition release** signed with the OLD key that contains the NEW public key compiled in.
3. Users who update to the transition release now have the new key embedded.
4. Subsequent releases are signed with the new key.
5. Users who skipped the transition release must manually download.

### Compromise response

If the signing key is believed compromised:

1. **Immediately revoke the key** — remove from the workstation, rotate any backup.
2. **Notify users** via every available channel that the key is compromised and updates should not be trusted until a new key is published.
3. **Publish the new fingerprint** on out-of-band channels.
4. **Issue a transition release** (step 2 above). Users must manually verify this release by fingerprint before trusting it.
5. **Audit release history** — determine whether any malicious release was published and which versions are affected.

The most dangerous window is between compromise and detection. During this window, the attacker can publish a signed malicious update that will be accepted by every user's `tokn update`. There is no revocation mechanism for already-accepted updates short of the user noticing aberrant behavior.

## Cross-references

- [Update Process](update-process.md) — how the key is used at update time
- [Threat Model](threat-model.md) — signing key compromise as a threat
- [Supply Chain](supply-chain.md) — build provenance attestation as a complementary verification layer
- [macOS Code Signing](macos-code-signing.md) — the Apple Developer ID certificate (separate key, separate purpose)
