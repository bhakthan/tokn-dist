# Decisions pending: Apple, immutability, provenance

Three items in [`README.md`](README.md)'s control table are blocked on a choice
rather than on engineering. This document makes a recommendation on each, states
the cost, and says what happens if you do nothing.

Read the recommendations first. The detail is there to justify them, not to make
you weigh everything yourself.

| Decision | Recommendation | Cost | Urgency |
|---|---|---|---|
| Apple Developer Program | **Enrol as Individual** | $99/yr, ~1–2 days | Medium — affects every macOS user today |
| Immutable releases | **Enable on `tokn-dist` only, for now** | Free, ~2 minutes | Low, but do it before adoption grows |
| Build provenance | **Do not pursue it yet. Harden the signing key instead** | $50–70 one-off | This is the one that matters most |

---

## 1. Apple Developer Program

### What to do

Enrol as an **Individual**, not an Organization.

1. Go to <https://developer.apple.com/programs/enroll/>.
2. Sign in with an Apple ID that has two-factor authentication enabled.
3. Choose **Individual / Sole Proprietor**.
4. Pay $99 USD (annual).
5. Wait for approval — typically 24–48 hours.

Then, in Xcode or the developer portal, create **two** certificates:

- **Developer ID Application** — signs the binaries.
- **Developer ID Installer** — signs the `.pkg`.

And create an **App Store Connect API key** (Users and Access → Integrations →
Keys) for notarization from CI. Prefer this over an Apple ID app-specific
password: it is revocable, scopable, and does not put an account password into
an environment variable.

Once you have those, everything else is already built. Run:

```bash
export APPLE_SIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export APPLE_INSTALLER_IDENTITY="Developer ID Installer: Your Name (TEAMID)"
export APPLE_TEAM_ID="TEAMID"
export APPLE_API_KEY_ID="..." APPLE_API_ISSUER_ID="..." APPLE_API_KEY_PATH=/path/to/AuthKey.p8

./scripts/macos-sign-notarize.sh --version 0.3.1
```

### Why Individual rather than Organization

Organization enrolment requires a **D-U-N-S number** from Dun & Bradstreet.
Obtaining one takes 2–4 weeks and requires a registered legal entity. That is a
long block for a control you need now.

The real tradeoff, stated plainly: an Individual certificate shows **your
personal name** in the signature, not a company name. Users running
`codesign -dv` will see it, and it appears in some Gatekeeper prompts. If TOKN is
later commercialised under a company, you can enrol that entity separately and
re-sign; certificates are not tied to the binaries retroactively, and
**notarized builds keep working after a certificate expires** because the
notarization ticket is independently timestamped. So this is reversible.

### What happens if you do nothing

macOS users continue to hit a Gatekeeper block. They can still install — `tokn
setup` prints the steps — but they must run `xattr -d com.apple.quarantine`,
which is a bad thing to train users to do reflexively.

This session improved that path: `tokn setup` on macOS now puts **checksum
verification before** the quarantine strip and explains that the strip is needed
because TOKN is not yet notarized. Previously the install steps came first and
verification was a muted footnote, which taught the wrong order.

That is mitigation, not a fix. Notarization is the fix.

---

## 2. Immutable releases — exact UI steps

There is no API for this. From GitHub's documentation:

1. Navigate to the repository on GitHub.
2. Under the repository name, click the **⚙ Settings** tab. (If you cannot see
   it, use the **…** dropdown, then **Settings**.)
3. Scroll to the **Releases** section.
4. Select **Enable release immutability**.

Repeat for each repository. It can also be enforced org-wide from the
organization's Settings page.

**Immutability applies only to future releases.** The existing `v0.3.1` stays
mutable, so nothing you have already published breaks.

### Recommendation: enable on `bhakthan/tokn-dist` first

`tokn-dist` is the public download channel — the one an attacker would target and
the one where the guarantee is worth something to users. Enable it there.

Hold off on `bhakthan/tokn` (the private source repo) until the release habit has
adjusted, because that is where the friction lands.

### The friction, so it is not a surprise

Once enabled, this stops working:

```powershell
# rebuild and re-upload to the current tag  -- NO LONGER POSSIBLE
gh release upload v0.3.1 ... --clobber
```

Every shipment then needs a **new version tag**. Deleting a release does *not*
free the tag for reuse, so there is no undo.

`scripts/release.ps1` was already updated for this. It refuses to upload to a
published immutable release *before transferring any bytes* — the dangerous case
is not a rejected upload but a **partial** one, where three of five binaries land
on a release that can then only be abandoned. Use:

