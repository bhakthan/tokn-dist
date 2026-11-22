# Skill-pack preflight

Inspect capabilities and prompt overrides before changing local configuration.
Skill packs are guidance that can be gated by the current license; they are
not newly compiled modes.

## What you'll learn

- Check the current feature set and installed skill-pack cache.
- Discover mode metadata and audit a synthetic prompt override.
- Distinguish a read-only preflight from installing packs or starting a trial.

## Before you start

| Requirement | Why |
|---|---|
| TOKN on `PATH` | Commands were verified with v0.3.118; check `tokn --help-all` for your build |
| PowerShell or Bash | Creates an isolated scratch folder |
| Model, key, network | Not needed for inspection |

`.env.example` is reference-only. Do not source it. The prompt fixture is copied
into scratch `.nospace/prompts/`; do not place it in your home configuration.

## 1. Inspect capabilities offline

Run this from the example folder to create a fresh scratch workspace.

**PowerShell**

```powershell
$EX = (Get-Location).Path
$WORK = Join-Path $env:TEMP ("skillpack-preflight-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $WORK | Out-Null
$env:TOKN_NO_REGISTER = "1"
$env:TOKN_NO_UPDATE_CHECK = "1"
Set-Location $WORK
tokn license features
tokn skillpack status
tokn skillpack list
tokn introspect --section modes
tokn wiki status
```

**Bash**

```bash
EX="$PWD"
WORK="${TMPDIR:-$HOME}/skillpack-preflight-$$"
mkdir "$WORK"
export TOKN_NO_REGISTER=1 TOKN_NO_UPDATE_CHECK=1
cd "$WORK"
tokn license features
tokn skillpack status
tokn skillpack list
tokn introspect --section modes
tokn wiki status
```

`wiki status` depends on the binary variant. A public build may direct readers
to hosted documentation; an embedded site is available only in a build that
includes it. Do not start a server or open a link automatically.

## 2. Audit a scratch-only prompt override

Continue in the same shell so `$EX` and `$WORK` still refer to the example
folder and scratch workspace.

**PowerShell**

```powershell
New-Item -ItemType Directory -Path "$WORK\.nospace\prompts" -Force | Out-Null
Copy-Item "$EX\fixture\prompts\mode\default.md" "$WORK\.nospace\prompts\mode-default.md"
Set-Location $WORK
tokn doctor prompts --repo-root . --findings-only
```

**Bash**

```bash
mkdir -p "$WORK/.nospace/prompts"
cp "$EX/fixture/prompts/mode/default.md" "$WORK/.nospace/prompts/mode-default.md"
cd "$WORK"
tokn doctor prompts --repo-root . --findings-only
```

The audit inspects prompt text; it does not install a skill pack or call a model.

## 3. Optional entitlement change

`tokn license trial` is not part of this exercise. It writes local license state
and starts a time-limited trial; use it only if you deliberately want that
change. Community inspection does not require a trial.

## What you should see

**Observed** with TOKN 0.3.118: feature inspection, skill-pack status/list,
prompt audit, and wiki status ran without a model call. The installed pack
cache and license report are machine-specific and are not copied here.

**Expected** for the scratch override: the prompt doctor reports findings, if
any, against that file. A clean report does not mean the override is appropriate
for every model or task. See `expected/reference-receipt.json` for the input
digest scope and limitations.

## Troubleshooting

| Symptom | Action |
|---|---|
| A pack is listed but gated | Check the current feature output; do not activate a trial just to finish this lab |
| Prompt override is not found | Confirm it is under scratch `.nospace/prompts/` and rerun with `--repo-root .` |
| Wiki is not embedded | Use the hosted documentation indicated by the public build |
| Output differs from the fixture note | Installed pack cache, license tier, and binary variant can differ |

## Cleanup

Remove only the scratch directory:

```powershell
Set-Location $HOME
Remove-Item -LiteralPath $WORK -Recurse
```

```bash
cd "$HOME"
rm -rf -- "$WORK"
```

## Try it

Compare one mode from introspection with the relevant skill-pack description.
Write down what the skill advises and what an actual tool or gate would still
need to verify.
