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
frontier model is *this* week — GPT-5.x, Claude Opus, Gemini 3, DeepSeek, GLM, or a
local model — across OpenAI, Azure, and gateway providers, with no rewrite and no
lock-in. The frontier moves; TOKN moves with it.

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
