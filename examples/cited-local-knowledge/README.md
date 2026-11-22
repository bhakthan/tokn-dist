# Cited local knowledge

Retrieve a passage from two fictional policy revisions without sending content
to a model. The local `hashing` embedder is deterministic and lexical-grade;
citations still need human review.

## What you'll learn

- Configure a local files knowledge base in a scratch copy.
- Index locally with the model-free hashing embedder.
- Check the cited source and revision rather than treating retrieved text as an instruction.

## Before you start

| Requirement | Why |
|---|---|
| TOKN on `PATH` | Commands were verified with v0.3.118; check `tokn --help-all` for your build |
| PowerShell or Bash | Copies the synthetic policies into scratch |
| Model, key, network | Not needed; the fixture uses hashing |

`.env.example` is reference-only. Do not copy `.nospace/` state back into this
checkout. Indexes are generated only in the scratch workspace.

## 1. Stage the local policy

Run this from this example folder.

**PowerShell**

```powershell
$EX = (Get-Location).Path
$WORK = Join-Path $env:TEMP ("cited-knowledge-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path "$WORK\.nospace" -Force | Out-Null
$env:TOKN_NO_REGISTER = "1"
$env:TOKN_NO_UPDATE_CHECK = "1"
Copy-Item "$EX\policies" $WORK -Recurse
Copy-Item "$EX\knowledge.example.yaml" "$WORK\.nospace\knowledge.yaml"
Set-Location $WORK
```

**Bash**

```bash
EX="$PWD"
WORK="${TMPDIR:-$HOME}/cited-knowledge-$$"
mkdir -p "$WORK/.nospace"
export TOKN_NO_REGISTER=1 TOKN_NO_UPDATE_CHECK=1
cp -R "$EX/policies" "$WORK/"
cp "$EX/knowledge.example.yaml" "$WORK/.nospace/knowledge.yaml"
cd "$WORK"
```

## 2. List, index, and diagnose

```sh
tokn knowledge list --json --air-gap --repo-root .
tokn knowledge index --kb handbook --air-gap --repo-root .
tokn knowledge doctor --air-gap --repo-root .
```

Indexing creates runtime files under scratch `.nospace/knowledge/handbook/`.
Running `doctor` before indexing is also useful: it reports the expected
“not indexed” condition, so do not interpret that pre-index check as a failure
of the hashing embedder.

## 3. Search and inspect the citation

```sh
tokn knowledge search "Who approves a refund?" -k 3 --air-gap --repo-root . --json
```

Open the cited policy passage and compare it with `policies/archive.md`.
`expected/citations.json` is a curated reference, not a copied search log.
The query can return several passages; check the cited heading, source, and
revision before answering.

## What you should see

**Observed** with TOKN 0.3.118 and the scratch fixture: `knowledge list` marked
the base lexical-grade and initially unindexed; `knowledge doctor` identified
that missing index; `knowledge index` indexed the local policy file into three
chunks; search returned citations into the local policy.

**Expected** after indexing: doctor reports the configured local source and
search includes the approval passage. Hashing supports lexical retrieval; it
does not establish semantic understanding or policy authority. See
`expected/reference-receipt.json` for the input digest scope and limitations.

## Troubleshooting

| Symptom | Action |
|---|---|
| No knowledge base is listed | Confirm `.nospace/knowledge.yaml` is in the scratch root |
| Source path is missing | Run from the scratch root containing `policies/` |
| Doctor says not indexed | Run `knowledge index` before search |
| Search returns multiple passages | Check the heading and revision; do not rely on rank alone |

## Cleanup

Remove only the scratch directory after review:

```powershell
Set-Location $HOME
Remove-Item -LiteralPath $WORK -Recurse
```

```bash
cd "$HOME"
rm -rf -- "$WORK"
```

## Try it

Change the search question to ask for the archived threshold. Cite the passage
you used and explain why the current policy takes precedence in this fictional
example.
