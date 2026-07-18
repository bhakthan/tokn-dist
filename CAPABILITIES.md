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

## Everything else

Memory & recall, background task tracking, code generation, a built-in wiki
(`tokn wiki serve` on full builds), self-hosted licensing, native web search,
and more. The fastest way to discover it all is simply:

```bash
tokn --help
```

…and, in a session, `/help` and `/learn <topic>`.

---

**This is a trial build for feedback.** Found something confusing, broken, or
missing? Open an issue in this repo or email **licensing@tokn.dev**.
