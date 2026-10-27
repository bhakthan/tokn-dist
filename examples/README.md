# TOKN examples

Synthetic, non-sensitive input files referenced by
[GETTING_STARTED.md](../GETTING_STARTED.md), plus step-by-step walkthroughs
that each run one real task end to end. None of them contain real data.

Every walkthrough needs your own LLM key and makes paid model calls. Domain
modes (compbio, oncology, finrisk, physai, precmed, clintrial, legalai,
geospatial, cybersec, atmchem, quantumsci, structbio, robotics) and the premium
critique and autodesign modes need the 14-day trial (`tokn license trial`); the
rest are expected to run on Community too.

New to TOKN? Start with [first-ten-minutes](first-ten-minutes/README.md).

| Walkthrough | What it shows | Extra requirements |
|---|---|---|
| [decision-council](decision-council/README.md) | Several decision models vote in parallel; a council escalates disagreements to an LLM | 2+ decision-model keys |
| [grid-screening](grid-screening/README.md) | `tokn harness evolve` improves its own harness on a substation N-1 screen | a decision-model key |
| [finrisk-system-one](finrisk-system-one/README.md) | A deterministic finrisk tool plus one typed decision request, graded from the run log | trial, a decision-model key |
| [compbio-gates](compbio-gates/README.md) | Computational-biology gates catch genome-build mixing and unpinned pipelines | trial |
| [oncology-governance](oncology-governance/README.md) | Six oncology scenarios check PHI, human-in-the-loop and decision-support framing | trial |
| [physai-fleet](physai-fleet/README.md) | `physai` mode generates a 14-agent warehouse robot fleet | trial |
| [science-review](science-review/README.md) | A reviewer finds three planted defects in a figure caption with `review_artifact` | — |
| [quality-flywheel](quality-flywheel/README.md) | `tokn flywheel run` grades a dataset over two cycles against a baseline | — |
| [loop-graph](loop-graph/README.md) | A governed graph of loops refuses a metric that is fooling itself; a held-out check confirms it | — |
| [skill-compose](skill-compose/README.md) | TOKN picks which skills, how many and in what order from a small library | — |
| [dataflow](dataflow/README.md) | Skills are ordered by what they consume and produce; a broken chain is flagged | — |
| [tool-contract](tool-contract/README.md) | An off-contract tool call is repaired instead of failing | — |
| [mcp-server](mcp-server/README.md) | `tokn serve` as an MCP server for Claude Desktop, VS Code or any MCP client | — |
| [webwright](webwright/README.md) | Code-first browser automation: the agent writes one re-runnable Playwright script | Python + Playwright |
| [precmed-variant](precmed-variant/README.md) | Precision-medicine safety gates on a synthetic tumour-board variant case (VUS, PGx, somatic–germline) | trial |
| [clintrial](clintrial/README.md) | AI-in-clinical-trials gates on a synthetic cohort and target-trial spec | trial |
| [legal-analysis](legal-analysis/README.md) | Citation checks, jurisdiction lock, counter-argument and disclaimer gates on a fictional matter | trial |
| [geospatial](geospatial/README.md) | CRS, cloud-masking, resolution and time-window gates on a synthetic Earth-observation study | trial |
| [cybersec](cybersec/README.md) | Defensive triage of a synthetic SSH config and auth log, inside scope gates | trial |
| [critique](critique/README.md) | Multi-role adversarial critique of a design proposal, with recorded dissent | trial |
| [autodesign](autodesign/README.md) | Autonomous design experiments on a landing page: weighted dimensions, binary gates, Pareto frontier | trial |
| [loop-engineering](loop-engineering/README.md) | `/loop define` with a goal, a check and a stop, over abstract lead-optimisation scores | — |
| [session-review](session-review/README.md) | `/review` audits what an agent session did to a small repo with a planted bug | — |
| [custom-hooks](custom-hooks/README.md) | Your own PreToolUse hook blocks writes to a protected path; a PostToolUse hook writes an audit log | — |
| [air-quality](air-quality/README.md) | Air-quality model evaluation gates (MFB/MFE/NMB/R²) on synthetic modelled vs observed data | trial |
| [quantum-experiment](quantum-experiment/README.md) | Error-budget, tier-labelling, ZNE and NISQ/FT gates on synthetic device specs | trial |
| [structural-biology](structural-biology/README.md) | The FSC-0.143 resolution gate and AlphaFold3 governance on a synthetic cryo-EM summary | trial |
| [robotics-twin](robotics-twin/README.md) | Robotics and digital-twin safety gates on a synthetic mission spec | trial |
| [pharma-phase3](pharma-phase3/README.md) | An end-to-end Phase 3 analysis package with an endpoint-provenance check, all fictional | — |
| [diligence-pack](diligence-pack/README.md) | An end-to-end diligence pack on a fictional company, with every figure traced to evidence | — |
| [memory](memory/README.md) | Teach a preference in one session and have it recalled in the next (`/recall`, write-back) | — |
| [checkpoints](checkpoints/README.md) | Roll back a bad agent edit with checkpoints, `/undo` and `/rewind` | — |
| [codebase-graph](codebase-graph/README.md) | Blast-radius analysis with `/codebase blast` on a small synthetic Go service | — |
| [first-ten-minutes](first-ten-minutes/README.md) | Onboarding: version and licence checks, first `agent-run`, the REPL, offline judgments | — |
| [judgments](judgments/README.md) | Offline governed judgments on recorded runs: no model, no network | — |
| [full-stack-app](full-stack-app/README.md) | Build a small full-stack task-manager app from a written spec, then check it | — |
| [flows](flows/README.md) | Multi-step workflows started from the REPL | — |
| [tabular-prediction](tabular-prediction/README.md) | A local, offline tabular model makes predictions on a synthetic CSV, alongside the LLM | Python + model weights |
| [web-agent](web-agent/README.md) | The interactive `webagent` mode on a public page (compare with webwright) | Chromium |
| [peer-collab](peer-collab/README.md) | Two people, two agents, one fictional reactor safety dashboard | — |
| [self-improvement](self-improvement/README.md) | Improve a prompt bundle within budgets, with a sealed held-out check (`tokn rrsi`) | — |
| [workflow-discovery](workflow-discovery/README.md) | Write, check and inspect a workflow graph the model follows step by step (`tokn procgraph`) | trial |
| [clinical-council](clinical-council/README.md) | Several models agree a synthetic precision-medicine case, with optional infographics | trial |
| [agent-loop-essentials](agent-loop-essentials/README.md) | Task anchor, repo map, a predictability report checked against an outcome contract | — |
| [sdk-generation](sdk-generation/README.md) | Ingest a small OpenAPI spec, generate client SDKs, validate them | language toolchains |
| [domain-plugin](domain-plugin/README.md) | Scaffold, validate and install your own small domain plugin | — |
| [event-trigger](event-trigger/README.md) | Start agent runs from events: a local folder queue first, Azure Service Bus optional | your own broker (optional) |
| [federation](federation/README.md) | A leader fans a task out to two local workers and applies the results back | — |
| [agent-team](agent-team/README.md) | A declarative team (planner, implementer, reviewer) builds a small app | — |
| [authority-frames](authority-frames/README.md) | When the agent acts, asks or stops: permission, ask-or-act and stuck signals | — |
| [hands-off-run](hands-off-run/README.md) | A long autonomous run with budgets, checkpoints and a verified finish | — |
| [credit-underwriting](credit-underwriting/README.md) | Financial-risk gates on a synthetic small-business loan file | trial |
| [meeting-to-poc](meeting-to-poc/README.md) | Meeting minutes to a design plan to a proof-of-concept scaffold; optionally pulls minutes from your own Microsoft 365 via WorkIQ | your own M365 tenant (optional) |
| [computer-use-models](computer-use-models/README.md) | Drive a browser with self-hosted computer-use models (Fara, MagenticBrain) on your own GPU endpoints | your own GPU endpoints |
| [ontology-sparql](ontology-sparql/README.md) | Load a synthetic Turtle ontology, query it with SPARQL, and watch the reasoner infer new facts; Fabric/Snowflake connectors optional | none (warehouse optional) |
| [knowledge-bundles](knowledge-bundles/README.md) | Validate, migrate, export and import portable knowledge bundles through the agent's OKF tools | none |
| [openshell](openshell/README.md) | Run TOKN in an NVIDIA OpenShell sandbox: generated profile, enforcing egress policy, non-root image; keys never enter the sandbox | Linux or WSL 2, OpenShell, Docker or Podman |
| [agent-organization](agent-organization/README.md) | Agensh-style self-organizing organization: workers claim tasks on a shared board, a supervisor feeds failed checks back, local GGUF models for air gap, scale-out and upstream Agensh | Git, Python; local models optional |
| [decisions-api](decisions-api/README.md) | OpenAI / Azure OpenAI Decisions API (`/v1/decisions`) from the OpenAI SDK and through `tokn system-one` | OpenAI or Azure OpenAI key, Python |
| [loops-and-ship-ready](loops-and-ship-ready/README.md) | `/loop define`, prompt loops, find-and-refute, `tokn ship-ready`, `/rewind` and REPL keys on a small buggy repo | Git, Python |
| [t3code](t3code/README.md) | Drive TOKN from T3 Code's web, desktop or mobile app as a Local ACP command: modes, model picker, inline diffs, resume | T3 Code |
| [coding-clis](coding-clis/README.md) | Use TOKN with Claude Code, Codex, Copilot CLI, Gemini CLI and Antigravity: MCP tools, `/conduct` peers, config import | Any of those CLIs |
| [gemini-api](gemini-api/README.md) | Let the agent use Google's Gemini API CLI through a safe `gemini_api` tool: analyze files, images, speech, deep-research agents | `gemini-api`, a Gemini API key |
| [single-agent-loop](single-agent-loop/README.md) | Fold a router and its subagents into one agent loop with skills and tools, proving each step with evals (`tokn single-loop`); offline demo built in | none |
| [dynamic-workflows](dynamic-workflows/README.md) | Background agent fleets from one prompt: bundled workflows, the `iterative-refine` controller, the `ultrawork` keyword, save/resume, domain capsules | — |
| [decision-circuits](decision-circuits/README.md) | Turn keyword/regex decisions into typed, testable decision circuits: starter packs, static analysis, test vectors, generated Python, detect/draft, profile, ledger — all offline (`tokn circuit`) | Python 3.9+ (optional) |
| [delegation-and-signoff](delegation-and-signoff/README.md) | Rate a task on stakes, reversibility, ambiguity and frequency to get an automation level and the controls it needs (`tokn delegate`), then sign off a change and catch drift (`tokn sign-off`) | Git |
## `decision-council/` — several decision models, one council

