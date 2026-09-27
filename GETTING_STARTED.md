# Getting started with TOKN — no API key, no trial

This is the hands-on path. Every command below runs in the free **Community**
tier: **no API key, no model provider, no trial activation.** None of them sends
your code, your files or your prompts anywhere.
The expected output is printed for each step so you can tell success from
failure without guessing.

> **What "offline" means here.** The commands themselves do the work locally.
> TOKN's *startup* is separate: on first run it records a one-time anonymous
> install count, and once a day it checks whether a newer release exists. Neither
> carries your data, and both are opt-out. For a strictly silent run, set these
> first:
>
> ```bash
> export TOKN_NO_REGISTER=1 TOKN_NO_UPDATE_CHECK=1        # macOS / Linux
> ```
> ```powershell
> $env:TOKN_NO_REGISTER = "1"; $env:TOKN_NO_UPDATE_CHECK = "1"   # Windows
> ```
>
> `TOKN_NO_TELEMETRY=1` and `DO_NOT_TRACK=1` are accepted as equivalents to the
> first. Startup also resolves your licence file, which is why you may see a
> tier banner on stderr; that is local bookkeeping, not a request.

Roughly fifteen minutes, start to finish.

- [0. Before you start](#0-before-you-start)
- [1. Install and confirm](#1-install-and-confirm)
- [2. Three domain previews](#2-three-domain-previews)
- [3. Governed judgments, offline (no key)](#3-governed-judgments-offline-no-key)
- [4. Optional: your own Jev key](#4-optional-your-own-jev-key)
- [5. Optional: a configured LLM and the agent session](#5-optional-a-configured-llm-and-the-agent-session)
- [What is free, and what is not](#what-is-free-and-what-is-not)

---

## 0. Before you start

### Platform support

**Developer-license support is not ready on Apple Silicon (macOS arm64).**

The arm64 binary is available for Community use; the previews and offline
judgment examples require no developer licence. This does not imply that
**developer-license workflows** are ready. It is a readiness notice, not a
diagnosis of a particular activation failure. The trial is limited to one per machine, so
**do not spend it on an Apple Silicon Mac**: evaluate licensed features on
Windows, Linux, or an Intel Mac instead. macOS on Intel is fully supported,
licensing included. If this blocks you, open an issue — that is the signal we
act on.

See the [Platform support table](README.md#platform-support) for the full matrix.

### Prerequisites

| You need | For | Check it with |
|----------|-----|---------------|
| A terminal | everything | — |
| `gh` (GitHub CLI) | downloading the release assets | `gh --version` |
| `openssl` 3.x | verifying the release signature | `openssl version` |
| A TOKN binary on your `PATH` | everything after step 1 | `tokn --version` |

Two notes, because a missing tool here is the most common first-run failure:

- **`openssl` must be 3.x.** Signature verification uses `-rawin`, which is how
  OpenSSL 3 does ed25519. macOS and most Linux distributions already ship it;
  on Windows, Git for Windows installs it at
  `C:\Program Files\Git\usr\bin\openssl.exe`.
- **`gh` is a convenience, not a requirement.** You can download the assets from
  the [releases page](https://github.com/bhakthan/tokn-dist/releases/latest) by
  hand. `gh` is recommended because it fetches the artifact rather than scraping
  a web page.

Nothing else is needed for this guide. In particular: **no API key, no model
provider, no Docker, no Python, no language toolchain.**

### Where output goes

Nothing in this guide writes to disk unless you redirect it yourself. When you
do — step 3 asks you to save two small JSON files — put them somewhere you own,
under your user account, **not** in a system directory and not inside a git
repository you intend to commit:

**Windows (PowerShell)**
```powershell
$WORK = Join-Path $HOME "tokn-tryout"
New-Item -ItemType Directory -Force -Path $WORK | Out-Null
Set-Location $WORK
```

**macOS / Linux**
```bash
WORK="$HOME/tokn-tryout"
mkdir -p "$WORK" && cd "$WORK"
```

Everything below assumes you are in that directory. To undo this guide
completely, delete it.

---

## 1. Install and confirm

Download and **verify** the binary — the full download, checksum and signature
procedure is in the [README](README.md#1-download). Do not skip the signature
step; it is the layer that actually establishes authenticity.

Then confirm the binary runs:

```text
tokn --version
```

Expected: a version line ending in `v0.3.44` or later, and a `variant:` field.
The public download reports `variant: public`, which means the ~64 MB embedded
documentation wiki is not compiled in. Everything in this guide is unaffected —
the previews, the lessons and the judgment engine are all in the binary.

```text
tokn community list
```

Expected: a catalog of three domain previews. If you see
`unknown command "community"`, your binary predates v0.3.44 — run `tokn update`
(that one command does need internet access) and try again.

You may also see a one- or two-line notice about your licence state, for example
that you are running the free Community tier. That notice is informational.
Nothing in this guide requires a licence.

### Optional: check everything at once

If you would rather confirm the whole free tier in one go before reading on,
this repository ships a smoke script that runs all three previews and the
offline judgment walkthrough. It needs the `tokn` binary and nothing else — no
key, no provider, no trial — and keeps every scratch file in a temp directory
it deletes on exit.

```bash
# macOS / Linux, from a clone or download of this repository
bash scripts/community-smoke.sh
```

```powershell
# Windows PowerShell, from a clone or download of this repository
.\scripts\community-smoke.ps1
```

It prints a named `ok` / `FAIL` line per check and exits `0` only if all of them
pass. A `FAIL` line names what it expected, so you can jump straight to the
matching section below. The rest of this guide walks the same commands by hand,
which is worth doing at least once — the script confirms your install, but it
does not explain the output.

---

## 2. Three domain previews

A preview feeds a **fixed synthetic case** to a **real TOKN domain validator** —
the same exported function the licensed domain plug calls — and prints what it
decided. Each preview shows one **accepted** case and one **blocked** case, and
the blocked case shows the finding text the validator actually produced.

Previews read no file you supply, write nothing, activate no domain and register
no domain tool, and the preview itself makes no network call. The inputs are
compiled in. That is precisely why they are free and safe to run anywhere. (The
startup bookkeeping noted at the top of this guide is separate from the preview
and is opt-out.)

### 2a. `powergrid` — a bus that sags after an outage

```text
tokn community demo --domain powergrid
```

Expected output (abridged):

```text
TOKN community preview — powergrid
Transmission planning — post-contingency bus voltage limits

Question:  After the worst single element outage, is every bus still inside the
           voltage band the reliability standard allows?
Exercises: powergrid.ValidationPipeline.ValidateVoltages with
           powergrid.DefaultPowerGridConfig (NERC TPL-001-5 N-1 band)

Synthetic case A — bus holds up after the outage
  BUS_230_ALDER:   0.982 pu
  allowed band:    0.90–1.10 pu (NERC_TPL_001_5, N-1)
  Verdict: ACCEPTED
  Findings: none

Synthetic case B — the same bus, 0.15 pu lower
  BUS_230_ALDER:   0.831 pu
  Verdict: BLOCKED
  Findings:
    - [CRITICAL] UNDERVOLTAGE at BUS_230_ALDER: 0.8310 pu < 0.90 pu limit (N-1)
```

**Why it matters.** The finding names the bus, the measured value, the limit it
broke and the severity. In the licensed domain that finding is what the N-1 gate
reads: with `require_n1_compliance` and `block_reporting_with_violations` set, a
study carrying it cannot advance to a reportable state. The agent cannot write it
up as clean.

### 2b. `geospatial` — an area that is plausible and wrong

```text
tokn community demo --domain geospatial
```

Expected output (abridged):

```text
Synthetic case A — area computed in EPSG:5070
  CRS:  EPSG:5070 — returned by SuggestEqualArea for this location
  Verdict: ACCEPTED
  Findings: none

Synthetic case B — the same polygon, area computed in EPSG:3857
  CRS:  EPSG:3857 — Web Mercator, the default of most web maps
  Verdict: BLOCKED
  Findings:
    - WEB MERCATOR FOR AREA: EPSG:3857 distorts area severely at high latitudes
      and must NOT be used for area computation — use an equal-area projection
```

**Why it matters.** Web Mercator is conformal, not equal-area: it inflates area
with latitude. Nothing about the result looks wrong — you get a plausible number
in the right units that is simply not the area. The validator refuses the
operation rather than returning it, and suggests EPSG:5070 for that location.

### 2c. `batterypass` — a passport that contradicts itself

```text
tokn community demo --domain batterypass
```

Expected output (abridged):

```text
Synthetic case A — passport says LFP, cathode says LiFePO4
  Verdict: ACCEPTED
  Findings: none

Synthetic case B — passport says NMC811, cathode still says LiFePO4
  Verdict: BLOCKED
  Findings:
    - chemistry element mismatch: declared="NMC811" cathode="LiFePO4"
      missing=Ni,Mn,Co forbidden=Fe,P
    - required elements absent from the cathode formula: Ni, Mn, Co
    - elements present that contradict the declared chemistry: Fe, P
```

**Why it matters.** NMC811 normalises to NMC, which requires nickel, manganese
and cobalt (all absent here) and forbids iron and phosphorus (both present). Two
sections of one EU Battery Passport disagree — the kind of defect that survives
human review because each section is individually well-formed. In the licensed
domain the cross-section consistency gate blocks publication on this finding.

### Machine-readable form

```text
tokn community demo --domain batterypass --json
tokn community list --json
```

The JSON carries the same cases plus `"preview_only": true` and a `"scope"`
block. Read that block for what it is — a **declaration** about the preview's
code path, not telemetry:

```json
"scope": {
  "kind": "declarative",
  "preview_writes_files": false,
  "preview_network_calls": false,
  "excludes": "TOKN process startup, which is outside this command: licence resolution, a one-time anonymous install count (disable with TOKN_NO_REGISTER=1) and a daily update check (disable with TOKN_NO_UPDATE_CHECK=1)",
  "evidence": "preview_writes_files is exercised by temp-directory isolation tests in community_cmd_test.go; preview_network_calls is a code-path declaration, not a runtime measurement"
}
```

`kind: "declarative"` is the important field. If you are gating something on
this, gate on your own observation of the process, not on TOKN's self-report.

---

## 3. Governed judgments, offline (no key)

A **governed judgment** separates two things most agent frameworks blur: the
*bounded interpretation* (a typed question answered by a provider) and the
*deterministic policy* (a rule table that turns answers into an action). The
provider never decides the action. The policy never interprets.

Here the provider is a **local rules baseline** — no model, no key, no network.

### 3a. Get the example bundle

A bundle is the versioned triple of contract, deployment and policy.

**Windows (PowerShell)**
```powershell
tokn judgments example | Set-Content -Encoding ascii bundle.json
tokn judgments validate --bundle bundle.json
```

> Use `Set-Content -Encoding ascii`, not `>`. Windows PowerShell 5.1 writes
> UTF-16 when redirecting, and TOKN rejects that with
> `invalid_bundle: JSON is not valid UTF-8`. PowerShell 7 defaults to UTF-8, so
> `>` works there — the explicit form is correct on both.

**macOS / Linux**
```bash
tokn judgments example > bundle.json
tokn judgments validate --bundle bundle.json
```

Expected output of `validate`:

```json
{
  "approval_verified": false,
  "bundle_hash": "sha256:0229217063661521c9646383e583398a53717f8b7cf8980b4109f56a29d37d18",
  "contract": {
    "id": "coding.completion-evidence",
    "version": "1.0.0"
  },
  "valid": true
}
```

Note `"approval_verified": false`. Validation checks the *shape* of the bundle.
It does not authenticate that anyone in your organisation approved it, and it
says so rather than letting you assume otherwise.

### 3b. Write two request files

The contract's input schema requires exactly seven fields. The first request
describes a run that finished cleanly; the second describes the same run with
recorded tool failures.

Save as `request-clean.json`:

```json
{
  "state": {
    "status": "completed",
    "answer_present": true,
    "telemetry_complete": true,
    "tool_calls": 12,
    "tool_errors": 0,
    "tool_blocks": 0,
    "steps": 7
  },
  "context": {
    "trace_id": "local-demo-1",
    "environment": "local"
  }
}
```

Save as `request-errors.json`:

```json
{
  "state": {
    "status": "completed",
    "answer_present": true,
    "telemetry_complete": true,
    "tool_calls": 12,
    "tool_errors": 2,
    "tool_blocks": 1,
    "steps": 7
  },
  "context": {
    "trace_id": "local-demo-2",
    "environment": "local"
  }
}
```

Both files are also in [`examples/judgments/`](examples/judgments/) in this repo.

### 3c. The success case

```text
tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --air-gap
```

`--air-gap` forbids external judgment adapters outright; the rules provider
remains available. `--mode advisory` is the strongest mode offered — there is no
enforcing mode, by design.

Expected (abridged — `judgment_id`, hashes and timestamps will differ):

```json
{
  "schema": "tokn.governed-judgment/1",
  "mode": "advisory",
  "status": "judged",
  "provider": "rules",
  "result": {
    "answers": {
      "evidence_complete":  { "selected_answer": "true",  "selected_probability": 1 },
      "execution_clean":    { "selected_answer": "true",  "selected_probability": 1 },
      "telemetry_complete": { "selected_answer": "true",  "selected_probability": 1 }
    },
    "model": "completion-rules-v1",
    "probability_source": "deterministic"
  },
  "decision": {
    "action": "continue",
    "matched_rule": "runtime-evidence-present",
    "reason_code": "RUNTIME_EVIDENCE_ONLY",
    "applied": false
  }
}
```

Exit code `0`.

Read `"applied": false` and `"reason_code": "RUNTIME_EVIDENCE_ONLY"` together:
the judgment recommends `continue`, it was **not** applied to anything, and the
reason code states exactly what the evidence was — the runtime finished and an
answer exists. Not that the work is correct. The contract says so explicitly in
its own `excluded_uses`.

### 3d. The failure case

Same bundle, same command, the request with recorded tool failures:

```text
tokn judgments evaluate --bundle bundle.json --file request-errors.json --mode advisory --air-gap
```

Expected — the changed lines:

```json
  "result": {
    "answers": {
      "execution_clean": { "selected_answer": "false", "selected_probability": 1 }
    }
  },
  "decision": {
    "action": "revise",
    "matched_rule": "unclean-execution",
    "reason_code": "RECORDED_EXECUTION_FAILURE",
    "applied": false
  }
```

Exit code `0`. The run succeeded; the *judgment* is `revise`.

That distinction matters: a non-zero exit would mean the tool failed. A `revise`
action means the tool worked and is telling you something about your run.

### 3e. What a rejected input looks like

Delete `"tool_blocks"` from a request and re-run:

```text
Error: judgment request: judgments: invalid_input: state.tool_blocks: is required
```

Exit code `1`. The error names the field and nothing else — error details are
redacted and never echo your state back at you.

### Caveats worth internalising

- **Probabilities here are deterministic, not calibrated.** The rules provider
  emits `0` or `1` and labels the source `"deterministic"`. When you swap in a
  model provider the source becomes `elicited_uncalibrated` or
  `model_distribution` — and `elicited_uncalibrated` means exactly that: a number
  the model produced, with no calibration claim attached. Do not threshold on it
  as if it were a calibrated probability.
- **A judgment authorises nothing.** `"applied": false` is not a placeholder. The
  engine has no executor, no approver and no tool registry. It cannot run a tool,
  approve a change, or open a gate.
- **Your data was not transmitted.** With the `rules` provider and `--air-gap`,
  the evaluation makes no external call: none of your state, bundle or request
  leaves your machine.
- **Nothing was written** except the two files you saved yourself.

---

## 4. Optional: your own Jev key

Everything above is free and offline. This step is not offline.

**Before you run it, three things are true and worth stating plainly:**

- **It transmits.** `triage` sends the task text you supply to the Jev API. Only
  that text — TOKN does not discover or attach repository content — but that text
  does leave your machine.
- **It may cost money.** Calls are billed by your provider under your key.
- **Its confidence is uncalibrated.** Treat the output as advisory.

Use synthetic or explicitly approved text. Never secrets, credentials, customer
data, or anything you are not authorised to send to a third party.

Check configuration **without** calling the API first:

**Windows (PowerShell)**
```powershell
tokn system-one status --air-gap
```

**macOS / Linux**
```bash
tokn system-one status --air-gap
```

Expected:

```json
{
  "backend": "jev",
  "configured": false,
  "model": "jev-latest",
  "endpoint": "",
  "reason": "external calls disabled by air-gap/offline mode"
}
```

That is the preflight: it reports what is configured and never prints your
credential. Now supply a key and run the triage:

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

`status` now reports `"configured": true`. `triage` returns an advisory typed
assessment of the text. It does not edit code, run tools, or change routing.

Keep keys out of source control. `tokn config doctor` shows every config file and
environment variable TOKN picks up, with secrets redacted.

For several typed questions over one shared state, use `tokn system-one evaluate
--file <request.json>`; the file you name is exactly what gets transmitted. It is
distinct from `tokn system-one batch`, which runs *independent* states with
bounded parallel calls rather than sharing one. Run
`tokn system-one evaluate --help` for the exact input shape.

---

## 5. Optional: a configured LLM and the agent session

The interactive agent session needs a generative model provider. Configure one
using [SETUP.md](SETUP.md) — OpenAI, Azure OpenAI, Anthropic, Gemini, OpenRouter,
Fireworks, or a local runtime such as Ollama or llama.cpp. TOKN is
bring-your-own-model: **usage is billed by your provider, under your key.**

```bash
tokn auth status        # confirms a provider is configured and ready
tokn agent-repl
```

Inside the session, the built-in lessons work in the public build even though the
embedded wiki does not ship with it:

```text
/learn community
/learn judgments
/learn system-one
```

The domain previews and the offline judgment examples in sections 2 and 3 need
none of this. They were the point of this guide.

---

## 6. Optional: the `decision-models` skill pack

TOKN bundles a skill pack that adapts TypeSafe's MIT-licensed agent skill,
pinned to its upstream revision. It teaches bounded decision design — workflow
shape, structured state, batching independent work over shared state, handling
uncertainty, and keeping the final policy deterministic — expressed against
TOKN's own interfaces.

It is **included in the public binary**. Installing it needs no npm, no SDK, no
GitHub token and no network call: the bundle is embedded in the binary you
already downloaded.

```bash
tokn plugin catalog                      # decision-models appears in the list
tokn plugin install decision-models
tokn plugin list                         # tokn-decision-models ... skills=1
```

Expected install output, abbreviated:

```text
Installed plugin "tokn-decision-models" as Agent Plugins 1.0.0 package
  Path:   <TOKN_HOME>/plugins/tokn-decision-models
  Skills: 1

Diagnostics (1):
  [info] assets: Skills-only pack: no domain commands, agents or hooks are included.
```

That diagnostic is expected and is not an error. This pack is **instructions
only** — it deliberately ships no tools, no hooks and no agents, so installing it
cannot change what TOKN is allowed to do.

Everything it writes goes under your TOKN home (`~/.tokn/plugins/`, or
`%USERPROFILE%\.tokn\plugins\` on Windows), never into your repository. Set
`TOKN_HOME` first if you want it somewhere else.

Then, inside an agent session, read it:

```text
/skill inspect tokn-decision-models:typesafe-ai-decisions   # summary
/skill invoke  tokn-decision-models:typesafe-ai-decisions   # full instructions
```

The imported ID is `<plugin>:<skill>` — run `/skill list` if you want to see the
exact string rather than copy it.

Both commands only print, and neither calls a model:

- **`inspect` shows the summary** — category, version, description, and how many
  gotchas and reference files the skill carries.
- **`invoke` prints the instruction text in full.** Despite the name it does not
  invoke a task, does not run tools and does not activate anything. Using the
  skill is the step *after*: read it, then make your request in your own words.
  That request runs on your configured model at your own cost (section 5).

If `tokn plugin catalog` does not list `decision-models`, your binary predates
the pack — run `tokn update`. Use the commands above rather than
`tokn skillpack install`, which resolves against a source tree you will not have.

---

## 7. Developer path: tools, skills, hooks, permissions

These are four different things, and the difference is a permissions boundary,
not vocabulary:

| | What it is | What it can do |
|---|---|---|
| **Tool** | an executable capability the model may call | reads and writes, runs commands |
| **Skill** | reusable instructions | nothing on its own — it only changes what the model is told |
| **Hook** | your command, run at a lifecycle event | runs with **your** permissions |
| **Permission / trust** | the gate over the three above | decides what is even offered |

Work in that order: **discover → inspect → opt in**. Nothing below enables
anything by itself.

The same path is built into the binary, so you do not need this page to find it:

```bash
tokn community guide     # or just: tokn community
```

It renders locally, needs no model provider or licence, and writes nothing.

Two contexts appear in this section. They are not interchangeable:

- **`shell`** — your normal terminal. Everything in step 1 works here with no
  model provider, no key and no licence.
- **`repl`** — inside `tokn agent-repl`, where `/` commands live. The REPL needs
  a configured model provider (section 5).

### 7a. Discover — shell, no key required

```bash
tokn agent-tools --mcp-disabled   # every tool available right now
tokn plugin catalog               # skill packs and domain plugins you can install
tokn plugin list                  # what is already installed and visible
tokn doctor --list                # every model provider and how to connect it
```

All four exit `0` offline. `--mcp-disabled` matters: without it TOKN tries to
dial configured MCP servers, so you are inspecting the network as well as your
tools. Add it whenever you only want to look.

Expect the tool list to be **shorter than the marketing number** — around 26 in a
plain session:

```text
TOKN Agent Tools (26 tools)

  FILE OPERATIONS
    apply_unified_diff      Apply a single-file unified diff to an existing file …
    edit_file               Replace exact text in a file under the repository root.
    read_file               Read a file from the repository.
  SEARCH
    grep_search             Search file contents.
  GIT
    git_diff                Show git diff.
```

That is the point, not a defect. Domain tools register only when you actually run
that domain's mode, so a default session is not carrying thirty domains' worth of
capability it has no reason to hold.

Note that `tokn plugin list` reports everything on your machine that TOKN can
see, which may include packages installed by other agent tools — so a non-empty
list does not mean TOKN installed them.

### 7b. Inspect — repl, before enabling anything

```text
/help                  list every slash command
/skill list            discovered skills, with their IDs
/skill inspect <id>    metadata — category, version, description, counts
/skill invoke <id>     print the skill's full instruction text
/skills status         installed skill packs
/plugin list           installed plugins
/hooks list            read the hook settings files
/permissions show      current file-access rules
/trust audit           what this workspace has been granted
/mcp                   configured MCP servers
/mode                  the active mode
```

Three traps worth stating plainly, because the names suggest more than the
commands do:

- **`/skill invoke` does not invoke anything.** It prints the skill's
  instruction text and stops. Using a skill is two steps: print it, then make
  your request in your own words. `/skill inspect` is the *summary* —
  category, version, description, counts — not the instructions.
- **`/hooks list` reports configuration, not activation.** It reads
  `.claude/settings.json` and `.claude/settings.local.json` and shows what is
  written there. It does not execute a hook, and it does not tell you which
  hooks are active in the current session — it prints
  `Configuration check only; no hooks executed or installed.` and labels its own
  trust readout `cached; not proof that hooks are loaded`. Treat a clean
  listing as "the file parses", nothing more.
- **Neither `/tools` nor `/skill rescan` exists.** Use `tokn agent-tools` in the
  shell for tools, and `/reload-plugins` to rescan skills.

`/skill list` shows installed-skill IDs. Do not reach for `tokn skills list` in
the shell for this — that command is a different thing and requires
`--from <file>` pointing at a JSON array of skill cards; without it you get
`Error: required flag(s) "from" not set`.

### 7c. Opt in — deliberately

Skills are the safe thing to add first, because they add no capability:

```bash
tokn plugin install decision-models      # shell
```
```text
/skill invoke tokn-decision-models:typesafe-ai-decisions   # repl — prints it
```

`/skill invoke` prints the instruction text; it does not start a task. Read it,
then make your request in your own words.

Installing a plugin writes under your TOKN home (`$TOKN_HOME/plugins`, default
`~/.tokn/plugins`). A session that is **already running will not see it** until
the registry is rescanned — use `/reload-plugins` in the REPL, which rescans
those roots in place. That is enough for a skills-only pack such as
`decision-models`. A pack that also carried commands, agents or hooks would
need a restart, because `/reload-plugins` refreshes the skill registry only.

Installing a pack never widens what the agent may *do*. The external typed-judgment
tools are a separate, explicit opt-in — a flag you pass when starting the session:

```bash
tokn agent-repl --system-one              # shell
```

That exposes `system_one_evaluate`, `system_one_batch` and `system_one_triage`
inside the session, under the same permission and hook rules as every other
tool. Without the flag they are simply not registered, however many skill packs
you have installed. The flag's own help says what it costs you: *supplied state
leaves this machine; advisory only, no automatic routing*. To check the
configuration before deciding, `tokn system-one status --air-gap` inspects it
offline and makes no decision API calls.

Each of those three tools also prompts before it transmits, printing the exact
payload — `This state will leave this machine:` followed by the JSON — and
defaults to **no** if you just press Enter. So the opt-in is two gates deep: the
flag at start-up, then per-call consent with the payload in front of you.

Hooks are the unsafe thing, so TOKN separates *writing configuration* from
*granting consent* — and neither one, on its own, makes a hook run.

A hook runs your command with your permissions at an agent lifecycle event, so
three separate things must line up: the configuration must be written, the
workspace must be trusted for the `hooks` capability, and the agent must be
restarted afterwards. `/hooks add` says as much when it saves the file.

Here is the whole loop in a **disposable** workspace — create an empty directory
for it, not a repository you care about:

```text
/hooks add PreToolUse echo hook-preview     # repl — writes settings only
/hooks list                                 # repl — reads it back
```

Write the command **unquoted**. `/hooks add PreToolUse "echo hook-preview"`
stores the quote characters as part of the command, which is not what you meant.

`/hooks add` produces the nested shape the runtime actually loads:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "*", "hooks": [ { "type": "command", "command": "echo hook-preview" } ] }
    ]
  }
}
```

and `/hooks list` reports exactly this, with nothing executed:

```text
settings.json: PreToolUse matcher="*" handlers=1
1 configured hook handler(s). Configuration check only; no hooks executed or installed.
Session workspace trust: untrusted; hooks permitted: false (cached; not proof that hooks are loaded).
```

Read that last line carefully: the hook is **configured and still inert**. Open
the file and read it yourself, then grant the narrowest possible trust:

```bash
tokn trust --capability hooks         # shell — grant hooks for THIS repo
```

It tells you precisely what you are agreeing to before it does anything:

```text
Granting trust will allow this repository to:
  • run shell commands defined in this repo's .claude/settings.json hooks

Only do this for a repository you authored or have reviewed.
```

After the grant, `/hooks list` in a **new** session reports
`hooks permitted: true`. There is no `tokn trust grant` subcommand — the grant is
the bare `tokn trust` command with `--capability`; `tokn trust status`,
`tokn trust list` and `tokn trust revoke` are the related ones. The path is
optional — `tokn trust --capability hooks <path>` trusts a specific workspace
instead of the current directory. Answer the confirmation yourself; do not
script past it.

To undo the configuration, `/hooks remove <event>` drops that event from the
project settings. Like adding, it takes effect on restart.

Two further cautions, from the commands' own output:

- A grant is **pinned to the file contents**. Editing `.claude/settings.json`
  after granting can make the earlier grant stale, and you will be asked again.
- `/hooks list` reports configuration, not effect. **Confirm a hook actually
  fires** — for example with a harmless `echo` in a disposable workspace —
  before you depend on it.
- **A hand-written settings file may be in a shape the runtime cannot load.**
  The loader wants `event → matcher → hooks` arrays; a flat list of handlers
  under the event is rejected. TOKN reports this instead of silently repairing
  it, and — importantly — it does not rewrite your file:

  ```text
  Warning: invalid or unsupported hooks in …\.claude\settings.json:
  json: unknown field "PreToolCall"; no settings will be rewritten
  Showing the fields the runtime understands; unsupported fields are not included.
  0 configured hook handler(s).
  ```

  Note the asymmetry: `PreToolCall` is accepted as an *alias* when you type it
  into `/hooks add` (it is normalised to `PreToolUse`), but it is not a valid key
  *inside* the settings file. If you see the warning above, fix the file — or
  delete the block and re-add it with `/hooks add`, which always writes the
  supported shape.

A cloned repository is untrusted by default and none of its hooks, MCP servers,
`CLAUDE.md` command expressions or prompt overrides are honoured. That is the
intended state. Never grant hook trust in a repository you did not write or
review.

### 7d. Customize — one safe example

TOKN treats **prompt text as data**. Every mode's system prompt is a file you can
replace, without rebuilding anything.

Put the override in your **user-global** prompts directory:

**macOS / Linux**
```bash
mkdir -p ~/.tokn/prompts
printf 'Answer in at most five lines. Show the command, not the prose.\n' \
  > ~/.tokn/prompts/mode-lean.md
```

**Windows (PowerShell)**
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.tokn\prompts" | Out-Null
'Answer in at most five lines. Show the command, not the prose.' |
  Set-Content -Encoding utf8 "$env:USERPROFILE\.tokn\prompts\mode-lean.md"
```

The file name is the template key with `/` replaced by `-`: `mode/lean` →
`mode-lean.md`, `domain/nucsci` → `domain-nucsci.md`. Use `/mode lean` in the
REPL to select it.

Resolution order is **project → user-global → built-in default**, and the
project tier is deliberately harder to reach: a repository can only replace
TOKN's own system and safety prompts if you have explicitly granted that
workspace the `prompts` capability. A repo you cloned cannot quietly rewrite the
agent's instructions. `~/.tokn/prompts/` needs no grant, because only you can
write there.

Prompt overrides change what the model is *told*. They do not add a tool, do not
relax a gate, and do not affect the domain previews in section 2.

---

## What is free, and what is not

| | Community (free) | Licensed |
|---|---|---|
| Domain previews (`tokn community`) | ✅ fixed synthetic cases, read-only | — |
| Governed judgments, `rules` provider, offline | ✅ | — |
| System One / Jev typed decisions | ✅ your own key, your own cost | — |
| Built-in lessons (`/learn`) | ✅ | — |
| `decision-models` skill pack (bundled, offline) | ✅ | — |
| Core agent loop | ✅ your own model, your own cost | — |
| Domain lifecycle state machines | ❌ | ✅ |
| Domain gates that block state transitions | ❌ | ✅ |
| Domain tool surface, hooks, validators, subagents | ❌ | ✅ |
| Domain slash commands and subagents | ❌ | ✅ |

A preview shows you that a check exists and what it decides on one fixed case. It
is not the workflow. The licensed domain is the workflow: the lifecycle, the full
validator set, the gates that actually block, the tools and the subagents.

**All output is decision-support on synthetic or supplied data.** It is not
engineering, regulatory, clinical, legal or compliance advice, it may be wrong,
and it must be independently verified. You are responsible for compliance and
assume all risk. See [LICENSE.md](LICENSE.md).

---

## If something goes wrong

| Symptom | Almost always |
|---------|---------------|
| `unknown command "community"` | Binary older than v0.3.44 — run `tokn update` |
| `Signature Verification Failure` | **Stop.** Do not run the binary; open an issue |
| `openssl: unrecognized option '-rawin'` | OpenSSL 1.x — install OpenSSL 3.x |
| `--domain is required` | `tokn community demo` needs `--domain`; run `tokn community list` |
| `unknown community preview "…"` | Only the previews listed by `tokn community list` exist |
| `judgments: invalid_bundle: JSON is not valid UTF-8` | Windows PowerShell 5.1 wrote UTF-16 via `>`; regenerate with `tokn judgments example \| Set-Content -Encoding ascii bundle.json` |
| `judgments: invalid_input: state.… is required` | The request is missing one of the seven required state fields |
| `external judgment requires --allow-external` | You asked for a non-`rules` provider; for offline use keep the `rules` deployment and `--air-gap` |
| `required flag(s) "from" not set` | You ran `tokn skills list`; for installed skills use `/skill list` in the REPL |
| A skill you just installed is missing | Run `/reload-plugins` in the REPL — a running session does not rescan on its own |
| `unknown field "PreToolCall"; no settings will be rewritten` | Your `.claude/settings.json` uses the flat legacy shape; re-add the hook with `/hooks add`, which writes the `event → matcher → hooks` form the runtime loads |
| `/hooks list` looks right but nothing runs | Configuration is not activation: the workspace also needs `tokn trust --capability hooks` and an agent restart, and `/hooks list` never reports which hooks are live |
| A prompt override has no effect | Check the filename (`mode/lean` → `mode-lean.md`) and use `~/.tokn/prompts/`; the project-level path needs a workspace trust grant |
| Licensed feature unavailable on Apple Silicon | Expected — see [Platform support](README.md#platform-support) |

`tokn --help` is always the authoritative, version-accurate command catalog.
`tokn config doctor` shows what configuration is actually in effect.

Questions, bugs, licensing: **open an issue in this repository.**
