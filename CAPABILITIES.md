# What TOKN can do

**TOKN is the harness around your models.** It helps an agent understand a
task, use tools, collaborate and check its work. Bring a cloud model or prepare
a local setup; choose the workflows and controls your task needs.

Updated for **[v0.3.115](https://github.com/bhakthan/tokn-dist/releases/tag/v0.3.115)**.
This is a selected product overview; use the commands below for your installed build.
Availability depends on your platform, licence, model and installed tools.
See [platform support](README.md#platform-support) before starting a trial.

```sh
tokn --help
tokn introspect
```

Those commands describe your installed build. Inside an agent session,
`/help` lists commands and `/learn <topic>` opens a built-in lesson.
For installation and your first run, start with [GETTING_STARTED.md](GETTING_STARTED.md).

### CLI shortcuts

```text
tokn                        # interactive session
tokn "fix the failing test" # session that runs this prompt first
tokn -p "summarise this"    # one-shot: run, print, exit
tokn -c                     # resume the last unfinished run in this repo
tokn -m <model>             # set the model name for this run
```

## Point it at a repo and just ask — your first 5 minutes

Configure a model with [SETUP.md](SETUP.md), open a repository and start
`tokn` (bare `tokn` opens the same session as `tokn agent-repl`). Ask in plain language:

```text
Give me a short tour of this repository, citing the files you read.
Trace a login request from its route to the database.
Make the smallest fix, then run the relevant tests.
```

These are example requests, not recorded results. TOKN can read and search code,
edit files and run development tools, subject to your permissions. Builds and
tests still need the project's own toolchain.

Walkthrough: [first ten minutes](examples/first-ten-minutes/README.md).

## Bring your own models — local or cloud

Choose a hosted provider or a local runtime such as Ollama, llama.cpp/GGUF or
ONNX Runtime GenAI. Hosted options include OpenAI, Azure OpenAI, Anthropic,
Gemini, Bedrock, Vertex AI and OpenAI-compatible endpoints.

```sh
tokn doctor --list
tokn doctor --provider ollama
```

Model capabilities vary. Select a model appropriate for the workflow; a small
local model is not interchangeable with a tool-calling or vision-capable model.
Provider calls use your credentials and may incur charges.

**Offline operation requires preparation.** Stage the runtime, weights and any
workflow dependencies before disconnecting. Choose local endpoints and the
command's documented air-gap option (`--air-gap` or `--airgap`; check its help).
Disable install registration and update checks with `TOKN_NO_REGISTER=1` and
`TOKN_NO_UPDATE_CHECK=1`. Cloud calls send inputs to your configured provider.
For enforced isolation, use host-level network controls; TOKN settings are not
an operating-system sandbox.

Walkthrough: [local llama.cpp](examples/local-llamacpp/README.md).

## Compose a solution, not just a chat

A useful solution may need several kinds of model, not one large chatbot:

| Role | Example job |
|---|---|
| Language or coding model | Plan the task, write code and explain the result |
| Vision model | Inspect an approved image |
| Small decision model | Answer bounded classification or routing questions |
| Tabular predictor | Compute predictions from local numerical or categorical data |
| Tools and human review | Run checks and decide whether a result is fit for use |

`tokn solution` helps plan and run these combinations where the required
components are available. Execution and external calls require explicit opt-in.
Optional generated-Python execution is **not sandboxed**.

Walkthroughs: [solution graphs](examples/solution-graphs/README.md),
[three local models on one claim](examples/insurance-loss-inspection/README.md)
and [local tabular prediction](TABULAR.md).

## Typed decisions — fast, bounded judgments beside the LLM

**System One** asks typed questions rather than requesting an essay: a choice,
a probability or a score. Use it for triage, routing and bulk labelling.
Backends include Jev, OpenAI/Azure Decisions API, Microsoft-Decision-1,
Nimble and self-hosted Clef models.

```sh
tokn system-one models
tokn system-one status
```

Decisions are advisory, not permission to act. Grounded decisions can attach
retrieved evidence; insufficient evidence can yield an unknown answer.
The separate `tokn judgments` rules provider supports offline evaluation.

Walkthroughs: [grounded decisions](examples/grounded-decisions/README.md),
[decision council](examples/decision-council/README.md) and
[offline judgments](examples/judgments/README.md).

## Always-on agents — wake, work and hand off

`tokn always-on` runs an agent from a durable inbox. An event wakes a bounded
run; a later event can continue the same session. Check status and enforce
per-run and daily token budgets.

**Two desks can work one case.** Each agent has its own workspace, state, tool
selection and budget. Configured peers can hand off a case with a bounded
handoff chain. An insurance intake desk, for example, can ask a review desk
for advice and use its reply to draft a note for a human.

Unattended runs deny actions that need approval. TOKN does not install a
background service: use your operating system's scheduler if you need one.
This is an inbox worker, not a promise of autonomous end-to-end business action.

```sh
tokn always-on --help
```

Walkthroughs: [one intake agent](examples/always-on-claims-intake/README.md)
and [two collaborating desks](examples/always-on-claims-desks/README.md).

## TOKNish — a checkable receipt for agent work

When agents collaborate, "done" is not much to review.
**TOKNish federation adds a checkable record to the exchange.**

Imagine a worker checking a code change:

| Question | What the record helps you inspect |
|---|---|
| What came back? | "Unit tests passed." |
| What supports it? | A test-run log, with "integration tests not checked" left explicit |
| Was the recorded exchange altered? | Audit checks on message integrity and, with the shared token, authentication |

This is an illustration, not literal output or a claim that the answer is true.
For a session that used TOKNish:

```sh
tokn toknish audit <session-id> --gloss
```

The command reads the existing audit record and can show a plain-English
reading. Use `--help` for log locations and authentication options.
Missing records and unchecked authentication are not proof of verification.
**A clean exchange still needs correct tests and appropriate human review.**

**TOKNish-M is separate and experimental.** Its benchmark compares compact
model answers with ordinary prose, measuring quality and answer size.
It does not automatically enable a compact-answer mode for live sessions,
and shorter answers are not a guaranteed saving for every model or task.
Inspect the pilot with `tokn tkm bench --help`; actually running a benchmark
needs a configured model and makes model calls.

## Goals, loops and workflows — the right size for the job

Start with one request. Add repetition or collaboration only when needed:

| Need | Use |
|---|---|
| Keep working toward a defined check | `/loop define`, then `/loop run` |
| Repeat a prompt on a schedule | `/loop 15m <prompt>` |
| Let a prompt loop pace itself | `/loop auto <prompt>` |
| Coordinate several roles or tasks | A workflow or agent team |
| Continue a case across separate events | An always-on inbox agent |

Use the workflow's limits and review its expected model usage before running.
Walkthroughs: [loops and checks](examples/loops-and-ship-ready/README.md),
[dynamic workflows](examples/dynamic-workflows/README.md) and
[agent teams](examples/agent-team/README.md).

## Self-organizing teams of agents — scale without a central orchestrator

`tokn agora org` lets workers claim tasks, share findings and submit patches.
The host verifies work before merging. Workers can use local model endpoints
or run on other machines; remote operation needs explicit setup.

Plan capacity and model-call costs before scaling out. Local models require
staged weights and sufficient memory. A worker reporting success is not a
substitute for verification.

Walkthrough: [agent organization](examples/agent-organization/README.md).

## Software factory: a gated pipeline of agent roles

`tokn factory` runs work items through a pipeline you declare in `factory.yaml`.
The file sets the intent, domain invariants, gates, budgets and intake sources.
Each stage has its own role: product, architect, implementer, reviewer, test,
release and observer. The observer can turn CI failures and incidents into
drafted work items, and those items go through the same gates as any other.

- **Your gates, not the agent's opinion.** Typed decision-model checks, test
  thresholds, blast-radius limits and budgets. Prod releases and spec changes
  wait for a named human approver.
- **Mix models per role.** Each role can use a frontier model, a Hugging Face
  open-weights model or a local model. `data_boundary: local` keeps a role on a
  loopback endpoint.
- **Audit and resume.** Events are append-only and hash-chained, and
  `tokn factory verify` re-checks them. An interrupted run picks up where it
  stopped.

Agent fixes can still be wrong. The gates and tests you configure decide what
is caught. Review what reaches prod, and budget for several rework rounds.

Walkthrough: [RNA-seq software factory](examples/rnaseq-software-factory/README.md).

## Measure and improve — keep the checks independent

- **Quality flywheel:** evaluate examples, try a fix and re-evaluate against a baseline.
- **Graph of Loops:** check proposed improvements against broader outcomes,
  independent tests and human judgment.
- **Evidence-earned prompting:** propose corrections from observed failures;
  regression-check recurring changes before human-approved promotion.
- **Design loops:** explore candidates against your checks and retain a
  reviewable record of the experiment, including independent validation status.

These workflows help expose regressions; they do not prove an agent cannot
make mistakes or optimize the wrong goal.

Walkthroughs: [quality flywheel](examples/quality-flywheel/README.md),
[governed loops](examples/loop-graph/README.md),
[evidence-earned prompting](examples/evidence-earned-prompting/README.md)
and [autodesign](examples/autodesign/README.md).

## Check your work — and take it back

`tokn ship-ready` checks a change and reports READY or NOT READY. Missing or
inapplicable checks are reported as skipped, not passed. A READY result only
covers the checks that ran; it is not a security or correctness certification.

In the interactive session, `/rewind` restores a recorded checkpoint;
`/rewind undo` reverses that rewind. Checkpoints are not a replacement for
version control.

Walkthrough: [loops, ship-ready and rewind](examples/loops-and-ship-ready/README.md).

## Works with your existing coding agent

Use TOKN from an MCP-capable coding client:

```sh
tokn serve --mode mcp
```

Other integrations include ACP clients such as T3 Code, plus A2A, webhooks and
an OpenAI-compatible tool endpoint. Follow the relevant setup guide; publishing
a network service needs authentication and deliberate exposure controls.

Walkthroughs: [coding CLIs](examples/coding-clis/README.md),
[MCP server](examples/mcp-server/README.md) and [T3 Code](examples/t3code/README.md).

## Images, browser work and knowledge

With appropriate models and dependencies, TOKN can work with images, drive a
browser, and prepare reusable knowledge artifacts.

| Task | Walkthrough |
|---|---|
| Repeatable, code-first browser work | [Webwright](examples/webwright/README.md) |
| Screenshot-guided browser actions | [Computer-use models](examples/computer-use-models/README.md) |
| Photo damage checks with human referrals | [Loss inspection](examples/insurance-loss-inspection/README.md) |
| Draft a reviewable ontology from tables | [Ontology from tables](examples/ontology-from-tables/README.md) |
| PostgreSQL and CSV ontologies, model enrichment, shared-state decision batches and external RDF-row SHACL checks | [PostgreSQL + Excel-exported CSV](examples/postgresql-auto-ontology/README.md) |
| Query and reason over RDF | [Ontology and SPARQL](examples/ontology-sparql/README.md) |
| Move a portable knowledge bundle | [Knowledge bundles](examples/knowledge-bundles/README.md) |

Model access, browsers, packages and external data sources are separate
dependencies, not included simply because TOKN is one binary. Check each
walkthrough's prerequisites. Experimental biomolecular integrations have
additional preflight and review requirements; see their
[current scope](examples/biomolecular-modeling/README.md).

## Domain harnesses

TOKN offers **38 domain modes** with field-specific tools, checks and review
workflows. Launch an entitled mode with `tokn agent-repl --mode <name>`.
Inspect your installed roster with `tokn introspect --section modes`.

| Mode | Focus |
|---|---|
| `appsec` | Application security review |
| `atmchem` | Atmospheric chemistry and air quality |
| `batterypass` | Battery Passport preparation and conformance |
| `climsci` | Climate analysis |
| `clintrial` | Clinical-trial analysis |
| `compbio` | Computational biology workflows |
| `cybersec` | Defensive cybersecurity |
| `drugdisc` | Drug-discovery analysis |
| `edagent` | Sandbox-only emergency-department scenarios |
| `energy` | Energy systems and carbon accounting |
| `esg` | Sustainability reporting |
| `finrisk` | Financial risk and compliance analysis |
| `genomics` | Genomic analysis |
| `geospatial` | Earth observation and spatial analysis |
| `greenenergy` | Renewable-energy projects |
| `grideng` | Power-grid engineering |
| `gridfm` | Power-grid model validation |
| `healthrcm` | Healthcare revenue cycle |
| `insurance` | Claims, underwriting and reserving support |
| `legalai` | Legal and regulatory analysis |
| `matsci` | Materials science |
| `mfgquality` | Manufacturing quality |
| `mobility` | Vehicle and mobility engineering |
| `neurosci` | Neuroscience data analysis |
| `nucsci` | Nuclear-science analysis |
| `oilgas` | Oil and gas engineering |
| `oncology` | Cancer research and decision support |
| `pharmacovig` | Pharmacovigilance case review |
| `physai` | Physics reasoning |
| `precmed` | Precision-medicine analysis |
| `quantumsci` | Quantum experiments and computing |
| `robotics` | Robotics and digital twins |
| `semicon` | Semiconductor engineering |
| `spacemarine` | Space and maritime engineering |
| `structbio` | Structural biology |
| `synbio` | Synthetic biology with screening controls (requires admin approval; excluded from trials) |
| `tradecomp` | Trade-compliance review |
| `transcriptomics` | RNA-seq quality and analysis |

Community includes fixed read-only previews for power-grid, geospatial and
Battery Passport checks. Full domain workflows require appropriate entitlement;
some accept only synthetic or sandbox inputs. `synbio` is excluded from
self-issued trials and requires explicit administrator approval. **A licence
does not bypass safety gates.** Installing a skill pack does not unlock a domain.

Outputs are decision support, not professional advice, certification or
permission to make clinical, legal, financial or operational decisions.
Try the [Community quick start](README.md#community-quick-start--no-trial-required)
or browse the [synthetic walkthroughs](examples/README.md).

## Customize with visibility and control

Add instructions, skills, plugins and prompt overrides without rebuilding TOKN.
Workspace capabilities such as hooks, MCP connections and prompt overrides
require explicit trust. Installing instructions is not granting permission to
execute tools.

```sh
tokn config doctor
tokn doctor prompts
```

The first shows active configuration with secrets redacted; the second audits
prompt configuration without editing it. In a session, `/teach` captures
reusable guidance and `/recall` searches saved knowledge.

Review data before sharing it with a model or saving it. Scope tool permissions
to the job, and use an appropriate sandbox where isolation is required.
Walkthroughs: [custom hooks](examples/custom-hooks/README.md),
[memory](examples/memory/README.md) and
[OpenShell](examples/openshell/README.md).

---

This is a **feedback-first evaluation distribution**. Report problems through
issues in this repository, without posting secrets or sensitive data.
TOKN is proprietary software; AI output must be independently verified.
See the [License & Disclaimer](LICENSE.md) for terms and restrictions.
