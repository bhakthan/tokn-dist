# TOKN — download & try

**TOKN** is the harness around your AI models: it helps them code, use tools,
work together and check results. One downloadable binary brings **38 domain
modes**, local or cloud models, offline licensing and in-place updates.
This repo hosts releases, guides and examples; the source is private.

```text
Your goal -> TOKN + your models and tools -> checks -> reviewable result
```

---

## Why TOKN? Value for teams running agents in production

Most agents look great in a demo and get fragile in production. TOKN is the
**harness around the model** — tools, checks and controls for turning a request
into reviewable work. A few concrete ways it adds value, in plain terms:

- **Check improvements against the real goal.** Agents that tune themselves often
  push one number up while the real goal quietly gets worse.
  *Example: a support bot's "tickets resolved" climbs because it learned to close
  hard tickets fast — while renewals fall.* TOKN's **Graph of Loops** lets you
  check a proposed improvement against independent outcomes and human review,
  rather than trusting one rising score. → `tokn loopgraph` · `/learn loopgraph`

- **Measure quality, then fix it — on a loop.** You can't improve what you don't
  score. *Example: you suspect your agent "sometimes invents a citation." TOKN
  turns that worry into a countable metric, grades a batch of runs, applies a fix,
  and re-grades against your configured baseline.*
  → `tokn flywheel` · `/learn flywheel`

- **Field-specific checks.** Medicine, finance and engineering need more than a
  plausible answer. *Example: flag missing evidence in a study, or hold a
  financial analysis for the required review.* Domain workflows add checks and
  gates, but remain decision support—not professional approval.
  → see **Domain harnesses** in [CAPABILITIES.md](CAPABILITIES.md)

- **Local workflows that can be prepared for an air gap.** Tabular prediction
  uses explicit local data and pre-staged model files, with no runtime model
  downloads. For agent workflows, select a local model and `--air-gap`; cloud
  models necessarily send their inputs to the configured provider. Disable
  unrelated install registration and update checks with `TOKN_NO_REGISTER=1`
  and `TOKN_NO_UPDATE_CHECK=1`. Enforce network isolation at the host boundary
  when required; runtime settings are not an OS sandbox.

- **Customize without waiting for a vendor.** Override prompts with files.
  *Example: a new model follows instructions differently—you tune the prompt
  without recompiling. Workspace overrides require explicit trust.*
  → `/learn customize`

**See it clearly:** `tokn config doctor` shows exactly which config files and env
vars are in effect (secrets redacted); `tokn introspect` prints a machine-readable
capability contract.

**Learn more:** the full tour is in **[CAPABILITIES.md](CAPABILITIES.md)**. Inside
a session, `/learn` opens an interactive lesson for any concept above
(e.g. `/learn loopgraph`), and `tokn --help` is always the authoritative,
version-accurate catalog.

---

