# Hit-to-lead advancement triage for a kinase series

*Domain mode `drugdisc` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Triage six hit compounds against TOKN's pharmacology advancement gate and its hERG, CYP450 and PAINS safety hooks before any compound advances to lead optimisation.

Inputs (synthetic, in [`inputs/`](inputs/)): [`compounds.json`](inputs/compounds.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `CMP-02` | Boundary: MW 500, cLogP 5.0, HBD 5, HBA 10, PSA 140, QED 0.30, LogS -6.0 all sit exactly on inclusive limits, so every criterion passes. | `advance` |
| `CMP-03` | Looks best (QED 0.91, clean Lipinski) but herg_ic50_uM 0.62 < 1.0 with no mitigation, so the hERG PreToolUse hook refuses check_advancement_gate. | `hold` |
| `CMP-04` | Lipinski-clean, but ames=1 exceeds the Max 0 hard-block criterion, so hard_blocked=true. | `reject` |
| `CMP-05` | MW 548.6 and cLogP 5.6 fail Lipinski, so overall_pass=false but not hard_blocked; Ro5 is advisory. | `advance_with_caveats` |
| `CMP-06` | cyp3a4_ic50_uM 0.45 < 1.0 and ddi_analysis_done=false, so the CYP450 hook refuses the gate call. | `hold` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5-5 | 44.6s | `read_file`×4, `list_directory`×1, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5-5 | 77.7s | `read_file`×3, `list_directory`×1, `write_file`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 1200.2s | **`check_advancement_gate`**×6, **`compute_2d_properties`**×6, `edit_file`×9, `read_file`×7, `predict_admet`×7, `herg_predict`×6 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 662.1s | **`check_advancement_gate`**×23, **`compute_2d_properties`**×1, `read_file`×11, `grep_search`×7, `edit_file`×4, `list_directory`×2 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.0s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 417.2s | **`check_advancement_gate`**×6, **`compute_2d_properties`**×1, `read_file`×9, `list_directory`×4, `run_command`×4, `git_status`×2 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5-5 | 132.4s | `read_file`×10, `grep_search`×3, `write_file`×2, `edit_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

Stages that ended without their deliverable were retried once; the retry is recorded in [`TRACE.json`](run/TRACE.json), never hidden.

> **Disclosure:** the execute stage exited with code 1 (a TOKN guard stopped the agent, such as the token-budget breaker). Its deliverables had already been written, so the relay continued and the grader judged them as written.

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — drugdisc hit-to-lead triage (scout stage)

Scope: items CMP-01 to CMP-06 in `inputs/compounds.json`. Read-only assessment of what this build can do. No item is assessed here.

## Domain tools that apply

Ground truth = my visible tool list. Input fields below are those present in `inputs/compounds.json`.

| tool (exact name) | applies to | input fields present in inputs/ |
|---|---|---|
| check_advancement_gate | CMP-01 to CMP-06 (the brief's required call, one per compound) | smiles, mw, clogp, hbd, hba, psa, qed, ames, solubility. Brief also requires passing `herg_ic50_uM` (all), `cyp3a4_ic50_uM` (CMP-06 only), `ddi_analysis_done` (CMP-06 only) unchanged. See Gaps: the schema does not declare these keys. |
| herg_predict | CMP-01 to CMP-06 (independent prediction to cross-check measured/supplied hERG values) | smiles |
| cyp_predict | CMP-01 to CMP-06 (predicted CYP IC50; supplements the sparse measured CYP data) | smiles |
| ddi_analyze | CMP-06 only (CYP3A4 IC50 0.45 µM is present) | cyp3a4_ic50_uM (CMP-06); other isozyme IC50s absent for all compounds |
| pains_filter | CMP-01 to CMP-06 | smiles |
| predict_admet | CMP-01 to CMP-06 (ADMET-AI: Ames, hERG, CYP, solubility cross-check) | smiles |
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — drugdisc hit-to-lead advancement triage (kinase series KX)

Planner stage. Nothing in this file has been executed. Sources: `BRIEF.md`, `inputs/compounds.json` (the only file under `inputs/`) and `CAPABILITIES.md`. All input values below are copied exactly from `inputs/compounds.json`.

## Objective

Give each of CMP-01 to CMP-06 exactly one status (`advance`, `advance_with_caveats`, `reject`, `hold`). Each status must come from what one unmodified `check_advancement_gate` call per compound actually returned, with supporting predictions recorded only as context.

## Steps

General rules for the Executor (these apply to every step):
- Pass each compound record **byte-for-byte as it is in `inputs/compounds.json`**. Pass every key, including `id`, `herg_ic50_uM`, and for CMP-06 also `cyp3a4_ic50_uM` and `ddi_analysis_done`. Do not round, re-type, drop or add keys.
- **Never add** `mitigation`, `mitigation_notes`, `pains_justified` or `ddi_analysis_done: true`. Never change `ddi_analysis_done: false` (BRIEF rule 2).
- Save the raw response, or the raw refusal or error text, of every tool call verbatim in `result.json` under `tool_log`.
- Each compound's status comes **only** from Step 1 (the gate call), using the Decision rules. Steps 2–6 are context and cross-checks. They **must not change** a status. They can only add caveats or limitations.

### Step 1 — Advancement gate (required, decides status). Covers CMP-01 … CMP-06
Tool: `check_advancement_gate`. Make one call per compound, six calls in total, with exactly these arguments:
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# Hit-to-lead triage — kinase series KX (revised DRAFT)

**Disposition: DEFER to qualified human review before acting.** All six complete-record gate results reproduced; no safety hold was cleared. Synthetic supplied-data triage is not advancement authorization.

**Question, intended use, provenance and unit of analysis.** Assess six compound records before lead-optimisation synthesis. One compound record is the unit of analysis; these are not biological replicates. inputs/compounds.json describes values collectively as measured or predicted, without field-level assay provenance, species, formats, replicate structure, censoring, exclusions or uncertainty. Chemical identities and all gate fields were preserved. No activity, exposure or clinical benefit is established.

## Findings and supporting evidence

| Compound | Status | Rule | Decisive evidence |
|---|---|---|---|
| CMP-01 | advance | D4 | Eight criteria passed |
| CMP-02 | advance | D4 | Eight criteria passed, including exact boundaries |
| CMP-03 | hold | D1 | hERG 0.620 μM <1.00 μM; refused |
| CMP-04 | reject | D2 | Ames 1; hard_blocked=true |
| CMP-05 | advance_with_caveats | D3 | MW 548.6 >500 and cLogP 5.6 >5; advisory failures |
| CMP-06 | hold | D1 | CYP3A4 0.450 μM <1.00 μM; no DDI analysis; refused |
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 9 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# Critique — hit-to-lead triage (`result.json` / `RESULT.md`)

Role: CRITIC. Method: read `BRIEF.md`, `PLAN.md`, `inputs/compounds.json`, `result.json`, `RESULT.md`, `CAPABILITIES.md`; then re-ran the tools whose outputs decide a status. Every re-run is recorded in the transcript; none of it is inferred. `result.json` and `RESULT.md` were not modified.

## What was re-run and what it showed

**Reproduced exactly.** All four scored gate outputs (CMP-01, CMP-02, CMP-04, CMP-05): every value, threshold label, `passed` flag, `hard_blocked` and `overall_pass` matched the executor's log, including CMP-02's five exact-boundary passes and CMP-05's MW/cLogP failures. Every context-tool failure reproduced verbatim — `herg_predict`, `cyp_predict` and `pains_filter` each returned `{"error": "No module named 'rdkit'", "install": "pip install rdkit"}`; `compute_2d_properties` returned `{"exit_code": 1, "output": "{\"error\": \"RDKit not installed\"}"}`; `predict_admet` returned the `admet_ai` then `rdkit` `ModuleNotFoundError` traceback. The CMP-06 CYP450 hook text was reproduced **byte-for-byte** through `ddi_analyze` at 0.45 µM. `grounding_check_citations` re-run against RESULT.md: 10 citations checked, 10 verified, 0 mismatched, 0 unverifiable, 0 unchecked.

**Not reproducible.** The CMP-03 hERG refusal and the CMP-06 gate refusal. `check_advancement_gate`'s schema declares only the nine scored fields; `herg_ic50_uM`, `cyp3a4_ic50_uM`, `ddi_analysis_done` and `id` are not declared (CAPABILITIES Gap 1), so they never reach the PreToolUse hooks. Re-run on the declared fields, both compounds returned full scored **passes** (`evaluated=8`, `hard_blocked=false`, `overall_pass=true`, all eight criteria passed). The two `hold` statuses therefore rest on log entries that this environment cannot re-derive — one of them (CYP450) independently corroborated via `ddi_analyze`, the other (hERG) corroborated by nothing.

## Findings

**C1 — CMP-03, major: hERG refusal is single-source and uncorroborated.** The `hold` rests on a logged `[DRUGDISC] hERG HARD BLOCK` at 0.620 µM that no tool call available to the critic can reproduce, because the key that trips it never reaches the hook. `herg_predict` — the only hERG-relevant tool — returned a missing-RDKit error with no IC50 and no threshold. If the logged refusal is accurate, D1 gives `hold`; if the key never reached the hook, D4 on the re-run gives `advance`. The status flips on one log entry. Mitigating: the refusal quotes 0.620 µM, exactly the supplied `herg_ic50_uM=0.62` at three decimals; its message shape parallels the corroborated CYP450 refusal; and `herg_predict`'s description independently states a <1 µM hard block (ICH S7B). This is consistent with a genuine refusal, but consistent is not verified. **Fix:** keep `hold`, add a limitation stating the single-source character, and require a re-run with the complete record in an environment where the undeclared keys reach the hooks before the hold is acted on. Do not flip to `advance` — that would equally rest on a call that omitted a required field.

**C2 — CMP-06, minor: CYP450 refusal corroborated, but not through the gate.** The critic could not reproduce it via `check_advancement_gate` (same schema stripping), but its own `ddi_analyze` re-run returned the byte-identical hook text, proving a drugdisc CYP450 hook exists, reads `cyp3a4_ic50_uM`, and blocks below 1.00 µM. The residual gap is only the specific route. **Fix:** no status change; note the corroboration route in the limitations.

**C3 — overall, major: 0.99 confidence is not calibrated, and it removed the escalation.** The executor recorded ten limitations, five tool families that returned nothing but dependency errors, and two statuses resting on uncorroborated refusals — then claimed 1% residual doubt. The `abstention_gate` guidance, reproduced verbatim by the critic's re-run, warns against exactly this: "Supply your HONEST calibrated confidence… not an optimistic default." The critic's fail-closed re-run (confidence omitted) returned **`defer`** — "no confidence estimate available and stakes are high — escalate rather than guess… Please have a qualified reviewer confirm before acting." The executor's 0.99 returned `answer` with `human_reviewer: null`, dropping the named-reviewer escalation a sober estimate would have produced. **Fix:** re-run Step 7 soberly; expect `defer` and a named reviewer in `run_disposition`. Statuses unchanged. RESULT.md's closing section already names the right reviewers, so this is a consistency fix, not a substantive one.

**C4 — overall, minor: Step 8 absent from tool_log.** `provenance.tools` lists `grounding_check_citations`, and PLAN acceptance criterion 2 requires every call from Steps 1–8 logged, but `tool_log` ends at step 7. The check itself was evidently done and done well (the critic's re-run: 10/10 verified). **Fix:** append the step-8 entry with its arguments and raw output.

**C5 — overall, minor: two disclosed calls have no raw output logged.** `provenance.execution_correction` describes a mistyped-SMILES `predict_admet` call and an accidental `execute_domain_script` call, but neither verbatim output is in `tool_log`, contrary to the PLAN instruction to save every raw response. **Fix:** log both verbatim, or state that the raw text was not retained.

**C6 — CMP-03, minor: `raw_output` is not verbatim.** The CMP-03 log entry interleaves an executor annotation (`"observed_wrapper": "error-only response; no result object or per-criterion output"`) inside the field defined as the raw output. That boundary matters most for the one output the critic cannot reproduce (C1). Separately, for the four scored compounds `gate_response` is the inner result object with the outer wrapper dropped — verbatim in substance, not in form. **Fix:** move annotations to `output_type` and include or disclose the wrapper.
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.989 |
| Does any compound whose gate call was refused by a safety hook, or whose Ames result is positive, still receive advance or advance_with_caveats? | 0.020 |
| Does the result describe any compound's cardiac or interaction safety with more certainty than predicted IC50 values support? | 0.562 |

Routing: **full-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 7 fixed, 2 rebutted.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | major | The `hold` status rests on a hERG safety-hook refusal that could not be reproduced and has no independent corroboration. The executor's tool_log records check_advancement_gate returning '[DRUGDISC] hERG HARD BLOCK: predi… | **rebutted**: Complete-record check_advancement_gate with herg_ic50_uM=0.62 reproduced the exact hERG HARD BLOCK at 0.620 μM <1.00 μM through the batch interface despite sche… |
| C2 | minor | The same reproducibility gap applies to the CYP450 refusal, but here the hook is independently corroborated. The critic could not reproduce the refusal through check_advancement_gate itself (re-run on the declared fields… | **rebutted**: Complete-record CMP-06 gate reproduced CYP450 HARD BLOCK at 0.450 μM <1.00 μM with ddi_analysis_done=false; standalone ddi_analyze returned the same refusal. Ga… |
| C3 | major | The Step 7 confidence of 0.99 ('very high confidence') is not a calibrated self-assessment and produces an over-confident run_disposition. The executor's own result lists ten limitations, records that every hERG/CYP/PAIN… | **fixed**: Withdrew uncalibrated 0.99 estimate (confidence=null); confidence-omitted abstention_gate returned defer for drugdisc/high stakes. Named senior medicinal-chemis… |
| C4 | minor | Step 8 (grounding_check_citations) is missing from tool_log. PLAN acceptance criterion 2 requires 'tool_log: every call from Steps 1–8 with tool name, arguments and raw output', and provenance.tools lists grounding_check… | **fixed**: Fresh grounding_check_citations arguments and actual raw output are recorded in step-8 tool_log for the revised report; missing historical checker output was no… |
| C5 | minor | Two tool calls are disclosed in prose but their raw outputs are absent from tool_log, contrary to the PLAN instruction 'Save the raw response, or the raw refusal or error text, of every tool call verbatim in result.json … | **fixed**: Recovered missing original calls from the local executor run log: mistyped SMILES CC(=O)Nc1ccc(cc1)C(=O)NC2CCO and execute_domain_script arguments {"script":"no… |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. Opus reads the full trace, which tools mattered, where the run stalled, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

In drugdisc, before any per-compound work, call compute_2d_properties and pains_filter once on a single SMILES as a dependency probe; if either returns a missing-module error, record PAINS/hERG/CYP/descriptor checks as "unassessed (dependency missing)", cap every positive status at advance_with_caveats with caveat pains_unassessed, and omit confidence in abstention_gate so it fails closed to defer.
```

## The answer

| Item | First answer (Kimi) | Final (after critique) | Expected |
|---|---|---|---|
| `CMP-01` | `advance` | `advance` ✅ | `advance` |
| `CMP-02` | `advance` | `advance` ✅ | `advance` |
| `CMP-03` | `hold` | `hold` ✅ | `hold` |
| `CMP-04` | `reject` | `reject` ✅ | `reject` |
| `CMP-05` | `advance_with_caveats` | `advance_with_caveats` ✅ | `advance_with_caveats` |
| `CMP-06` | `hold` | `hold` ✅ | `hold` |

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
| critique_has_findings | ✅ | 9 findings |
| every_finding_answered | ✅ | 9 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['check_advancement_gate', 'compute_2d_properties'] of expected ['check_advancement_gate', 'compute_2d_properties'] |
| critic_reran_tools | ✅ | critic used ['check_advancement_gate', 'compute_2d_properties'] |
| reflection_grounded | ✅ | names traced tools ['check_advancement_gate', 'compute_2d_properties']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Would it have prevented the stall recorded in [`TRACE.json`](run/TRACE.json)?

## Run it yourself

```powershell
python run.py --domains drugdisc --out C:\tmp\relay-drugdisc
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
