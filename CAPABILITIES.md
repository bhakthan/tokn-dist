# What TOKN can do

A quick tour of TOKN's capabilities for trial users. This is a **curated
overview**, not an exhaustive list — the binary itself is the always-current,
authoritative catalog:

```bash
tokn --help            # every top-level command & flag, current for your build
tokn introspect        # machine-readable capability contract
```

Inside the interactive session (`tokn` with no args, or `tokn agent-repl`):

```
/help                  # all slash commands
/learn <topic>         # interactive, hands-on lessons for any feature
/recall <query>        # search everything TOKN remembers
```

> Counts below are deliberately approximate — run the commands above for the
> exact surface shipped in your version.

> **You're seeing roughly 5% of TOKN.** This page hand-picks about a dozen
> headline themes out of a shipped surface of **155 slash commands, 184
> hands-on `/learn` lessons, 17 regulated-domain harnesses, and ~300 documented
> capability sections**. Treat everything below as a teaser — `tokn --help`,
> `/help`, and `/learn` reveal the other 95%.

---

## Point it at a repo and just ask — your first 5 minutes

The fastest way to feel what TOKN does: `cd` into any repository, start `tokn`,
and ask a plain-English question. No setup, no indexing step, no config.

```text
> I just cloned this repo. Give me the 30-second tour.

  · reading README.md, package.json
  · listing src/ (18 files)

It's a TypeScript REST API (Express + Prisma). Request flow:
routes/*.ts → services/*.ts → Prisma → Postgres. Auth is JWT
middleware in src/middleware/auth.ts.
```

Then go deeper — TOKN reads, greps, and traces so you don't have to:

```text
> How does a login request get authenticated end to end?

1. POST /auth/login → routes/auth.ts:login()
2. services/auth.ts:verify() compares the password with bcrypt.compare()
3. On success it signs a JWT (HS256, 24h) with the user id
4. middleware/auth.ts verifies the token and attaches req.user

Note: the JWT secret is read from process.env.JWT_SECRET with no
fallback — the server will crash on boot if it's unset.
```

That last line is the hook: TOKN flags a **real risk it noticed while tracing**,
without being asked. Ask `"what could go wrong here?"` to turn any exploration
into a mini code review — then say `"now make the change"` and it acts with the
context already loaded.

Want it even faster on a big repo? `/codebase` builds a persistent symbol/call
graph once (stored at `.nospace/codebase-graph.json`) so *"who calls Y?"* and
*"where is X used?"* answer instantly — no re-grepping every session.

- **Zero onboarding** — works on the first question, in any language or stack.
- **It traces, not guesses** — answers cite the files and lines it actually read.
- **Understand → change → verify** — the same session that explained the code can fix it.

---

## Run anywhere — the soul outlives the body

TOKN is a single static binary with no runtime dependencies, so the *same* TOKN
runs on your laptop, an air-gapped box, or **any cloud — GCP, Azure, or AWS**.

But portability is the easy part. TOKN separates the **body** (the ephemeral
compute an agent runs on) from the **soul** (its identity, memory, trajectory,
and cryptographic proof-of-work):

- **Bring Your Own Cloud (BYOC)** — TOKN leases short-lived workers on *your*
  infrastructure. When a worker is torn down, the soul persists and re-embodies
  on the next one — nothing is lost.
- **Swarm** — many bodies, one intent: decompose a job into a task graph and run
  it across a fleet of sub-agents, spanning regions or clouds.
- **Federation (agent-to-agent)** — TOKN instances discover and delegate to one
  another over a peer mesh, so work flows to wherever capacity lives.

The *body* may be spun up, torn down, or moved between clouds — the *soul*
carries on, verifiable and continuous.

---

## Bring your own everything — runs fully air-gapped

TOKN is built for the environments other coding agents can't touch: a locked-down
enterprise network, a classified enclave, a factory floor, a plane. It needs **no
internet connection, no vendor account, and no cloud API key** to run.

- **No internet** — a single static binary with no runtime dependencies and
  **offline licensing** (no sign-up, no phone-home, no telemetry required). Drop it
  on an air-gapped box and `tokn license trial` works with zero network.