A wind-fleet maintenance triage of 24 turbines. Several typed decision models
(for example TypeSafe Jev, Bespoke Labs Nimble and Microsoft decision-1) answer
the same questions in parallel with `tokn system-one batch`. A deterministic
council merges their votes and escalates only the rows they disagree on. A
reasoning LLM then settles those rows with `tokn agent-run` and builds the crew
plan. A grader checks the result against the written policy, offline.

It **needs keys for two or more decision-model backends and one LLM**, and makes
paid model calls. It runs on both the trial and the Community tier. Start at
[decision-council/README.md](decision-council/README.md).

## `grid-screening/` — step-by-step domain walkthrough

A complete, hands-on example of a real domain task: screening five
substations for transformer loading and N-1 security. TOKN improves its own
harness with `tokn harness evolve` (Propose–Probe–Compose), and a typed
decision model chooses each substation's action. A deterministic rule
overrides the model, so its output is advisory only. All data is synthetic.

Unlike the rest of this folder, this example **needs your own LLM key and a
decision-model backend**, and it makes paid model calls (about US$2–3 per
run). It runs on both the trial and the Community tier. Start at
[grid-screening/README.md](grid-screening/README.md).

## `judgments/`

Two request files for the offline governed-judgment walkthrough. Both use the
local `rules` provider, so evaluating them makes no external judgment call and
needs
**no API key**.

