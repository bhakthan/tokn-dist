# Programmable molecular design: one reviewed program, two admitted models

This worked operator walkthrough exercises **TOKN v0.3.127+**'s
`tokn biomol program` contract. It is an advanced handoff, not a demo model:
TOKN takes a typed synthetic calibration backbone, admits one ProteinMPNN
inverse-folding stage, verifies that stage's sampled sequence, and then admits
a separate Boltz-2 prediction of that exact sequence.

The files in this directory contain **no biological target, real sequence,
signature, model weight, endpoint, key or private path**. The supplied backbone
coordinates are a fictional eight-residue geometry used to explain the typed
workflow and the distance-matrix comparison. They are not a validated protein
structure and must not be interpreted as a binder, drug, therapeutic, foldable
design or laboratory instruction.

You need:

- TOKN v0.3.127 or newer;
- a local Linux amd64 Docker/NVIDIA host for real `apply` commands;
- a separate, complete ProteinMPNN staging area and complete Boltz-2 staging
  area, with reviewed manifests, images, weights, data terms and reviewer key;
- an authorized external reviewer who can inspect private state and sign exact
  admission bytes offline.

The `init`, `prepare` and `status` commands do not call a model. Real `apply`
calls `Service.Run` and therefore requires the existing model adapters'
dependencies, policy, signatures and external review. On Windows, `program`
refuses private-state operations rather than guessing at effective ACLs.
macOS can prepare private state but cannot perform the Linux GPU run.

## 1. Read the program before provisioning anything

`program-spec.json` is deliberately explicit:

- eight sequential canonical residues;
- the four backbone atoms `N`, `CA`, `C`, `O` for every residue;
- a reviewed positive ProteinMPNN seed;
- exactly two model jobs;
- a run-time budget that must cover both configured adapter timeouts.

The sequence is not supplied as an input. It is produced later by ProteinMPNN.
The program has no loop, model selector, shell, arbitrary URL, target, motif,
hotspot, sequence override or inline code field.

Inspect the interfaces without loading any model:

```text
tokn version
tokn biomol catalog
tokn biomol program --help
tokn biomol program init --help
tokn biomol program prepare --help
tokn biomol program apply --help
tokn biomol program status --help
```

Validate the public JSON templates locally if Python is available:

```powershell
Get-ChildItem .\*.json | ForEach-Object {
    python -m json.tool $_.FullName *> $null
    if ($LASTEXITCODE -ne 0) { throw "Invalid JSON: $($_.Name)" }
}
```

## 2. Stage two disjoint configurations

Copy these templates outside the repository and replace every placeholder:

- `proteinmpnn-config.template.json`: adapter `proteinmpnn`, policy
  `external-review-design-v1`, a fixed model-ready source/image/cache,
  selected GPU UUID, external design reviewer public key and complete
  manifests;
- `boltz2-config.template.json`: omitted selector for the existing legacy
  Boltz-2 profile, policy `external-review-v1`, and a separate private
  output/scratch root;
- `bindings.template.json`: the two exact absolute config paths.

The configs must be distinct. Their source, weight, output and scratch roots
must not overlap; neither config path may sit inside the other config's
runtime roots. TOKN pins effective config digests and refuses later changes.
No endpoint, API key, model-provider account or network fallback is used by the
program.

For Linux operators, keep each config mode 600, every ancestor controlled by
root or the current operator, and state/output roots mode 700. Keep
`program-spec.json` private if the actual coordinates are confidential. This
public copy is synthetic.

## 3. Initialize immutable private state

Choose a state path that does not exist under an existing private parent:

```sh
tokn biomol program init \
  --spec /absolute/private/program-spec.json \
  --bindings /absolute/private/bindings.json \
  --state /absolute/private/tokn-program-state
```

`init` is read-only with respect to the models: it validates the closed schema,
typed backbone, profile selectors and budget, creates a random program
instance, and writes an initial `program.json`. It does not create an approval,
download an asset or run a model.

Expected first status:

```json
{
  "schema": "tokn-biomol-program-v1",
  "action": "init",
  "stage": "design",
  "outcome": "awaiting_design_review",
  "model_jobs_used": 0,
  "model_jobs_remaining": 2,
  "run_seconds_reserved": 7200,
  "run_seconds_remaining": 7200,
  "acceptance": "held_unvalidated",
  "parity": "not_verified",
  "provenance": "computational_unvalidated"
}
```

## 4. Review and approve ProteinMPNN — stage one

