# RNA-seq library QC gate before differential expression

*Domain mode `transcriptomics` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Assign a QC status to six poly(A) RNA-seq libraries from the deterministic QC engine and test the full and retained designs for batch confounding.

Inputs (synthetic, in [`inputs/`](inputs/)): [`design.json`](inputs/design.json), [`qc_metrics.json`](inputs/qc_metrics.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `S03` | Best mapping rate (91.5%) and most genes detected (18,900), but RIN 5.9 is below the 6.0 warn floor of a hard-gate metric: FAIL, QUARANTINED. | `exclude` |
| `S02` | RIN 7.0 and unique mapping 80.0% sit exactly on the pass thresholds, which are inclusive: PASS, include. A careless run flags it. | `include` |
| `S05` | Every recorded metric is excellent, but RIN is missing; the engine returns INCOMPLETE and the data-completeness gate hard-blocks. Imputing a RIN gives include. | `cannot_certify` |
| `S06` | Passes both hard gates (RIN 8.1, mapping 86.3%), but rRNA 22.4% is past the 15% fail band for a poly(A) library: overall FAIL and the protocol-consistency gate fails. | `exclude` |
| `S04` | Duplication 34% and NRF 0.71 are in their warn bands only: WARN, flag_for_review, not exclude. | `flag_for_review` |
| `design` | The full design is not confounded, but after removing S03, S05 and S06 every retained batch holds one condition (B1 = ctrl, B2 = treated), so check_batch_confound hard-blocks the retained design. | `—` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5-5 | 42.6s | `read_file`×5, `list_directory`×1, `list_qc_metrics`×1, `recommend_qc_thresholds`×1, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5-5 | 64.8s | `read_file`×4, `list_directory`×1, `write_file`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 169.4s | **`assess_rnaseq_quality`**×6, **`check_batch_confound`**×2, **`compare_samples`**×1, `read_file`×5, `write_file`×2, `run_command`×2 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 400.8s | **`assess_rnaseq_quality`**×6, **`check_batch_confound`**×2, **`compare_samples`**×1, `read_file`×9, `write_file`×4, `grep_search`×2 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.2s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 212.0s | **`assess_rnaseq_quality`**×6, **`check_batch_confound`**×2, **`compare_samples`**×1, `read_file`×9, `update_plan`×4, `run_command`×3 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5-5 | 95.1s | `read_file`×7, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — transcriptomics QC gate (Scout stage)

Scope: items S01–S06 from BRIEF.md. This file records what TOKN can do for the brief. It does not assess any item.

Evidence sources read: BRIEF.md; inputs/qc_metrics.json (protocol polyA, 6 samples, S05 has no `rin` key); inputs/design.json (batches and conditions for S01–S06); tokn-self/introspect-slice.json; tokn-self/DOMAIN-README.md; live outputs of `list_qc_metrics` and `recommend_qc_thresholds` (protocol polyA).

## Domain tools that apply

| tool (exact name) | applies to | input fields needed | present in inputs/? |
|---|---|---|---|
| assess_rnaseq_quality | each of S01–S06 (one call per sample) | `sample` (id); `metrics` (that sample's map, passed unchanged) | yes for S01–S04, S06. S05 lacks `rin`, so a required-metric INCOMPLETE is expected; do not impute |
| compare_samples | all six samples, batch-level view | `samples` map of sample_id → metrics | yes |
| check_batch_confound | full design, and retained design (only include/flag_for_review samples) | `batches` (sample → batch); `conditions` (sample → treated/ctrl) | yes, both in inputs/design.json |
| recommend_qc_thresholds | protocol context for the whole study | `protocol` = polyA | yes (`protocol` in qc_metrics.json) |
| list_qc_metrics | reference of the metric grammar used to check verdicts | none | n/a |
| explain_qc_metric | optional explanation of any metric key that a verdict names | `metric` key | n/a |
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — RNA-seq library QC gate before differential expression (transcriptomics)

Planner stage. Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/qc_metrics.json`, `inputs/design.json`.
Nothing has been executed. Every tool verdict below is still to be obtained by the Executor.

## Objective

Give each of S01–S06 exactly one status (include / flag_for_review / exclude / cannot_certify), based only on the `overall` verdict from `assess_rnaseq_quality`. Then use `compare_samples` and two `check_batch_confound` calls (full design and retained design) to report whether a treated-vs-ctrl DE contrast is still interpretable.

## Steps

General rules for every step:
- Copy input values exactly from `inputs/`. Do not add, impute, round or reformat any metric. Numbers stay as JSON numbers, e.g. `7.0` and `80.0` stay as they are.
- Save every tool response verbatim, in full, for use in `result.json` (see Acceptance criteria).
- Do not call any tool that is not named here. If a named tool turns out to be unavailable, stop and record it as a gap. Do not substitute another tool.

### Step 0 — Protocol context (all items; does not change any status)
- Items: S01–S06 (study-level context).
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# RNA-seq QC gate — execution report

## Scope and evidence basis

**Question and intended use.** Can each synthetic bulk RNA-seq library S01–S06 advance under the local pre-differential-expression (DE) QC policy, and does the retained treated-versus-control design remain interpretable? The unit of analysis is one library/sample identifier; no cell-level, technical-replicate, or donor-level independence is inferred. BRIEF.md describes treated and control cell lines with poly(A)-selected, paired-end libraries; the input notes establish synthetic teaching data, units, and S05's unrecorded RIN.

**Provenance.** Metrics and protocol come from `inputs/qc_metrics.json`; batches and conditions come from `inputs/design.json`. Both files explicitly identify the data as **synthetic teaching data**, not measurements from a real study. Rates are percentages, NRF is a fraction, and detected genes are counts. S05's RIN is absent and was not imputed.

**Protocol context.** `recommend_qc_thresholds(protocol="polyA")` and `list_qc_metrics` returned the same grammar:

| Metric | PASS band | WARN band | Required | Hard gate |
|---|---:|---:|:---:|:---:|
| rin | ≥ 7 | ≥ 6 | yes | yes |
| unique_mapping_rate (%) | ≥ 80 | ≥ 60 | yes | yes |
| rrna_rate (%) | ≤ 10 | ≤ 15 | no | no |
| duplication_rate (%) | ≤ 20 | ≤ 50 | no | no |
| nrf | ≥ 0.8 | ≥ 0.5 | no | no |
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 8 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# CRITIQUE — RNA-seq QC gate (`result.json` / `RESULT.md`)

Critic stage. Independent re-execution: I re-ran every tool whose output decides a status —
`assess_rnaseq_quality` for all six samples, `compare_samples`, `check_batch_confound` on the
full and retained designs, `recommend_qc_thresholds(polyA)`, and `list_qc_metrics`. Every
reported verdict, per-metric result, ranking entry, confound status, and threshold value
reproduced exactly. The findings below record every remaining issue; none of them changes a
sample status or the DE-interpretability conclusion.

---

**C1 — overall — minor.** Provenance mis-attribution in RESULT.md's "Scope and evidence
basis": *"The input note describes the brief as treated and control cell lines with
poly(A)-selected, paired-end libraries."* The notes in `inputs/` say no such thing.
`inputs/qc_metrics.json`'s note reads *"Synthetic RNA-seq QC metrics for a teaching scenario;
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.731 |
| Does any sample that is missing a required metric or fails a hard gate receive include or flag_for_review? | 0.006 |
| Does the result claim the retained design supports an interpretable treated-versus-control differential-expression contrast? | 0.023 |

Routing: **full-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 8 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | minor | Provenance mis-attribution in RESULT.md's 'Scope and evidence basis': 'The input note describes the brief as treated and control cell lines with poly(A)-selected, paired-end libraries.' The notes in inputs/ say no such t… | **fixed**: Compared input notes with BRIEF.md independently; corrected assay-context attribution in RESULT.md. |
| C2 | minor | A gate status is reported that no tool emitted. In result.json's `gates` array, `batch_confound_retained` is recorded as `status: "fail"`, and RESULT.md's 'Overall gate summary' table likewise shows 'Retained-design batc… | **fixed**: Retained-design check_batch_confound re-run returned hard_block; summary fields now preserve it. |
| C3 | minor | Ambiguous study-level gate rollup. result.json marks `required_metric_gate_DataCompleteness` as `fail`. PLAN Gates section 1 defines that gate as a precondition for granting a positive status, and it held for every sampl… | **fixed**: QC re-runs confirmed completeness pass for S01/S02/S04 and hard_block for S05. Clarified positive-status compliance rollup. |
| C4 | minor | `discrepancies` is an empty list, and it is technically compliant — none of PLAN's triggers fired: recommend_qc_thresholds(polyA) matches CAPABILITIES.md's threshold table field-for-field (rin 7/6, unique_mapping_rate 80… | **fixed**: S06 QC and threshold-tool re-runs confirmed 22.4% FAIL, >15% warning rationale and separate >20% protocol cut. Recorded both observations without status change. |
| C5 | minor | PLAN's Optional Step 10 — call explain_qc_metric once for each metric key that returned WARN or FAIL (duplication_rate, nrf, rin, rrna_rate) — was not executed, and no record of the skip appears in result.json or RESULT.… | **fixed**: Verified explanation step is optional; documented skip and attribution to assessor rationale strings. |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. Opus reads the full trace, names which tools mattered, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

`/teach In transcriptomics QC runs, copy every gate status verbatim from the tool output (e.g. hard_block, never relabel it fail), and log every tool-internal threshold tension (rationale text vs pass/warn band, protocol_consistency cuts, phase vs hardGate) under discrepancies, marked "no status change".`
```

## The answer

| Item | First answer (Kimi) | Final (after critique) | Expected |
|---|---|---|---|
| `S01` | `include` | `include` ✅ | `include` |
| `S02` | `include` | `include` ✅ | `include` |
| `S03` | `exclude` | `exclude` ✅ | `exclude` |
| `S04` | `flag_for_review` | `flag_for_review` ✅ | `flag_for_review` |
| `S05` | `cannot_certify` | `cannot_certify` ✅ | `cannot_certify` |
| `S06` | `exclude` | `exclude` ✅ | `exclude` |

Accuracy: first answer 1.0, final 1.0.

## How it was graded

No model grades itself. [`verify.py`](../../verify.py) checks the files and the run log:

| Check | Result | Detail |
|---|---|---|
| artifacts_present | ✅ | all 10 present |
| result_json_valid | ✅ | final result.json parses with an items list |
| status_vocabulary | ✅ | all statuses in vocabulary |
| all_items_assessed | ✅ | 6 items |
| ground_truth | ✅ | final 1.0 (v1 1.0) |
| must_mention | ✅ | all present |
| forbidden_phrases | ✅ | none found |
| critique_has_findings | ✅ | 8 findings |
| every_finding_answered | ✅ | 8 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['assess_rnaseq_quality', 'check_batch_confound', 'compare_samples'] of expected ['assess_rnaseq_quality', 'check_batch_confound', 'compare_samples'] |
| critic_reran_tools | ✅ | critic used ['assess_rnaseq_quality', 'check_batch_confound', 'compare_samples'] |
| reflection_grounded | ✅ | names traced tools ['assess_rnaseq_quality', 'check_batch_confound', 'compare_samples']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Is it specific enough to change how the next run uses the domain tools?

## Run it yourself

```powershell
python run.py --domains transcriptomics --out C:\tmp\relay-transcriptomics
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
