# Functional-safety release gate for five ADAS functions

*Domain mode `mobility` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Gate five ADAS functions on ASIL decomposition validity, FMEDA hardware metrics and V&V completion before the release board.

Inputs (synthetic, in [`inputs/`](inputs/)): [`asil_decomposition.json`](inputs/asil_decomposition.json), [`fmeda_metrics.json`](inputs/fmeda_metrics.json), [`vv_evidence.json`](inputs/vv_evidence.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `FN-LKA` | Has the best metrics in the batch (PMHF 3.1 FIT, SPFM 99.7%, 99.1% requirement coverage, no open defects) but decomposes ASIL D into B + A, which sums to 3 < 4; asil_decompose_verify returns an error. | `decomposition_invalid` |
| `FN-ACC` | Sits exactly on three thresholds: C -> B + A sums to exactly 3 (valid), SPFM 99.0% equals the target (pass), and requirement coverage 95.0% equals the V&V threshold (accepted). A careless run calls it marginal or failing. | `release_candidate` |
| `FN-TJA` | SPFM 98.9% is 0.1 points below the 99% target; everything else passes, so rounding or eyeballing gives release_candidate. | `hw_metrics_fail` |
| `FN-APA` | Strong hardware metrics and 98% coverage, but one open defect makes safety_validation_report refuse V&V completion. | `vv_incomplete` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5-5 | 44.8s | `read_file`×7, `edit_file`×3, `list_directory`×1, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5-5 | 100.1s | `read_file`×7, `list_directory`×1, `write_file`×1, `git_status`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 897.2s | **`asil_decompose_verify`**×27, **`fmea_fta_engine`**×25, **`safety_validation_report`**×25, `read_file`×9, `run_command`×5, `write_file`×5 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 815.6s | **`safety_validation_report`**×9, **`asil_decompose_verify`**×8, **`fmea_fta_engine`**×7, `read_file`×25, `grep_search`×3, `write_file`×2 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.1s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 410.6s | **`asil_decompose_verify`**×7, **`safety_validation_report`**×7, **`fmea_fta_engine`**×5, `read_file`×25, `run_command`×4, `edit_file`×4 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5-5 | 132.9s | `read_file`×8, `grep_search`×5, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — mobility release gate (5 ADAS functions)

Scout stage. Nothing here assesses FN-AEB, FN-LKA, FN-ACC, FN-TJA or FN-APA.
Sources read: BRIEF.md; inputs/asil_decomposition.json; inputs/fmeda_metrics.json;
inputs/vv_evidence.json; tokn-self/introspect-slice.json; tokn-self/DOMAIN-README.md;
my live tool list.

## Domain tools that apply

| tool (exact name) | applies to | input fields needed, and whether present in inputs/ |
|---|---|---|
| `asil_decompose_verify` | Check 1 (decomposition) for all 5 functions, from `asil_decomposition.json` | `safety_req`, `architecture`, `independence_claims`, `decomposed_requirements`, `parent_asil`, `child_asils`. All present in every record. Schema is loose (`{}`), so pass each record unchanged. |
| `fmea_fta_engine` | Check 2 (hardware metrics) for all 5 functions, from `fmeda_metrics.json` | `architecture`, `failure_rates`, `asil_req`. All present in every record. Tool description says it returns PMHF, SPFM, LFM. |
| `safety_validation_report` | Check 3 (V&V) for all 5 functions, from `vv_evidence.json` | `all_evidence`, `safety_case`, `vv_report_path`, `requirements_covered_pct`, `defects_open`. All present in every record. |

Not used for this brief (no matching input in `inputs/`): `hara_automate`, `safety_case_build`,
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — ISO 26262 release-gate review of five ADAS functions (mobility domain)

Planner stage. This plan has not been run. No item has a status yet.
Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/asil_decomposition.json`,
`inputs/fmeda_metrics.json`, `inputs/vv_evidence.json`, `tokn-self/DOMAIN-README.md`,
`tokn-self/introspect-slice.json`.

## Objective

Give each of FN-AEB, FN-LKA, FN-ACC, FN-TJA and FN-APA exactly one status from
{`release_candidate`, `decomposition_invalid`, `hw_metrics_fail`, `vv_incomplete`}. The status comes from three
tool checks run in a fixed order: `asil_decompose_verify`, then `fmea_fta_engine`, then
`safety_validation_report`. Record the result in `result.json` and `RESULT.md` as a DRAFT for safety-manager review.

## Steps

General instructions for the Executor:
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# DRAFT — revised ADAS mechanical release-gate review

## Evidence and decision basis

Every supplied function record was freshly checked with `asil_decompose_verify`, `fmea_fta_engine`, and `safety_validation_report`. The explicit FN-LKA decomposition rejection and FN-APA V&V rejection were retried with identical complete inputs and repeated. Two separate negative probes contrasted ACC’s supplied no-error responses with rejection when only its child ASILs changed to A/A or only coverage changed to 94%.

**Basis: BRIEF’s rejection-based mechanical definitions.** Non-error decomposition and V&V responses expose action/instruction, not explicit positive verdict fields. The observed rejection channel is `error`. No-error is interpreted as mechanical acceptance under BRIEF, not proof of compliance or functional safety.

**Blocking clarification for human release:** PLAN R1/R3 really require explicit positive verdict fields in addition to no error. Contrary to critique C3’s quotation, literal PLAN does not equate no error alone with PASS. Literal PLAN would leave all five `decomposition_invalid`. The differentiated BRIEF classifications below do not satisfy that literal requirement. The safety manager must clarify or obtain structured verdicts before release use. Decision-1 requested full revision; its routing is not engineering evidence.

## Ordered outcomes

| Function | Decomposition | Hardware | V&V | First failing check | Status |
|---|---|---|---|---|---|
| FN-AEB | PASS under BRIEF | PASS | PASS under BRIEF | none | `release_candidate` |
| FN-LKA | FAIL | PASS | PASS under BRIEF | decomposition | `decomposition_invalid` |
| FN-ACC | PASS under BRIEF | PASS | PASS under BRIEF | none | `release_candidate` |
| FN-TJA | PASS under BRIEF | FAIL | PASS under BRIEF | hardware | `hw_metrics_fail` |
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 11 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# CRITIQUE — mobility release-gate review (result.json / RESULT.md)

Critic stage. Every raw tool output the executor quoted was re-run in this session and reproduces exactly: five `asil_decompose_verify` calls, five `fmea_fta_engine` calls, five `safety_validation_report` calls, plus identical-input repeats and control probes. The raw record is honest. The findings below are about what was concluded from it, and about what the deliverable is missing.

Severity is a label, not a filter: every issue found is listed.

## C1 — Four of five statuses contradict the tool outputs (blocking, overall)

The BRIEF defines `decomposition_invalid` as "`asil_decompose_verify` rejects the ASIL decomposition", and rule 2 says "A tool error is a rejection." The tool rejected **only FN-LKA**. The executor instead assigned `decomposition_invalid` to all five, on the reading that a response carrying no explicit `valid`/`passed`/`accepted` field is a FAIL.

My control probes establish the tools' verdict channel:

- `asil_decompose_verify` with parent `C`, children `[A,A]` → explicit error: *"child ASILs [A A] (sum 2) do not cover parent C (3) per ISO 26262-9 §5"* — the tool actively validates non-D parents, and its message states the operative coverage rule (child ASIL sum vs parent).
- `safety_validation_report` at 94% coverage → explicit error: *"requirements_covered_pct 94.0% is below the 95% threshold required for V&V completion"*; at exactly 95.0% → no error.
- `safety_validation_report` with a missing field → *"safety_validation_report requires all_evidence"*.

So: rejection = explicit error; no error = accepted, for these tool contracts. Under the tool's own stated coverage rule, FN-AEB (B+C=5 ≥ D=4), FN-ACC (B+A=3 ≥ C=3), FN-TJA (C+B=5 ≥ D=4) and FN-APA (A+A=2 ≥ B=2) were all returned without error — accepted. PLAN R1's PASS condition ("returns without error **and** no field that indicates rejection") is satisfied by all four.

Applying PLAN R4 with those verdicts:

| Function | Correct status | Basis |
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.997 |
| Does any function whose ASIL decomposition asil_decompose_verify rejected still receive release_candidate? | 0.033 |
| Does the result report FN-TJA's SPFM of 98.9% as meeting the 99% SPFM target? | 0.005 |

Routing: **full-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 11 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | blocking | Four of the five statuses contradict the tool outputs and the BRIEF's status definitions. I re-ran all 15 calls and every raw output the executor quoted reproduces exactly, so the raw record is honest — but the interpret… | **fixed**: Re-ran every supplied record. Corrected BRIEF statuses to AEB/ACC release_candidate (DRAFT), LKA decomposition_invalid, TJA hw_metrics_fail, APA vv_incomplete; … |
| C2 | blocking | result.json fails the PLAN's acceptance criteria for structure and completeness. PLAN says 'result.json is complete only if it is valid JSON containing' seven elements. Missing entirely: `tool_log` (criterion 3 — 15 entr… | **fixed**: Added first-failure/draft/verdict/metric/observation blocks, targets provenance, discrepancies, not_assessed, summary and disclaimer, preserving original shape.… |
| C3 | major | The controlling interpretation — 'no explicit positive verdict field, therefore FAIL' — was adopted without any discriminating test, and it is internally inconsistent. The plan's Step-3 instruction says 'Inspect the outp… | **fixed**: Recorded observed error rejection channel and ran independent negative probes: ACC changed to A/A rejects at parent C; ACC coverage changed to 94 rejects while … |
| C4 | major | Gate G4 (Evidence integrity) is marked 'warn' on a claim the artifact does not support. The G4 detail says 'Raw observations and reported numbers are preserved in the evidence text below', and RESULT.md says 'All require… | **fixed**: Used the finding's fallback: marked G4 not satisfied and explicitly stated selective quotations are not a preserved full raw log. Comprehensive log write blocke… |
| C5 | major | The confidence and validation language is stronger than the evidence. result.json reports confidence 0.93, and RESULT.md claims 'High confidence comes from direct input-file reads, repeated tool calls, explicit error mes… | **fixed**: Removed unsupported prior JSON/decision-comparison validation claim; reduced assessed confidence to 0.85 in BRIEF classification, not safety or completeness. Co… |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. Opus reads the full trace, names which tools mattered, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule
Before writing pass/fail rules for any domain tool, call it once with a known-good and once with a known-bad input, then record the observed verdict channel (e.g. error field vs result field) in PLAN.md and never require a verdict field the tool did not return.
```

## The answer

| Item | First answer (Kimi) | Final (after critique) | Expected |
|---|---|---|---|
| `FN-ACC` | `decomposition_invalid` | `release_candidate` ✅ | `release_candidate` |
| `FN-AEB` | `decomposition_invalid` | `release_candidate` ✅ | `release_candidate` |
| `FN-APA` | `decomposition_invalid` | `vv_incomplete` ✅ | `vv_incomplete` |
| `FN-LKA` | `decomposition_invalid` | `decomposition_invalid` ✅ | `decomposition_invalid` |
| `FN-TJA` | `decomposition_invalid` | `hw_metrics_fail` ✅ | `hw_metrics_fail` |

Accuracy: first answer 0.2, final 1.0.

## How it was graded

No model grades itself. [`verify.py`](../../verify.py) checks the files and the run log:

| Check | Result | Detail |
|---|---|---|
| artifacts_present | ✅ | all 10 present |
| result_json_valid | ✅ | final result.json parses with an items list |
| status_vocabulary | ✅ | all statuses in vocabulary |
| all_items_assessed | ✅ | 5 items |
| ground_truth | ✅ | final 1.0 (v1 0.2) |
| must_mention | ✅ | all present |
| forbidden_phrases | ✅ | none found |
| critique_has_findings | ✅ | 11 findings |
| every_finding_answered | ✅ | 11 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['asil_decompose_verify', 'fmea_fta_engine', 'safety_validation_report'] of expected ['asil_decompose_verify', 'fmea_fta_engine', 'safety_validation_report'] |
| critic_reran_tools | ✅ | critic used ['asil_decompose_verify', 'fmea_fta_engine', 'safety_validation_report'] |
| reflection_grounded | ✅ | names traced tools ['asil_decompose_verify', 'fmea_fta_engine', 'safety_validation_report']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Is it specific enough to change how the next run uses the domain tools?

## Run it yourself

```powershell
python run.py --domains mobility --out C:\tmp\relay-mobility
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