Start from `review-design.template.json`. Replace only the externally reviewed
evidence values and expiry:

- `operator_assertion` names the private reviewer assertion;
- `operator_evidence` is the SHA-256 of retained operator-identity evidence;
- `target_evidence` is the SHA-256 of retained review evidence;
- `purpose` is a human explanation of at least eight characters;
- `design_authority` is the externally retained design-authorization evidence;
- `no_hard_exclusion: true` and `uncertainty: "none"` are reviewer assertions,
  not TOKN conclusions.

Then prepare:

```sh
tokn biomol program prepare \
  --state /absolute/private/tokn-program-state \
  --review /absolute/private/review-design.json \
  > /absolute/private/design-challenge.json
```

`prepare` makes no model call. It writes a private
`design.prepared.json` containing:

- the exact canonical model request;
- the 32-hex one-use request ID;
- the complete challenge and digest;
- the pinned config path/digest;
- the program instance/spec binding;
- the operator review.

The public command prints only the digest-bearing admission challenge. The
authorized reviewer must inspect the private prepared record as well. For the
ProteinMPNN v2 policy, the challenge binds adapter, capability, policy domain,
model/profile, source/image/manifests, fixed argv/environment, GPU identity,
config digest, generated PDB digest, timeout/resources and review.

Sign the exact `signing_bytes` value with the configured **external**
Ed25519 reviewer key. Do not sign the surrounding JSON, a reserialized
challenge, the public status view or a copied request. TOKN has no private key
and cannot manufacture an approval.

One prescriptive external-review handoff is:

```powershell
# Run outside TOKN, in the reviewer's approved signing environment.
Get-Command openssl -ErrorAction Stop
$challenge = Get-Content -Raw /absolute/private/design-challenge.json |
    ConvertFrom-Json
$encoding = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText(
    "/absolute/private/design-signing-bytes.txt",
    [string]$challenge.challenge.signing_bytes,
    $encoding
)
openssl pkeyutl -sign -rawin `
    -inkey /absolute/reviewer/ed25519-private.pem `
    -in /absolute/private/design-signing-bytes.txt `
    -out /absolute/private/design-signature.bin
$signature = [Convert]::ToBase64String(
    [IO.File]::ReadAllBytes("/absolute/private/design-signature.bin")
)
@{ signature = $signature } |
    ConvertTo-Json |
    Set-Content -NoNewline /absolute/private/design-signature.json
```

The private key never enters TOKN or the repository. Confirm that
`design-signing-bytes.txt` contains the exact UTF-8 `signing_bytes` without an
added final newline, and retain an approval record only according to the
reviewer's retention policy. Use the reviewer's approved equivalent if OpenSSL
or this command form is not accepted in that environment.

Put only the standard-base64 signature in a private file shaped by
`signature.template.json`, then apply:

```sh
tokn biomol program apply \
  --state /absolute/private/tokn-program-state \
  --signature /absolute/private/design-signature.json
```

Before launch, TOKN rechecks the effective config, expiry, revocation, signature,
preflight blockers and prepared challenge. It writes the immutable launch
record and then enters the existing ProteinMPNN `Service.Run`. A failed admission
does not consume a launch; an admitted indeterminate execution does.

`apply` returns after the model job completes. It verifies:

- the private receipt;
- terminal `Job` identity;
- exact model/config/request/argv/manifests;
- the expected `seqs_job.fa` artifact name, bytes and SHA-256;
- the native record and one sampled record;
- seed, fixed sample identity, canonical alphabet and backbone length.

Only the sampled record becomes the private predecessor for the next stage.
The native sequence is not silently substituted.

## 5. Review and approve Boltz-2 — stage two

After design succeeds, start a **different** review from
`review-predict.template.json`. Do not reuse the design signature and do not
copy `design_authority` into prediction; that capability belongs only to the
ProteinMPNN stage.

Prepare:

```sh
tokn biomol program prepare \
  --state /absolute/private/tokn-program-state \
  --review /absolute/private/review-predict.json \
  > /absolute/private/predict-challenge.json