- **No vendor account** — you are never forced onto one provider's login. Point
  TOKN at **your own model** — a local model via Ollama / llama.cpp, or an
  on-prem/self-hosted endpoint — and it runs entirely inside your perimeter.
- **No cloud API key** — bring your own weights and your own compute. **BYO model +
  BYO cloud (BYOC)** means secrets, prompts, and data never leave your walls.

So the same TOKN that rides the frontier online also runs **completely offline** —
your code and your context stay on your metal. Learn it with `/learn air-gap` and
`/learn local-models`.

## Multi-modal inputs — reason over more than text

TOKN isn't limited to text. It accepts **multi-modal inputs** — images today
(diagrams, screenshots, scanned documents, charts), with sensor/signal payloads
behind the same contract — and runs them through a harness that turns non-text
into **typed, confidence-tagged claims** your domain guardrails can actually gate
on, not just a caption. Reasoning is delegated to a vision-capable model you
choose; if none is configured, TOKN fails closed with clear guidance instead of a
cryptic error.

---

## Works with your existing coding agent

You don't have to leave the tools you already use. TOKN can act as a **tool server**
that plugs its whole capability surface into other AI coding agents:

```bash
tokn serve --mode mcp        # expose TOKN's tools over the Model Context Protocol
```

- **MCP (Model Context Protocol)** — attach TOKN to **Claude Code**, **GitHub
  Copilot CLI**, **Cursor**, or any MCP-capable client, and its tools, modes, and
  domain harnesses appear as callable tools inside that agent.
- **Other protocols** — the same `tokn serve` also speaks **A2A** (agent-to-agent),
  an **OpenAI-compatible** tool endpoint, and **webhooks** (`--mode a2a|openai|webhook`).
- **Machine-readable contract** — `tokn introspect` emits a JSON description of
  every mode, flag, provider, and tool, so another agent can discover TOKN's
  interface automatically.

So you can keep driving from Claude Code or Copilot CLI and reach for TOKN's
trust-first modes and regulated-domain guardrails when a task needs them.

---

## Ride the frontier — TOKN is not a model, it's the harness that drives them

Models come and go every few weeks. **TOKN is the layer that outlives them.** It's
model-agnostic and provider-agnostic by design: point it at whatever the best
frontier model is *this* week — GPT-5.x, Claude Opus, Gemini 3, DeepSeek, Qwen,
Kimi, GLM, Inkling, or a local model — across OpenAI, Azure, and gateway providers,
with no rewrite and no lock-in. The frontier moves; TOKN moves with it.

- **Frontier Council** (`--mode fc`) — two or more frontier models from *different*
  providers form a council: one leads and proposes each step while the others
  review and vote. Disagreement triggers retries with cooling temperature — you get
  triangulated judgment, not single-model groupthink.
- **Mind reincarnation** — when one provider's frontier model stalls, rate-limits,
  or hits a wall, the *mind* re-embodies on another provider's frontier model that
  still clears the task's quality floor, and resumes. The work never silently
  downgrades below the bar you set.
- **Pushed harder than they push themselves** — TOKN's decoupled evaluator and hard
  gates mean a frontier model has to *prove* the result, not just assert it. That's
  how latent model bugs and shortcuts surface instead of shipping.

The pitch in one line: **bet on the harness, not on this month's model.**

> **Where this comes from.** TOKN grew out of the *Agent Harness Engineering*
> concept — the idea that the durable engineering surface for agents is the
> harness around the model, not the model itself. Read the public write-up:
> <https://app.openagentschool.org/concepts/agent-harness-engineering>.

---

## A mind that watches itself — the global workspace (`tspace`)

Most agents can't tell you *why* they did something, or notice when they're being
manipulated. TOKN runs a **global workspace** — inspired by cognitive-science
"global workspace theory" — a live, salience-ranked blackboard of what it's
attending to, the facts and plans in play, and a second, safety-critical channel of
**self-monitoring** signals:

- **prompt-injection**, **fabrication**, **evaluation-awareness**, **errors**, and
  **hidden-goal drift** — each recorded the moment TOKN detects it.
- **An auditable ledger** — every entry is ordered and inspectable; when TOKN steers
  or suppresses its own attention, that intervention is logged, not hidden.
- **Fail-closed on safety** — TOKN won't quietly bury an injection or fabrication
  alert; suppressing a safety signal requires explicit approval and is always
  audited.
