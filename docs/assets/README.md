# Community illustrations

Two light-theme editorial infographics for the public README:

| File | Purpose |
|---|---|
| [community-breadth.png](community-breadth.png) | Illustrative domain families and the Community/licensed-workflow boundary |
| [community-depth.png](community-depth.png) | Tools, skills, plugins, hooks and a human-reviewed path from intent to findings |

Generated with **GPT-image-2.5** through Azure OpenAI and `tokn docs illustrate`.
Both PNGs are native **3840 x 2160** outputs, not upscaled. TOKN added its
invisible provenance watermark. These are conceptual illustrations, not
screenshots or evidence of a completed live workflow. The battery-passport
example represents a fixed synthetic Community preview, not production approval.
Decorative marks are illustration elements, not a separate product identity.

The reproducible inputs are in [community-infographics.json](community-infographics.json).
The prompts contain only public capability descriptions. Generation used TOKN's
default light-theme style and negative guidance, with no prompt overrides.
Generated results are nondeterministic; inspect wording and access claims before
publishing a regenerated image.

## Regenerate

Requires TOKN with `docs illustrate` and access to a GPT-image-2.5 Azure OpenAI
deployment. For Entra authentication, also install the Azure CLI and run
`az login`; alternatively supply your own `AZURE_OPENAI_API_KEY`. Image generation
sends these prompts to your configured account and incurs provider charges.
No other image package or browser is needed for PNG output.

From this repository in PowerShell:

```powershell
tokn docs illustrate --help
az --version # needed only for Entra authentication
$env:AZURE_OPENAI_ENDPOINT = "https://YOUR-ACCOUNT.cognitiveservices.azure.com/openai/v1"
$env:AZURE_OPENAI_IMAGE_DEPLOYMENT = "YOUR-GPT-IMAGE-2.5-DEPLOYMENT"
tokn docs illustrate --spec .\docs\assets\community-infographics.json --out-dir .\docs\assets --format png --dry-run
# Opt in to generation; this overwrites the two named image files.
tokn docs illustrate --spec .\docs\assets\community-infographics.json --out-dir .\docs\assets --format png
```

If TOKN is missing, follow the [installation guide](../../README.md#1-download).
If Entra authentication is desired and `az` is missing, install the Azure CLI:
Windows `winget install --exact --id Microsoft.AzureCLI`; macOS
`brew install azure-cli`; Linux use the distribution-specific commands in
[Microsoft's Azure CLI installation guide](https://learn.microsoft.com/cli/azure/install-azure-cli).
Then run `az login` and retry. Never put credentials in the spec or source control.
