# TOKN examples

Synthetic, non-sensitive input files referenced by
[GETTING_STARTED.md](../GETTING_STARTED.md), plus step-by-step walkthroughs
that each run one real task end to end. None of them contain real data.

Reviewed against **v0.3.118**; see the
[releases page](https://github.com/bhakthan/tokn-dist/releases/latest) for the
latest binary. Minimum versions are per walkthrough; an older minimum is not
release news.
Hosted-model examples need your own provider access and may incur charges;
local-model examples need a running model server and staged weights.
Offline/catalog examples explicitly say when no model call is needed.
Domain and premium-mode examples need an applicable licence or the
14-day trial (`tokn license trial`); most non-domain examples also run on
Community. In the table, “trial” means a trial or applicable licence.

“Offline” describes the task's model/data path, not a promise of zero
startup traffic or zero disk writes. For a disconnected session, stage all
dependencies first, set `TOKN_NO_REGISTER=1` and `TOKN_NO_UPDATE_CHECK=1`,
and review other configured integrations. Follow each page's output and
cleanup notes; do not commit generated run records or credentials.

New to TOKN? Start with [first-ten-minutes](first-ten-minutes/README.md).

## Learning lanes

Pick the outcome you want, then follow the lane left to right. Each step needs
less help than the one before it. Every folder has a `.env.example` that lists
exactly what that walkthrough needs.

| Lane | Path | Needs a model? |
|---|---|---|
| **Start without a model** | [first-ten-minutes](first-ten-minutes/README.md) → [judgments](judgments/README.md) → [factory-evidence-tour](factory-evidence-tour/README.md) | No (one optional live step) |
| **Talk to a model safely** | [cli-session-lab](cli-session-lab/README.md) → [airgap-model-preflight](airgap-model-preflight/README.md) → [checkpoints](checkpoints/README.md) | Optional, then yes |
| **Build and prove a change** | [full-stack-app](full-stack-app/README.md) → [verified-completion](verified-completion/README.md) → [migration-parity](migration-parity/README.md) | Yes, then no |
| **Measure and improve** | [loop-engineering](loop-engineering/README.md) → [quality-flywheel](quality-flywheel/README.md) → [verified-improvement](verified-improvement/README.md) → [session-drift-lab](session-drift-lab/README.md) | Yes, yes, then optional, then no |
| **Know what you can use** | [skillpack-preflight](skillpack-preflight/README.md) → [cited-local-knowledge](cited-local-knowledge/README.md) → [knowledge-bundles](knowledge-bundles/README.md) | No (last step optional) |
| **Coordinate** | [flows](flows/README.md) → [peer-collab](peer-collab/README.md) → [agent-organization](agent-organization/README.md) → [federation](federation/README.md) | Varies |
| **Apply a domain** | Pick a domain row in the table below. Check its entitlement, tools and which decisions stay with a human. | Usually |

**What the levels mean.** *Worked*: a supplied fixture, the exact command and an
expected receipt. *Guided*: a changed input, a partial scaffold and an external
checker. *Problem-only*: a new input and a stop condition, with no answer or grader
visible to the agent. A machine-readable index of every walkthrough, including
level, model, network and writes, is in [catalog.json](catalog.json).

## All walkthroughs

| Walkthrough | What it shows | Extra requirements |
|---|---|---|
| [factory-evidence-tour](factory-evidence-tour/README.md) | The built-in Software Factory demo walked as an evidence chain: status, store verification and a receipt you check yourself | TOKN v0.3.118+, Python 3, Git; no model |
| [migration-parity](migration-parity/README.md) | Port a small program without silently changing behaviour: record legacy outputs, verify a candidate, ratchet a known-gaps ledger, plus guided `atmchem` and `batterypass` oracles | TOKN v0.3.118+, Python 3; no model |
| [cli-session-lab](cli-session-lab/README.md) | The CLI front door: REPL, one-shot `-p`, piped input, continue vs resume vs browsing a saved session | none offline; a model for the optional live steps |
| [airgap-model-preflight](airgap-model-preflight/README.md) | Check what a staged local model can do with no internet: provider doctors, checksums, licence review, then an optional local run | a staged local model for the optional run |
| [session-drift-lab](session-drift-lab/README.md) | Grade recorded sessions with a categorical expectation and raise a drift alarm across six cycles, without a new model call | none |
| [skillpack-preflight](skillpack-preflight/README.md) | Find out what your licence, skill packs, prompts and wiki variant allow before changing your machine | none |
| [cited-local-knowledge](cited-local-knowledge/README.md) | Index two policy files locally and retrieve a cited answer without sending them to a model | none |
| [rnaseq-software-factory](rnaseq-software-factory/README.md) | A gated agent pipeline turns RNA-seq CI failures and incidents into reviewed, tested, human-approved releases, mixing frontier, open-weights and local models per role | TOKN v0.3.115+, Python 3.10+ + numpy/pandas/scipy/pytest/pyyaml, Git; live profiles: trial, model keys |
| [decision-council](decision-council/README.md) | Several decision models vote in parallel; a council escalates disagreements to an LLM | 2+ decision-model keys |
| [postgresql-auto-ontology](postgresql-auto-ontology/README.md) | Infer an OWL/RDFS ontology from PostgreSQL tables, then review it by explicit ID | Azure PostgreSQL you control; optional Azure OpenAI or decision-model access (billed) |
| [grid-screening](grid-screening/README.md) | `tokn harness evolve` improves its own harness on a substation N-1 screen | a decision-model key |
| [finrisk-system-one](finrisk-system-one/README.md) | A deterministic finrisk tool plus one typed decision request, graded from the run log | trial, a decision-model key |
| [compbio-gates](compbio-gates/README.md) | Computational-biology gates catch genome-build mixing and unpinned pipelines | trial |
| [semicon-signoff](semicon-signoff/README.md) | Tapeout signoff for six macros: unconstrained timing is blocked, boundary slack and LVS traps are caught | trial |
| [adas-safety-gate](adas-safety-gate/README.md) | Five ADAS functions gated on ASIL decomposition, FMEDA metrics and V&V | trial |
| [appsec-triage](appsec-triage/README.md) | Triage a static-analysis queue before release: each candidate is reportable, suppressed or blocked | trial |
| [auto-route-grid](auto-route-grid/README.md) | `--auto-route` moves one grid-engineering task between OpenAI model rungs step by step | trial, Azure OpenAI |
| [auto-route-transcriptomics](auto-route-transcriptomics/README.md) | `--auto-route` moves a TOKN-authored RNA-seq case between Claude Haiku, Sonnet and Opus by step | trial, Anthropic API or compatible gateway, Python 3 + numpy |
| [rnaseq-goal-engineering](rnaseq-goal-engineering/README.md) | Goal scopes: a reviewer's correction on one RNA-seq run becomes a verified lesson that every later run in the scope applies | trial, Anthropic API or compatible gateway, Python 3 + numpy |
| [figure-honesty](figure-honesty/README.md) | A structbio figure gate measures an FSC plot, flags a resolution title that does not match the 0.143 crossing, and figure corrections become goal-scope lessons | trial, Anthropic API or compatible gateway, Python 3 + matplotlib |
| [visual-perception-loop](visual-perception-loop/README.md) | Typed vision tools check a rendered landing page: layout, colours, assertions and pixel diffs, then an agent rebuilds the page from a screenshot | TOKN v0.3.105+, Chrome or Chromium, Anthropic API or compatible gateway |
| [figure-extraction](figure-extraction/README.md) | Reads a chart, circuit and flow diagram back into data (FSC crossing, OpenQASM, Mermaid), with measured round-trip checks | TOKN v0.3.105+, Chrome or Chromium, Anthropic API or compatible gateway, Python 3.9+ + matplotlib, numpy |
| [change-tracking](change-tracking/README.md) | Tracks which shapes moved or appeared between two frames, measured from pixels and checked against a known answer | TOKN v0.3.105+, Anthropic API or compatible gateway, Python 3.9+ + Pillow |
| [verified-completion](verified-completion/README.md) | The completion gate runs your tests before an agent may finish, `--require-patch` holds a run with no edit, and `self-harness` accepts a prompt change only when it measurably helps | TOKN v0.3.112+, Go 1.22+, Python 3.9+, Git, a model key |
| [battery-passport](battery-passport/README.md) | Pre-publication gate check of six Battery Passport drafts: compliance, carbon-footprint method, due diligence, chemistry | trial |
| [climate-ensemble](climate-ensemble/README.md) | Five CMIP6 regional projection claims checked for calibrated likelihood and ensemble size | trial, optional Python deps |
| [criticality-package](criticality-package/README.md) | Criticality-safety QA review of six spent-fuel pool storage packages | trial |
| [dft-candidate-screen](dft-candidate-screen/README.md) | Five cathode-coating candidates from a DFT batch: convergence, pseudopotentials, phase stability | trial |
| [energy-board-pack](energy-board-pack/README.md) | Release gate for a quarterly energy and carbon board pack | trial |
| [green-project-screen](green-project-screen/README.md) | Green-finance eligibility screen for five solar, wind and hydrogen projects | trial |
| [grid-surrogate-trust](grid-surrogate-trust/README.md) | Six surrogate power-flow predictions verified before an operator may use them | trial |
| [interconnection-screen](interconnection-screen/README.md) | Five interconnection requests through an N-1-1 screen and an IBR stability gate | trial |
| [lead-advancement](lead-advancement/README.md) | Hit-to-lead advancement triage for six compounds in a kinase series | trial, optional Python deps |
| [mission-compliance](mission-compliance/README.md) | Pre-pass go/no-go for a five-satellite LEO constellation: orbit, link margin, debris disposal | trial |
| [neuro-recording-qc](neuro-recording-qc/README.md) | Data-quality and ethics review of six recordings before a group analysis | trial, optional Python deps |
| [rnaseq-qc](rnaseq-qc/README.md) | RNA-seq library QC gate before differential expression, including batch confounding | trial |
| [well-work-orders](well-work-orders/README.md) | Pre-job safety and design review for six pad work orders | trial |
| [wgs-report-readiness](wgs-report-readiness/README.md) | WGS run QC and report-readiness review for six samples, including consent | trial |
| [claim-scrub](claim-scrub/README.md) | Six healthcare claims scrubbed before submission: code-pair edits, unit limits, medical necessity, prior authorization, PHI | trial |
| [claims-reserving-review](claims-reserving-review/README.md) | Insurance claims, underwriting fairness and reserve items reviewed, citing policy clauses, with no final coverage determination | trial |
| [ghg-inventory-check](ghg-inventory-check/README.md) | GHG inventories, a Scope 3 calculation and a disclosure claim checked for factor provenance, double counting and greenwashing | trial |
| [ppap-capability-release](ppap-capability-release/README.md) | Lot release for seven characteristics from raw SPC data, gauge R&R and the PFMEA | trial |
| [shipment-release-review](shipment-release-review/README.md) | Seven fictional export shipments: sanctions screening, export classification, licensing and end-use red flags | trial |
| [expedited-case-triage](expedited-case-triage/README.md) | Seven synthetic safety case reports triaged for seriousness, expectedness and the expedited reporting clock | trial |
| [oncology-governance](oncology-governance/README.md) | Six oncology scenarios check PHI, human-in-the-loop and decision-support framing | trial |
| [physai-fleet](physai-fleet/README.md) | `physai` mode generates a 14-agent warehouse robot fleet | trial |
| [science-review](science-review/README.md) | A reviewer finds three planted defects in a figure caption with `review_artifact` | — |
| [quality-flywheel](quality-flywheel/README.md) | `tokn flywheel run` grades a dataset over two cycles against a baseline | — |
| [verified-improvement](verified-improvement/README.md) | A pharmacovigilance triage prompt is optimized, confirmed on held-out cases and gated on a measured noise band | — |
| [loop-graph](loop-graph/README.md) | A governed graph of loops refuses a metric that is fooling itself; a held-out check confirms it | — |
| [skill-compose](skill-compose/README.md) | TOKN picks which skills, how many and in what order from a small library | — |
| [dataflow](dataflow/README.md) | Skills are ordered by what they consume and produce; a broken chain is flagged | — |
| [tool-contract](tool-contract/README.md) | An off-contract tool call is repaired instead of failing | — |
| [mcp-server](mcp-server/README.md) | `tokn serve` as an MCP server for Claude Desktop, VS Code or any MCP client | — |
| [rnaseq-mcp-server](rnaseq-mcp-server/README.md) | TOKN writes a standalone RNA-seq QC MCP server (read-only annotations, structured output, paging, actionable errors), checked by an independent MCP client | Anthropic API or compatible gateway, Python 3.10+ |
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
| [ethnointelligence](ethnointelligence/README.md) | The Environment Contract: declared vs. probed vs. open context, an invalid declaration refused, and finrisk refusing to guess a regime | v0.3.125; step 4 needs a model and the finrisk trial |
| [judgments](judgments/README.md) | Local advisory checks on supplied run evidence, not proof of answer correctness | — |
| [full-stack-app](full-stack-app/README.md) | Build a small full-stack task-manager app from a written spec, then check it | — |
| [flows](flows/README.md) | Multi-step workflows started from the REPL | — |
| [tabular-prediction](tabular-prediction/README.md) | A local tabular baseline predicts from synthetic CSVs; optional foundation-model setup | Python; weights only for optional backends |
| [web-agent](web-agent/README.md) | The interactive `webagent` mode on a public page (compare with webwright) | Chromium |
| [peer-collab](peer-collab/README.md) | Two people, two agents, one fictional reactor safety dashboard | — |
| [self-improvement](self-improvement/README.md) | Improve a prompt bundle within budgets, with a sealed held-out check (`tokn rrsi`) | — |
| [evidence-earned-prompting](evidence-earned-prompting/README.md) | Insurance-claims SQL: each failure (unknown column, wrong literal, join fan-out) earns one evidence-cited prompt patch; recurring patches become promotion candidates, never auto-promoted (`tokn earned-prompt run`) | none offline; a model provider for the optional live step |
| [workflow-discovery](workflow-discovery/README.md) | Write, check and inspect a workflow graph the model follows step by step (`tokn procgraph`) | trial |
| [clinical-council](clinical-council/README.md) | Several models agree a synthetic precision-medicine case, with optional infographics | trial |
| [agent-loop-essentials](agent-loop-essentials/README.md) | Task anchor, repo map, a predictability report checked against an outcome contract | — |
| [sdk-generation](sdk-generation/README.md) | Ingest a small OpenAPI spec, generate client SDKs, validate them | language toolchains |
| [domain-plugin](domain-plugin/README.md) | Scaffold, validate and install your own small domain plugin | — |
| [event-trigger](event-trigger/README.md) | Start agent runs from events: a local folder queue first, Azure Service Bus optional | your own broker (optional) |
| [always-on-claims-intake](always-on-claims-intake/README.md) | An always-on claims intake agent: events wake one worker, sessions carry over between runs, unattended writes are denied and a daily token budget is enforced (`tokn always-on`) | Python 3.10+, tokn v0.3.99+, Azure OpenAI with `az login` (or llama.cpp) |
| [always-on-claims-desks](always-on-claims-desks/README.md) | Two always-on agents from separate instances, each with its own workspace, state, budget and tool allowlist, hand one insurance claim back and forth with `handoff` (`tokn always-on`) | Python 3.10+, git, tokn v0.3.100+, Azure OpenAI with `az login` (or llama.cpp, not live-tested) |
| [federation](federation/README.md) | A leader fans a task out to two local workers and applies the results back | — |
| [local-llamacpp](local-llamacpp/README.md) | Run TOKN against a local GGUF model served by llama.cpp, offline once weights are downloaded | llama.cpp, a GGUF model |
| [insurance-loss-inspection](insurance-loss-inspection/README.md) | Three local models on one synthetic auto claim: a coding model drives insurance mode, a vision model answers photo damage checks, a decision model triages from a summary | llama.cpp, three GGUF models, tokn v0.3.95+ |
| [toknish](toknish/README.md) | Auditable worker exchanges, with authentication checked using the run token; a separate compact-answer pilot benchmark | `tokn` on PATH; Ollama/local model or cloud provider |
| [agent-team](agent-team/README.md) | A declarative team (planner, implementer, reviewer) builds a small app | — |
| [authority-frames](authority-frames/README.md) | When the agent acts, asks or stops: permission, ask-or-act and stuck signals | — |
| [hands-off-run](hands-off-run/README.md) | A long autonomous run with budgets, checkpoints and a verified finish | — |
| [credit-underwriting](credit-underwriting/README.md) | Financial-risk gates on a synthetic small-business loan file | trial |
| [meeting-to-poc](meeting-to-poc/README.md) | Meeting minutes to a design plan to a proof-of-concept scaffold; optionally pulls minutes from your own Microsoft 365 via WorkIQ | your own M365 tenant (optional) |
| [computer-use-models](computer-use-models/README.md) | Drive a browser with self-hosted computer-use models (Fara, MagenticBrain) on your own GPU endpoints | your own GPU endpoints |
| [ontology-sparql](ontology-sparql/README.md) | Load a synthetic Turtle ontology, query it with SPARQL, and watch the reasoner infer new facts; Fabric/Snowflake connectors optional | none (warehouse optional) |
| [ontology-from-tables](ontology-from-tables/README.md) | `tokn ontology` drafts a reviewable ontology (OWL, R2RML, TMDL) from a folder of CSVs, one table, SQLite, PostgreSQL/MySQL or Parquet | none (Python for SQLite/Parquet, Docker for PostgreSQL/MySQL, both optional) |
| [knowledge-bundles](knowledge-bundles/README.md) | Validate, migrate, export and import portable knowledge bundles through the agent's OKF tools | none |
| [openshell](openshell/README.md) | Run TOKN in an NVIDIA OpenShell sandbox: generated profile, enforcing egress policy, non-root image; keys never enter the sandbox | Linux or WSL 2, OpenShell, Docker or Podman |
| [agent-organization](agent-organization/README.md) | Agensh-style self-organizing organization: workers claim tasks on a shared board, a supervisor feeds failed checks back, local GGUF models for air gap, scale-out and upstream Agensh | Git, Python; local models optional |
| [decisions-api](decisions-api/README.md) | OpenAI / Azure OpenAI Decisions API (`/v1/decisions`) from the OpenAI SDK and through `tokn system-one` | OpenAI or Azure OpenAI key, Python |
| [grounded-decisions](grounded-decisions/README.md) | One call searches the web and a local knowledge base, then answers typed questions with sources; thin evidence returns unknown instead of a guess. Travel-approval scenario with a decision circuit and replayable evidence packs | System One backend (WebIQ key optional) |
| [domain-relay](domain-relay/README.md) | Six models work one domain brief in seven stages (discover, plan, execute, critique, decide, revise, reflect), and code grades the result. Graded walkthroughs for batterypass, climsci, drugdisc, edagent, energy, gridfm and mobility, each ending with a proposed `/teach` rule | trial, keys for the models you use (see `.env.example`) |
| [loops-and-ship-ready](loops-and-ship-ready/README.md) | `/loop define`, prompt loops, find-and-refute, `tokn ship-ready`, `/rewind` and REPL keys on a small buggy repo | Git, Python |
| [t3code](t3code/README.md) | Drive TOKN from T3 Code's web, desktop or mobile app as a Local ACP command: modes, model picker, inline diffs, resume | T3 Code |
| [coding-clis](coding-clis/README.md) | Use TOKN with Claude Code, Codex, Copilot CLI, Gemini CLI and Antigravity: MCP tools, `/conduct` peers, config import | Any of those CLIs |
| [gemini-api](gemini-api/README.md) | Let the agent use Google's Gemini API CLI through a safe `gemini_api` tool: analyze files, images, speech, deep-research agents | `gemini-api`, a Gemini API key |
| [single-agent-loop](single-agent-loop/README.md) | Fold a router and its subagents into one agent loop with skills and tools, proving each step with evals (`tokn single-loop`); offline demo built in | none |
| [dynamic-workflows](dynamic-workflows/README.md) | Background agent fleets from one prompt: bundled workflows, the `iterative-refine` controller, the `ultrawork` keyword, save/resume, domain capsules | — |
| [decision-circuits](decision-circuits/README.md) | Turn keyword/regex decisions into typed, testable decision circuits: starter packs, static analysis, test vectors, generated Python, detect/draft, profile, ledger — all offline (`tokn circuit`) | Python 3.9+ (optional) |
| [delegation-and-signoff](delegation-and-signoff/README.md) | Rate a task on stakes, reversibility, ambiguity and frequency to get an automation level and the controls it needs (`tokn delegate`), then sign off a change and catch drift (`tokn sign-off`) | Git |
| [replay-worlds](replay-worlds/README.md) | Record evolve pools as replay worlds, then replay, rank and explain exploration policies offline — degenerate worlds, off-record counts and honest UNDECIDED verdicts | Nothing (a model provider only for the optional real evolve run) |
| [solution-graphs](solution-graphs/README.md) | Hand-write, validate, generate and run a guarded solution graph with measured checks; see --execute, --allow-external, --air-gap and --allow-code refuse | Python 3.11+; model provider for optional steps 9–10 |
| [ax-runner](ax-runner/README.md) | Run TOKN as a runner for Google's AX control plane (pre-stable): generate manifests, test the runner locally, and track spend against a ceiling | TOKN, git; Docker and an AX cluster optional |
| [biomolecular-modeling](biomolecular-modeling/README.md) | Inspect the experimental Boltz-2 catalog, reproduce a refused preflight without a GPU, then prepare a future externally reviewed protein-only container run | none for catalog/diagnostics; Linux GPU/Docker and reviewed staged artifacts for execution |
| [protein prediction and embeddings](biomolecular-modeling/additional-adapters/README.md) | Separate Chai-1, ESM C and OpenBind-0 selectors; GPU-free refused preflights, not fabricated inference | none for diagnostics; separately staged and reviewed GPU execution |
| [design and genomic models](biomolecular-modeling/design-and-genomics/README.md) | ProteinMPNN, RFdiffusion and seven CLI-only genomic profiles; target-free refused preflights and private-evidence boundaries | none for diagnostics; RFdiffusion3 execution remains held |
| [biomolecular shadow routing](biomolecular-modeling/shadow-routing/README.md) | Synthetic offline next-action advice, typed decision replay and holdout routing benchmarks; no model execution or scientific acceptance | none |

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

This example **needs your own LLM access and a decision-model backend**,
and it makes paid model calls. Costs depend on the models, provider prices
and run length; no current cost is established here. It runs on both the
trial and the Community tier. Start at
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

Follow [judgments/README.md](judgments/README.md) to create a scratch folder,
copy the request files and generate `bundle.json`, including a compatible
Windows PowerShell form.

Both exit `0`. The difference is in `decision.action` — a `revise` judgment means
the command worked and is telling you something about the run it was given.

For the full walkthrough, including how a malformed request is rejected, see
[judgments/README.md](judgments/README.md).

`decision.applied` is always `false`: a judgment is advisory and authorises
nothing.

## Running all of it unattended

`../scripts/community-smoke.sh` (bash) and `../scripts/community-smoke.ps1`
(PowerShell) check the Community on-ramp, three domain previews and the
same two judgment cases, asserting the expected decisions. They do not read the files in this
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
