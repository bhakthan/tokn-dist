# Release-key verification

The release public key lets you check the signature on `SHA256SUMS`.
**The public key is safe to share; a private key or licence file is not.**
You do not need signing credentials or source-code access to verify a download.

## Published release public key

```text
Algorithm: Ed25519
Public key (base64):
3O2DznsYRy+OU2gTIbpvOfw0O6tUIIRQfiOUDbfoHxo=

SHA-256 fingerprint of the raw 32-byte public key:
364e425ec887eb4b13e0c83927679f603608eab679c893fd3f8e508a22c7d14a
```

Use the [manual verification steps](../../README.md#2-verify-what-you-downloaded).
The signature covers the manifest; the manifest's checksum must then match
the binary you will execute.

```text
Trusted public key -> verify manifest signature
                               |
                               v
                      compare binary checksum
                               |
                               v
                      inspect and use download
```

## Trust is more than a matching checksum

A key and fingerprint fetched from the same compromised account as the binary
are not independent evidence. Where your risk level requires independent
verification, obtain a trusted reference through a separate authenticated
publisher channel. Two pages in this repository are not two independent
trust roots.

A valid signature does not establish that a program is bug-free. If a signing
key or publisher account is believed compromised, follow the publisher's
verified incident guidance rather than trusting a replacement key posted in
an unverified issue or message.

## If verification stops working

Do not disable verification, accept an unexpected fingerprint or edit the
signature to make a check pass. Record the version, platform and error,
then use the [private reporting route](../../SECURITY.md#reporting-a-vulnerability).
A legitimate key change needs authenticated publisher guidance; this page
does not promise automatic key migration.

## Licensing is separate

Release verification authenticates downloaded software. A licence controls
feature entitlement; it is not a sandbox, an approval for a model's result or
a data-protection boundary. Do not post licence material in issues or feedback.