```powershell
git tag v0.3.2 && git push origin v0.3.2
./scripts/release.ps1 -Version 0.3.2 -Upload -Draft -Publish
```

`-Draft` attaches every asset before anything is visible or frozen; `-Publish`
then publishes. This ordering is better even without immutability, because users
never see a half-populated release.

---

## 3. Build provenance — recommendation: **do not pursue it yet**

This is the one where the honest answer is not "here is how to do it."

### Why it does not currently work

Three facts compound:

1. Releases are built on a workstation by `scripts/release.ps1`, so there is no
   CI build to attest. Provenance is a claim that *a specific workflow produced
   these exact bytes*; it cannot be added to a local build afterwards.
2. Artifact attestations are free in public repositories but require **GitHub
   Enterprise Cloud** in private ones. `bhakthan/tokn` is private.
3. Attestations are stored against the repository that *runs* the workflow.
   Users download from public `tokn-dist` but would have to verify against
   private `tokn` — **a repository they cannot read.**

Point 3 is the killer. Even if you bought GHEC, public users still could not
verify. Buying GHEC to fix this would be spending money on a control that remains
unusable by the people it is meant to protect.

### The options, and why each falls short

| Option | Verdict |
|---|---|
| Buy GitHub Enterprise Cloud | **No.** Fixes point 2 only; point 3 still blocks public verification |
| Make `bhakthan/tokn` public | Works completely, but forfeits the closed source. A product decision, not a security one |
| Build in a workflow inside public `tokn-dist`, checking out the private source | Technically works. **But** it puts private source on a public repository's runners; a malicious pull request could exfiltrate it. Requires strict trigger hygiene and is a real new risk |
| Keep the ed25519 signature as the trust anchor | **Recommended** |

### Why deferring is defensible rather than lazy

TOKN already has a working signature chain, and this session verified it
end-to-end against the live release: the published `SHA256SUMS` verifies under
the published key, a wrong key is rejected, and a tampered manifest is rejected.

For a closed-source product, that ed25519 signature delivers most of what
provenance would, and in one respect delivers **more**: it verifies fully offline
against a key TOKN controls, with no dependency on GitHub, Sigstore, or network
availability. Attestation would add a public transparency-log entry and a
workflow-and-commit binding — genuinely valuable for an open-source project where
users can audit the source those commits refer to, and much less so when the
source is private.

So the marginal gain here is small, the architectural cost is high, and the
options each carry a real downside.

### What to do instead — and this is the actual priority

**Get the signing key off the general-purpose workstation.**

That key is the single point whose compromise means remote code execution on
every TOKN user, via an update they were right to trust. It currently lives as a
file in `~/.tokn-release/`. No amount of provenance tooling compensates for that,
and fixing it is cheap:

- A **YubiKey** ($50–70) holding the signing key non-exportably, or
- **Azure Key Vault / GCP KMS / AWS KMS**, with signing performed by the service
  so the private key never exists on disk.

[`key-management.md`](key-management.md) has the detail and the rotation
considerations — note in particular that rotation is genuinely painful, because
already-shipped binaries embed the *old* public key and will reject anything
signed by a new one. That is precisely why the key must not leak in the first
place.

Second priority: publish the key fingerprint on a channel that is **not** under
the same GitHub account. Both current copies share one trust root, so a single
account compromise rewrites both — see the fingerprint table in
[`README.md`](README.md).

### Revisit provenance when

- `bhakthan/tokn` goes public, **or**
- releases move into CI for other reasons, **or**
- a customer contractually requires SLSA attestation.

Until one of those is true, `.github/workflows/supply-chain.yml` still earns its
place: the **SBOM generation and vulnerability scanning jobs work today** and do
not depend on attestation.

Making that true required a fix during this session. The three `actions/attest@v4`
steps were unguarded, and the jobs run in a chain
(`build-and-attest` → `sbom` → `vulnscan`) linked by `needs:`. Because a failed
step fails its job, and a failed job skips everything downstream, the blocked
attestation would have taken down the two jobs that *do* work — the workflow
would have delivered nothing on its first run.

Attestation is now opt-in behind a repository variable. To enable it once the
blockers above are resolved, set `ENABLE_ATTESTATION=true` in
*Settings → Secrets and variables → Actions → Variables*. With it unset, the
workflow logs a notice explaining the skip and continues, so SBOMs and
vulnerability scans are still produced.