```

Before producing this challenge, TOKN reopens the verified design job, receipt
and sampled FASTA, revalidates the exact private record and rebuilds the
historical design challenge. The new prediction request has:

- one chain `A`;
- the sampled ProteinMPNN sequence;
- mode `off`;
- seed `42`;
- one sample;
- three recycles;
- no Backbone, arbitrary selector or caller-supplied structure.

The signed request purpose visibly binds the canonical program specification
and predecessor request/challenge/artifact digests. The legacy Boltz-2 v1
challenge exposes `SHA256(request)` rather than expanding all those fields
into the public document. Its reviewer therefore inspects the private prepared
record, verifies the predecessor evidence and signs that exact hash-bearing
challenge.

Use the same exact-byte signing procedure for `predict-challenge.json`, writing
to a separate `predict-signature.json`. A valid design signature is expected to
fail over the prediction challenge because the effective request digest and
policy binding differ.

Sign and apply the prediction stage:

```sh
tokn biomol program apply \
  --state /absolute/private/tokn-program-state \
  --signature /absolute/private/predict-signature.json
tokn biomol program status \
  --state /absolute/private/tokn-program-state
```

The completed view exposes no sequence or coordinates. It contains the finite
stage/outcome, remaining reserved jobs/time, opaque job ID, exact
`held_unvalidated` / `not_verified` markers and the final finite
`geometry_rms_angstrom` metric.

## 6. Interpret the geometry check

The final CPU-only check reads `request_model_0.cif` from the exact terminal
Boltz-2 job and verifies its chain/residue/atom identity. It extracts C-alpha
coordinates, then computes the root mean square of pairwise C-alpha distance
differences against the supplied synthetic backbone.

This measure is invariant to translation, rotation and reflection. It does not
assess chirality, side chains, stereochemistry, physical validity, stability,
target engagement, binding, biological activity, safety, novelty or function.
`0.0 Å` would not prove that a molecular design is usable; synthetic fixture
tests do not validate ProteinMPNN or Boltz-2 on a GPU. No pass/fail threshold
is applied.

## 7. Demonstrate recovery without replay

After an admitted `apply` has written its launch marker, interrupt the CLI
or restart the host. Do not delete program files or service locks.

Run the same stage `apply` again with the **same signature file**:

```sh
tokn biomol program apply \
  --state /absolute/private/tokn-program-state \
  --signature /absolute/private/DESIGN_OR_PREDICT_SIGNATURE.json
```

TOKN requires the stored approval fingerprint to match, reads the one-use
receipt and reconciles the existing job. It does not call `Service.Run` for a
new job, prepare a new signature or fill in a successful result. If the receipt
is absent, the job is ambiguous, state is damaged or container termination is
unresolved, the stage remains indeterminate and the program tells you not to
invent a second launch.

For a model job that did start, use the existing opaque job ID with
`tokn biomol status` or `tokn biomol cancel` under that stage's config. Do not
remove `active.lock`, replay an approval, swap a config or rename output roots
to force progress.

## 8. Use the stopped path to teach the boundary

These negative checks are safe only against copies in a disposable private
directory:

1. Change one ProteinMPNN config hash after `init`; the next `prepare` must
   refuse administrator-config drift.
2. Put the design signature into the prediction `apply`; stage authority must
   refuse.
3. Tamper with the sampled sequence in `design.result.json`; `predict prepare`
   must fail receipt/artifact verification.
4. Change `program-spec.json` after init; sealed state must ignore the external
   file and continue to use its pinned declaration.
5. Repeat an admitted interrupted stage with a different signature encoding;
   recovery must reject the launch-signature mismatch.

Never use these mutations on production state. They illustrate fail-closed
behavior, not a supported repair procedure.

## 9. Clean up private state

After a completed or intentionally cancelled synthetic run, archive only what
your policy requires, then remove the explicit disposable state/config
directories. Real operator state may include review assertions, signatures,
sequences and artifact evidence; treat it as confidential.

Do not commit `state/`, `.nospace/`, `.tokn/`, configs, reviewer public/private
keys, signed approvals, logs or generated artifacts. The included `.gitignore`
defends against common mistakes.

## Templates in this directory

| File | Purpose |
|---|---|
| `program-spec.json` | Complete fictional typed backbone and fixed two-job budget |
| `bindings.template.json` | Exact two-config binding schema |
| `proteinmpnn-config.template.json` | Private administrator model/config fields |
| `boltz2-config.template.json` | Separate legacy prediction config fields |
| `review-design.template.json` | Stage-one external review with design authority |
| `review-predict.template.json` | Stage-two review without design authority |
| `signature.template.json` | Shape only; contains no valid approval |
| `.env.example` | No-secret startup controls; confirms no model endpoint is needed |

All execution remains experimental. Synthetic orchestration tests are not live
ProteinMPNN/Boltz-2 GPU evidence, and successful process completion does not
promote `held_unvalidated` or `not_verified`.
