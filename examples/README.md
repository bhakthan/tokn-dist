# TOKN examples

Synthetic, non-sensitive input files referenced by
[GETTING_STARTED.md](../GETTING_STARTED.md), plus step-by-step walkthroughs
that each run one real task end to end. None of them contain real data.

Every walkthrough needs your own LLM key and makes paid model calls. Domain
modes (compbio, oncology, finrisk, physai) need the 14-day trial
(`tokn license trial`); the rest are expected to run on Community too.

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
