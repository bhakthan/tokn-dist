# Pre-publication gate check of six Battery Passport drafts

*Domain mode `batterypass` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Run six synthetic Battery Passport drafts through the EU 2023/1542 mandatory-attribute, CF methodology, due-diligence and chemistry-consistency checks and classify each.

Inputs (synthetic, in [`inputs/`](inputs/)): [`chemistry_declarations.json`](inputs/chemistry_declarations.json), [`passports.json`](inputs/passports.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `BP-02` | Every EU mandatory attribute is present, the CF share is 0.71 and the audit is fresh, so all three gates pass. But the label declares LFP while the cathode is LiNi0.6Mn0.2Co0.2O2: bp_check_chemistry returns consistent=false, missing=[Fe,P], forbidden=[Co,Ni,Mn]. Status is inconsistent. | `inconsistent` |
| `BP-03` | Boundary just inside: primaryDataShare is exactly 0.50. The gate test is share < 0.50, so it passes. Status is compliant, not non_compliant. | `compliant` |
| `BP-04` | Boundary just outside: primaryDataShare 0.49 gives 'primaryDataShare=0.49 is below threshold 0.50'. Status is non_compliant, even though the EU gate and the chemistry check pass. | `non_compliant` |
| `BP-05` | Looks identical to BP-01, but lastAuditDate 2024-03-02 is more than 365 days old, so the due-diligence gate blocks it. | `non_compliant` |
| `BP-06` | Na-ion contains none of the watch-list materials, so due diligence is a no-op, and bp_check_chemistry returns consistent=true because the chemistry is unknown. A careless run calls it compliant, but the EU gate reports that combo NAION:EV is not in the matrix. | `not_assessable` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5-5 | 36.6s | `read_file`×5, `list_directory`×1, `write_file`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5-5 | 157.5s | `read_file`×6, `list_directory`×2, `write_file`×2, `git_status`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 430.5s | **`bp_check_compliance`**×9, **`bp_check_cf_methodology`**×9, **`bp_check_due_diligence`**×9, **`bp_check_chemistry`**×9, `read_file`×5, `run_command`×4 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | FW-GLM-5.3 | 289.2s | **`bp_check_chemistry`**×6, **`bp_check_compliance`**×6, **`bp_check_cf_methodology`**×6, **`bp_check_due_diligence`**×6, `read_file`×7, `write_file`×2 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 1.0s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 627.9s | **`bp_check_compliance`**×6, **`bp_check_chemistry`**×6, **`bp_check_cf_methodology`**×6, **`bp_check_due_diligence`**×6, `run_command`×13, `read_file`×8 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5-5 | 132.0s | `read_file`×6, `run_command`×2, `list_directory`×1, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

Stages that ended without their deliverable were retried once; the retry is recorded in [`TRACE.json`](run/TRACE.json), never hidden.

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — SCOUT stage, batterypass pre-publication gate check

Scope: items BP-01 to BP-06 in `inputs/passports.json` and `inputs/chemistry_declarations.json`.
Evidence: BRIEF.md, both inputs, `tokn-self/introspect-slice.json`, `tokn-self/DOMAIN-README.md`, and the live tool list. Where these disagree, the live tool list governs (see Gaps).

## Domain tools that apply

Every passport (BP-01 to BP-06) needs the same four gate calls plus one chemistry call. The payload is passed as `body`, serialized to a JSON string.

| tool (exact name) | Items / input | Input fields needed (present in `inputs/`) |
|---|---|---|
| `bp_check_compliance` | BP-01 to BP-06, `passports.json` | `body` ← `payload` (stringified); `chemistry` ← `chemistry`; `application` ← `application` |
| `bp_check_cf_methodology` | BP-01 to BP-06 | `body` ← `payload`. Reads `payload.CarbonFootprint`: `carbonFootprintStudyMethod`, `primaryDataShare`, `systemBoundary`, `functionalUnit` (all present) |
| `bp_check_due_diligence` | BP-01 to BP-06 | `body` ← `payload`. Reads `payload.MaterialComposition.batteryMaterials` and `payload.SupplyChainDueDiligence`: `dueDiligencePolicyURI`, `lastAuditDate` (all present) |
| `bp_check_chemistry` | BP-01 to BP-06, `chemistry_declarations.json` | `declared_chemistry` ← `declared_chemistry`; `cathode_composition` ← `cathode_composition` (matched by `passport`) |
| `bp_load_payload` (optional pre-check) | BP-01 to BP-06 | `body` ← stringified `payload`. Confirms the payload parses before gating. Not required by the brief. |
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — pre-publication gate check of six Battery Passport drafts (batterypass)

Planner stage. This file is the only output of this stage. Nothing has been executed.
Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/passports.json`, `inputs/chemistry_declarations.json`, `tokn-self/DOMAIN-README.md`, `tokn-self/introspect-slice.json`.

## Objective

Run the four batterypass checks (`bp_check_compliance`, `bp_check_cf_methodology`, `bp_check_due_diligence`, `bp_check_chemistry`) on each of BP-01 to BP-06, then record exactly one status per passport (`compliant` | `non_compliant` | `inconsistent` | `not_assessable`) in `result.json` and `RESULT.md`, using the mechanical rules below.

## Ground rules for the Executor (apply to every step)

- **Do not edit any payload** (BRIEF rule 6). This includes reordering keys, fixing values, or replacing `NMC` with `NMC811`.
- **`body` serialization.** `body` is the passport's `payload` object from `inputs/passports.json`, serialized to a JSON **string** (for example `json.dumps(payload)`). Do not pass the object itself, because the batterypass parse hooks reject it. Do not include the outer `id`/`chemistry`/`application` wrapper.
- **`chemistry` / `application`.** Pass the top-level `chemistry` and `application` fields of the passport entry, character for character. Never use `Labels.declaredChemistry` or `MaterialComposition.batteryChemistry` such as `NMC811` or `NMC622`.
- **Quote every issue string verbatim**, and keep the full raw tool response for each call.
- **Run every call for every passport**, even after a higher-precedence status is already determined (BRIEF rule 1). That is 6 x 4 = 24 gate/chemistry calls, plus 6 optional parse pre-checks.
- **Retry policy.** If a call fails with a transport, tool, or parse error rather than returning a result, check that `body` is a string and retry once with an unchanged payload. If it still fails, record the error verbatim and apply the "errored" rows of the Decision rules.
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# Battery Passport pre-publication gate report

**Domain:** `batterypass`  
**Revision execution date (UTC):** 2026-11-06; clock independently observed at 23:58:15 UTC.

All four checks were independently rerun for every passport using the unchanged payloads and exact chemistry/application keys from `inputs/`. All six original statuses were reproduced.

> Statuses reflect TOKN batterypass gate projection of EU 2023/1542; not a legal certification or publication authorization. Synthetic data. Successful `Issues: null` results are normalized to empty arrays; complete raw responses retain null.

## Decision ledger

| Passport | Gate keys | Chemistry consistent | EU | CF | DD | Status | Basis |
|---|---|---|---|---|---|---|---|
| BP-01 | NMC / EV | true | Pass | Pass | Pass | compliant | R4 |
| BP-02 | LFP / EV | false | Pass* | Pass* | Pass* | inconsistent | R1 |
| BP-03 | NMC / Industrial | true | Pass | Pass | Pass | compliant | R4 |
| BP-04 | LFP / LMT | true | Pass | Fail | Pass | non_compliant | R3 |
```

### 4. Critique — FW-GLM-5.3

A different model family re-runs the tools and files 8 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# CRITIQUE — executor's `result.json` / `RESULT.md` (batterypass pre-publication gate check)

**Critic method.** I read `BRIEF.md`, `PLAN.md`, `inputs/passports.json`, `inputs/chemistry_declarations.json`, `result.json` and `RESULT.md`, then re-ran every gate whose output decides a status — all 24 calls (`bp_check_chemistry` ×6, `bp_check_compliance` ×6, `bp_check_cf_methodology` ×6, `bp_check_due_diligence` ×6) on the unmodified payloads from `inputs/passports.json`, passing each `payload` as a JSON-string `body` and the top-level `chemistry`/`application` values character for character.

**Outcome of the re-run.** Every gate outcome the executor reported is **correct and reproduced exactly**:

| Passport | chemistry | EU | CF | DD | Reported status | Re-derived status |
|---|---|---|---|---|---|---|
| BP-01 | NMC/EV | pass | pass | pass | compliant (R4) | compliant (R4) ✓ |
| BP-02 | LFP/EV | pass | pass | pass | inconsistent (R1) | inconsistent (R1) ✓ |
| BP-03 | NMC/Industrial | pass | pass (0.50) | pass | compliant (R4) | compliant (R4) ✓ |
| BP-04 | LFP/LMT | pass | **fail** | pass | non_compliant (R3) | non_compliant (R3) ✓ |
| BP-05 | NMC/EV | pass | pass | **fail** | non_compliant (R3) | non_compliant (R3) ✓ |
| BP-06 | NaIon/EV | **fail (D2 matrix)** | pass | pass | not_assessable (R2) | not_assessable (R2) ✓ |

So there is **no wrong status, no skipped gate, and no fabricated gate result**. All four issue strings are quoted verbatim and match my re-run character for character. The defects are in **deliverable conformance and evidence completeness**, which is where the findings below sit. Severity labels are exactly that — labels; every issue found is listed.
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.026 |
| Does any passport whose bp_check_chemistry result is consistent=false still receive compliant or non_compliant? | 0.006 |
| Does the result describe any passport as legally certified or approved for the EU market, rather than as passing TOKN's gate projection? | 0.003 |

Routing: **full-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 8 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | blocking | result.json does not conform to the deliverable schema defined in PLAN.md's Acceptance criteria. The required top-level keys 'brief', 'disclaimer' and 'execution_date' are absent (result.json's actual top-level keys are … | **fixed**: Confirmed missing PLAN audit fields independently. Added brief, disclaimer, execution_date, chemistry/application, status_basis, checks, all_issues, discrepanci… |
| C2 | major | No raw tool response and no exact call input is recorded for any of the 24 calls. PLAN.md's ground rules require 'keep the full raw tool response for each call', and acceptance checklist item 3 requires each check to car… | **fixed**: Each check now records exact arguments, including the compact serialized unchanged payload body for all three body-based gates, plus the complete observed raw r… |
| C3 | minor | The chemistry failure output for BP-02 is only partially reproduced. The tool returned error='consistency mismatch declaredChemistry=LFP cathodeActiveMaterial=LiNi0.6Mn0.2Co0.2O2 reason=chemistry element mismatch: declar… | **fixed**: BP-02 chemistry rerun confirmed the full error and error_detail. Both are preserved in JSON, and the complete raw response is reproduced in RESULT.md. |
| C4 | minor | result.json carries fields outside the specified shape, including an empty 'critique_response' array. An empty critique_response inside the executor's own output reads as a placeholder for this critique stage and could l… | **fixed**: Populated critique_response with one entry per finding at this reviser stage, as explicitly required. It is no longer an empty placeholder; original relay field… |
| C5 | minor | The stated confidence (0.99 in both result.json and RESULT.md) is higher than the evidence supports for the deliverable as a whole. The six statuses are directly backed by tool output that I reproduced, but the deliverab… | **fixed**: Confidence reduced to 0.95 and scoped only to the six statuses under configured tools. Structural conformance is checked separately; legal compliance and physic… |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. Opus reads the full trace, which tools mattered, where the run stalled, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

/teach In batterypass gate-check briefs, the Executor must write result.json in the exact PLAN acceptance shape on the first pass (checks.{chemistry,eu_compliance,cf_methodology,due_diligence} with called, input incl. serialized body, raw, issues, error; status_basis; all_issues; discrepancies:[]; payload_modified:false), and must treat a gate's "gate blocked" error string as a recorded failing result rather than a tool fault to retry.
```

## The answer

| Item | First answer (Kimi) | Final (after critique) | Expected |
|---|---|---|---|
| `BP-01` | `compliant` | `compliant` ✅ | `compliant` |
| `BP-02` | `inconsistent` | `inconsistent` ✅ | `inconsistent` |
| `BP-03` | `compliant` | `compliant` ✅ | `compliant` |
| `BP-04` | `non_compliant` | `non_compliant` ✅ | `non_compliant` |
| `BP-05` | `non_compliant` | `non_compliant` ✅ | `non_compliant` |
| `BP-06` | `not_assessable` | `not_assessable` ✅ | `not_assessable` |

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
| execute_used_domain_tools | ✅ | used ['bp_check_cf_methodology', 'bp_check_chemistry', 'bp_check_compliance', 'bp_check_due_diligence'] of expected ['bp_check_cf_methodology', 'bp_check_chemistry', 'bp_check_compliance', 'bp_check_due_diligence', 'bp_query_passport'] |
| critic_reran_tools | ✅ | critic used ['bp_check_cf_methodology', 'bp_check_chemistry', 'bp_check_compliance', 'bp_check_due_diligence'] |
| reflection_grounded | ✅ | names traced tools ['bp_check_cf_methodology', 'bp_check_chemistry', 'bp_check_compliance', 'bp_check_due_diligence']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Would it have prevented the stall recorded in [`TRACE.json`](run/TRACE.json)?

## Run it yourself

```powershell
python run.py --domains batterypass --out C:\tmp\relay-batterypass
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).
