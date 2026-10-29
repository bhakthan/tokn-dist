# Boltz-2 with TOKN: inspect now, provision a GPU host later

Requires **TOKN v0.3.69 or newer**. The first two steps need no GPU, Docker,
Python, model weights, LLM key or paid model call. No scientific inference has
been run for this example. The adapter is **experimental and disabled by default**.

This is a protein-only extension of `structbio`, not the existing cryo-EM/FSC
walkthrough. It supports one-chain prediction and two-to-four-protein cofolding,
not ligands, affinity, design or genomics. See
[structural-biology](../structural-biology/README.md) for experimental priors.
For Chai-1, ESM C embeddings and OpenBind-0, see
[additional adapters](additional-adapters/README.md).
ProteinMPNN, RFdiffusion and the seven genomic kits have separate CLI-only
[design and genomics examples](design-and-genomics/README.md), not Boltz permissions.
For GPU-free next-action recommendations and offline action-label benchmarks,
see [shadow routing](shadow-routing/README.md) (v0.3.71+); it never runs or
approves a scientific job.

## 1. Inspect the real catalog

Confirm the executable is installed (`Get-Command tokn` in PowerShell,
`command -v tokn` in a POSIX shell), then:

```text
tokn version
tokn biomol catalog
tokn biomol --help
```

The JSON catalog reports `boltz2`, stock version `2.2.1`, modes `off`/`exact`,
protein prediction/cofolding and `experimental_disabled_by_default`.
It does not execute upstream code, install anything or accept licenses.

## 2. Observe a real, deliberately failed preflight

Run from this example directory. `preflight-request.json` has no biological
input, reviewer claims or signature. `disabled.json` opts into **nothing**.
The config must be outside a repository, even for this diagnostic.

PowerShell:

```powershell
$dir = Join-Path ([IO.Path]::GetTempPath()) ("tokn-biomol-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$config = Join-Path $dir "disabled.json"
Copy-Item .\disabled.json $config
$request = (Resolve-Path .\preflight-request.json).Path
tokn biomol preflight --config $config --request $request
$code = $LASTEXITCODE
Remove-Item -LiteralPath $config
Remove-Item -LiteralPath $dir
if ($code -eq 0) { throw "Expected a refused, disabled-runtime preflight" }
```

POSIX shell:

```sh
dir="$(mktemp -d)"
cp disabled.json "$dir/disabled.json"
tokn biomol preflight --config "$dir/disabled.json" --request "$PWD/preflight-request.json"
code=$?
rm "$dir/disabled.json"
rmdir "$dir"
test "$code" -ne 0
```

Expected: a JSON report with `runtime_ready: false`, observed missing
prerequisites/admission evidence, `acceptance: held_unvalidated` and
`parity: not_verified`, followed by a nonzero command exit. On Windows,
unsupported Linux execution is one of the blockers. No inference job or model
cache is created. Ordinary TOKN session logging is separate.

**Do not change the config to enabled just to silence the report.**
`tokn biomol check` is different: it executes the upstream check inside an
admitted GPU container and requires signed review.

## 3. Stage an actual future Linux GPU environment

This section is an operator procedure, **not a validated model run**.
No runnable biological target or fabricated approval is supplied.

The flow requires all of: Linux amd64; Docker Engine plus NVIDIA Container
Toolkit and compatible GPU/driver; a preloaded content-pinned image with the
kit's complete runtime stack; the complete pinned kit; weights and unpacked
`mols/` data; reviewed complete SHA256 manifests and ancillary-data terms;
immutable read-only host source/cache mounts; private durable output; a
dedicated bounded tmpfs scratch mount; and an external reviewer's public key.

