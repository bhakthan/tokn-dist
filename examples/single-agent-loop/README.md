# Example: Single agent loop — fold a router and its subagents into one loop

> "We have a router and five subagents. Which ones can become skills, and how
> do we prove nothing got worse?"

Many agent systems begin as a router that hands each request to a specialist
subagent. As models get better, most of those subagents are just a prompt plus
a few API calls. They work better as **skills and tools inside one agent
loop**: there are no handoffs to lose context in and no routing rules to
maintain, and the system costs less to run. `tokn single-loop` helps you make
that change step by step, measuring before and after each one:

| Step | Command | What it tells you |
|---|---|---|
| Measure | `audit` | Which agents always run together, and a proposed verdict per agent |
| | `coverage` | Which chains of agents seen in production your eval tasks actually exercise |
| | `estimate` | Token forecast for the paid eval run, from a small probe run |
| Fold | `fold` | A `SKILL.md` and tool specs scaffolded from a subagent's prompt |
| Decide | `compare` | A before/after verdict over two eval runs: score, tokens, writes, routes |
| Keep as tool | `schema`, `check-response` | A fixed reply shape for subagents that keep their own context |

Every analysis is **offline and deterministic**. Nothing calls a model.
Nothing is written unless you pass `--write`. You decide every verdict.

