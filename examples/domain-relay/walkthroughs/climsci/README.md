# Likelihood and plausibility check of five CMIP6 regional projection claims

*Domain mode `climsci` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Classify five synthetic regional projection claims by physical plausibility of the field, model-family independence, and whether the stated IPCC likelihood term follows from the deduplicated ensemble agreement.

Inputs (synthetic, in [`inputs/`](inputs/)): [`catalog_requests.json`](inputs/catalog_requests.json), [`ensemble_claims.json`](inputs/ensemble_claims.json), [`field_ranges.json`](inputs/field_ranges.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `CL-01` | Boundary: 9 of 10 independent families agree, so p = 0.90 exactly. 'likely' (0.66-0.90) also contains 0.90, but the scan is top-down and 'very likely' (0.90-0.99) matches first. Stated 'very likely' is correct, so supported, not miscalibrated. | `supported` |
| `CL-02` | The raw count is 9/12 = 0.75, which maps to 'likely' and matches the stated term. But the 12 models are only 7 families (CESM x3, EC-Earth x3, MPI-ESM x2). 4 of 7 agree, so p = 0.571, which is 'about as likely as not'. Status is miscalibrated. | `miscalibrated` |
| `CL-03` | Looks good: 8 independent families, p = 0.875, stated 'likely' matches. But the pr field max is 18.4 in declared units of kg m-2 s-1, which is almost certainly mm/day mislabelled. It is far above the 0.0220001 tolerance limit, so the item is implausible. The rules forbid silently converting units to rescue it. | `implausible` |
| `CL-04` | Ten models, all agreeing, p = 1.0, stated 'virtually certain'. The family map collapses them to 4 families (UKESM, CNRM, IPSL, ACCESS), which is below 5. Status is insufficient_ensemble. | `insufficient_ensemble` |
| `CL-05` | Two boundaries. The tos min of 265.8 K is below the 270 K plausible minimum but inside the 265.5 K tolerance band, so it is plausible. KIOST-ESM is not in the family map, so it counts as its own family: 6 families, 4 agree, p = 0.667 >= 0.66, which is 'likely'. Dropping KIOST-ESM gives 3/5 = 0.60, wrongly 'about as likely as not'. Status is supported. | `supported` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5-5 | 56.8s | `read_file`×6, `list_directory`×2, `write_file`×1, `edit_file`×1, `run_command`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5-5 | 101.5s | `read_file`×6, `list_directory`×1, `grep_search`×1, `write_file`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 1070.3s | **`query_cmip6_catalog`**×5, **`compute_ensemble_stats`**×5, `validate_physical`×11, `read_file`×9, `run_command`×7, `write_file`×6 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 572.2s | **`query_cmip6_catalog`**×5, **`compute_ensemble_stats`**×5, `read_file`×9, `run_command`×7, `validate_physical`×6, `grep_search`×2 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.2s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 254.9s | **`query_cmip6_catalog`**×5, **`compute_ensemble_stats`**×5, `read_file`×11, `validate_physical`×5, `run_command`×5, `update_plan`×3 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5-5 | 125.7s | `read_file`×12, `grep_search`×4, `list_directory`×1, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

Stages that ended without their deliverable were retried once; the retry is recorded in [`TRACE.json`](run/TRACE.json), never hidden.

> **Disclosure:** the execute stage exited with code 3 (a TOKN guard stopped the agent, such as the token-budget breaker). Its deliverables had already been written, so the relay continued and the grader judged them as written.

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — climsci scout stage

Scope: capability inventory for BRIEF.md (items CL-01 to CL-05). Items are not assessed here.
Sources read: BRIEF.md; inputs/catalog_requests.json, ensemble_claims.json, field_ranges.json;
tokn-self/introspect-slice.json; tokn-self/DOMAIN-README.md; my live tool list (ground truth).

## Domain tools that apply

| tool (exact name) | applies to | input fields needed | present in inputs/? |
|---|---|---|---|
| query_cmip6_catalog | CL-01..CL-05 (live cross-check only) | variable_id, experiment_id, table_id, member_id, deduplicate (tool also takes source_id) | yes, all in catalog_requests.json. region, season, baseline_start/end have no parameter in this tool |
| compute_ensemble_stats | CL-01..CL-05 (live cross-check only) | variable_id, experiment_id, region, deduplicate | yes. season and baseline_start/end have no parameter in this tool |
| validate_physical (summary mode) | CL-01..CL-05, rule 2 band check | variable, units, min, max | yes, all in field_ranges.json. Units are compared, never converted, as the brief requires |
| review_artifact | RESULT.md / result.json (later stage) | text, traceable (declared values from field_ranges.json and family counts), artifact_path | not yet; needed at the deliverable stage |

Not applicable to these inputs (no NetCDF file, no figure, no download, no regrid needed):
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — climsci relay, Planner stage

Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/catalog_requests.json`, `inputs/ensemble_claims.json`, `inputs/field_ranges.json`, `tokn-self/DOMAIN-README.md`.
This plan has **not** been executed. No item status is decided here.

## Objective

For each of CL-01 to CL-05, assign exactly one status (`implausible`, `insufficient_ensemble`, `miscalibrated`, `supported`). Base it on the physical tolerance-band check of `field_ranges.json` and on the family-deduplicated sign-agreement fraction from `ensemble_claims.json`. Run the required live catalog cross-checks and record their results as evidence.

## Steps

General instructions for the Executor:
- The input files are authoritative (BRIEF rule 1). Live tool results are evidence only and never change a status.
- If a tool returns a Python, dependency or network error, copy the error text verbatim into that item's `evidence.tool_errors` and continue.
- Tool names are the exact names in CAPABILITIES.md. Pass only the listed parameters. `region` is the one exception: it is a real parameter of `compute_ensemble_stats` only. `season`, `baseline_start` and `baseline_end` have no tool parameter. Record them in evidence as labels only.
- All five items use `member_id = "r1i1p1f1"` and `deduplicate = true`.

### Step 1 — Live catalog cross-check (rule 1). Covers CL-01..CL-05.
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# Final review of synthetic CMIP6 projection claims

## Method and scope

All three input files declare synthetic data. The supplied family map, sign flags and field extrema are authoritative; this report is not a regional climate study. Every item was independently recomputed and all required domain tools rerun. Status precedence is implausible > insufficient_ensemble > miscalibrated > supported. The minimum ensemble size is five independent families.

Likelihood labels follow the first matching inclusive interval in BRIEF rule 4, using exact fractions. The printed AR6 probability ranges are separate from those selection intervals. Family agreement fractions are not empirical event probabilities. Physical checks use the tolerance bands and declared units without conversion.

## CL-01 — supported

**Claim:** Summer near-surface air temperature in box A rises by 2041-2060 relative to 1995-2014.
**Stated likelihood:** very likely (90–100 %).

- Physical check: extrema [268.1, 312.6] K; tolerance band [164, 356] K. Manual check passes; validate_physical rerun returned PASS in summary mode.
- Independence: 10 families; 9 agree; p = 9/10 = 0.9000. Derived term: very likely (90–100 %).
- Mapping: ACCESS-CM2 → ACCESS; CanESM5 → CanESM; CESM2 → CESM; EC-Earth3 → EC-Earth; IPSL-CM6A-LR → IPSL; MPI-ESM1-2-LR → MPI-ESM; UKESM1-0-LL → UKESM; GFDL-ESM4 → GFDL; MIROC6 → MIROC; NorESM2-LM → NorESM.
- All family votes are internally consistent. Full flags, request arguments, errors and named gates are in result.json.
- Decision rule 4: supported.
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 7 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# CRITIQUE — climsci relay, Critic stage

Scope: `BRIEF.md`, `PLAN.md`, `inputs/` (all three files), `result.json`, `RESULT.md`. Every tool whose output decides or evidences a status was re-run by me: `validate_physical` in summary mode for all five items, `query_cmip6_catalog` and `compute_ensemble_stats` for all five items, `review_artifact` on the RESULT.md prose, and an independent recomputation of the family map, N_fam, A_fam, p, derived term and band check directly from `inputs/`.

**What checks out.** All five statuses are mechanically correct and reproduce exactly from `inputs/` under the plan's decision rules: CL-01 `supported` (N_fam=10, A_fam=9, p=0.9000 → very likely, matches stated; band 164–356 K passes), CL-02 `miscalibrated` (N_fam=7, A_fam=4, p=0.5714 → about as likely as not, stated likely), CL-03 `implausible` (max 18.4 > 0.0220001 kg m-2 s-1; rule 1 precedence), CL-04 `insufficient_ensemble` (N_fam=4 < 5), CL-05 `supported` (N_fam=6 including unmapped KIOST-ESM as its own family, A_fam=4, p=0.6667 → likely, matches). The boundary cases are handled correctly (p = 0.90 → very likely; p = 2/3 → likely). Every `validate_physical` verdict, tolerance range and the CL-03 violation string match my re-runs verbatim. All ten live catalog/statistics calls fail with the identical `ModuleNotFoundError: No module named 'intake'` traceback that the deliverable quotes verbatim, and the deliverable correctly does not let those failures change any status. No input value was ignored: variable/experiment/table/member/region arguments, seasons, baselines, extrema, units, family map and sign flags all appear in the evidence. Every likelihood term in both files carries its AR6 probability range.

## Findings

### C1 — overall — blocking
**Step 6 (`review_artifact`) was never recorded, and it fails when actually run.** PLAN Step 6 requires `review_artifact` on the RESULT.md prose and says any critical finding "must be fixed in the text before the deliverable is final"; the acceptance criteria require "RESULT.md: Step 6 has run on it with no unresolved critical findings." Neither file records any `review_artifact` output — every per-item `tools_used` array in `result.json` lists only `query_cmip6_catalog`, `compute_ensemble_stats`, `validate_physical`, `run_command` — yet RESULT.md's provenance line claims "tools used … and `review_artifact`". That is a tool claim with no recorded output, i.e. a gate marked pass without evidence. I ran `review_artifact` on RESULT.md with the traceable values from `inputs/field_ranges.json`, `inputs/ensemble_claims.json` and BRIEF rule 2: `passed: false`, "review BLOCKED (critical findings): 2 critical, 8 high" — `code_artifact_drift` ("artifact has no recorded producing code") and `incomplete_provenance` ("missing environment, producing_code"), plus untraceable numbers 90, 100, 66, 33, 2100, 99, 270, 0.97.
**Fix:** run `review_artifact` on the final RESULT.md and record its verbatim output in `result.json`; clear the two critical findings by declaring the producing computation (the inline family-map / p computation over `inputs/ensemble_claims.json`) and the runtime environment in the provenance; declare the flagged numbers as traceable with sources (90/100/66/33/99 = AR6 ranges from the DOMAIN-README table required by rule 5; 270 K = untoleranced plausible bound from BRIEF rule 2; 2100 = claim text in `inputs/ensemble_claims.json`; 0.97 = self-assessed confidence). Note honestly: several of the "high" findings are the tool flagging mandatory calibrated language rather than real defects, and are cleared by declaring those sources — but the two critical provenance gaps are real.

### C2 — overall — major
**`result.json` does not conform to the acceptance-criteria evidence schema.** The criteria require an evidence *object* with named fields (`family_map`, `n_independent_families`, `n_agreeing_families`, `p` as fraction string and 4-dp decimal, `derived_term` with AR6 range, `band_check` with variable/units/min/max/band_low/band_high/pass and the `validate_physical` verdict, `catalog_query`, `ensemble_stats`, `decision_rule_fired`, `gates`, `tool_errors`), plus per-item keys `item`, `claim` (verbatim) and `stated_likelihood`. `result.json` uses `id` instead of `item`, has no `claim` or `stated_likelihood` fields (both live only inside the first free-text evidence string), and makes `evidence` an *array* of tool-prefixed prose strings. Every required value is present and correct on my recomputation, but a second reader applying the acceptance criteria mechanically cannot extract the named fields.
**Fix:** restructure each item's evidence into the specified object with named keys; promote `item`, `claim`, `stated_likelihood` to item level; move the verbatim intake tracebacks into `catalog_query`, `ensemble_stats` and a `tool_errors` key.

### C3 — overall — major
**Missing top-level `provenance` object in `result.json`.** The acceptance criteria require top-level provenance with the input files used, the tools called, `data_layer: "L2-model-output"` and a statement that the inputs are synthetic. `result.json` has no such field; the information exists only in RESULT.md prose and inside each item's first evidence string, so `result.json` alone does not meet the completeness criterion.
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.023 |
| Does the result accept CL-02's stated likelihood 'likely' as correct for the deduplicated ensemble? | 0.009 |
| Does the result treat the CL-04 ten-model ensemble as having at least five independent model families? | 0.002 |

Routing: **full-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 7 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | blocking | The Step 6 calibrated-language/provenance gate was not actually run, and it fails when run. PLAN Step 6 requires review_artifact on the RESULT.md prose (kind="claim", domain="climsci") and states that any critical findin… | **fixed**: Added actual producing code and observed runtime. Baseline review independently reproduced two critical provenance gaps; the final artifact review output is rec… |
| C2 | major | result.json does not conform to the acceptance-criteria schema for item evidence. The criteria require an evidence OBJECT with named fields (family_map, n_independent_families, n_agreeing_families, p as a fraction string… | **fixed**: Retained existing top-level fields and id identifiers while adding item, verbatim claim and stated_likelihood. Replaced free-text evidence with all plan-require… |
| C3 | major | result.json is missing the required top-level 'provenance' object. The acceptance criteria require top-level provenance recording the input files used, the tools called, data_layer: "L2-model-output", and a statement tha… | **fixed**: Added top-level provenance listing synthetic inputs, hashes, tools, data layer, producing code and runtime. |
| C4 | minor | A word on the plan's banned list appears in the deliverable. PLAN Step 6's manual scan forbids 'certainly', 'definitely', 'surely', 'might', 'possibly', 'could', 'probably' anywhere in the deliverable text; RESULT.md lin… | **fixed**: Removed the banned availability wording; final language scans cover both deliverables. |
| C5 | minor | Unexplained 'corrected' wording in the top-level Physical plausibility gate detail: 'The corrected summary-mode validate_physical verdicts agree.' No correction is documented anywhere in result.json or RESULT.md, and my … | **fixed**: Removed the undocumented revision adjective. All five independent physical-tool reruns agree with manual checks: PASS, PASS, FAIL, PASS, PASS. |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. Opus reads the full trace, which tools mattered, where the run stalled, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

/teach climsci: copy every domain-tool verdict (validate_physical, review_artifact, query_cmip6_catalog and compute_ensemble_stats errors) into result.json verbatim from that stage's own tool output; never regenerate a tool verdict or error string from your own computation or from a previous stage's file.
```

## The answer

| Item | First answer (Kimi) | Final (after critique) | Expected |
|---|---|---|---|
| `CL-01` | `supported` | `supported` ✅ | `supported` |
| `CL-02` | `miscalibrated` | `miscalibrated` ✅ | `miscalibrated` |
| `CL-03` | `implausible` | `implausible` ✅ | `implausible` |
| `CL-04` | `insufficient_ensemble` | `insufficient_ensemble` ✅ | `insufficient_ensemble` |
| `CL-05` | `supported` | `supported` ✅ | `supported` |

Accuracy: first answer 1.0, final 1.0.

## How it was graded

No model grades itself. [`verify.py`](../../verify.py) checks the files and the run log:

| Check | Result | Detail |
|---|---|---|
| artifacts_present | ✅ | all 10 present |
| result_json_valid | ✅ | final result.json parses with an items list |
| status_vocabulary | ✅ | all statuses in vocabulary |
| all_items_assessed | ✅ | 5 items |
| ground_truth | ✅ | final 1.0 (v1 1.0) |
| must_mention | ✅ | all present |
| forbidden_phrases | ✅ | none found |
| critique_has_findings | ✅ | 7 findings |
| every_finding_answered | ✅ | 7 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['compute_ensemble_stats', 'query_cmip6_catalog'] of expected ['compute_ensemble_stats', 'query_cmip6_catalog'] |
| critic_reran_tools | ✅ | critic used ['compute_ensemble_stats', 'query_cmip6_catalog'] |
| reflection_grounded | ✅ | names traced tools ['compute_ensemble_stats', 'query_cmip6_catalog']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Would it have prevented the stall recorded in [`TRACE.json`](run/TRACE.json)?

## Run it yourself

```powershell
python run.py --domains climsci --out C:\tmp\relay-climsci
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