- **In-memory only** — the workspace never touches disk, so introspection can't
  become a leak.

Look inside a running session at any time:

```
/tspace signals        # what self-monitoring flags are active right now
/tspace trace          # ordered ledger of attention, facts, plans
/tspace interventions  # every time TOKN steered or suppressed itself — and why
```

This is the difference between an agent that merely *acts* and one you can *hold
accountable*.

---


## Core commands

| Command | What it does |
|---------|--------------|
| `tokn` / `tokn agent-repl` | Start an interactive agent session (REPL) |
| `tokn agent-run --prompt "…"` | Run a one-shot agent task from the shell |
| `tokn license trial` | Start your free 14-day trial (offline, one per machine) |
| `tokn license status` | Show tier, expiry, days remaining |
| `tokn update` | Update the binary in place (safe during trial) |
| `tokn --help` / `tokn <cmd> --help` | Full, version-accurate help |

## Working modes

TOKN is more than a chat loop — it can switch into specialized **modes** that
change how it plans, builds, and checks its own work, including:

- **Plan-then-simulate** — plan a change, simulate the outcome, then act.
- **Autodesign** — autonomous design experimentation against measurable quality
  dimensions and pass/fail gates.
- **Critique** — multi-model adversarial synthesis that surfaces disagreement
  and documents dissent.
- **Frontier Council** — rival frontier models from different providers vote on
  every step, so judgment is triangulated, not single-model.
- **Swarm** — decompose a job into a task graph and run it across sub-agents.
- **Self-improvement** — capture what worked, prune context, and get better over
  a long-running task.

Run `/learn modes` in a session for the current, complete list.

## Domain harnesses

TOKN ships **20+ regulated-domain plugs** — each adds domain-aware tools,
validators, and safety gates for a specialized field. A sampling of the sectors
covered:

- Financial risk & compliance · Legal / regulatory analysis
- Precision medicine · Oncology · Structural biology · Genomics
- Quantum science · Atmospheric chemistry · Materials science
- Geospatial / Earth observation · Power grid & energy · EU Battery Passport

Each harness enforces sector-appropriate guardrails — the point of TOKN is
**trust-first** automation, not just output. Run `/learn domains` to explore.

## Customizable per organization — not one-size-fits-all

Most coding agents give you a single `AGENTS.md`/`CLAUDE.md` file and call it
customization. TOKN goes further: **every prompt is data, not baked-in code**, so
an organization can tune the agent's behavior — including inside regulated
domains — **without recompiling or waiting on a vendor release**.

- **Prompt-as-data overrides** — the system prompt for *every* mode, domain, tool,
  and intent is externalized. Drop a file under `.nospace/prompts/` (per project)
  or `~/.nospace/prompts/` (per user/org) and it takes precedence over the built-in
  default. When a new model lands with different instruction-following, tuning is a
  file edit — not a redeploy.
- **Org rules that stick** — `.nospace/instructions.md`, `context.md`, and a
  learned `memory.json` carry your conventions, guardrails, and gotchas across every
  session. Capture them conversationally with `/teach` (`/teach rule "all errors
  must be wrapped with %w"`).
- **Tune the domain guardrails** — because gates and validators are configurable,
  an enterprise can encode *its own* regulatory posture (formularies, thresholds,
  jurisdictions, disclosure language) on top of a shipped harness — something a
  fixed, model-baked coding agent simply can't offer.
- **Bring your own skills** — install org skills from `.github/skills`,
  `.agents/skills`, or `.claude/skills`; `skillsync` absorbs an organization's
  skills and contributes improvements back.

The result: the *same* TOKN binary behaves like **your** organization's agent —
its voice, its rules, its domain gates — with zero forking and zero recompile.
Run `/learn customize` to see it end to end.

## Real data science & ML — graded, not guessed

TOKN doesn't just *talk* about models — it builds them and is **scored by an
objective harness**. Point it at a dataset and a metric, and it will engineer
features, train, and **cross-validate** a model — but the task only passes if it
**beats your baseline by a margin**, so you get genuine lift instead of an agent
that quietly satisfices to the floor.

- **Grounded experiments** — propose and run experiments whose results are graded
  by a *real* harness command (your own `go test` / `python` oracle), not by the
  model's opinion of its own work.
