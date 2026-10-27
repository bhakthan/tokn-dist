# Chai-1, ESM C and OpenBind-0 with TOKN

This walkthrough uses TOKN's real catalog and deliberately refused preflight.
It needs **no GPU, Docker, Python, weights, LLM key or biological input**.
Requires **TOKN v0.3.70 or newer**; v0.3.69 contains only the original
Boltz-2 adapter.

| Adapter | Bounded purpose | Important distinction |
|---|---|---|
| `chai1` | Protein prediction or two-protein cofolding | Not ligand design, affinity, templates or remote MSA search |
| `esmc` | ESM C 300M per-residue embeddings for one protein | Vectors, not structures, confidence or biological-function predictions |
| `openfold3` | OpenBind-0 protein prediction/cofolding | Explicit `openbind0` variant, fixed seed 42; no preview2 fallback |

All execution is experimental, disabled by default and externally reviewed.
No live GPU compatibility, containment, capacity, numerical parity, accuracy
or scientific validation is established by this example.

## 1. Inspect before provisioning

Check TOKN exists (`Get-Command tokn` on PowerShell, `command -v tokn` on POSIX),
then run:

```text
tokn version
tokn biomol catalog
tokn biomol --help
```

The catalog is metadata, not permission to execute a model. Inspection never
installs packages, downloads weights, accepts terms or invokes model code.

## 2. Run a deliberately refused preflight

From this directory, choose `chai1`, `esmc` or `openfold3`.
Each disabled config opts into nothing; each request is an empty check with no
target, review evidence, expiry or signature. The explicit `adapter` selectors
must agree. Keep the diagnostic config outside every repository.

PowerShell:

```powershell
$adapter = "chai1"
$dir = Join-Path ([IO.Path]::GetTempPath()) ("tokn-model-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $dir | Out-Null
$config = Join-Path $dir "disabled.json"
try {
    Copy-Item ".\$adapter-disabled.json" $config -ErrorAction Stop
    $request = (Resolve-Path ".\$adapter-preflight.json").Path
    tokn biomol preflight --config $config --request $request
    if ($LASTEXITCODE -eq 0) { throw "Expected a refused, disabled-runtime preflight" }
} finally {
    if (Test-Path -LiteralPath $config) { Remove-Item -LiteralPath $config -ErrorAction Stop }
    Remove-Item -LiteralPath $dir
}
```

POSIX:

```sh
adapter=chai1
dir="$(mktemp -d)"
cp "$adapter-disabled.json" "$dir/disabled.json"
tokn biomol preflight --config "$dir/disabled.json" --request "$PWD/$adapter-preflight.json"
code=$?
rm "$dir/disabled.json"
rmdir "$dir"
test "$code" -ne 0
```

Repeat with `esmc` and `openfold3`. Expect nonzero exit, `runtime_ready: false`,
`acceptance: held_unvalidated`, `parity: not_verified`, and explicit blockers.
Enabling a config alone cannot supply dependencies or signed review.
No inference job is created.

Do not enable the config or invent signatures just to remove these diagnostics.
`biomol check` executes admitted upstream code; it is not static preflight.

## 3. Future Linux GPU execution is an operator procedure

The new adapters require a separately provisioned local Linux amd64
Docker/NVIDIA host, compatible H100 80GB/driver, an explicitly selected GPU
UUID, preloaded pinned image and full runtime stack, complete immutable source
and model-cache inventories, retained licenses/data terms, protected disjoint
state/scratch roots and an external reviewer's public key.
Use [Docker Engine](https://docs.docker.com/engine/install/) and
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
instructions for the host distribution. TOKN does not provision this implicitly.

Use `tokn biomol catalog` for the installed version's selected profiles and
supported tasks. The sibling [configuration template](../config.template.json)
illustrates shared administrator controls, not a complete configuration for
these adapters: each also requires its own pinned image/cache, GPU UUID and
review profile. An operator must supply those records. This walkthrough supplies
no runnable target, model files or fabricated approval.

```text
tokn biomol prepare --config ABS_CONFIG --request ABS_UNSIGNED_REQUEST
tokn biomol preflight --config ABS_CONFIG --request ABS_SIGNED_REQUEST
tokn biomol run --config ABS_CONFIG --request ABS_SIGNED_REQUEST --run-timeout 0
tokn biomol status --config ABS_CONFIG --job JOB_ID
tokn biomol cancel --config ABS_CONFIG --job JOB_ID
```

For a separately reviewed, target-free upstream diagnostic, use:

```text
tokn biomol check --config ABS_CONFIG --request ABS_SIGNED_CHECK_REQUEST
```

This executes upstream code and needs its own signed check request; a successful
check does not authorize a prediction or establish scientific validity.

An external reviewer signs the exact prepared bytes offline; TOKN never signs.
New adapters require their own model/profile/GPU-bound authority, not a Boltz
approval. Review authenticates an assertion, not automated biological safety.
All uncertainty remains denied; no automatic retry or model substitution.
Unconfirmed container termination stays `cleanup_unresolved`.

Chai uses one sample with fixed fold settings and generated protein-only FASTA.
OpenBind-0 uses a generated protein-only query and fixed seed-list `[42]`;
user runner YAML, templates and remote MSA search are not accepted.
ESM C has no sampling/recycling semantics and exports bounded private numeric
embeddings; the agent receives metadata, not vectors. Neither successful
execution nor model confidence establishes experimental truth. Results remain
`held_unvalidated` / `not_verified`.

## Attribution

The adapters invoke the pinned
[Anthropic reference release](https://github.com/anthropics/uplifting-biomolecular-modeling/tree/f4f62fa6592ae4938d49b1757bea0cfeff9f468e)
without bundling its code or weights. Retain Apache-2.0 LICENSE/NOTICE and each
kit's third-party notices. Chai's code/model license does not relicense its data
or ESM2 dependencies. ESM C uses the pinned Biohub model cards/notices and
applicable policy, not an assumed blanket Apache grant. OpenBind's primary
[announcement](https://openbind.uk/news/blog-openbind-0-advancing-open-molecular-structure-prediction/)
explicitly includes OB0 model weights under Apache-2.0; retain that evidence
alongside the code license and separate data/dependency terms. This does not
automatically accept terms or authorize a target.