Use the official [Docker Engine](https://docs.docker.com/engine/install/)
and [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
instructions for your Linux distribution. TOKN never installs, pulls images
or downloads weights. Docker Desktop, WSL and remote Docker contexts are not
execution fallbacks.

`config.template.json` shows actual fields but contains invalid placeholders.
Keep the completed administrator config outside repositories and configured
roots, protected with mode 600 and protected ancestry. Output must be private
mode 700. Scratch must be a dedicated private tmpfs of at most 8 GiB / 20000
inodes. Source/cache need administrator-controlled read-only host mounts;
Docker `ro` alone does not stop host mutation.

`request.template.json` is likewise **not runnable**. Replace it only with an
independently reviewed benign protein request. Prediction accepts exactly one
chain; cofolding two to four, IDs A–D in order. Canonical amino acids only,
at most 1024 residues/chain and 2048 total; samples 1–4, recycles 1–10.
External MSAs/files, arbitrary YAML and extra arguments are rejected.

## 4. Review, admit and run explicitly

On the provisioned Linux host:

```sh
tokn biomol prepare --config /etc/tokn-biomol/config.json --request /srv/reviews/unsigned.json
tokn biomol preflight --config /etc/tokn-biomol/config.json --request /srv/reviews/signed.json
tokn biomol run --config /etc/tokn-biomol/config.json --request /srv/reviews/signed.json --run-timeout 0
tokn biomol status --config /etc/tokn-biomol/config.json --job JOB_ID
tokn biomol cancel --config /etc/tokn-biomol/config.json --job JOB_ID
```

An external authorized reviewer signs the exact prepared UTF-8 `signing_bytes`
offline and adds its standard-base64 Ed25519 signature as `approval.signature`.
Do not sign the surrounding JSON or invent review evidence. TOKN accepts only
the public key; it has no signer. The signature authenticates the reviewer's
assertion, not independent biosecurity/identity verification or a safety guarantee.
Any uncertainty or hard exclusion must remain denied.

The signature binds the full effective request/config, staged manifests/image,
policy/profile, operator/target evidence, purpose, short expiry and one-use nonce.
A retry, changed setting, relocated config or new check job needs a new review.
Check requests use `kind: upstream_check`, `task: check`, `mode: exact`,
empty chains and zero sampling parameters; they cannot authorize a prediction.

Optional one-shot agent integration uses the same service:

```text
tokn agent-run --mode structbio --structbio-workflow computational --biomol-config ABS_CONFIG --prompt "Inspect the biomolecular catalog and admission requirements."
```

Set model credentials explicitly in the operator's process environment and
select the provider/model as needed; normal domain licensing applies.
The minimal loop is memory-only: repository environment/config, executable
hooks, skills, Git and checkpoints are not initialized.
Only six reserved biomolecular
tools are callable; no generic shell, file editing, outbound MCP, peer extension
or interactive mode switch can become an alternative executor.

## 5. Interpret the outcome honestly

Structures/confidence and host-owned provenance are exported only after bounded
identity/artifact checks. Successful execution still means
`acceptance: held_unvalidated`, `parity: not_verified`.
Confidence is descriptive, not experimental truth, binding affinity or efficacy.
No calibrated low-confidence threshold or per-residue NPZ analysis is provided.

Missing weights or unsupported hosts deny admission. Exit 3 remains NOT ACTIVE;
exit 5 remains KERNELS-REFUSED, regardless of artifacts. Exit 0 without valid
expected output fails. Failed jobs retain IDs and nonzero exits.
`cleanup_unresolved` means container termination was not proven; do not treat it
as cancellation or start another job by removing locks.

Future scientific acceptance requires real approved single-chain and complex
runs, effective containment checks, named hardware/image/driver evidence and
repeatable stock/exact comparison. No scientific outputs or speedups are
fabricated in this walkthrough.

## Upstream attribution and licenses

The adapter invokes
[Anthropic's uplifting-biomolecular-modeling](https://github.com/anthropics/uplifting-biomolecular-modeling/tree/f4f62fa6592ae4938d49b1757bea0cfeff9f468e)
at `f4f62fa6592ae4938d49b1757bea0cfeff9f468e`.
Original optimization code is Apache-2.0, copyright 2026 Anthropic, PBC.
Retain root LICENSE/NOTICE, `boltz2/STOCK.md`, third-party notices and every
applicable license text when staging it. Boltz-2 stock code/weights are MIT per
the [provider](https://github.com/jwohlwend/boltz/blob/v2.2.1/README.md);
ancillary-data terms require separate review. Apache coverage does not relicense
third-party artifacts. This example bundles no upstream source or weights.
