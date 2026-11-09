# Pre-pass go/no-go review for a five-satellite LEO constellation

*Domain mode `spacemarine` · five models and a decision model, one brief, graded by a deterministic checker. Verdict: **PASS**.*

## The problem

Assign go, no_go or hold to five satellites from TLE freshness, downlink margin and IADC 25-year disposal compliance.

Inputs (synthetic, in [`inputs/`](inputs/)): [`disposal_plans.json`](inputs/disposal_plans.json), [`link_budgets.json`](inputs/link_budgets.json), [`orbit_states.json`](inputs/orbit_states.json).

### What a careless run gets wrong

Each item hides a trap. The models never saw this list; the grader did.

| Item | Trap | Correct status |
|---|---|---|
| `SAT-3` | Best link margin (11.2 dB) and shortest disposal lifetime (4.1 years), but its TLE epoch is 96.5 hours old, so the TLE-freshness hook blocks orbit_propagate: hold, not go. | `hold` |
| `SAT-2` | Sits exactly on two boundaries: TLE age 72.0 h is not above the 72 h limit, and margin 3.0 dB satisfies margin >= 3.0, so link_closes is true. A careless run marks it hold or no_go. | `go` |
| `SAT-4` | Margin 2.9 dB is 0.1 dB below the 3.0 dB minimum; rounding to 3 dB gives go, but link_budget_calc returns link_closes false. | `no_go` |
| `SAT-5` | Everything else is clean, but the predicted post-mission lifetime of 25.4 years exceeds the IADC 25-year guideline, so the disposal plan is non-compliant. | `no_go` |

## The relay, step by step

| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |
|---|---|---|---|---|---|
| 0 | Discover | claude-haiku-5.5 | 50.1s | `read_file`×7, `edit_file`×2, `list_directory`×1, `write_file`×1, `run_command`×1 | [`CAPABILITIES.md`](run/CAPABILITIES.md) |
| 1 | Plan | claude-opus-5.5 | 169.9s | `read_file`×7, `list_directory`×2, `write_file`×2, `git_status`×1 | [`PLAN.md`](run/PLAN.md) |
| 2 | Execute | Kimi-K3.1-Pro | 475.3s | **`orbit_propagate`**×5, **`link_budget_calc`**×5, **`debris_compliance_check`**×5, `read_file`×9, `write_file`×3, `grounding_check_citations`×2 | [`RESULT.md`](run/RESULT.md) |
| 3 | Critique | claude-opus-5.5-fast | 138.6s | **`link_budget_calc`**×6, **`orbit_propagate`**×5, **`debris_compliance_check`**×5, `read_file`×7, `tle_omm_fetch`×5, `write_file`×2 | [`CRITIQUE.md`](run/CRITIQUE.md) |
| 4 | Decide | Microsoft-Decision-1 | 0.9s | — | [`decision.json`](run/decision.json) |
| 5 | Revise | gpt-6.1-sol | 252.8s | **`orbit_propagate`**×5, **`debris_compliance_check`**×5, **`link_budget_calc`**×5, `read_file`×14, `tle_omm_fetch`×5, `run_command`×4 | [`result.json`](run/result.json) |
| 6 | Reflect | claude-opus-5.5 | 97.4s | `read_file`×10, `grep_search`×4, `list_directory`×1, `write_file`×1 | [`REFLECTION.md`](run/REFLECTION.md) |

### 1. Discover — claude-haiku-5.5

Before anyone plans, TOKN describes itself. The discover stage reads `tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, not on what a model assumes exists.

From [`CAPABILITIES.md`](run/CAPABILITIES.md):

```text
# CAPABILITIES — spacemarine scout pass

Scope: SAT-1 … SAT-5 go/no-go per `BRIEF.md`. Scout pass only; no items assessed here.

Sources read: `BRIEF.md`; `inputs/orbit_states.json`, `inputs/link_budgets.json`, `inputs/disposal_plans.json`; `tokn-self/introspect-slice.json` (version 0.3.0, contract 1.0); `tokn-self/DOMAIN-README.md` (domain 0.1.0). Tool list checked against both.

## Domain tools that apply

