# Domain relay: five models, one brief, graded by code

One domain problem goes down a seven-stage relay. Each stage is a different model, chosen for what it does well. Every stage runs inside TOKN's real domain mode, with the real domain tools and safety hooks. A deterministic grader then decides pass or fail. No model grades itself.

Twice in every run, **TOKN reflects on TOKN**:
- **Before the plan**, it reads its own capability contract (`tokn introspect`) and the tools actually registered for the mode.
- **After the run**, it reads its own trace and proposes a `/teach` rule for next time.

```text
 brief + synthetic inputs (with hidden traps)
        │
 0  DISCOVER   claude-haiku-5.5      TOKN reads itself → CAPABILITIES.md
 1  PLAN       claude-opus-5.5       acceptance criteria, one deciding tool call per item → PLAN.md
 2  EXECUTE    Kimi-K3.1-Pro         runs the domain tools → result.json (kept as result.v1.json)
 3  CRITIQUE   FW-GLM-5.3            re-runs the tools independently, files findings → critique.json
 4  DECIDE     Microsoft-Decision-1  typed yes/no probabilities route the revision → decision.json
 5  REVISE     gpt-6.1-sol           answers every finding: fixed / rebutted / deferred → result.json
 6  REFLECT    claude-opus-5.5       TOKN reads its own trace, proposes a /teach rule → REFLECTION.md
 7  GRADE      verify.py             ground truth, wording, tool use from the run log → evaluation.json
```

## Why a relay instead of one agent

| One model, one pass | The relay |
|---|---|
| The model that did the work also judges it | A different model family critiques, and code grades |
| "I checked" is a claim | Tool use is counted from TOKN's run log, not from the model's prose |
| A wrong first answer ships | The first answer is kept beside the final one, so you see what the critique changed |
| Every follow-up question is another LLM call | Decision-1 answers several typed questions in about one second |
| Lessons stay in the transcript | The reflection writes a `/teach` rule you can keep |

## Walkthroughs

Each walkthrough is a real, graded run. It includes the inputs, every stage's artifact, the decision probabilities, the critique-and-response table and the grader's checks. Read one end to end before running your own.

| Domain | Problem | Verdict |
|---|---|---|
| [batterypass](walkthroughs/batterypass/README.md) | Gate-check six EU Battery Passport drafts before publication | PASS |
| [climsci](walkthroughs/climsci/README.md) | Check five CMIP6 regional claims for plausibility, model independence and likelihood wording | PASS |
| [edagent](walkthroughs/edagent/README.md) | PHI-screen and constrained-output intake QA of six synthetic ED cases | PASS |
| [drugdisc](walkthroughs/drugdisc/README.md) | Triage six kinase hit compounds against the advancement gate and hERG, CYP450 and PAINS hooks | PASS |
| [gridfm](walkthroughs/gridfm/README.md) | Verify six grid foundation-model OPF predictions and assign each a fail-closed trust disposition | PASS |
| [mobility](walkthroughs/mobility/README.md) | Gate five ADAS functions on ASIL decomposition, FMEDA hardware metrics and V&V completion before the release board | PASS |
| [energy](walkthroughs/energy/README.md) | Decide which of six energy and carbon analyses can go to the board, with provenance, scenario-disclosure and market-disclaimer gates | PASS |
| [transcriptomics](walkthroughs/transcriptomics/README.md) | Assign a QC status to six RNA-seq libraries and test the study design for batch confounding before differential expression | PASS |
<!-- walkthrough rows -->

Start with **[batterypass](walkthroughs/batterypass/README.md)**. Its six drafts include one whose declared chemistry contradicts its cathode, which only a cross-section check catches.

## What is in this folder

| Path | What it is |
|---|---|
| [`run.py`](run.py) | The relay driver. It runs the stages, retries a stage once when it produces nothing, and waits out gateway rate limits. |
| [`verify.py`](verify.py) | The deterministic grader. |
| [`prompts/`](prompts/) | One prompt per stage. Prompts are data: edit them, not the code. |
| [`scenarios/<domain>/`](scenarios/) | `brief.md`, synthetic `inputs/`, and `scenario.json` (ground truth, expected tools, traps). |
| [`walkthroughs/<domain>/`](walkthroughs/) | Published runs: a step-by-step README plus every artifact in `run/`. |
| [`.env.example`](.env.example) | Every key the relay needs, with placeholders only. |

All data is synthetic. No real patients, compounds, sites, assets or organisations appear.

## Prerequisites

`run.py` checks each of these and stops with guidance if one is missing.

| Need | Why | Install / set up |
|---|---|---|
| TOKN with a domain license | Domain modes need the trial or a paid license | Download from this repo's releases, then `tokn license trial` |
| Python 3.11+ | Runs the driver and grader (standard library only) | Windows: `winget install Python.Python.3.12` · macOS: `brew install python@3.12` · Linux: your package manager |
| Azure CLI, logged in | Gets a short-lived token for gpt-6.1-sol | Install from <https://aka.ms/azcli>, then `az login` |
| Model access | Your own gateway or endpoints for the six models | Copy `.env.example` to `.env` and fill in every key |

Some domain tools also use optional Python packages, for example `rdkit` for drugdisc's PAINS cross-check. When one is missing, the tool returns the exact install command and the run records the check as **unassessed** rather than passing it. That is the behaviour the walkthroughs show.

## Run it

```powershell
cd examples/domain-relay
copy .env.example .env        # then edit .env; never commit it
python run.py --domains drugdisc --out C:\tmp\relay-drugdisc
python run.py --domains drugdisc,matsci --parallel 2 --out C:\tmp\relay-two
```

- `--out` must be an absolute path to a folder that does not exist yet.
- `--resume-from N` restarts an existing run at stage N.
- `--stages 0,1` runs only the stages you list.

Each domain writes `<out>/<domain>/ws/`, which holds every artifact plus `TRACE.json`. It also writes `logs/` and `evaluation.json`. A results matrix lands in `results/`.

Expect 20–60 minutes per domain, and paid model calls on every stage except grading.

## Check your understanding

- Pick a walkthrough and cover the "Correct status" column. Can you predict which items the executor got wrong on its first try?
- The critic and the reviser are different model families. What failure does that guard against that a second pass by the same model would not?
- Decision-1 returns probabilities, not prose. Where in your own workflow would a typed yes/no gate replace an LLM call?
- Read one `/teach` rule from a reflection. Is it specific enough to change the next run's behaviour, or is it advice?

## Make your own scenario

Copy any `scenarios/<domain>/` folder and change four things:
- the brief;
- inputs with at least one trap a careless run would miss;
- `ground_truth`, derived from what the domain tools actually return;
- `expected_tools`, using real tool names. Run `tokn introspect`, or let stage 0 list them for you.

Then run it. The grader needs no changes.
