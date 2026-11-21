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
8. Then product asks for something new: turn a single-cell notebook prototype into a
   hardened cell-type annotation service. That service calls a **local open-weights
   transcriptomics model**, Cell2Sentence (C2S-Scale, GGUF on llama.cpp). The same
   agents, gates and human approval carry it to prod.

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
| A **domain specialist model inside the product**: frontier agents build a service around a local open-weights model, with guardrails | the third loop (`REQ-SC-0001`), `rnaseq_de/sc.py` |
| An **auditable evidence chain** | `verify/REPORT.md`, `tokn factory verify` |

## Requirements

| Profile | Needs | Cost |
|---|---|---|
| `offline` | Python 3.10+, `numpy pandas scipy pytest`; Git and TOKN v0.3.115+ for spec validation | none, with no model calls |
| `trio` | Git, TOKN, PyYAML and the offline Python packages, plus an Anthropic key (Opus), an Azure OpenAI deployment (gpt-6-astra), a decision-model backend, and a TOKN **trial or licence** | billed by your providers; about $5 per implement+review round |
| `hybrid` | the trio requirements, plus a Hugging Face token (open-weights coder) and a local [Ollama](https://ollama.com) with one pulled coder model | frontier roles billed; local roles free |
| `c2s-hybrid` (optional showcase on `trio`/`hybrid`) | hybrid requirements plus a loopback server, or llama.cpp `llama-server` and a C2S-Scale GGUF (2B Q4_K_M is about 1.6 GB and runs on CPU) | local inference; provider roles still billed |

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

## Step 1: Offline. Prove the case is real (no keys, about 5 min)

```bash
python run.py --profile offline
```

This builds the synthetic case and checks that the test isn't rigged:

```text
PASS  make_case deterministic: seed 7: 23 files + key + intake identical across two runs
PASS  seed 7 protected bytes match baseline: data and golden files
PASS  grader FAILS on seed: {"recall": 0.14, "precision": 0.6364, "rin_filtered": false, ...}
PASS  pytest fails on seed: 9 failed, 1 passed
PASS  grader PASSES on seed+reference_fix: {"recall": 0.99, "precision": 1.0, ...}
PASS  pytest passes on seed+reference_fix: 30 passed
PASS  grader FAILS the single-cell prototype once sc is required: {"sc_prompts_exact": false, "sc_fail_closed": false, ...}
PASS  grader PASSES the hardened single-cell reference: {"sc_correct": 1.0, "sc_wrong": 0.0, "sc_isg_recall": 8, ...}
PASS  stress gate FAILS on seed: {"lagarias_min_gap": -13.98, "off_line_exponent": 0.9334, ...}
PASS  stress gate PASSES seed+reference_fix outside the near-miss band: {"lagarias_min_gap": 0.246, "off_line_exponent": 0.5025, ...}
PASS  off-line exponent FAILS a batch-blind Welch that passes the shipped case: {"recall": 0.98, "off_line_exponent": 0.7615, ...}
PASS  spec validate (trio models): {"valid": true, ...}
PASS  spec validate (hybrid models): {"valid": true, ...}
PASS  spec validate (c2s-hybrid models): {"valid": true, ...}
offline PASSED
```

The seed pipeline is measurably broken. A known-good fix
(`reference_fix/`) measurably passes. All three model specs validate. Agents never
see `reference_fix/` or the answer key. The offline single-cell checks use
`fake_c2s.py`, a deterministic stand-in, so no model is needed. Keeping the grader
outside the candidate tree is not OS isolation: run only trusted candidates here, or use
a separate restricted environment without credentials.

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
| DE adjusts for batch (`expression ~ condition + batch`, Student t); error decay is checked on four fixed cohort sizes | a batch-blind test whose error stops shrinking once batches are unbalanced |
| Every stress tier keeps a positive relative gap | passes the 12-sample case and breaks on a bigger or unbalanced one |

After the third loop's request, the single-cell prototype must meet these too:

| Single-cell invariant | What the prototype gets wrong |
|---|---|
| QC (mitochondrial fraction, heterotypic doublets) runs **before** the model | sends every barcode, including dying cells and doublets |
| The prompt is the model-card template over a descending-count cell sentence | orders genes alphabetically, not by expression |
| No cell, sample or subject identifier goes on the wire | prefixes the prompt with `subject_ref` and the cell ID |
| A label counts only if the alias table maps it **and** the cell's markers support it | writes the model's raw text as the cell type |
| An unreachable model or invalid completion fails closed (exit 4, nothing written) | labels the cell `unknown` and carries on |
| The endpoint is loopback only | sends cells to any URL |
| Composition is separate from expression; DE is per cell type on donor pseudobulks | one pooled cell-level t-test, ignoring cell type and donor |
| `subject_ref` never appears in any output | writes it into `celltypes.tsv` |

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

## Step 4: The third loop. A local transcriptomics specialist inside the product

When the incident loop settles, `run.py` appends a product request, `REQ-SC-0001`.
The Observer files it as a Feature, and from then on the test gate also grades the
single-cell service (`sc_ok == 1`). Skip this loop with `--no-feature`.

The data in `data/sc/` is a synthetic PBMC-like panel: about 230 cells from four
donors per arm, five cell types, plus traps. These include dying (mitochondria-heavy) cells, heterotypic
doublets, platelet- and DC-like cells outside the vocabulary, a B-cell
**abundance** shift (composition, not DE), and an interferon program switched on in
treated monocytes that donor-pseudobulk DE must find without a flood of false calls.

The design rule the agents must implement is:
**C2S proposes, the guardrail disposes, the factory tests, a human approves.**

- [Cell2Sentence](https://huggingface.co/vandijklab) reads a cell as a sentence of gene
  symbols ordered by expression and names its cell type. It runs locally as a GGUF on
  llama.cpp, so no cell data leaves the machine.
- The service maps each answer through an anchored, versioned alias table and keeps it
  only when the cell's own markers support it. Otherwise the cell is `unassigned` with a
  reason. When the model is unreachable it fails closed.
- Gates grade against `fake_c2s.py`, so a pass never depends on a sampled model output.
  The real model runs after the loop on the deployed package. Live accuracy is evidence; a missing result or wrong-label rate above 5% fails showcase verification.

To include the real model, install llama.cpp and download a C2S-Scale GGUF:

```bash
winget install ggml.llamacpp          # macOS: brew install llama.cpp
pip install -U huggingface_hub
hf download mradermacher/C2S-Scale-Gemma-2-2B-GGUF C2S-Scale-Gemma-2-2B.Q4_K_M.gguf --local-dir models
```

Set `FACTORY_C2S_GGUF=models/C2S-Scale-Gemma-2-2B.Q4_K_M.gguf` in `.env`. `run.py`
starts `llama-server` on `127.0.0.1`, records the file's SHA-256 (and refuses a file that doesn't
match `FACTORY_C2S_SHA256` when you pin it), grades the shipped service, and stops the
server. You can also pass `--c2s-url` for a server you run yourself. The larger
`C2S-Scale-Gemma-2-27B` Q2_K (about 10 GB) works the same way.

**The `c2s-hybrid` profile.** `python run.py --profile c2s-hybrid` runs the hybrid
factory and requires the local C2S model up front: preflight checks for
`llama-server` and `FACTORY_C2S_GGUF` (or a loopback `--c2s-url`). Copy
`profiles/c2s-hybrid.env.example` to start. C2S-Scale is the service's data-plane
model, not a factory role, because it has no tool calling, so
`spec/models.c2s-hybrid.yaml` binds the same roles as `models.hybrid.yaml`.

Two further checks treat C2S's label as one view of a cell and its marker genes as the
other (the spec calls this the "Euler-dual" check, after the sum/product duality of
the zeta function; again, an analogy):

- `c2s_invalid_token_rate`: gene symbols in a cell sentence that aren't in the panel.
  It must be 0.
- `c2s_euler_discrepancy`: the share of QC-passing, in-vocabulary model proposals (including
rejected proposals) that lack independent top-100 marker support. It must be at most 0.25.

**Quantisation drift.** Set `FACTORY_C2S_ANCHOR` to the `c2s-showcase.json` of a
trusted reference quantisation of the **same base model**, service version, prompt and decoding
settings. The grader checks the counts hash and QC-passing barcodes; older anchors without that
fingerprint must be regenerated. It reports `gguf_anchor_kl = D_KL(current || anchor)` over the five
final labels plus `unassigned`, using natural logs and 0.0001 smoothing per bin. Above 0.035 the
runner appends a generated incident to `intake/incidents.jsonl` for a later tick on **this run**. KL
is report-only: a change in the label mix neither proves quantisation caused it nor measures
accuracy. Cell-by-cell swaps can leave the mix unchanged. Without an anchor no KL is measured.

**Observed** (reference service, 2B Q4_K_M, CPU only, 205 cells after QC): **71% of
known cells correctly labelled and 0% wrongly labelled** in about 270 s. Every miss was a
refusal (`unmapped` or `unsupported`), not a wrong label. A refusal is cheap to review.
A confident wrong label in a DE table is not. The showcase fails only if the service
crashes or labels more than 5% of known cells wrongly.

The fail-closed rule, pinned and digest-checked weights, and comparing a stock model
against a specialist follow the conventions in Anthropic's
[uplifting-biomolecular-modeling](https://github.com/anthropics/uplifting-biomolecular-modeling).
The panel is reduced and synthetic: it exercises the factory and the guardrails, and is
not a benchmark of C2S.

## Stress gates: near misses before counterexamples

A grader that only says PASS or FAIL can't tell a comfortable pass from one that's a
single sample away from failing. This example borrows a framing from Lagarias's
reformulation of the Riemann hypothesis: the hypothesis holds if and only if
`sigma(n) <= H_n + exp(H_n) log(H_n)` for every n, so the *margin* at each n, not just
the sign, says how close a case is to a counterexample. The factory applies that
framing to the pipeline. It's an analogy for gate design; nothing here is derived from
the Riemann hypothesis.

**The ladder.** `stress.py` regenerates the case on four different designs and runs the
candidate CLI on each. The grader then scores every tier:

| Tier | Design | What it probes |
|---|---|---|
| `n12_low_replicate` | 3 samples per condition × batch cell, one RIN 4.1 library | power and the RIN filter at small n |
| `n60_batch_imbalance` | control B1:B2 = 20:10, treated 10:20 | whether batch leaks into the condition effect |
| `n120_borderline_rin_mixed_strand` | RIN near the cut-off, mixed strandedness | QC edge cases at scale |
| `n2520_high_dropout` | library size × 0.08 | low-depth behaviour (no separate dropout model) |

`lagarias_min_gap` is the smallest **compound** gap `(ceiling - load) / ceiling`. At each bulk tier
the load is `max(1, observed_FDP / 0.05) × (1 + batch_leak)`; for the optional single-cell case the
load is `1 + marker_discrepancy`. The heuristic ceiling is `1 + 0.35 × (alpha(n)/n) /
(alpha(12)/12)` with `alpha(n) = H_n + exp(H_n) log(H_n)`. The separate `min_criterion_margin`
checks shipped-case recall and precision (floors 0.90), plus each bulk tier's recall (floor 0.90)
and realised directional false discovery proportion (ceiling 0.05). This is **not** an estimate of
expected FDR across experiments. No calls gives FDP zero but fails recall. The stress gate requires
a positive margin; equality is a counterexample even if the underlying criterion is inclusive.
Error-path metric values are fail-closed sentinels, not measurements.

**The off-line exponent.** At N = 24, 48, 96 and 192 the two conditions have opposite 2:1 batch
imbalances. For the same pre-specified well-expressed null genes the grader centres log2FC errors by
their median at each size, then fits `log(RMS error) = intercept + slope × log(N)`. It reports `1 +
slope`: square-root decay gives 0.5 and a constant residual floor gives 1. Centring deliberately
ignores global offsets. Each size uses a new simulated cohort, not nested observations.

The 0.55 cutoff is a regression check for this fixed generator, not a statistical test for bias.
Four points cannot distinguish a batch leak from another noise floor or prove asymptotic behaviour.
As a sensitivity check, in-memory fits across seeds 2027–2038 gave 0.480–0.516 for the adjusted
reference and 0.736–0.780 for its batch-blind control. Those ranges are not confidence intervals; a
different simulator or candidate can cross the cutoff for other reasons.

**Thresholds** in `spec/factory.yaml`, test gate:

| Metric | Fail | Needs a human | Meaning |
|---|---|---|---|
| `lagarias_min_gap` | ≤ 0 | 0 < gap < 0.05 | a counterexample in some tier / a near miss |
| `off_line_exponent` | > 0.55 | | slower decay than the fixture cutoff |
| `min_criterion_margin` | ≤ 0 | 0 < gap < 0.05 | closest individual criterion, including tier recall and FDP |
| `c2s_euler_discrepancy` | > 0.25 | | see Step 4 |
| `c2s_invalid_token_rate` | ≠ 0 | | see Step 4 |

The needs-a-human band goes to the approvers named in the test gate's `signoff` block.
`--approve-blast-radius` doesn't cover it: a live run that lands in the band stops at
the test gate until someone signs off.

**Observed** (offline profile):

| Candidate | Shipped case | `lagarias_min_gap` | `off_line_exponent` | Verdict |
|---|---|---|---|---|
| seed | recall 0.14 | −13.98 (`n60_batch_imbalance`) | 0.93 | FAIL |
| reference fix (batch-adjusted OLS, Student t) | recall 0.99 | 0.246 (`n12_low_replicate`) | 0.50 | PASS |
| batch-blind Welch (negative control) | recall 0.98 | 0.054 | 0.76 | FAIL on the exponent |

The negative control matters. A batch-blind Welch test passes the shipped case and
has positive compound gaps. Its fitted slope nevertheless fails the scaling check. The reference's residuals fall 0.143 → 0.104 → 0.072 → 0.051
as N doubles, close to the N^-1/2 slope.

The grader records `observer_signals` (including `lagarias_counterexample` and
`off_line_zero_detected`) in its JSON. Only the live anchor-KL signal is automatically written to
incident intake.

## Step 5: Read the evidence

Each run writes `out/<timestamp>-<profile>/`:

| Path | What it is |
|---|---|
| `verify/REPORT.md` | the verdict: DE metrics on the code **deployed to prod**, chain integrity, decision records, and per-role model attribution |
| `seed/.nospace/factory/events.jsonl` | the append-only, hash-chained event log (work items, runs, gates, decisions) |
| `seed/` (git history) | each agent change as a commit you can `git log` and `git show` |
| `targets/{dev,staging,prod}/` | what each environment received from the demo deploy target |
| `c2s-showcase.json` | the real-model run of the shipped service (when C2S is configured): accuracy, refusals, timing and the GGUF's SHA-256 |
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
| Synthetic case is deterministic | PASS (seed 7: 23 files + key + intake identical across two runs; protected bytes also match the seed-7 baseline) | `det1/`, `offline-report.json` |
| Grader fails on the seed pipeline | PASS (recall 0.14, precision 0.6364, RIN filter, strandedness, confounder refusal, PII all not met) | `offline-report.json` |
| pytest fails on the seed pipeline | PASS (as expected: 9 failed, 1 passed) | `offline-report.json` |
| Grader passes on seed + reference fix | PASS (recall 0.99, precision 1.0, all checks true, data intact) | `fixed/`, `offline-report.json` |
| pytest on seed + reference fix | PASS (30 passed, including 14 single-cell tests) | `fixed/`, `offline-report.json` |
| Grader fails the single-cell prototype | PASS (prompts, IDs on the wire, QC, doublets, fail-closed, input validation and DE all not met) | `offline-report.json` |
| Grader passes the hardened single-cell reference | PASS (100% correct, 0% wrong, doublet recall 0.875, 8 interferon genes, 2 false calls) | `fixed/`, `offline-report.json` |
| Spec validation, trio models | PASS (valid, 0 errors, 0 findings) | `spec-trio/`, `offline-report.json` |
| Stress gate fails on the seed | PASS (gap −13.98 at `n60_batch_imbalance`, exponent 0.93) | `offline-report.json` |
| Stress gate passes the reference fix outside the near-miss band | PASS (gap 0.246 at `n12_low_replicate`, exponent 0.50, criterion margin 0.10) | `offline-report.json` |
| Exponent fails a batch-blind Welch control | PASS (recall 0.98 on the shipped case, exponent 0.76) | `offline-report.json` |
| Spec validation, hybrid models | PASS (valid, 0 errors, 0 findings) | `spec-hybrid/`, `offline-report.json` |
| Spec validation, c2s-hybrid models | PASS (valid, 0 errors, 0 findings) | `spec-c2s-hybrid/`, `offline-report.json` |

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