| tool (exact name) | applies to | input fields needed and present in `inputs/` |
|---|---|---|
| `orbit_propagate` | Orbit freshness gate (`hold` rule) and delta-v gate, all five satellites | `tle_line1`, `tle_line2` (present in `orbit_states.json`); `epoch_age_hours` (present); `delta_v_closes` (present, boolean per satellite). Brief rule 2: pass the orbit record as given. |
| `link_budget_calc` | Downlink margin gate (3.0 dB), all five satellites | Present in `link_budgets.json`: `freq_ghz`, `eirp_dbw`, `distance_km`, `bandwidth_hz`. **Missing (required or needed):** `atmospheric_loss_db` (required by the schema; `atmospheric_model` is a text label, not a dB value), `g_over_t_dbk` or antenna gain plus system noise temperature, `data_rate_bps`, `required_ebn0_db`. See Gaps. |
| `debris_compliance_check` | IADC 25-year disposal gate, all five satellites | `orbit.altitude_km` (present); `disposal_plan` with `post_mission_lifetime_years` (present, used to set `compliant`). **Missing:** `perigee_alt_km`, `apogee_alt_km`, `area_to_mass_m2_per_kg` or `area_m2`+`mass_kg`. `reference_standard` = `"IADC"` (present). |
| `tle_omm_fetch` | Optional cross-check of TLE format and checksums before `orbit_propagate` (not required by the brief) | `tle_line1`, `tle_line2` (present); `start_time` optional. Offline; returns `checksum_line1_ok`, `checksum_line2_ok`, `epoch_age_hours`, `fresh`. |

Tools checked and judged not applicable to this brief: `conjunction_screen`, `constellation_design`, `earth_observation_plan`, `pass_predict`, `launch_window_calc`, `radiation_assess`, `thermal_node_model`, `link_budget_marine_comms`, `itar_ear_screen`, and all marine tools (`hull_resistance_estimate`, `stability_check`, `cii_eexi_calculate`, `marpol_compliance_check`, `maritime_reg_qa`, `ais_decode_analyze`, `oceanographic_forecast`, `seakeeping_bem`, `cfd_case_setup`). The brief asks nothing about them.

## Gates and rules that will constrain the answer
```

### 2. Plan — claude-opus-5.5

The planner turns the brief into acceptance criteria and names the tool call that decides each item.

From [`PLAN.md`](run/PLAN.md):

```text
# PLAN — spacemarine pre-pass go/no-go review (SAT-1 … SAT-5)

Planner stage. Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/orbit_states.json`, `inputs/link_budgets.json`, `inputs/disposal_plans.json`, `tokn-self/DOMAIN-README.md`, `tokn-self/introspect-slice.json`. This plan has not been executed. Every input value below was copied from `inputs/`. Where the plan states what a tool is expected to do, that is a prediction. The tool's real output overrides it.

## Objective

For each of SAT-1 … SAT-5, give exactly one status (`go`, `no_go` or `hold`) by applying the BRIEF.md precedence rules to real outputs from `orbit_propagate`, `link_budget_calc` and `debris_compliance_check`. Record the results in `result.json` and `RESULT.md`.

## Steps

General execution rules (these apply to every step):

- **E1.** Make exactly one call per tool per satellite, using the values listed. Do not add, drop, round or "fix" any value. Do not invent values for fields that are missing from `inputs/`, such as `atmospheric_loss_db`, `g_over_t_dbk`, `data_rate_bps`, `required_ebn0_db`, `perigee_alt_km`, `apogee_alt_km` or area-to-mass. The one allowed retry is described in Step 2.
- **E2.** Save the raw output of every call, or the raw error or block message, verbatim. A "blocked" or "refused" call is an outcome, not a failure to retry.
- **E3.** Run Steps 1–3 for **all five** satellites, including any that turn out to be `hold`. For held satellites, the link and disposal results are recorded as `informational_only` and must not affect the status (BRIEF rule 1: "Request a fresh TLE before judging anything else").
- **E4.** Calls for different satellites are independent and may run in parallel.

### Step 0 (optional, informational only): TLE format cross-check
- **Items:** SAT-1 … SAT-5.
```

### 3. Execute — Kimi-K3.1-Pro

