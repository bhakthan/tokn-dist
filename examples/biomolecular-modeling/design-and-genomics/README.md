# Design and genomic models: inspect before execution

These examples exercise TOKN's real catalog and disabled-runtime preflight.
They contain **no biological inputs, approvals or signatures** and need no GPU,
Docker, Python, weights, LLM key or paid model call.
Requires **TOKN v0.3.70 or newer**; confirm the selected adapter appears in
`tokn biomol catalog`.

| Adapter | Bounded purpose |
|---|---|
| `proteinmpnn` | One reviewed backbone to one sampled protein sequence; not structure prediction |
| `rfdiffusion1` | One fixed-length unconditional backbone; no target, motif or binder |
| `rfdiffusion3` | Separate backbone executor; **execution held** for checkpoint-specific license evidence |
| `evo2` | One short DNA sequence score; no genomic generation |
| `enformer` | PyTorch human tracks; separate weights and input length from the official model |
| `enformer_deepmind` | Official TensorFlow human tracks from its pinned offline model |
| `borzoi` | One reviewed human SNV, one explicitly selected SAD target |
| `chrombpnet` | Exactly two reviewed disjoint accessibility regions; no singleton padding |
| `flashzoi` | Track index zero from four replicates; no invented biological label |
| `gpnstar` | One reviewed aligned variant score; not pathogenicity classification |

These are CLI-only profiles. The existing structbio prediction/embedding agent
rejects them; a prediction approval cannot authorize design or genomic analysis.
No genomic generation, clinical interpretation, synthesis, automatic folding
or iterative design is enabled.

## Run a real refused preflight

Check TOKN exists (`Get-Command tokn` on PowerShell, `command -v tokn` on POSIX).
Then inspect:

```text
tokn version
tokn biomol catalog
tokn biomol --help
```

From this directory, choose an adapter from the table. The config must be copied
outside repositories even for this diagnostic. For example, in PowerShell:

```powershell
$adapter = "evo2"
$dir = Join-Path ([IO.Path]::GetTempPath()) ("tokn-model-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$config = Join-Path $dir "disabled.json"
try {
    Copy-Item ".\$adapter-disabled.json" $config -ErrorAction Stop
    $request = (Resolve-Path ".\$adapter-preflight.json").Path
    tokn biomol preflight --config $config --request $request
    if ($LASTEXITCODE -eq 0) { throw "Expected a disabled-runtime refusal" }
} finally {
    if (Test-Path -LiteralPath $config) { Remove-Item -LiteralPath $config -ErrorAction Stop }
    Remove-Item -LiteralPath $dir
}
```

POSIX:

```sh
adapter=evo2
dir="$(mktemp -d)"
cp "$adapter-disabled.json" "$dir/disabled.json"
tokn biomol preflight --config "$dir/disabled.json" --request "$PWD/$adapter-preflight.json"
code=$?
rm "$dir/disabled.json"
rmdir "$dir"
test "$code" -ne 0
```

Repeat with the other adapters. Expect nonzero exit, `runtime_ready: false`,
explicit dependency/admission blockers, `held_unvalidated` and `not_verified`.
No inference job, model cache or scientific result is created.
`biomol check` is different: it executes admitted upstream code.

## Future execution requires an operator

Provision a local Linux amd64 Docker/NVIDIA host, a compatible reserved GPU UUID,
the adapter's complete pinned image/runtime/source/weights/reference cache,
retained licenses and reviewed terms, immutable read-only manifests, private
durable state, bounded scratch and an external reviewer's public key.
Use the official [Docker Engine](https://docs.docker.com/engine/install/) and
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
instructions for the host distribution. TOKN installs or downloads none of this.

An operator prepares a typed request and an authorized external reviewer examines
its input identity, ownership, purpose, hard exclusions, uncertainty and exact
execution profile before signing the prepared bytes offline:

```text
tokn biomol prepare --config ABS_CONFIG --request ABS_UNSIGNED_REQUEST
tokn biomol preflight --config ABS_CONFIG --request ABS_SIGNED_REQUEST
tokn biomol run --config ABS_CONFIG --request ABS_SIGNED_REQUEST --run-timeout 0
tokn biomol status --config ABS_CONFIG --job JOB_ID
tokn biomol cancel --config ABS_CONFIG --job JOB_ID
```

A separately reviewed, target-free upstream diagnostic uses:

```text
tokn biomol check --config ABS_CONFIG --request ABS_SIGNED_CHECK_REQUEST
```

This is executed upstream code, not static preflight. It requires its own signed
check request and cannot authorize a design or genomic analysis.

Design and genomic analysis have separate policy versions and capabilities.
Enabling a config, accepting terms or possessing a signing key is not proof of
biological safety, identity or data-owner consent. RFdiffusion3's checkpoint-rights
hold cannot be cleared with a config switch or reviewer assertion.

Genomic public job responses intentionally omit input/output hashes and numeric
scores: low-entropy SNV and scalar-result hashes can identify a private locus.
Full evidence and artifacts remain in privileged private state.

No live inference, containment acceptance, capacity, numerical parity, accuracy
or scientific usefulness has been established by these examples. Process success
does not promote `held_unvalidated` / `not_verified`.

## Attribution

The adapters invoke the pinned
[Anthropic reference release](https://github.com/anthropics/uplifting-biomolecular-modeling/tree/f4f62fa6592ae4938d49b1757bea0cfeff9f468e)
without bundling source, weights or reference genomes. Preserve its Apache-2.0
LICENSE/NOTICE, each kit's third-party notices and the separate model/data terms.
ProteinMPNN, RFdiffusion and genomic model assets do not share one blanket
license. In particular, the Enformer PyTorch checkpoint's attribution conditions
differ from the official TensorFlow model, and ENCODE usage policy is not the
ChromBPNet code's MIT license.