The method and the file formats follow Anthropic's
[single-agent-loop-kit](https://github.com/anthropics/single-agent-loop-kit),
so traces and eval results you prepared for the kit work here unchanged.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.67 or later | Ships `tokn single-loop` | `tokn single-loop --help` |
| Nothing else for steps 1–7 | The demo data is built into TOKN | — |
| A model provider (step 8 only) | Try the folded skill in a live session | see [SETUP.md](../../SETUP.md) |

It runs on every tier, including the free Community tier.

### What leaves your machine

Nothing, in steps 1–7. They read local files and print reports. Step 8 starts
a normal `tokn agent-repl` session, which sends your prompts to the model
provider you configured.

## 1. Export the demo

The demo is a synthetic outdoor-gear support desk: a `router` and five
subagents (`orders`, `shipping`, `returns`, `billing`, `diagnostics`), with 62
production traces and three eval runs.

bash:

```bash
tokn single-loop demo --export "$HOME/tokn-single-loop"
cd "$HOME/tokn-single-loop"
```

PowerShell:

```powershell
tokn single-loop demo --export "$HOME\tokn-single-loop"
Set-Location "$HOME\tokn-single-loop"
```

Expected:

```text
wrote …/baseline/results.jsonl
wrote …/inventory.tsv
wrote …/probe/results.jsonl
wrote …/prompts/returns.md
wrote …/traces.jsonl
wrote …/v1-fold-returns/results.jsonl
```

| File | What it is |
|---|---|
| `traces.jsonl` | One JSON object per agent call: `trace_id`, `ts`, `agent`, optional `duration_ms`, `input_tokens` |
| `inventory.tsv` | One row per agent: owner, purpose, tools, who invokes it, how much context it reads |
| `baseline/results.jsonl` | The eval run of today's system: one row per task rep, with grade, tokens, calls, writes |
| `v1-fold-returns/results.jsonl` | The same tasks after `returns` was folded into a skill |
| `probe/results.jsonl` | A small 2-task probe run, used for the token estimate |
| `prompts/returns.md` | The `returns` subagent's system prompt |

Just want to see everything at once? `tokn single-loop demo` (with no
`--export`) runs every analysis below and prints one report.

## 2. Audit: what runs together, and what should each agent become?

```bash
tokn single-loop audit --traces traces.jsonl --inventory inventory.tsv --main router
```

Expected (shortened):

```text
62 traces, 151 calls.

| agent | calls | % of traces | % of time | median ms | median input tokens |
|---|---|---|---|---|---|
| router | 62 | 100% | 12% | 494 | 900 |
| orders | 27 | 44% | 21% | 2037 | 1810 |
| shipping | 22 | 35% | 16% | 1775 | 1418 |
| returns | 17 | 27% | 14% | 2091 | 2597 |
| billing | 15 | 24% | 11% | 1788 | 2068 |
| diagnostics | 8 | 13% | 25% | 7920 | 36104 |
...
| Agent | Verdict | Why | Evidence | Confidence |
|---|---|---|---|---|
| router | main | becomes the single loop (proposed) | router or entry point: becomes the single loop | high |
| orders | merge:shipping | runs together with its partner (proposed) | orders → shipping in 35% of traces, coupling 1.00 | high |
| shipping | merge:orders | runs together with its partner (proposed) | orders → shipping in 35% of traces, coupling 1.00 | high |
| returns | fold | becomes a skill plus tools (proposed) | default: a prompt plus API calls that needs no separate context | high |
| billing | fold | becomes a skill plus tools (proposed) | default: a prompt plus API calls that needs no separate context | high |
| diagnostics | as-tool | earned its own context; called as a tool (proposed) | reads a median 36104 input tokens per call (threshold 20000); first ask whether a tool could return less | high |
```

How to read it:

- **Coupling** for a pair is the number of traces where both run, divided by
  the traces of the rarer one. `orders → shipping` has coupling 1.00: every
  time `shipping` runs, `orders` ran first. A pair with coupling ≥ 0.50 that
  appears in ≥ 5% of traces is a **merge** candidate.
- **fold** is the default: a prompt plus API calls becomes a skill plus tools
  in the main loop.
- **as-tool** is for an agent that really needs its own context.
  `diagnostics` reads a median of 36k tokens per call. That is too much to
  pull into the main loop, so it stays separate and is called as a tool.
- **keep** is for anything you decide to leave alone.

The output also includes a draft **PLAN.md**: the verdicts, a worklist
(one item per change), a break map of what could go wrong, and places for
eval notes. Save it with `--write` (to `.nospace/single-loop/`), then edit any
verdict you disagree with. The verdicts are proposals; you decide.

## 3. Coverage: do the evals exercise every chain?

Before you change an agent, make sure some eval task runs it. `coverage`
groups production traces into chains (the set of agents a request touched)
and lists which tasks run each chain and whether they pass today:

```bash
tokn single-loop coverage --traces traces.jsonl --variant baseline --exclude router
```

Expected:

```text
| chain | agents | traces | % of traces | tasks that run it | passing today |
|---|---|---|---|---|---|
| 1 | orders + shipping | 22 | 35% | t01, t02 | t01 |
| 2 | returns | 12 | 19% | t03, t04, t07 | t03, t07 |
| 3 | billing | 10 | 16% | t05, t07 | t05, t07 |
| 4 | diagnostics | 8 | 13% | t06 | t06 |
| 5 | billing + returns | 5 | 8% | t07 | t07 |
| 6 | orders | 5 | 8% | t01, t02, t08 | t01, t08 |
Every listed chain has at least one task.
```

Now try the small probe run, which only has two tasks:

```bash
tokn single-loop coverage --traces traces.jsonl --variant probe --exclude router
```

Expected: three chains show `**none (gap)**` and the command exits with
status **1**:

```text
3 chain(s) have no task. Add a task that runs each one and grades its end before changing those agents.
```

The non-zero exit makes `coverage` usable as a CI gate: you cannot fold
`returns` while no eval would notice it breaking.

## 4. Estimate: what will the eval run cost?

Eval runs make paid model calls. Forecast the tokens from the small probe run
first:

```bash
tokn single-loop estimate probe --tasks 8 --reps 2 --heavy 1
```

Expected:

```text
8 task(s) × 2 rep(s); 2 measured.
- input: 66k to 590k tokens
- output: at least 7.5k tokens
- input, likely (with heavy tasks): ~130k tokens
No prices are applied. Show this before the paid run and again next to the actual.
- Only 2 of 8 tasks measured: input is a range, output a lower bound.
```

With only 2 of 8 tasks measured, the input is a range and the output a lower
bound. When the probe covers every task, the estimate is exact. `--heavy 1`
says one planned task looks like the heaviest measured one (`diagnostics`).
After the real run, add `--actual baseline` to see the actual tokens next to
the forecast.

## 5. Fold: turn a subagent into a skill

Scaffold a skill from the `returns` subagent's prompt:

```bash
tokn single-loop fold returns --prompt prompts/returns.md \
  --tools check_return_window,create_return \
  --description "Use when the customer wants to return or exchange an item."
```

PowerShell (quote the comma list, or PowerShell turns it into an array):

```powershell
tokn single-loop fold returns --prompt prompts/returns.md `
  --tools "check_return_window,create_return" `
  --description "Use when the customer wants to return or exchange an item."
```

Expected (the skill, shortened):

```markdown
---
name: returns
description: Use when the customer wants to return or exchange an item.
---
# Returns
## How to do it
- Check the order date with check_return_window before offering a return.
- Explain the return label steps in plain words.
- Only issue a store credit if the customer asks for one.
- Ask the router to send billing questions to the billing agent.
## Rules and why
- Never create a return for an item outside the 30-day window. — _why: …; if it must never be broken, check it inside a tool instead._
## Reference
- Window: 30 days from delivery
- Restocking fee: none for unused items
<!--
Deleted from the old prompt (persona or old-model instructions):
  - [persona] You are Riley, a friendly returns specialist for an outdoor gear shop.
  - [old-model] Think step by step before you answer.
-->
```

followed by one spec stub per tool (`# Tool: check_return_window`, …).

`fold` sorts the old prompt's lines into steps, hard rules and reference
data. It also drops the persona and old-model instructions, and lists them so
a person can confirm. It is a scaffold, not a finished skill: fill in "done
well means", the reason for each rule, and the tool specs. Notice the line
*"Ask the router to send billing questions…"*. In a single loop there is no
router, so that line must change too.

Add `--write` to save `skills/returns/SKILL.md` and `tools/*.md` under
`.nospace/single-loop/` (or `--out <dir>`). Existing files are never
overwritten without `--force`.

## 6. Compare: did folding `returns` make anything worse?

The demo includes an eval run made after `returns` was folded. Compare it with
the baseline:

```bash
tokn single-loop compare baseline v1-fold-returns --exclude router
```

Expected (shortened):

```text
Metric `task_complete`, 8 common task(s).

| | baseline | v1-fold-returns |
|---|---|---|
| score | 0.875 | 0.875 |
| model calls (mean) | 4.8 | 4.4 |
| input tokens (mean) | 7925 | 7662 |

## Tasks that changed
- t04: 0.50 → 1.00 (one rep)
- t07: 1.00 → 0.50 (one rep)

## Writes that changed
- t07: [create_return \| create_return] → [create_return \| none]

## Paths that changed
- t03: returns called in 100% → 0% of reps
...
## Verdict
**same or better overall, but got worse on some tasks**: t07.
The person decides: keep and go on / keep and stop / fix / revert.
```

The score held and the run got cheaper, but task `t07` got worse in one rep,
where a `create_return` write disappeared. That is the kind of break a
handoff hides. The verdict is one of:

| Verdict | Meaning |
|---|---|
| no verdict yet | Tasks are missing from one run; finish it first |
| does not hold | The overall score dropped |
| same or better overall, but got worse on some tasks | Look at the named tasks before you decide |
| holds | Same or better everywhere |

Add `--fail-if-worse` in CI to exit non-zero on **does not hold**. Add
`--price-in` and `--price-out` (dollars per million tokens) to show cost.
Comparing two runs that do not have the same tasks gives *no verdict yet*:

```bash
tokn single-loop compare v1-fold-returns probe --exclude router
```

## 7. Keep as a tool: a fixed reply shape

`diagnostics` stays separate. When the main loop calls it as a tool, its reply
should have a fixed shape the loop can rely on:

```bash
tokn single-loop schema
```

prints a JSON Schema with five required fields: `conclusion`, `evidence`,
`actions_taken`, `confidence` (`high`, `medium` or `low`) and `caveats`.
Check a reply against it:

bash:

```bash
echo '{"conclusion":"Disk on db-2 is 94% full","evidence":["df -h on db-2"],"actions_taken":[],"confidence":"high","caveats":[]}' > good.json
echo '{"conclusion":"looks fine"}' > bad.json
tokn single-loop check-response good.json
tokn single-loop check-response bad.json
```

PowerShell:

```powershell
'{"conclusion":"Disk on db-2 is 94% full","evidence":["df -h on db-2"],"actions_taken":[],"confidence":"high","caveats":[]}' | Set-Content good.json
'{"conclusion":"looks fine"}' | Set-Content bad.json
tokn single-loop check-response good.json
tokn single-loop check-response bad.json
```

Expected: `good.json` passes (exit 0). `bad.json` exits 1 with
`reply does not fit the schema: passed on at confidence low`, and prints the
reply wrapped safely: the raw text as `conclusion`, confidence `low`, and a
caveat that names the missing field. The main loop never gets a malformed
reply.

## 8. Optional: use the folded skill in a live session

TOKN loads `SKILL.md` files from `.nospace/skills/` and `.github/skills/` in a
repo, and from `~/.tokn/skills/` for every project. Write the scaffold and
copy it in:

bash:

```bash
tokn single-loop fold returns --prompt prompts/returns.md \
  --description "Use when the customer wants to return or exchange an item." --write
mkdir -p .nospace/skills
cp -r .nospace/single-loop/skills/returns .nospace/skills/
git init -q
tokn agent-repl
```

PowerShell:

```powershell
tokn single-loop fold returns --prompt prompts/returns.md `
  --description "Use when the customer wants to return or exchange an item." --write
New-Item -ItemType Directory -Force .nospace\skills | Out-Null
Copy-Item -Recurse .nospace\single-loop\skills\returns .nospace\skills\
git init -q
tokn agent-repl
```

Then ask:

```text
I bought a tent 40 days ago and it leaks. Can I return it?
```

Expected: the main loop loads the `returns` skill and applies its 30-day rule
itself, with no handoff to a separate agent. The scaffold has no real
`check_return_window` tool, so the model works from the rule text. In your own
system, wire the tool specs from step 5 to real APIs.

## Using your own system

1. Export one JSON line per agent call from your tracing into
   `traces.jsonl`. If your fields have other names, pass `--trace-key`,
   `--agent-key` and `--ts-key`.
2. Run `audit` and write the inventory with `--write`. Fill in the columns
   the traces cannot tell (owner, tools, `context_read`), then run `audit`
   again.
3. Write `results.jsonl` from your eval harness, one row per task rep (see
   `tokn single-loop --help` for the fields), and run `coverage` until it
   exits 0.
4. For each worklist item in PLAN.md: make one change, run the evals,
   `compare` with the previous run, and record your decision.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `coverage` exits 1 | A chain has no eval task. Add a task that runs it and grades the end result, or pass `--min-traces` to hide rare chains. |
| `compare` says *no verdict yet* | The two runs do not have the same tasks. Finish the run, or use `--skip-tag` to leave a group out of both. |
| `fold` says `accepts 1 arg(s), received 2` in PowerShell | Quote the `--tools` list: `--tools "a,b"`. |
| `--write` refuses to overwrite | Pass `--force`, or choose another `--out`. |
| Every agent gets `fold` | Your traces probably have no `input_tokens`. Add them, or fill `context_read` in the inventory (for example `60k`) for agents that read a lot. |