The executor runs the domain tools and records every item with the tool output that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); the excerpt below is the final write-up, after the critique and revision.

From [`RESULT.md`](run/RESULT.md):

```text
# Spacemarine — final pre-pass review

## Evidence and decision

All mandatory orbit, link and debris calls were independently re-run for every satellite with the supplied numerical records. All five standalone TLE checks were also run. The scenario statuses are unchanged; the evidence-quality qualifications are materially revised. The brief governs: stale orbit state takes precedence, and the link and declared-lifetime thresholds are inclusive.

| Satellite | Orbit call / supplied age | Link tool outcome / supplied margin | Declared disposal lifetime / call outcome | Status and rule |
|---|---|---|---|---|
| SAT-1 | accepted; 18 h | true; 7.4 dB | 6.2 years; accepted | **go / D5** [src:sat1#0-533] |
| SAT-2 | accepted; 72 h | true; 3 dB | 11 years; accepted | **go / D5** [src:sat2#0-532] |
| SAT-3 | refused_stale; 96.5 h | true; 11.2 dB (informational only) | 4.1 years; accepted (informational only) | **hold / D1a** [src:sat3#0-548] |
| SAT-4 | accepted; 20 h | false; 2.9 dB | 9.5 years; accepted | **no_go / D2b** [src:sat4#0-541] |
| SAT-5 | accepted; 40 h | true; 6.1 dB | 25.4 years; blocked | **no_go / D2c** [src:sat5#0-540] |

Every orbit record declares delta-v closure. Every link outcome uses `supplied_evidence` with `computed=false`; “true” predicts closure under the brief, not an independent full-budget verification. Debris acceptance echoes caller-declared compliance derived from the input lifetime; it does not independently establish IADC compliance. Missing output fields remain null in `result.json`.

## Per-satellite conclusions
```

### 4. Critique — claude-opus-5.5-fast

A different model family re-runs the tools and files 12 finding(s). It is told to find faults, not to agree.

From [`CRITIQUE.md`](run/CRITIQUE.md):

```text
# CRITIQUE — spacemarine pre-pass go/no-go review

Critic stage. I re-ran every tool whose output decides a status:

- `orbit_propagate` for all five satellites, using the exact input records.
- `link_budget_calc` for all five, using the exact input records.
- `debris_compliance_check` for all five, with `IADC` and `compliant = lifetime <= 25`.
- `tle_omm_fetch` for all five, with `start_time = 2025-06-10T06:00:00Z`. I derived that time from SAT-1's epoch (2025-06-09T12:00Z) plus its supplied 18 h age.

**Re-run outcomes.**

| Sat | orbit_propagate | link_closes / margin | debris | Correct status | Result's status |
|---|---|---|---|---|---|
| SAT-1 | accepted, checksums false/false | true / 7.4 (supplied_evidence) | compliant=true, computed=false | go (D5) | go ✔ |
| SAT-2 | accepted at 72 h, checksums false/false | true / 3 (supplied_evidence) | compliant=true, computed=false | go (D5) | go ✔ |
| SAT-3 | **blocked**: "TLE epoch age 96.5 hours exceeds maximum 72.0 hours" | true / 11.2 (info only) | compliant=true (info only) | hold (D1a) | hold ✔ |
```

### 5. Decide — Microsoft-Decision-1

A decision model answers small, typed questions about the critique. It returns a probability, not prose, and the probability routes the next stage.

| Question | P(yes) |
|---|---|
| Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used? | 0.651 |
| Does any satellite whose TLE epoch is older than 72 hours receive go? | 0.006 |
| Does the result describe a link with margin below 3.0 dB as closing? | 0.033 |

Routing: **full-revision**.

### 6. Revise — gpt-6.1-sol

The reviser must answer every finding, not only the ones it agrees with: 12 fixed.

