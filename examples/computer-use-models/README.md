# Example: Computer-use models on your own endpoint (MagenticBrain-14B and Fara1.5-9B)

> "Take one screenshot-driven step toward a goal on a harmless page, then run a short multi-step trajectory, using a computer-use model I host myself."

This walkthrough shows how to point TOKN at two computer-use models you host yourself: a planner (`MagenticBrain-14B`) and a browser-action model (`Fara1.5-9B`). TOKN does not host models. You bring an endpoint, and every screenshot and page text goes to it.

| Capability | Model | TOKN command | Needs a browser |
|---|---|---|---|
| Single observe-think-act step | Fara1.5-9B | `tokn fara-step` | No |
| Multi-step trajectory (approval-gated) | Fara1.5-9B | `tokn fara-run` | Only with `--live-browser` |
| Offline plumbing check (no endpoint) | Fara1.5-9B | `tokn fara-run --dry-run` | No |
| Chat / planning agent loop | MagenticBrain-14B | `tokn agent-run --prompted-tools` | No |

This is not the default web agent. See [Choosing a path](#choosing-a-path).

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57+ | Ships the `fara-*` commands and `--prompted-tools` | `tokn version` |
| Licence tier: **Community** | `fara-step`, `fara-run`, and the default `agent-run` mode are not in the premium list in `internal/license/policy.go` | Nothing to buy |
| Your own hosted endpoint for each model | TOKN calls an OpenAI-style chat endpoint you control; it does not host models | Endpoint reachable (see step 2) |
| Azure subscription, with quota for a GPU SKU that fits each model | Azure ML managed online endpoints run the models on GPUs. TOKN does not name a SKU: **see the model card** for each model's memory needs | `az account show` |
| Azure ML workspace + managed online endpoints | The endpoint URL shape TOKN accepts is `https://<endpoint>.<region>.inference.ml.azure.com/v1` | `az ml workspace show` |
| Azure CLI with the `ml` extension | Create, inspect, and fetch keys for the endpoint | `az version` then `az extension list -o table` |
| Chrome, Chromium, or Edge | Only for `fara-run --live-browser`. TOKN drives the browser over CDP, not Playwright | `chrome --version` / `chromium --version` / `msedge --version` |
| Playwright | **Not needed** for these commands. Only the separate web-agent path uses it (see [../web-agent/](../web-agent/)) | n/a |

### Preflight: install the tools

Windows (PowerShell):
```powershell
winget install -e --id Microsoft.AzureCLI
az extension add -n ml
```

macOS (Homebrew):
```bash
brew install azure-cli
az extension add -n ml
```

Linux (Debian/Ubuntu, using Microsoft's Azure CLI install script):
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az extension add -n ml
```

For `--live-browser` only, install any one of Chrome, Chromium, or Edge. If none is found, `fara-run` stops with an install hint.

## 1. Deploy your endpoints (placeholders only)

Create the managed online endpoint with the Azure portal or the Azure ML docs. Pick your own GPU SKU using the model card.

```bash
az login
az account set --subscription <your-subscription>
az ml online-endpoint show -n <your-endpoint-name> -w <your-workspace> -g <your-resource-group>
```

```powershell
az login
az account set --subscription <your-subscription>
az ml online-endpoint show -n <your-endpoint-name> -w <your-workspace> -g <your-resource-group>
```

Two endpoints, one per model, is the simplest layout. Use separate `<your-endpoint-name>` values for `MagenticBrain-14B` and `Fara1.5-9B`.

**Auth.** Pick one:

- **Entra ID (preferred).** Set `AZURE_OPENAI_USE_DEFAULT_CREDENTIAL=true` and run `az login`. For `*.inference.ml.azure.com` hosts TOKN requests the `https://ml.azure.com/.default` scope automatically. Your identity needs data-plane access to the endpoint. The scope selection is verified in source; whether your endpoint accepts it depends on its auth mode.
- **Key.** Fetch the endpoint key yourself and put it in an env var. Never paste it into a file in this repo.

```bash
az ml online-endpoint get-credentials -n <your-endpoint-name> -w <your-workspace> -g <your-resource-group> --query primaryKey -o tsv
```

**Billing warning.** GPU endpoints bill while idle. Delete each endpoint after testing:

```bash
az ml online-endpoint delete -n <your-endpoint-name> -w <your-workspace> -g <your-resource-group> --yes
```

## 2. Readiness: what TOKN checks, and what it does not

- **TOKN does not run an endpoint probe** in the `fara-*` or `agent-run` paths reviewed for this example. A missing or failing endpoint surfaces as an error from the completion call. For `fara-step`, the message is `fara completion failed: ...`.
- Config errors are caught before any network call: a missing endpoint, key or credential, or deployment name fails with a message that names the variable (for example `AZURE_OPENAI_DEPLOYMENT is required when NOSPACE_MODEL_PROVIDER=azure-openai`).
- So check readiness yourself before a live run:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" -H "Authorization: <your-auth-header-value>" "https://<your-endpoint-name>.<region>.inference.ml.azure.com/v1/models"
```

Expect `200` once the deployment is up. If you get anything else, do not run TOKN against it yet.

## 3. Configure TOKN (placeholders only)

Set the same variables for both models. Change `AZURE_OPENAI_DEPLOYMENT` and `NOSPACE_MODEL_NAME` per model.

```bash
export NOSPACE_MODEL_PROVIDER=azure-openai
export AZURE_OPENAI_ENDPOINT="https://<your-endpoint-name>.<region>.inference.ml.azure.com/v1"
export AZURE_OPENAI_DEPLOYMENT="<your-deployment-name>"
export NOSPACE_MODEL_NAME="<your-deployment-name>"
export AZURE_OPENAI_USE_DEFAULT_CREDENTIAL=true   # or set AZURE_OPENAI_API_KEY instead
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "azure-openai"
$env:AZURE_OPENAI_ENDPOINT = "https://<your-endpoint-name>.<region>.inference.ml.azure.com/v1"
$env:AZURE_OPENAI_DEPLOYMENT = "<your-deployment-name>"
$env:NOSPACE_MODEL_NAME = "<your-deployment-name>"
$env:AZURE_OPENAI_USE_DEFAULT_CREDENTIAL = "true"   # or set AZURE_OPENAI_API_KEY instead
```

Optional: `AZURE_OPENAI_API_VERSION` (defaults to `2024-10-21`). For LLM setup in general, see [../../SETUP.md](../../SETUP.md).

## 4. Offline plumbing check (no endpoint, no credentials)

Run this first. It parses a canned Fara reply and does not call the network.

```bash
tokn fara-run --dry-run
tokn fara-step --dry-run
```

```powershell
tokn fara-run --dry-run
tokn fara-step --dry-run
```

**Expected, not a recorded run:** both commands print a parsed action and exit 0.

## 5. Single Fara step against a static screenshot

Save any screenshot of a simple page as `shot.png` in a scratch folder. Then:

```bash
tokn fara-step --goal "Click the link labelled More information" --image shot.png
```

```powershell
tokn fara-step --goal "Click the link labelled More information" --image shot.png
```

Add `--json` for machine-readable output. Repeat `--image` to send screenshots; only the most recent three are sent.

**Expected, not a recorded run:** a single typed action (click, type, scroll, and so on) with coordinates. This step does not click anything on your machine.

## 6. Smoke trajectory on a harmless public page

`fara-run` is the multi-step loop. Without `--live-browser` it uses a no-op actuator, so the steps only exercise the loop with synthetic observations. Use `--live-browser` to drive a real page.

```bash
tokn fara-run --goal "Read the heading on the page" --live-browser --url https://example.com --max-steps 3
```

```powershell
tokn fara-run --goal "Read the heading on the page" --live-browser --url https://example.com --max-steps 3
```

Safety defaults:

- `--max-steps 3` caps the trajectory. The default is 8.
- The browser is headless unless you add `--headed`.
- Critical actions pause for approval. Without `--auto-approve`, a paused action is not executed, so leave that flag off for this smoke test.
- `--browser-no-sandbox` is unsafe and is only for root inside a container. Do not use it here.

**Expected, not a recorded run:** the loop runs up to three steps, prints each action, and stops at the step cap or when the page heading has been read.

## 7. MagenticBrain-14B as a planner

MagenticBrain runs through the normal agent loop. Point it at a scratch repo root so it cannot touch your work:

```bash
export NOSPACE_PROMPTED_TOOLS=true
tokn agent-run --prompt "Reply with one word: ready." --repo-root <your-scratch-folder> --max-steps 2 --prompted-tools
```

```powershell
$env:NOSPACE_PROMPTED_TOOLS = "true"
tokn agent-run --prompt "Reply with one word: ready." --repo-root <your-scratch-folder> --max-steps 2 --prompted-tools
```

`--prompted-tools` (or `NOSPACE_PROMPTED_TOOLS=true`) routes tool calls through text blocks instead of the OpenAI `tools` array. The flag's help text says the MaaP vLLM server rejects that array with HTTP 424.

**Expected, not a recorded run:** a one-word reply, then exit.

## Choosing a path

| Path | Command | Models | GPUs | Notes |
|---|---|---|---|---|
| Default web agent | `tokn agent-run --mode webagent` (see [../web-agent/](../web-agent/)) | LLM backend chosen with `--webagent-backend` | No | Needs Python and Playwright |
| Webwright scripting | See [../webwright/](../webwright/) | Your chosen LLM | No | Writes a re-runnable Playwright script as the artifact |
| **This example** | `tokn fara-*` and `agent-run --prompted-tools` | Your MagenticBrain-14B / Fara1.5-9B endpoints | Yes, on your endpoint | The computer-use models run where you host them |

The web agent's `--webagent-backend` flag selects an LLM backend for its own loop. None of those backends is the Entra-authenticated MaaP path used here. Use the `fara-*` commands or `agent-run --prompted-tools` above instead.

## What to look for

- `tokn fara-run --dry-run` and `tokn fara-step --dry-run` exit 0 without any endpoint configured.
- With the endpoint configured, `fara-step` returns one action, not an error.
- `fara-run --live-browser` opens the page you named and stops at your step cap.
- A paused critical action prints a pending approval and does not run.

## What leaves your machine

- Your goal text, screenshots, and page text go to the endpoint you configured in step 3.
- TOKN does not add a separate cloud call in these paths. Your endpoint sees the same content you would send to any hosted model.
- Use a harmless page for the smoke test, and do not point `--url` at a site with real credentials.

## Troubleshooting

**Endpoint not ready (deployment still creating, or stopped).** The readiness check in step 2 returns non-200. Wait for the deployment to show healthy with `az ml online-endpoint show`, then retry. `fara-step` reports `fara completion failed`.

**401 or 403.** Your key or Entra identity is wrong or lacks data-plane access. Check that `AZURE_OPENAI_API_KEY` matches the current key from `get-credentials`, or that `az login` used an identity with access to the endpoint. Keys rotate, so refetch after a change.

**Quota error on deploy.** The GPU SKU you chose has no quota in that region. Pick a different SKU or region, or request quota in the Azure portal. Check the model card for the memory the model needs.

**HTTP 424 from the endpoint.** The server rejected the tools array. Use `--prompted-tools` on `agent-run`. `fara-*` already sends no tools array.

**`--live-browser` says no browser found.** Install Chrome, Chromium, or Edge (step 0). Re-run.

**"... is required when NOSPACE_MODEL_PROVIDER=azure-openai".** A variable from step 3 is unset. The message names it.

## Verified from source vs not yet verified

Verified from the TOKN source (`environment-manager`):

- Command names and flags for `fara-step` and `fara-run`, including `--dry-run`, `--live-browser`, `--max-steps`, and `--auto-approve`.
- Azure env vars for the `azure-openai` provider, and the Entra switch `AZURE_OPENAI_USE_DEFAULT_CREDENTIAL`.
- The `ml.azure.com` token scope for `*.inference.ml.azure.com` hosts.
- `--prompted-tools` and `NOSPACE_PROMPTED_TOOLS`.
- The community tier for these commands.

Not verified (do not treat as fact):

- Any automatic endpoint readiness gate. None was found in these paths. Step 2 is a manual check.
- That either model responds correctly to the prompts above. Expected outputs are not recorded runs.
- GPU SKU and quota needs. These come from the model cards, which were not checked.
- That the Entra path works end-to-end against your endpoint's auth mode.
- Whether `fara-run` stops cleanly on an endpoint error mid-trajectory.
- The Azure CLI install commands in step 0 are general Azure CLI guidance, not taken from TOKN source.
