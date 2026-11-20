# RNA-seq software factory: agents that find, fix, ship and watch

A small RNA-seq differential-expression (DE) pipeline has real bugs. CI is red,
and staging has already logged an incident. Instead of a person writing tickets,
a **TOKN software factory** does the work end to end:

1. An **Observer** turns the CI failure and the incident into drafted work items.
2. **Product** and **Architect** agents refine the item and design a fix.
3. An **Implementer** writes the fix and its regression tests.
4. A **Reviewer** on a *different* model, plus a decision model, checks every domain
   invariant.
5. **Test** runs pytest and a grader that the candidate code can't modify.
6. **Release** deploys to dev and then staging, then **waits for a human** before prod.
7. Once v1 is live, a new prod incident arrives. The Observer drafts the next item
   and the loop runs again with no human ticket.

Every step is written to an append-only, hash-chained store. Afterwards
`tokn factory verify` proves that nothing was edited after the fact.

All data is **synthetic**: generated counts, synthetic sample sheets and invented
subject references. There's no real patient or lab data.

## What you'll learn

| Concept | Where you see it |
|---|---|
| A declarative **FactorySpec** (intent, domain invariants, gates, budgets, intake) | `spec/factory.yaml` |
| **Mixing models per role** across frontier, open-weights and local models | `spec/models.trio.yaml`, `spec/models.hybrid.yaml` |
| **Decision models** as typed gate checks, not free-text opinions | `decision:` under the review gate, and `decisions:` in the models files |
| **Human gates**: prod release and oversized changes | `--approve-prod`, `--approve-blast-radius` |
| The **continuous loop**: telemetry becomes the next work item | the second loop, after v1 reaches prod |
| An **auditable evidence chain** | `verify/REPORT.md`, `tokn factory verify` |

## Requirements

