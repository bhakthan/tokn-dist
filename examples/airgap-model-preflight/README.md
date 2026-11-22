# Air-gap model preflight

Separate static configuration checks from actual local inference. The first
path needs no model weights, server, endpoint, or key. The optional staged
path uses only locally supplied assets; this folder includes no weights.

## What you'll learn

- Read provider diagnostics without mistaking them for an inference test.
- Validate a staged asset's checksum before registering or serving it.
- Keep GGUF import distinct from an independently staged ONNX runtime.

## Before you start

| Requirement | Why |
|---|---|
| TOKN on `PATH` | Commands were verified with v0.3.118; check `tokn --help-all` for your build |
| PowerShell or Bash | Creates a scratch copy |
| Python 3 | Only for the optional checksum checker |
| A local runtime and a legally usable model | Only for the optional inference path |
| Network or key | Not needed by the static checks or disconnected path |

Model weights are not included. Before serving, check the model and runtime
licenses, file hash, disk/RAM needs, and the runtime installation steps in
[Local llama.cpp](../local-llamacpp/README.md). Do not download anything in the
disconnected exercise.

## 1. Static checks (no model)

Run this from the example folder.

**PowerShell**

```powershell
$EX = (Get-Location).Path
$WORK = Join-Path $env:TEMP ("airgap-preflight-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $WORK | Out-Null
$env:TOKN_NO_REGISTER = "1"
$env:TOKN_NO_UPDATE_CHECK = "1"
Copy-Item "$EX\task.txt","$EX\staging-manifest.example.json","$EX\check-local.py" $WORK
Set-Location $WORK
tokn doctor --provider ollama
tokn doctor --provider gguf
tokn doctor --provider onnx
tokn models status
```

**Bash**

```bash
EX="$PWD"
WORK="${TMPDIR:-$HOME}/airgap-preflight-$$"
mkdir "$WORK"
export TOKN_NO_REGISTER=1 TOKN_NO_UPDATE_CHECK=1
cp "$EX/task.txt" "$EX/staging-manifest.example.json" "$EX/check-local.py" "$WORK/"
cd "$WORK"
tokn doctor --provider ollama
tokn doctor --provider gguf
tokn doctor --provider onnx
tokn models status
```

These are static diagnostics. They can report configured local providers even
when no server is running; they do not prove that inference works.

## 2. Optional staged GGUF path

Copy a trusted GGUF file and a completed manifest into the scratch folder.
Set `artifact_path` to the local file name and replace the digest with its
independently verified SHA-256. Set `license_reviewed` to `true` only after
checking the model license yourself. Then:

```sh
python --version
python check-local.py staging-manifest.example.json
tokn models import staged-model.gguf --name workshop
tokn models serve workshop
```

Serving requires a compatible `llama-server` installation. Check
`llama-server --version` first; follow the linked setup guide if it is absent.
Review the model's actual license and resource needs before serving. Stop the
server with `tokn models stop` when finished.

If a suitable local tool-capable server is already running, a bounded
read-only inference can be tried with its actual local model name:

```sh
tokn agent-run --air-gap --model-provider gguf -m YOUR_LOCAL_MODEL_ID -p "Summarize task.txt"
```

This optional request is a live local inference, not a static preflight. For
ONNX, stage and start its own supported runtime; do not import an ONNX file as
GGUF. Use the actual provider model ID and local endpoint configured by that
runtime.

## What you should see

**Observed** with TOKN 0.3.118: static `doctor` checks for the three local
providers reported that no credential is needed and that a local runtime must
be running. `models status` reported the server stopped on that machine.
These results can differ on your machine and did not invoke a model.

`expected/preflight.md` lists the distinction between expected static checks
and a real local inference. `expected/reference-receipt.json` records the
input digest scope and limitations. No weights or runtime output are included.

## Troubleshooting

| Symptom | Action |
|---|---|
| Provider check succeeds but inference fails | Start the matching local server and confirm its configured model ID |
| GGUF server cannot start | Check `llama-server --version`; follow the local runtime guide |
| Checksum mismatch | Stop; obtain the expected digest from a trusted source |
| ONNX model is not recognized by GGUF tools | Use the separately staged ONNX runtime |
| No local model is available | Stop after the static checks; they are a complete first step |

## Cleanup

Stop any server you started, then remove only `$WORK`:

```powershell
tokn models stop
Set-Location $HOME
Remove-Item -LiteralPath $WORK -Recurse
```

```bash
tokn models stop
cd "$HOME"
rm -rf -- "$WORK"
```

The TOKN model registry is user state; review `tokn models list` and remove
only the alias you created if you no longer want it. Do not delete the source
weight file unless you own it.

## Try it

Explain why a passing static provider check is not sufficient evidence for
offline inference. Do not add a remote fallback to an air-gap request.
