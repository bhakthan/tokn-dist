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
Tool: `query_cmip6_catalog`. Make one call per item with these exact values:

| item | variable_id | experiment_id | table_id | member_id | deduplicate |
|---|---|---|---|---|---|
| CL-01 | `tas` | `ssp245` | `Amon` | `r1i1p1f1` | `true` |
| CL-02 | `pr` | `ssp245` | `Amon` | `r1i1p1f1` | `true` |
| CL-03 | `pr` | `ssp585` | `Amon` | `r1i1p1f1` | `true` |
| CL-04 | `tas` | `ssp585` | `Amon` | `r1i1p1f1` | `true` |
| CL-05 | `tos` | `ssp245` | `Omon` | `r1i1p1f1` | `true` |

Do not pass `source_id` because inputs/ gives none.
Record: the returned dataset/model list and the tool's deduplicated family count, **or** the verbatim error.
Effect on status: **none**. If the live family count differs from the Step 4 count, record the difference as a discrepancy note. Step 4 still decides.

### Step 2 — Live ensemble statistics cross-check (rule 1). Covers CL-01..CL-05.
Tool: `compute_ensemble_stats`. Make one call per item:

| item | variable_id | experiment_id | region | deduplicate |
|---|---|---|---|---|
| CL-01 | `tas` | `ssp245` | `box-A 30N-45N 10W-35E` | `true` |
| CL-02 | `pr` | `ssp245` | `box-B 35N-45N 0E-30E` | `true` |
| CL-03 | `pr` | `ssp585` | `box-C 5S-10N 95E-120E` | `true` |
| CL-04 | `tas` | `ssp585` | `box-D 50N-60N 0E-30E` | `true` |
| CL-05 | `tos` | `ssp245` | `box-E 60N-70N 20W-10E` | `true` |

Record: the returned "number of independent models", mean and percentiles, **or** the verbatim error. The region-string behaviour is unverified (CAPABILITIES Gap 6), so note it if the tool rejects or ignores the box string.
Effect on status: **none** (cross-check only, same as Step 1).

### Step 3 — Physical plausibility (rule 2). Covers CL-01..CL-05.
Tool: `validate_physical` in **summary mode**: pass `variable`, `units`, `min` and `max`, and do **not** pass `file`. Use these exact values from `inputs/field_ranges.json`:

| item | variable | units | min | max |
|---|---|---|---|---|
| CL-01 | `tas` | `K` | `268.1` | `312.6` |
| CL-02 | `pr` | `kg m-2 s-1` | `0.0` | `0.000184` |
| CL-03 | `pr` | `kg m-2 s-1` | `0.0` | `18.4` |
| CL-04 | `tas` | `K` | `255.3` | `305.9` |
| CL-05 | `tos` | `K` | `265.8` | `305.1` |

Then run a manual band check against the BRIEF tolerance band. This check is required and decides the result:

| variable | band_low | band_high |
|---|---|---|
| tas | 164 | 356 |
| pr | −0.0020011 | 0.0220001 |
| tos | 265.5 | 319.5 |