| Profile | Needs | Cost |
|---|---|---|
| `offline` | TOKN v0.3.115+, Python 3.10+, `numpy pandas scipy pytest pyyaml`, Git | none, with no model calls |
| `trio` | the offline requirements, plus an Anthropic key (Opus), an Azure OpenAI deployment (gpt-6-astra), a decision-model backend, and a TOKN **trial or licence** | billed by your providers; about $5 per implement+review round |
| `hybrid` | the trio requirements, plus a Hugging Face token (open-weights coder) and a local [Ollama](https://ollama.com) with one pulled coder model | frontier roles billed; local roles free |

The live profiles run each role in TOKN's `transcriptomics` domain mode. That
mode needs a trial (`tokn license trial`) or an applicable licence. The
`offline` profile doesn't.

Install the Python packages:

```bash
python -m pip install numpy pandas scipy pytest pyyaml
```

Download `tokn` v0.3.115 or newer from
[Releases](https://github.com/bhakthan/tokn-dist/releases). Put it on `PATH`,
drop it in this folder, or pass `--tokn <path>`. `run.py` checks for every
dependency before it starts. If something is missing, it lists all the gaps at
once with install commands for your OS.

## Step 1: Offline. Prove the case is real (no keys, about 30 s)

```bash
python run.py --profile offline
```

This builds the synthetic case and checks that the test isn't rigged:

```text
PASS  make_case deterministic: seed 7: 17 files + key + intake identical across two runs
PASS  grader FAILS on seed: {"recall": 0.14, "precision": 0.6364, "rin_filtered": false, ...}
PASS  pytest fails on seed: 9 failed, 1 passed
PASS  grader PASSES on seed+reference_fix: {"recall": 0.98, "precision": 1.0, ...}
PASS  pytest passes on seed+reference_fix: 10 passed
PASS  spec validate (trio models): {"valid": true, ...}
PASS  spec validate (hybrid models): {"valid": true, ...}
offline PASSED
```

The seed pipeline is measurably broken. A known-good fix
(`reference_fix/`) measurably passes. Both model specs validate. Agents never
see `reference_fix/` or the answer key.

### The bugs the factory has to find

| Domain invariant (from `spec/factory.yaml`) | What the seed gets wrong |
|---|---|
| Counts are non-negative integers; TPM/NumReads matrices are rejected | silently accepts fractional matrices |
| Samples with RIN < 6 are excluded before DE | keeps degraded samples |
| Strandedness is inferred from sense vs opposite-strand counts | assumes every library is forward-stranded |
| FDR is Benjamini–Hochberg; calls need padj < 0.05 and \|log2FC\| ≥ 1 | returns raw p-values; no BH correction |
| A design confounded with batch is refused | runs anyway and reports nonsense |
| `subject_ref` never appears in any output | leaks into `report.md` |
| `data/` and `golden/` are never modified | (a protected path the factory enforces) |

## Step 2: Trio. Frontier models plus a decision model

Copy the profile template and fill in your own values:

```bash
cp profiles/trio.env.example .env        # Windows: copy profiles\trio.env.example .env
```

Set the `FACTORY_DECISION_MODEL` only if your decision backend needs a specific deployment name. Otherwise each backend uses its own decision model; a chat model such as gpt-6-astra is not a decision model. If the decision call fails, the gate stops for a human rather than passing.

`.env` is git-ignored. `run.py` turns it into short-lived credential profiles
named by the spec's `models:` bindings, and deletes them when the run ends.

Then run:

```bash
python run.py --profile trio --approve-prod --approve-blast-radius
```

| Role | Model in `models.trio.yaml` | Why |
|---|---|---|
| architect, implementer | Claude Opus | hardest reasoning and code |
| product, reviewer, test, release, observer | gpt-6-astra | **cross-model review**: the reviewer isn't the model that wrote the code |
| review-gate decision | your `FACTORY_DECISION_BACKEND` (`jev`, `azure`, `openai`, `microsoft`, `gemini`, `compatible` or `local`) | a typed yes/no ("are all invariants preserved?") with a confidence floor |

The two flags are **your** approvals. The factory pauses at them either way.

- `--approve-prod` signs the prod release gate. Without it, the run stops at
  `release: awaiting approval`, and you can approve later with
  `tokn factory approve <gate-id>`.
- `--approve-blast-radius` approves a change that exceeds
  `max_files_per_change` or `max_lines_per_change`. The fix plus its new tests
  usually does.

To continue an interrupted run, use `--resume out/<run-dir>`.

### Batched decisions

Decision models are small, fast judgement calls, so the factory sends them in
batches rather than one call per signal:

- **Triage:** the Observer sends all new signals from one tick in a single batch call.
- **Gates:** gate decisions for items that finish at about the same time are micro-batched into one call. Each state is still judged independently, so one failed decision does not fail the others.
- **Budget:** a run that hits its token budget is reported as *budget exceeded*. The gate goes to `NEEDS_HUMAN`, so you can approve a retry. It is not recorded as denied.

The review-gate decision can also be Microsoft Decision-1.1. Set
`FACTORY_DECISION_BACKEND=microsoft` and `DECISION_API_MODEL=decision-1.1`, plus
`DECISION_API_ENDPOINT` and `DECISION_API_KEY` (see `profiles/trio.env.example`).

## Step 3: Mix and match. Frontier, open-weights and local in one run

The factory doesn't force a single provider. Each role binds its own model, with
optional fallbacks and a data boundary:

```yaml
# spec/models.hybrid.yaml (abridged)
models:
  default: { provider: anthropic, model: '{{OPUS_MODEL}}', env: anthropic-gateway }
  roles:
    architect:   { provider: anthropic,    model: '{{OPUS_MODEL}}',  env: anthropic-gateway }
    implementer:
      provider: huggingface                       # open-weights coder
      model: '{{HF_CODER_MODEL}}'
      env: hf
      fallback:
        - { provider: ollama, model: '{{OLLAMA_MODEL}}', env: ollama-local }
    reviewer:    { provider: azure-openai, model: '{{ASTRA_MODEL}}', env: azure-astra }
    test:        { provider: ollama, model: '{{OLLAMA_MODEL}}', env: ollama-local, data_boundary: local }
    observer:    { provider: ollama, model: '{{OLLAMA_MODEL}}', env: ollama-local, data_boundary: local }
  decisions:
    observer_triage: { backend: local }          # on-device, no network
    draft_check:     { backend: local }
    gate:            { backend: '{{DECISION_BACKEND}}', model: '{{DECISION_MODEL}}', env: decision }
```

```bash
ollama pull qwen2.5-coder:7b
cp profiles/hybrid.env.example .env
python run.py --profile hybrid --approve-prod --approve-blast-radius
```

`data_boundary: local` is enforced, not advisory. Those roles may only call a
loopback endpoint, so the Observer never sends raw sample metadata off the
machine. A local boundary also rejects a remote fallback or a remote decision
backend at validation time.

You can rebind any role to any provider TOKN supports. That includes other
coding harnesses through a role's `harness:` field. Before you spend
anything, check the bindings from the run's `seed/` directory:

```bash
tokn factory validate            # schema, routing and boundary checks
tokn factory models --preflight  # each role's model chain, and whether it can run
```

## Step 4: Read the evidence

Each run writes `out/<timestamp>-<profile>/`:

| Path | What it is |
|---|---|
| `verify/REPORT.md` | the verdict: DE metrics on the code **deployed to prod**, chain integrity, decision records, and per-role model attribution |
| `seed/.nospace/factory/events.jsonl` | the append-only, hash-chained event log (work items, runs, gates, decisions) |
| `seed/` (git history) | each agent change as a commit you can `git log` and `git show` |
| `targets/{dev,staging,prod}/` | what each environment received from the demo deploy target |
| `logs/` | the raw output of each `tokn factory` call |

Inspect a run yourself from the `seed/` directory:

```bash
tokn factory status --json      # items, stage, state, retries, spend
tokn factory events --json      # the full audit trail (JSON Lines)
tokn factory verify --json      # re-check the chain, blobs and gate semantics
```

### Results: offline profile (observed)

Run: `python run.py --profile offline --tokn <path-to-tokn>` (no keys or network).
Spec validation needs `tokn` v0.3.115 or later. Artifacts land in
`out/<timestamp>-offline/`.

| Check | Result | Artifact |
|---|---|---|
| Synthetic case is deterministic | PASS (seed 7: 17 files + key + intake identical across two runs) | `det1/`, `offline-report.json` |
| Grader fails on the seed pipeline | PASS (recall 0.14, precision 0.6364, RIN filter, strandedness, confounder refusal, PII all not met) | `offline-report.json` |
| pytest fails on the seed pipeline | PASS (as expected: 9 failed, 1 passed) | `offline-report.json` |
| Grader passes on seed + reference fix | PASS (recall 0.98, precision 1.0, all checks true, data intact) | `fixed/`, `offline-report.json` |
| pytest on seed + reference fix | PASS (10 passed) | `fixed/`, `offline-report.json` |
| Spec validation, trio models | PASS (valid, 0 errors, 0 findings) | `spec-trio/`, `offline-report.json` |
| Spec validation, hybrid models | PASS (valid, 0 errors, 0 findings) | `spec-hybrid/`, `offline-report.json` |

The offline profile makes no model, decision, or network call, so it writes no
decision records or agent commits. A `trio` or `hybrid` run produces them. Per stage, you will see:

| Stage | What you will see | Where |
|---|---|---|
| Product | work items from the intake | `seed/.nospace/factory/events.jsonl` |
| Architect, Implementer | one commit per agent change | `seed/` git history |
| Reviewer, Test/Eval | review and test records; the batched gate decision for the review | `seed/.nospace/factory/events.jsonl` (decision records) |
| Release | prod approval pause unless `--approve-prod` | `verify/REPORT.md` |
| Observer | triage of new signals in one batch per tick | `seed/.nospace/factory/events.jsonl` |

## Make it yours

- **Another domain:** change `domain.plug`, the invariants and the gates. The
  engine is domain-agnostic; only the spec is RNA-seq specific.
- **Your own CI and incidents:** point `intake.sources` at your CI export or
  incident feed instead of the replayed JSONL files.
- **Stricter or looser gates:** tune `min_reviewer_score`, the decision
  question, the `test.thresholds`, `blast_radius` and `budget`.
- **Your own approvers:** list them in `release.prod.approvers`. Spec changes
  and prod releases always stop for a human.

## Cleanup

Everything a run writes stays under `out/`. Delete it with `rm -rf out` (on
Windows, `Remove-Item -Recurse out`). Don't commit `out/`, `.env`, `.nospace/`
or `.tokn/`; the included `.gitignore` already excludes them.