| Finding | Severity | Issue (abridged) | Response |
|---|---|---|---|
| C1 | major | result.json does not follow the PLAN.md acceptance schema. Missing top-level keys: `summary` (go/no_go/hold arrays), `deviations`, `gates_not_assessed`, `caveats` (it uses `gates` and `limitations` instead). Every item i… | **fixed**: Preserved existing result shape and added PLAN acceptance keys and structured per-item evidence; absent tool fields are null. Summary and decisions are derived … |
| C2 | major | The input epoch_age_hours does not agree with the TLE epoch. In the orbit_propagate output, SAT-1's epoch is 2025-06-09T12:00Z and its age is 18 h, so the review time is 2025-06-10T06:00Z. Re-running tle_omm_fetch with s… | **fixed**: Independent tle_omm_fetch gives SAT-4 epoch 2025-06-08T16:00:00.000288Z and age 38 h at the inferred review time, versus supplied 20 h. Recorded caveat/deviatio… |
| C3 | major | The same epoch-age inconsistency applies here. tle_omm_fetch (start_time 2025-06-10T06:00:00Z) gives epoch 2025-06-07T20:00Z and epoch_age_hours=58, but the input says 40.0. The status (no_go via D2c) is unaffected, but … | **fixed**: Independent tle_omm_fetch gives SAT-5 epoch 2025-06-07T19:59:59.999712Z and age 58 h versus supplied 40 h. Recorded caveat/deviation; D2c unchanged. |
| C4 | major | SAT-1 is `go` even though orbit_propagate and tle_omm_fetch both report checksum_line1_ok=false and checksum_line2_ok=false, so neither TLE line passes the mod-10 checksum. The plan's D1b only covers a blocked or errored… | **fixed**: Both independent SAT-1 checksum flags are false. Added tle_check and qualified orbit acceptance and operational-use caveat. Kept scenario go per D5; the optiona… |
| C5 | major | This finding has three parts. (a) SAT-2 is `go` with both checksums false; orbit_propagate output is checksum_line1_ok=false and checksum_line2_ok=false. (b) Its margin is exactly 3.0 dB. link_budget_calc returned margin… | **fixed**: Reruns accept SAT-2 at 72 h and margin 3 dB with min_margin_db=3, supplied_evidence and computed=false; both checksums fail. Flagged zero headroom/freshness all… |

All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).

### 7. Reflect — claude-opus-5.5

TOKN reflects on TOKN a second time. The reflector reads the full trace, names which tools mattered, and proposes a `/teach` rule so the next run starts smarter.

From [`REFLECTION.md`](run/REFLECTION.md):

```text
## Proposed /teach rule

`/teach In spacemarine TLE reviews, always run tle_omm_fetch on every TLE with start_time set to (reference satellite epoch + its supplied epoch_age_hours), and record checksum failures and any supplied-age vs epoch-age mismatch as deviations before writing result.json.`
```

## The answer

| Item | First answer (Kimi-K3.1-Pro) | Final (after critique) | Expected |
|---|---|---|---|
| `SAT-1` | `go` | `go` ✅ | `go` |
| `SAT-2` | `go` | `go` ✅ | `go` |
| `SAT-3` | `hold` | `hold` ✅ | `hold` |
| `SAT-4` | `no_go` | `no_go` ✅ | `no_go` |
| `SAT-5` | `no_go` | `no_go` ✅ | `no_go` |

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
| critique_has_findings | ✅ | 12 findings |
| every_finding_answered | ✅ | 12 responses |
| decision_answered | ✅ | 3/3 typed answers |
| execute_used_domain_tools | ✅ | used ['debris_compliance_check', 'link_budget_calc', 'orbit_propagate'] of expected ['debris_compliance_check', 'link_budget_calc', 'orbit_propagate'] |
| critic_reran_tools | ✅ | critic used ['debris_compliance_check', 'link_budget_calc', 'orbit_propagate'] |
| reflection_grounded | ✅ | names traced tools ['debris_compliance_check', 'link_budget_calc', 'orbit_propagate']; has /teach rule: True |

## Reflect on it yourself

- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.
- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?
- Read the `/teach` rule above. Is it specific enough to change how the next run uses the domain tools?

## Run it yourself

```powershell
python run.py --domains spacemarine --out C:\tmp\relay-spacemarine
```

Set up `.env` and the prerequisites first; see the [relay README](../../README.md).

For a single-model version of this run that costs far less, see [mission-compliance](../../../mission-compliance/README.md).