| File | Describes | Expected decision |
|------|-----------|-------------------|
| `request-clean.json` | a run that finished with no recorded tool errors or blocks | `continue` / `RUNTIME_EVIDENCE_ONLY` |
| `request-errors.json` | the same run with 2 tool errors and 1 tool block | `revise` / `RECORDED_EXECUTION_FAILURE` |

Run them (from a directory you own — the commands write `bundle.json` there):

```bash
tokn judgments example > bundle.json
tokn judgments evaluate --bundle bundle.json --file request-clean.json  --mode advisory --air-gap
tokn judgments evaluate --bundle bundle.json --file request-errors.json --mode advisory --air-gap
```

Both exit `0`. The difference is in `decision.action` — a `revise` judgment means
the command worked and is telling you something about the run it was given.

For the full walkthrough, including how a malformed request is rejected, see
[judgments/README.md](judgments/README.md).

`decision.applied` is always `false`: a judgment is advisory and authorises
nothing.

## Running all of it unattended

`../scripts/community-smoke.sh` (bash) and `../scripts/community-smoke.ps1`
(PowerShell) run the three domain previews **and** the same two judgment cases,
asserting the expected decision for each. They do not read the files in this
directory — each script writes its own inline copies (identical `state` fields,
a different `trace_id`) into a temp directory it deletes on exit — so nothing
here is modified and the scripts work from a bare binary download too.

```bash
bash scripts/community-smoke.sh        # from the repository root
```

```powershell
.\scripts\community-smoke.ps1          # from the repository root
```

Exit code `0` means every check passed.