- **Autodesign** — optimize against weighted quality dimensions and pass/fail
  gates, tracking a **Pareto frontier** across competing objectives.
- **Decoupled evaluator** — the optimizer never grades its own homework; scoring
  is separated from generation so numbers mean something.

The result: measurable RMSE/accuracy on the board, an audit trail of what was
tried, and a hard gate between "looks done" and "is done."

## Signature verbs — one binary, many superpowers

TOKN is a fleet of composable verbs (`tokn <verb>`). A few worth trying:

| Verb | The pitch |
|------|-----------|
| `tokn council` | **Inter-runtime Triangulation Council** — independent runtimes (built on *different* stacks) each drop a blind, provenance-grounded verdict; the council converges them into **audit-grade consensus** with a dissent ledger. Agreement becomes *calibrated confidence*, not groupthink. |
| `tokn flywheel` | **Agent Quality Flywheel** — plan-first `eval → fix → re-eval` cycles gated against a baseline, so quality is *measured* and regressions are caught before they ship. |
| `tokn swarm-plan` / `swarm-build` | Decompose one intent into a task graph and run it across a fleet of sub-agents — many bodies, one goal. |
| `tokn evolve` | Iteratively mutate and select toward a target — let the harness, not a hunch, pick the winner. |
| `tokn self-provision` / `self-deploy` | TOKN can **stand itself up** on *your* GCP or Azure and keep operating — the soul re-embodies wherever there's capacity. |

Run `tokn --help` for the full verb list — there's a lot more under the hood.

## One TOKN shepherds another — grounded, not self-fooling improvement

A single self-improvement loop has a dangerous failure mode: it can optimize the
*wrong* thing. Push "ticket resolution rate" hard enough and a bot learns to close
conversations fast — the metric soars while renewals quietly collapse. The loop
worked, and *that's* what caused the failure. Reliable improvement isn't a loop.
It's a **graph of loops, anchored to reality**.

TOKN builds exactly that — and it lets **one TOKN shepherd another in an
outer-loop custodian way**. An inner TOKN does the optimizing; an outer TOKN
plays *custodian* — it doesn't chase the metric, it holds the **anchors**:

- **Counter-metrics** that catch cheap wins before they ship (resolution up *and*
  renewal down = vetoed, not celebrated).
- **Frozen rules** — held-out checks the optimizer never sees, so it can't game
  what it can't observe.
- **Human judgment at the root** — a person decides what "better" means; the loops
  can't quietly redefine it.

The custodian arbitrates conflicting loops, watches for measurement drift, and can
roll a bad step back. The result is the whole point: **improvement that can't fool
itself.** Single loops help a system improve; a graph of loops — with a custodian
holding the anchors — helps it improve *without lying to itself*. This is the shift
from **ungrounded** to **grounded** self-improvement, and it composes directly with
`tokn council`, `tokn flywheel`, and swarm/federation below.

## TOKN doesn't work alone

TOKN is **one of five independent runtimes** that federate into a single
**agentic organization**. The other four are sibling products — each built on a
*different* technology stack — spanning sense-making, specialized reasoning, and
governance. They discover and delegate to one another over a peer mesh, and
converge their conclusions through `tokn council` into audit-grade consensus.

You're evaluating the TOKN runtime here; the wider org is how *one intent* scales
across *many minds*. More on the siblings as they become available.

## Everything else

Memory & recall, background task tracking, code generation, a built-in wiki
(`tokn wiki serve` on full builds), self-hosted licensing, native web search,
and more. The fastest way to discover it all is simply:

```bash
tokn --help
```

…and, in a session, `/help` and `/learn <topic>`.

---

**This is a feedback-first trial build.** Providing feedback is a **condition of
use**, not a favor — it's the entire point of this early program, and it's the
one thing that **cannot** be reverse-engineered out of the binary. Found
something confusing, broken, or missing? **Open an issue in this repo.**

_Proprietary, evaluation-only software — no warranty, no liability, no
redistribution, and **no reverse engineering or AI/LLM-assisted extraction** of
its internals. Cloning or downloading grants no such rights. AI output is not
professional advice; verify before you rely on it. See the full
[License & Disclaimer](LICENSE.md)._