> Start here: download for your OS → **verify the signature** → put it on your
> `PATH` → try the **[Community quick start](#community-quick-start--no-trial-required)**.
> A trial is optional for premium features.
>
> Prefer a guided, copy-paste walkthrough? **[GETTING_STARTED.md](GETTING_STARTED.md)**
> takes you from a fresh download to five runnable domain previews and a full
> offline governed-judgment example, with the expected output printed for each
> step — no API key and no trial.
>
> ⚠️ **Platform note — Apple Silicon.** **Developer-license support is not ready on
> Apple Silicon (macOS arm64).** See [Platform support](#platform-support) before you
> download.

> Curious what it does? See **[CAPABILITIES.md](CAPABILITIES.md)** for a quick tour —
> or just run `tokn --help` after installing.

## Quick start — short forms

Once TOKN is on your `PATH` and a model is configured
([section 4](#4-point-tokn-at-a-model)):

```sh
tokn                              # interactive session (same as: tokn agent-repl)
tokn "fix the failing test"       # open the session and run this prompt first
tokn -p "summarise this repo"     # one-shot: run once, print, exit (agent-run)
echo "list TODOs" | tokn -p       # piped text with no prompt becomes the prompt
git diff | tokn -p "review this"  # piped text with a prompt is attached as data
tokn -c                           # resume the last unfinished run in this repo
tokn -p "..." -m <model>          # -m / --model sets the model name
tokn agent-run --help-all         # every flag; --help shows the essentials
```

Outside a terminal (CI, scripts), `tokn "..."` runs once instead of opening the
session. Use `--no-stdin` to ignore piped input. The long forms such as
`tokn agent-repl` and `tokn agent-run --prompt ...` still work and are clearer
in scripts.

## Recent highlights

Updated for **[v0.3.115](https://github.com/bhakthan/tokn-dist/releases/tag/v0.3.115)**.
These are selected capabilities, not the full command catalog:

- **Software factory.** Declare intent, invariants, gates and budgets in one
  spec. Agent roles then refine, build, review, test and release each change,
  with a human approving prod. An observer turns CI failures and incidents into
  the next work items. Roles can mix frontier, open-weights and local models.
  → [RNA-seq software factory](examples/rnaseq-software-factory/README.md)
- **Reviewable database and CSV ontologies.** Map source types and relationships,
  optionally enrich descriptions, then batch advisory decision questions.
  Generated SHACL shapes can be checked against actual RDF rows with external
  tools. Database constraints remain distinct from CSV inferences.
  → [PostgreSQL and an Excel-exported CSV](examples/postgresql-auto-ontology/README.md)
- **Always-on agents, with handoffs.** An inbox wakes an agent for a bounded
  run; later events can continue the same session. Two agents can pass a case
  between configured desks, each with its own workspace, tools and budget.
  Approval-requiring actions are denied when unattended.
  Start with [one intake agent](examples/always-on-claims-intake/README.md), then
  [two collaborating desks](examples/always-on-claims-desks/README.md).
- **TOKNish: checkable receipts for agent work.** Inspect the record behind a
  worker's result instead of relying on "done." See the
  [simple example below](#toknish--a-checkable-receipt-for-agent-work).
- **Local models working together.** Combine a coding model, a vision model
  and a small decision model on one synthetic insurance claim. They prepare
  evidence and referrals; a human decides.
  → [loss inspection](examples/insurance-loss-inspection/README.md) ·
  [local llama.cpp setup](examples/local-llamacpp/README.md)
- **Prompt changes backed by evidence.** Try a correction against recorded
  failures, then regression-check it before human-approved promotion.
  `tokn doctor prompts` also checks your prompt configuration without editing it.
  → [evidence-earned prompting](examples/evidence-earned-prompting/README.md)
- **Broader domain coverage.** The 38 modes include healthcare revenue cycle,
  manufacturing quality, ESG, insurance, trade compliance and pharmacovigilance.
  → [domain overview](CAPABILITIES.md#domain-harnesses)

Other walkthroughs cover [ontology from tables](examples/ontology-from-tables/README.md),
[grounded decisions](examples/grounded-decisions/README.md),
[agent teams](examples/agent-organization/README.md) and
[your existing coding CLI or editor](examples/coding-clis/README.md).

> 🔑 **Bring your own model.** TOKN needs an LLM provider (OpenAI, Azure OpenAI,
> Anthropic/Claude, Gemini, or a local runtime). See **[SETUP.md](SETUP.md)** to
> configure your provider and API key in under a minute.

> ⚖️ **Legal:** TOKN is proprietary, evaluation-only software provided **"as is",
> with no warranty and no liability**. It may **not** be copied, redistributed, or
> reverse-engineered — **including any attempt to extract, reconstruct, or retrain
> on its internals with AI/LLM tools**. Cloning or downloading this repo grants you
> **no** such rights. This is a **feedback-first program**: providing feedback is a
> **condition** of the trial. AI output is not professional advice and must be
> verified; you are responsible for compliance and assume all risk. By downloading,
> cloning, or using TOKN you agree to the **[License & Disclaimer](LICENSE.md)** —
> please read it.

---

## TOKNish — a checkable receipt for agent work

**Think of TOKNish as a receipt, not another chatbot.** When TOKN agents
collaborate, a result should come with a record you can inspect—not just "done."

For example, imagine asking a worker to check a small code change:

```mermaid
flowchart LR
    A["Task"] --> B["Worker"]
    B --> C["Reported result, evidence and uncertainty"]
    C --> D["Check the exchange record"]
    D --> E["Review tests and decide"]
```

| Without a receipt | What you want to review |
|---|---|
| "The checks passed." | **Result:** unit tests passed. **Evidence:** test-run log. **Not checked:** integration tests. |

That is the idea behind **TOKNish federation**: a checkable record of exchanged
messages, with evidence and uncertainty attached to claims.
The example above is an illustration, not literal output.

For an existing TOKNish session, the audit command can check the recorded
exchange and show a plain-English reading:

```sh
tokn toknish audit <session-id> --gloss
```

Use the session ID from your run; `tokn toknish audit --help` explains log
locations and authentication checks. **A clean audit does not prove that the
worker's answer is correct.** You still need tests and appropriate human review.

**Separate experiment: TOKNish-M** benchmarks shorter model answers against
ordinary prose. It is a benchmark pilot, not an automatic change to live agent
sessions or a promise of token savings.

## Local prediction — models beyond chat

Community users can build classifiers and regressors without a trial or API key:

```sh
tokn tabular --help
```

For a complete copy-paste run in a fresh scratch directory, follow
**[TABULAR.md](TABULAR.md#a-complete-first-run)**. It creates a starter and runs
inspection, diagnostics, evaluation and prediction with explicit absolute paths.
The starter is a small **synthetic example**, not a production benchmark.
Also try `maintenance` or `repair-cost`. Baseline execution needs Python 3.11+
with no extra packages. Inspection and scaffolding need only TOKN.

Optional **NVIDIA Kumo-Tabular** uses locally staged dependencies and hashed
classifier/regressor weights. Even the large checkpoints are individually under
1 GB (~855 MB and ~863 MB); both together, dependencies and RAM/VRAM need more
capacity. Nothing is installed or downloaded automatically.
Optional **Google TabFM** is also supported with staged local weights and its
required non-commercial licence acknowledgement; see the guide before choosing it.

The agent can create the workflow and explain evaluation; the predictor computes
the outputs. Probabilities and regression intervals are not proof of calibration
or permission to act. Numerical/categorical CSV is supported; automatic text
features and remote serving are not.

See **[TABULAR.md](TABULAR.md)** for offline preparation, model selection and
agent tools. In the REPL, `/learn tabular` explains the same workflow.

## Let TOKN improve its own harness — a worked domain example

**`tokn harness evolve`** runs TOKN on a real task and reads the evidence. It
then proposes harness improvements, tries each one in a throwaway copy, and
keeps the best. A judge grades each result against a rubric the agent never
sees. Your source data and guardrails are sealed for the whole run.

**[examples/grid-screening](examples/grid-screening/README.md)** walks through
this step by step on a substation N-1 screening task, with a decision model in
the loop. It needs your own LLM key and decision-model backend. In the REPL,
`/learn harness` explains the concepts.

**[examples/decision-council](examples/decision-council/README.md)** runs several
decision models from different vendors in parallel on a 24-turbine maintenance
table. A council vote escalates only the rows they disagree on, and a reasoning
LLM settles those rows. An offline grader checks the result against the policy.
It needs keys for two or more decision-model backends and one LLM.

**[examples/openshell](examples/openshell/README.md)** runs TOKN inside an
[NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) sandbox. One command
generates a provider profile, an enforcing egress policy and a non-root image,
then launches it. Your API key stays on the host and never enters the sandbox.
It needs Linux or WSL 2, OpenShell and Docker or Podman.

**[More walkthroughs](examples/README.md)** cover coding, domain checks,
browser tasks, knowledge workflows and collaborating agents. Each guide
explains its scenario, prerequisites and limitations. New to TOKN? Start with
[first-ten-minutes](examples/first-ten-minutes/README.md).

## Compose a solution, not just a chat

**`tokn solution` plans an application around your requirement:** combine a
configured language model, optional small models, tabular prediction, judgments,
specialists and tools where they are actually available. Review the graph, then
run it with measurable acceptance checks and an inspectable result.

```sh
tokn solution catalog --root .
tokn solution plan --help
tokn plugin install hybrid-solutions
```

In the REPL, `/learn hybrid-solutions` explains planning, generation and execution.
`run` and `solve` require `--execute`; remote calls separately require
`--allow-external`. Optional generated-Python execution needs `--allow-code`,
is off by default, general-domain-only and **is not a sandbox**. Python's own
file, network and subprocess operations do not inherit TOKN guards; execution
warnings make this explicit. Plans do not unlock domains or
turn model predictions into permission to act.

## Platform support

| OS | Architecture | Asset | Community tier | Developer-license activation |
|----|--------------|-------|----------------|------------------------------|
| Windows | x64 | `tokn_windows_amd64.exe` | supported | supported |
| Linux | x86_64 | `tokn_linux_amd64` | supported | supported |
| Linux | arm64 | `tokn_linux_arm64` | supported | supported |
| macOS | Intel | `tokn_darwin_amd64` | supported | supported |
| macOS | Apple Silicon | `tokn_darwin_arm64` | supported | **not ready** |

**Developer-license support is not ready on Apple Silicon (macOS arm64).** The
`tokn_darwin_arm64` download is available for Community use. The
[Community quick start](#community-quick-start--no-trial-required), including
the domain previews and offline judgment examples, needs no developer licence.
That download does not imply developer-license readiness or a workaround for it.
This is a readiness notice, not a diagnosis of a particular activation failure.

Two things follow from that, and we would rather say them plainly than let you
discover them:

- **Do not spend your trial on an Apple Silicon Mac.** The trial is limited to
  one per machine. Until developer-license support is ready, use a supported
  platform to evaluate licensed features instead.
- **This is about Apple Silicon specifically, not macOS.** macOS on Intel is
  fully supported, licensing included.

If licensing on Apple Silicon is a blocker for you, say so in an issue — that is
the signal we act on.

## 1. Download

Grab the latest build for your platform from the
**[releases page](https://github.com/bhakthan/tokn-dist/releases/latest)**:

| OS | Architecture | File |
|----|--------------|------|
| Windows | x64 | `tokn_windows_amd64.exe` |
| macOS | Apple Silicon | `tokn_darwin_arm64` |
| macOS | Intel | `tokn_darwin_amd64` |
| Linux | x86_64 | `tokn_linux_amd64` |
| Linux | arm64 | `tokn_linux_arm64` |

Every release also publishes **`SHA256SUMS`** and **`SHA256SUMS.sig`**. Download
them too — you need both for step 2.

The commands below pass **no tag**, so `gh` resolves the current latest release.
Prefer that over pinning a version in a document: a pinned tag in a README goes
stale on the next release and silently hands newcomers an old binary.

**Windows (PowerShell)**
```powershell
gh release download --repo bhakthan/tokn-dist `
  --pattern "tokn_windows_amd64.exe" --pattern "SHA256SUMS*" `
  --dir . --clobber
```

**macOS / Linux**
```bash
gh release download --repo bhakthan/tokn-dist \
  --pattern "tokn_$(uname -s | tr A-Z a-z)_*" --pattern "SHA256SUMS*" \
  --dir . --clobber
```

To pin a specific build instead, insert the tag as the first argument, e.g.
`gh release download v0.3.44 --repo bhakthan/tokn-dist …`. Prefer these URLs
over scraping the releases page: the assets are the artifact, the HTML is not.

## 2. Verify what you downloaded

TOKN is a binary that will run with your permissions on your machine. Verify it.
There are **two independent layers**, and they are not equally strong.

### The release public key

This is the ed25519 public key that signs every TOKN release manifest. It is
published here, in the README, **on purpose** — it has to reach you by a path
other than the download it authenticates:

```
3O2DznsYRy+OU2gTIbpvOfw0O6tUIIRQfiOUDbfoHxo=
```

It is also printed in the release notes of every release. The two should always
agree; if they ever disagree, **stop** and open an issue.

### Layer 1 — the checksum (integrity)

Confirms the bytes arrived intact and match what the release claims.

**Windows (PowerShell)**
```powershell
(Get-FileHash .\tokn_windows_amd64.exe -Algorithm SHA256).Hash.ToLower()
Select-String -Path .\SHA256SUMS -Pattern "tokn_windows_amd64.exe"
# the two hashes must match, character for character
```

**macOS**
```bash
shasum -a 256 -c SHA256SUMS --ignore-missing
```

**Linux**
```bash
sha256sum -c SHA256SUMS --ignore-missing
```

### Layer 2 — the signature (authenticity)

**This is the layer that actually matters.** The checksum alone buys you very
little: anyone who can replace the binary in a release can replace `SHA256SUMS`
in the same breath, and your checksum will match a file they wrote. The
signature is the part they cannot forge without the private key, which is never
in this repo, never in the binary, and never in CI logs.

`SHA256SUMS.sig` is base64 of a raw 64-byte ed25519 signature over the exact
bytes of `SHA256SUMS`. Verify it with OpenSSL — already present on macOS and
Linux, and shipped with Git for Windows at
`C:\Program Files\Git\usr\bin\openssl.exe`:

**Windows (PowerShell)**
```powershell
$ssl = "C:\Program Files\Git\usr\bin\openssl.exe"
$KEY = "3O2DznsYRy+OU2gTIbpvOfw0O6tUIIRQfiOUDbfoHxo="

# wrap the raw key as a PEM SubjectPublicKeyInfo (the prefix is the fixed
# 12-byte ed25519 DER header — it is the same for every ed25519 key)
"-----BEGIN PUBLIC KEY-----`nMCowBQYDK2VwAyEA$KEY`n-----END PUBLIC KEY-----" |
  Set-Content tokn-release.pem -Encoding ascii

# decode the base64 signature to raw bytes
[IO.File]::WriteAllBytes("$PWD\SHA256SUMS.sig.raw",
  [Convert]::FromBase64String((Get-Content SHA256SUMS.sig -Raw).Trim()))

& $ssl pkeyutl -verify -pubin -inkey tokn-release.pem `
  -rawin -in SHA256SUMS -sigfile SHA256SUMS.sig.raw
```

**macOS / Linux**
```bash
KEY=3O2DznsYRy+OU2gTIbpvOfw0O6tUIIRQfiOUDbfoHxo=

printf -- '-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA%s\n-----END PUBLIC KEY-----\n' "$KEY" \
  > tokn-release.pem
base64 -d < SHA256SUMS.sig > SHA256SUMS.sig.raw   # macOS: base64 -D

openssl pkeyutl -verify -pubin -inkey tokn-release.pem \
  -rawin -in SHA256SUMS -sigfile SHA256SUMS.sig.raw
```

Expected output — and **nothing else is acceptable**:

```
Signature Verified Successfully
```

Anything else (`Signature Verification Failure`, a non-zero exit code, an
OpenSSL error) means **do not run the binary**. A failure here is not a
formatting problem to work around; it is the check doing its job.

> **Two honest caveats.**
>
> 1. **Do not take the public key from the binary you are verifying.** TOKN
>    compiles this same key in so that `tokn update` can verify future releases,
>    but using it to check the download it came from is circular — a substituted
>    binary would simply carry a substituted key and cheerfully approve itself.
>    Use the key from this README, or from the release notes.
> 2. **`openssl` must not come from the download either.** Use your system's
>    OpenSSL or the one Git installed. This is why the instructions above use a
>    third-party tool rather than a `tokn verify` subcommand — asking an
>    unverified binary whether it is trustworthy is not a security check.
>
> OpenSSL 3.x is required (`-rawin` is how it does ed25519). Check with
> `openssl version`.

### After the first install, this is automatic

You only do the above **once**, for your first download. From then on:

```
tokn update
```

performs *both* layers itself before it will replace the running binary, and it
is **fail-closed** — no bypass environment variable, no `--force`, no "continue
anyway" prompt. It refuses a release with no `SHA256SUMS` at all, and it prints
which layer it applied so you can see whether authenticity was checked or only
integrity.

## 3. Put it on your PATH

**Windows (PowerShell)**
```powershell
Move-Item .\tokn_windows_amd64.exe C:\Tools\tokn.exe
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Tools", "User")
```

**macOS**
```bash
chmod +x tokn_darwin_arm64
sudo mv tokn_darwin_arm64 /usr/local/bin/tokn
```

**Linux**
```bash
chmod +x tokn_linux_amd64
sudo mv tokn_linux_amd64 /usr/local/bin/tokn
```

Verify:
```bash
tokn --version
tokn --help
```

## 4. Point TOKN at a model

TOKN is **bring-your-own-model** — it runs against a provider you already have
(OpenAI, Azure OpenAI, Anthropic/Claude, Gemini, OpenRouter, Fireworks) or a local
runtime (Ollama, llama.cpp/GGUF, ONNX). It even drives **computer-use** models —
Microsoft's **Fara1.5** (via `tokn fara-run`, with a real coordinate browser) and
**MagenticBrain**. Set two variables plus your key, e.g.:

```bash
export NOSPACE_MODEL_PROVIDER="openai"
export NOSPACE_MODEL_NAME="YOUR_MODEL_ID"
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
tokn auth status        # reports credential readiness, not a successful model call
tokn config doctor      # see every config file & env var TOKN picks up (secrets redacted)
```

Replace the placeholders before running. Prefer a file? The supported model
preferences and API keys above can go in an ignored `.env`; real environment
variables win. Endpoint overrides and authentication switches need explicit
environment configuration. **Full setup, Azure `az login` auth and local-model
preparation: [SETUP.md](SETUP.md).**

## Community quick start — no trial required

Available in **v0.3.44 and later**. After installing and verifying TOKN, these
features work in the free Community tier. No trial activation, no API key, no
model provider and no embedded wiki is required. Specialized domain *workflows*
remain separately licensed — what is free is described precisely below.

**Step-by-step version with expected output for every command:
[GETTING_STARTED.md](GETTING_STARTED.md).**

### Five domain previews you can run right now

Each preview feeds a small **fixed synthetic case** to a **real TOKN domain
validator** — the same exported function the licensed domain plug calls — and
prints what it decided. One case is accepted, one is blocked, and the blocked
case shows the finding text the validator actually produced.

```text
tokn community list
tokn community demo --domain powergrid
tokn community demo --domain geospatial
tokn community demo --domain batterypass
tokn community demo --domain finrisk
tokn community demo --domain atmchem
```

To run all five plus the offline judgment walkthrough in one unattended pass,
this repository also ships `scripts/community-smoke.sh` (bash) and
`scripts/community-smoke.ps1` (PowerShell). Each needs only the `tokn` binary,
works in a temp directory it deletes on exit, and exits `0` only if every check
passed.

| Preview | The question it answers |
|---------|-------------------------|
| `powergrid` | After a single-element outage, is every bus still inside the NERC TPL-001-5 N-1 voltage band? |
| `geospatial` | Is this coordinate reference system valid for computing **area**, or will the number be plausible and wrong? |
| `batterypass` | Does the chemistry declared on an EU Battery Passport agree with the cathode formula declared in the same document? |
| `finrisk` | Is this misstatement material — and under whose rules? Classified under IFRS; refused when no regime is named. |
| `atmchem` | Is this PM2.5 simulation good enough to support a regulatory statement, or does it fail the Boylan & Russell performance criteria? |
Add `--json` to either command for machine-readable output.

**What a preview is, honestly.** It computes locally, reads no file you supply,
writes nothing to disk, makes no network call of its own, activates no domain and
registers no domain tool — the inputs are compiled in, which is exactly why it is
free and safe to run anywhere. (TOKN's startup does its usual licence lookup and
may record a one-time anonymous install count or check for a newer release;
`TOKN_NO_REGISTER=1` and `TOKN_NO_UPDATE_CHECK=1` switch those off — see
[GETTING_STARTED.md](GETTING_STARTED.md).) It shows you *that a check exists and
what it decides*. The
licensed domain adds the lifecycle state machine, the full validator set, the
gates that block state transitions, the tool surface and the subagents. Preview
output is a decision-support illustration on synthetic data — **not**
engineering, regulatory, clinical or compliance advice.

### Offline governed judgments

Governed judgments separate typed model interpretation from deterministic policy.
They are advisory recommendations — never permission to execute a tool or bypass
a gate.

```text
tokn judgments example
tokn judgments evaluate --help
```

`judgments example` prints a local rules bundle to stdout; it runs no evaluation
and writes no file. `judgments evaluate` takes explicit bundle and request files;
with the `rules` provider and `--air-gap` it evaluates entirely offline, with no
model call. **A complete worked example — bundle, request, a passing run and a
failing run, with the exact output of each — is in
[GETTING_STARTED.md](GETTING_STARTED.md#3-governed-judgments-offline-no-key).**

### Optional: try a Jev decision model

Use your own Jev API key. `status` checks configuration without calling the decision
API. **Running `triage` sends the supplied task text to Jev and may incur provider
charges.** Use synthetic or approved text, never secrets or unapproved sensitive data.

**Windows (PowerShell)**
```powershell
$env:JEV_API_KEY = "YOUR_KEY"
tokn system-one status
tokn system-one triage --text "Add a unit test for trimming spaces"
```

**macOS / Linux**
```bash
export JEV_API_KEY="YOUR_KEY"
tokn system-one status
tokn system-one triage --text "Add a unit test for trimming spaces"
```

Keep keys out of source control. This triage example returns an advisory assessment;
it does not edit code or run tools. For multiple typed questions over the same state,
`tokn system-one evaluate` asks all of them against one explicitly supplied
state. (That is not the same as `tokn system-one batch`, which runs *independent*
states with bounded parallel calls.) Use `tokn system-one evaluate --help` for
the explicit input-file interface.

Jev is not the only option. Choose another backend with `SYSTEMONE_BACKEND`, and
list the known models with `tokn system-one models`:

| Backend | Model | Configure |
| --- | --- | --- |
| `openai` | OpenAI Decisions API (`gpt-6-luna`) | `OPENAI_API_KEY` |
| `azure` | Azure OpenAI Decisions API (`gpt-6-luna`, generally available; not in East US 2) | `AZURE_OPENAI_ENDPOINT` + `SYSTEMONE_MODEL` (your deployment name); `AZURE_OPENAI_API_KEY` or Microsoft Entra ID |
| `microsoft` | Microsoft-Decision-1 (Microsoft Foundry) | `DECISION_API_ENDPOINT`, `DECISION_API_KEY`, `DECISION_API_MODEL` |
| `compatible` | Bespoke Labs Nimble (hosted) | `SYSTEMONE_BASE_URL`, `SYSTEMONE_API_KEY`, `SYSTEMONE_MODEL` |
| `compatible` | Cloudflare Clef and Clef Flash (open weights) | self-hosted endpoint: `SYSTEMONE_BASE_URL`, `SYSTEMONE_MODEL` |

A question the model declines to answer is reported as refused, never guessed.
The same provider-charge and data cautions apply to every hosted backend.

### Optional: the bundled `decision-models` skill pack

TOKN embeds a skill pack adapting TypeSafe's MIT-licensed agent skill — bounded
decision design, structured state, batching independent work, keeping the final
policy deterministic. It is **in the public binary**: no npm, no SDK, no GitHub
token, no network call.

```bash
tokn plugin install decision-models
```

It installs under your TOKN home (`~/.tokn/plugins/`), never into your repository,
and is **instructions only** — no tools, no hooks, no agents. Inside an agent
session, `/skill inspect tokn-decision-models:typesafe-ai-decisions` shows the
summary and `/skill invoke ...` prints the full instruction text. Both only
print — despite the name, `invoke` does not start a task; read it, then make
your request in your own words, which runs on your model at your own cost. Full
walkthrough: **[GETTING_STARTED.md](GETTING_STARTED.md#6-optional-the-decision-models-skill-pack)**.

### Developer path: tools, skills, hooks, permissions

Four different things separated by a permissions boundary: a **tool** executes, a
**skill** is only instructions, a **hook** runs your command with your
permissions, and **trust** decides what is offered at all. The on-ramp is built
into the binary:

```bash
tokn community guide     # or just: tokn community
```

Discover them first — no key, no licence, all offline:

```bash
tokn agent-tools --mcp-disabled   # tools available right now
tokn plugin catalog               # installable skill packs and plugins
tokn plugin list                  # what is already visible
tokn doctor --list                # providers and how to connect one
```

Then inspect inside a session (`tokn` or `tokn agent-repl`) with `/skill list`, `/hooks list`,
`/permissions show`, `/trust audit` before enabling anything. Those commands
only report configuration — `/hooks list` in particular does not tell you which
hooks are live, and a workspace hook additionally needs
`tokn trust --capability hooks` plus a restart before it will run. Full path,
including a safe prompt-customization example:
**[GETTING_STARTED.md](GETTING_STARTED.md#7-developer-path-tools-skills-hooks-permissions)**.

### Learn without the wiki

The public download excludes the embedded wiki, **not the built-in lessons or these
Community features**. Inside a configured session (`tokn`, or `tokn agent-repl`), run:

```text
/learn system-one
/learn judgments
/learn decision-models
```

These explain typed decisions, shared-state batching, and governed judgments.
Configure a generative LLM using [SETUP.md](SETUP.md) for agent sessions;
the standalone Jev example above needs only Jev credentials, not an LLM key.
The domain previews and the offline judgment examples need neither.

---

## What TOKN is made of — concepts and commands

[![TOKN capability with control: describe, equip, work, check and review; tools, skills, plugins and hooks support the journey.](docs/assets/community-depth.png)](docs/assets/community-depth.png)
*From intent to a reviewable result. The battery-passport example is a fixed
Community preview, not a production approval. Click for the full 4K image.*

Most of TOKN is one of six things. They are genuinely different in what they can
*do to your machine*, which is why they have separate commands and a separate
permissions boundary. This table is the map; the walkthrough is
[GETTING_STARTED.md](GETTING_STARTED.md#7-developer-path-tools-skills-hooks-permissions).

Two places to type. **[shell]** is your normal terminal. **[repl]** is inside an
agent session you started with `tokn` (or `tokn agent-repl`), which needs a configured model
([SETUP.md](SETUP.md)). Everything marked [shell] below works with no model, no
key and no licence.

| Concept | What it actually is | Discover | Inspect | Use / enable |
|---|---|---|---|---|
| **Tool** | An executable function with a typed schema that the model may call during a session. Runs code. | `tokn agent-tools --mcp-disabled` [shell] | same command prints each schema | offered automatically in a session, subject to your permissions and approval prompts |
| **Skill** | Reusable instructions, with optional supporting files; actions still use the session's tools and permissions. | `/skill list` [repl] | `/skill inspect <id>` (metadata) [repl] | `/skill invoke <id>` **prints** the text [repl]; then make your request in your own words. `invoke` does not start a task |
| **Plugin / pack** | An installable bundle that *carries* skills (and, for some packs, more). | `tokn plugin catalog` [shell] | `tokn plugin list` [shell] | `tokn plugin install decision-models` [shell] — installs to `~/.tokn/plugins/`, never into your repo |
| **Hook** | A lifecycle callback that runs **your shell command** with **your** permissions at an agent event. | `/hooks list` [repl] — configuration only, not proof a hook is live | `/hooks test` is an alias of `/hooks list`: both validate the settings files and execute nothing [repl] | `/hooks add PreToolUse <command>` writes config [repl]; it does **not** activate it. Also needs `tokn trust --capability hooks <path>` [shell] and a restart |
| **Lesson** | Built-in explanations of TOKN's own ideas, shipped in the binary. | `/learn` lists every topic [repl] | — | `/learn judgments`, `/learn system-one`, `/learn decision-models` [repl] |
| **Preview** | A fixed synthetic case run through a real domain validator. | `tokn community list` [shell] | `--json` adds a machine-readable form | `tokn community demo --domain <name>` [shell] |

And four things that control the rest:

| Control | What it decides | Commands |
|---|---|---|
| **Trust** | Whether a workspace may use hooks, MCP servers, command expansion or prompt overrides at all. Nothing is granted implicitly. | `tokn trust status` / `tokn trust --capability hooks <path>` [shell]; `/trust audit` [repl] |
| **Permissions** | Which paths and operations a session may touch. | `/permissions show` [repl] |
| **Model config** | Which provider and model a session uses, and what it costs you. | `tokn doctor --list` [shell]; `/model`, `/models` [repl] |
| **Custom instructions** | Prompt text is data: mode and domain prompts are files you can replace without rebuilding. | write `~/.tokn/prompts/mode-<name>.md`, then `/mode <name>` [repl]. Project-level overrides require the `prompts` trust capability, so a cloned repo cannot quietly rewrite the agent's instructions |

**Typed decisions** are the idea underneath several of these: instead of asking a
model for prose and parsing hope out of it, you define the verdicts up front and
get a structured answer back. Two surfaces ship in the free tier —
`tokn judgments` (rules provider, fully offline, advisory only) and
`tokn system-one` (typed questions over one shared state) — plus the
`decision-models` skill pack, which teaches the design pattern. See
[Offline governed judgments](#offline-governed-judgments) above.

Three boundaries worth stating plainly, because they are easy to assume wrong:

- **Installing is not enabling.** Installing `decision-models` adds instructions,
  not executable domain access or permission grants.
  Adding a hook writes configuration, and the hook still does not run until you
  grant that workspace the `hooks` capability and restart.
- **Printing is not running.** `/skill invoke` and `/hooks test` both only
  report; neither executes anything (`/hooks test` is the same command as
  `/hooks list`). `/hooks list` shows what is *configured*, which is not the
  same as what is *loaded*.
- **Free is not silent.** The previews, `tokn judgments` with the rules provider,
  the lessons and all the discovery commands above need no key, no licence and no
  network. TOKN's own startup is separate: it resolves your licence file, counts
  the install once and checks for updates daily. Set `TOKN_NO_REGISTER=1` and
  `TOKN_NO_UPDATE_CHECK=1` to turn those two off. Anything that calls a model —
  an agent session, a Jev evaluation — runs on your credentials at your cost.

---

## What full domain access adds

[![TOKN across science, engineering and business, with Community core capabilities separated from licensed domain workflows.](docs/assets/community-breadth.png)](docs/assets/community-breadth.png)
*Breadth without hidden access promises: Community includes fixed air-quality,
battery-passport, financial-materiality, geospatial and power-grid previews. Specialized workflows retain their licensing
and safeguards. Click for the full 4K image. [Image sources](docs/assets/README.md).*

A **domain harness** adds field-specific tools, checks and review workflows.
TOKN has **38 domain modes** across science, engineering, healthcare and business.
Launch an entitled mode with `tokn agent-repl --mode <name>`.
The free tier previews five domains against real validators.

Browse the [domain overview](CAPABILITIES.md#domain-harnesses), or inspect
your installed roster with `tokn introspect --section modes`.

What a licence changes:

| | Community preview | Licensed domain |
|---|---|---|
| Input | five fixed synthetic previews, compiled in | domain-permitted data; some domains remain synthetic/sandbox-only |
| Surface | one validator call, printed | the domain's full tool set, callable by the agent |
| Process | a single verdict | a lifecycle state machine with named states |
| Gates | shown, not enforced on anything | enforced on transitions |
| Coverage | 3 domains | 38 domain modes; availability depends on entitlement |

**A licence does not bypass a domain's safety gates.** It enables entitled
workflows, not blocked transitions or weaker evidence requirements. Outputs
remain decision support, not clinical, legal or regulatory certification. And
**installing instructions is not unlocking a domain** — a skill pack like
`decision-models` is text, registers no domain tool or gate, and is not one of
the 38 domains. Running `tokn agent-repl --mode <domain>` engages the harness.

Full roster with a short description per domain:
**[CAPABILITIES.md](CAPABILITIES.md#domain-harnesses)**. Licensing availability
by platform is covered under [Platform support](#platform-support) — note in
particular that developer-licence support is **not ready** on Apple Silicon.

## 5. Optional: start your 14-day trial

TOKN runs in a free **community** tier by default. Start a **14-day trial**
for licensed features—trial issuance needs no account or internet connection:

```bash
tokn license trial        # or: tokn trial
tokn license status       # tier, expiry, days remaining
```

The trial writes a signed, machine-bound token to `~/.tokn/license.json` and is
limited to **one trial per machine**. When it expires, TOKN automatically
reverts to the community tier — the binary keeps working.

> **Restricted domains (`synbio`):** Not included in self-issued trials;
> requires explicit administrator approval.

> ⚠️ **Apple Silicon:** developer-license support is **not ready** on macOS
> arm64. Do not rely on a trial there to evaluate licensed workflows. The
> trial is one per machine — use it on Windows, Linux, or an Intel Mac. See
> [Platform support](#platform-support). The free Community tier, including the
> domain previews, works on Apple Silicon today.

## 6. Stay up to date (works during the trial)

TOKN updates itself in place — no reinstall, no package manager:

```bash
tokn update             # install the latest release
tokn update --check     # check only
tokn update --rollback  # revert to the previous version
```

Updating **does not** reset or invalidate an active trial.

---

## Tiers at a glance

| Tier | Cost | Features | Expiry |
|------|------|----------|--------|
| Community | Free | Core agent loop, built-in lessons, System One decisions, governed judgments, and read-only domain previews (`tokn community`); licensed domain workflows remain gated | Perpetual |
| Trial | Free | Standard licensed features (`synbio` excluded; requires admin approval) — see [Platform support](#platform-support); not ready on Apple Silicon | 14 days, one per machine |
| Pro / Enterprise | Paid | Full surface, production & regulated use (`synbio` requires explicit admin approval) | Annual / perpetual |

## Support & licensing

- Questions, trial extensions, or Pro/Enterprise licensing: **open an issue in this repo**
- Found a bug during your trial? Open an issue in this repo.

## Legal & disclaimer

TOKN is **proprietary, evaluation-only** software. **All Rights Reserved.**

- Provided **"AS IS", with no warranty of any kind.**
- The owner/contributors are **not liable for any damages** arising from its use.
- You **may not copy, redistribute, modify, or reverse-engineer** it.
- AI output **is not professional advice**, may be wrong, and **must be
  independently verified**. Domain features (medical, legal, financial, etc.) are
  decision-support only — **not** certified for clinical, production, or regulated
  use.
- **You are solely responsible for compliance** with all applicable laws
  (data protection, export control, sector regulations) and **assume all risk**.

**By downloading or using TOKN you accept the full
[License & Disclaimer](LICENSE.md).**

_This distribution repo contains released binaries only; the source code is
maintained privately and is not licensed hereunder._