`band_pass = (band_low ≤ min) AND (max ≤ band_high)`, with inclusive bounds and **no unit conversion**. The check uses the tolerance band, **not** the plausible range. A value that lies outside the plausible range but inside the band passes.
Record: the tool verdict (PASS/WARN/FAIL or error text), the band used, min, max and `band_pass`.
Effect on status: `band_pass = false` → `implausible`. If the tool verdict disagrees with the manual `band_pass`, the manual check decides (BRIEF rule 2 is authoritative, and CAPABILITIES says the tool's internal band is unverified). Record the disagreement.

### Step 4 — Family deduplication (rule 3). Covers CL-01..CL-05.
Tool: **none matches** (CAPABILITIES Gap 2). The live `deduplicate` flag works on the live catalog, not on the input map. Do the step deterministically by reasoning, or with a short inline computation that reads `inputs/ensemble_claims.json` directly. Do not hard-code the results.
Procedure for each item:
1. For each entry in `models`, set `family = model_families[source_id]` if the key exists. Otherwise set `family = source_id`. Example: `KIOST-ESM` in CL-05 is not in the map, so it is its own family.
2. `N_fam` = the number of distinct family values.
3. Record the full source_id→family mapping and `N_fam` in evidence.

Effect on status: `N_fam < 5` → `insufficient_ensemble` (unless Step 3 already gave `implausible`).

### Step 5 — Likelihood derivation (rule 4). Covers CL-01..CL-05.
Tool: **none matches** (CAPABILITIES Gap 1). Do this step by reasoning.
1. A family agrees if its members have `agrees_with_claimed_sign = true`. BRIEF says members of one family always agree. If the data ever contradicts this, record it as a data defect and count the family as agreeing only if **all** of its members are `true`.
2. `A_fam` = number of agreeing families. `p = A_fam / N_fam`. Never use the raw model count.
3. Compare using **exact fractions**: check `low·N_fam ≤ A_fam ≤ high·N_fam`. This avoids floating-point error at the boundaries 0.90, 0.66, 0.99 and 0.33.
4. Scan the rows in this order and take the **first** row that matches:
   virtually certain [0.99, 1.00] → very likely [0.90, 0.99] → likely [0.66, 0.90] → about as likely as not [0.33, 0.66] → unlikely [0.10, 0.33].
   A boundary value goes to the higher row. For example, p = 0.90 is "very likely".
5. If p < 0.10, no row matches. Set `derived_term = null`.
6. Record `A_fam`, `N_fam`, p as the fraction and as a decimal to 4 dp, `derived_term`, and `stated_likelihood`.

Effect on status: compare `stated_likelihood` with `derived_term` after trimming and lower-casing both strings. If they are equal → `supported`. If they differ, or `derived_term` is null → `miscalibrated`. Both apply only if Steps 3 and 4 did not set a higher-precedence status.
Compute p and `derived_term` for **every** item, including those already set to `implausible` or `insufficient_ensemble`, and record them as evidence.

### Step 6 — Calibrated-language check of the deliverable (rule 5). Covers RESULT.md and result.json text for all items.
Tool: `review_artifact`. Pass:
- `text` = the full RESULT.md prose.
- `kind` = `"claim"`.
- `domain` = `"climsci"`.
- `artifact_path` = `"RESULT.md"`.
- `traceable` = every number used: each item's min, max, band_low, band_high (`source: "inputs/field_ranges.json"` / `"BRIEF.md rule 2"`), N_fam, A_fam and p (`source: "inputs/ensemble_claims.json"`).
- `plain_language` = a one-paragraph description of Steps 3–5.

Also run a manual scan, because no IPCC-language validator tool exists (CAPABILITIES Gap 3):
- Every likelihood term must be followed by its AR6 probability range: virtually certain (99–100 %), very likely (90–100 %), likely (66–100 %), about as likely as not (33–66 %), unlikely (0–33 %).
- No everyday certainty or hedging words may appear ("certainly", "definitely", "surely", "might", "possibly", "could", "probably").
- Keep the rule-4 family-fraction bands and the AR6 probability ranges apart. They are separate concepts (CAPABILITIES note).

Effect on status: **none**. Any critical `review_artifact` finding (untraceable number, missing provenance) or language violation must be fixed in the text before the deliverable is final.

## Decision rules

Apply the rules in this exact order for each item. Stop at the first rule that fires:

1. **implausible**: Step 3 manual check gives `min < band_low` OR `max > band_high` for that item's variable.
2. **insufficient_ensemble**: Step 4 gives `N_fam < 5`. Note that `N_fam = 5` is sufficient.
3. **miscalibrated**: `lower(trim(stated_likelihood)) ≠ lower(trim(derived_term))`, or `derived_term` is null.
4. **supported**: none of the rules above fired. That means the band passes, `N_fam ≥ 5`, and the stated term equals the derived term.

Further constraints:
- Tool outputs from Steps 1, 2 and 6 never fire a rule.
- The `validate_physical` verdict from Step 3 never overrides the manual band check. It is recorded only.
- Use the variable from `field_ranges.json` to select the band. If it ever differs from `catalog_requests.json` `variable_id`, record a data defect and use `field_ranges.json`, since that file describes the field being checked.
- Unit strings are compared as given. Values are never rescaled. A `pr` value that looks like it is in mm/day is still tested as declared, in kg m-2 s-1.

## Gates

A positive status (`supported`) may be given only if **all** of the following gates pass for that item:

1. **Physical plausibility gate** (BRIEF rule 2; TOKN `PhysicalRanges`): the manual tolerance-band check passes.
2. **Model-family deduplication gate** (DOMAIN-README safety gate 3; TOKN `GetIndependentModels`): `N_fam ≥ 5`, counted with `model_families` and the unknown-model = own-family rule.
3. **IPCC calibrated-language gate** (DOMAIN-README safety gate 4; `ar6_confidence_gate` hook is active in the session log): the stated term equals the derived term, and the deliverable text uses that term with its AR6 probability range.
4. **Four-layer data-hierarchy gate** (DOMAIN-README safety gate 1): all inputs are L2 model output. Confirm that no observation or reanalysis data was mixed in, and record `data_layer: "L2-model-output"`.

Not applicable: the jet-colormap gate (no figure is produced) and bias-correction provenance (no bias correction is done). Record both as `"not_applicable"`. Do not mark them as passed.
Affect tier: all steps are T0/T1. No T2+ action (downloads, regrids, file deletion) is needed or allowed.

## Acceptance criteria

`result.json` is complete only when it contains:
- A top-level `items` array with **exactly five** entries, one each for `CL-01`, `CL-02`, `CL-03`, `CL-04` and `CL-05`, and no other items.
- For each item:
  - `item`
  - `claim` (copied verbatim)
  - `stated_likelihood`
  - `status`: exactly one of `supported` | `miscalibrated` | `insufficient_ensemble` | `implausible`
  - `evidence`, an object containing:
    - `family_map`: source_id → family, for every model listed
    - `n_independent_families` (N_fam), `n_agreeing_families` (A_fam), `p` as a fraction string and as a 4-dp decimal
    - `derived_term` (or null) with its AR6 probability range string
    - `band_check`: `variable`, `units`, `min`, `max`, `band_low`, `band_high`, `pass` (boolean), and the `validate_physical` verdict or error
    - `catalog_query`: the Step 1 result or verbatim error
    - `ensemble_stats`: the Step 2 result or verbatim error
    - `decision_rule_fired`: 1, 2, 3 or 4, from the Decision rules
    - `gates`: pass / fail / not_applicable for each of the four gates, plus jet-colormap and bias-correction marked `not_applicable`
    - any discrepancy or data-defect notes
- The `status` must follow mechanically from `evidence` under the Decision rules. A second reader recomputing from `inputs/` must get the same status.
- Top-level `provenance`: the input files used, the tools called, `data_layer: "L2-model-output"`, and a statement that the inputs are synthetic.
- RESULT.md: Step 6 has run on it with no unresolved critical findings. Every likelihood term in it carries its AR6 probability range.
