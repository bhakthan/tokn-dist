# PLAN — WGS run QC and report-readiness review, run `RUN-2026-11-SYN` (genomics mode)

Planner stage. Nothing here has been run. Every tool result below is a condition to check, not a known outcome.
Sources: `BRIEF.md`, `inputs/run_qc.json`, `inputs/variants.json`, `inputs/consent_manifest.json`, `CAPABILITIES.md`.

## Objective
Give each of GX-01 to GX-06 exactly one readiness status (`report_ready`, `report_with_caveats`, `fail_qc` or `blocked`) for hand-off to clinical sign-out. Base it on WGS QC grading, GRCh38 coordinate validation, the HGVS nomenclature gate, and consent. Record everything in `result.json` and `RESULT.md`, and do not classify, sign or assert pathogenicity.

## Context the Executor must record before any tool call (Step 0)
- **Clinical intent.** Set `clinical_intent = true` in `result.json` with this reason: *"Readiness review gating candidate variants for clinical return of results (sign-out hand-off) is clinical intent under genomics-mode rules."* No tool sets `GenomicsContext.ClinicalIntent` (CAPABILITIES Gap 6), so record this as a declaration, not as a tool result.
- **precmed hand-off.** Record `precmed_handoff.required = true` and `precmed_handoff.performed = false`, with the note *"No precmed tool visible in this session; VUS/PHI/CLIA/PGx validation pending qualified reviewer."* Do not switch modes and do not call any precmed tool.
- **Assembly.** Use GRCh38 for every coordinate (`variants.json` `"assembly": "GRCh38"`, `run_qc.json` `"reference": "GRCh38"`).
- **No signing.** Do not sign, classify (ACMG) or state pathogenicity. `report_ready` means ready for hand-off, not signed.

## Steps

Run every step for every item, even after an item is already known to be `blocked`, so the record is complete. Log each call in `result.json.tool_calls` with the exact input and the exact (verbatim or truncated-verbatim) response.

### Step 1 — QC grading (all items) — no domain tool exists
- **Items:** GX-01 to GX-06.
- **Tool:** none. CAPABILITIES lists no QC-grading tool (Gap 1). Read `inputs/run_qc.json` with `read_file` and grade each metric against the BRIEF table. Thresholds are inclusive. Do not round, impute or re-derive any value.
- **Thresholds:**
  - `wgs_mean_coverage`: pass if ≥ 30, warning if ≥ 20 and < 30, fail if < 20.
  - `wgs_bases_gt10x`: pass if ≥ 95, warning if ≥ 90 and < 95, fail if < 90.
  - `wgs_mapping_rate`: pass if ≥ 98, warning if ≥ 95 and < 98, fail if < 95.
  - `wgs_duplication_rate`: pass if ≤ 15, warning if > 15 and ≤ 25, fail if > 25.
  - `wgs_titv_ratio`: pass if ≥ 2.0, warning if ≥ 1.9 and < 2.0, fail if < 1.9.
- **Input values (copied from `run_qc.json`) and the grades the Executor must reproduce independently.** If your grade differs from the one below, recheck against the thresholds and report the discrepancy.

| Item | mean_cov | bases_gt10x | mapping | dup | titv | Expected grades |
|---|---|---|---|---|---|---|
| GX-01 | 36.2 | 97.1 | 99.2 | 9.8 | 2.05 | all pass |
| GX-02 | 30.0 | 96.4 | 98.9 | 15.0 | 2.04 | all pass (30.0 and 15.0 sit on inclusive pass boundaries) |
| GX-03 | 27.4 | 95.8 | 98.6 | 18.6 | 2.03 | mean_coverage **warning**, duplication_rate **warning**, others pass |
| GX-04 | 41.0 | 98.0 | 99.0 | 8.9 | 1.84 | titv_ratio **fail** (1.84 < 1.9), others pass |
| GX-05 | 44.8 | 98.7 | 99.4 | 7.2 | 2.07 | all pass |
| GX-06 | 38.5 | 97.6 | 99.1 | 10.4 | 2.06 | all pass |

- **Status effect:** any `fail` makes `fail_qc` available. Any `warning` with no `fail` makes `report_with_caveats` available. Precedence is applied in Decision rules.

### Step 2 — Coordinate validation on GRCh38 (all items)
- **Items:** GX-01 to GX-06.
- **Tool:** `genomic_coord_ops`.
- **Exact inputs.** Copy the chromosome string verbatim. `position` is an integer.
  1. GX-01: `{"operation": "validate", "chromosome": "chr13", "position": 32340300, "assembly": "GRCh38"}`
  2. GX-02: `{"operation": "validate", "chromosome": "chr17", "position": 7674220, "assembly": "GRCh38"}`
  3. GX-03: `{"operation": "validate", "chromosome": "17", "position": 43124027, "assembly": "GRCh38"}`
  4. GX-04: `{"operation": "validate", "chromosome": "chr2", "position": 47403191, "assembly": "GRCh38"}`
  5. GX-05: `{"operation": "validate", "chromosome": "chr16", "position": 2081000, "assembly": "GRCh38"}`
  6. GX-06: `{"operation": "validate", "chromosome": "chr7", "position": 140753336, "assembly": "GRCh38"}`
- **Status effect:**
  - A response saying the coordinate is valid or within bounds on GRCh38 sets `coordinate.validated = true`.
  - A response saying it is invalid or out of range sets `validated = false`, and the item becomes `blocked`.
  - A tool error, an unsupported operation, or a response that states no validity sets `validated = "unassessed"`, and the item becomes `blocked` (fail-closed; see rule D2).

### Step 3 — Chromosome normalization (GX-03 only)
- **Item:** GX-03. It is the only chromosome without the `chr` prefix.
- **Tool:** `genomic_coord_ops`.
- **Exact input:** `{"operation": "normalize", "chromosome": "17", "convention": "chr"}`
- **Record:** the normalized name from the response, expected to be `chr17`. If the response gives no name, record "unassessed".
- **Status effect:** this step is for reporting only, with one exception. If Step 2 for GX-03 was rejected **only because of the naming convention** (the response says so explicitly), re-run validate with the normalized name: `{"operation": "validate", "chromosome": <normalized name returned>, "position": 43124027, "assembly": "GRCh38"}`. Use the re-run result as the GX-03 coordinate verdict and log both calls. Renaming the chromosome is a lossless change of convention, not a liftover. If Step 2 was rejected for any other reason, do not re-run, and GX-03 is `blocked`.

### Step 4 — HGVS parse (all items, informational)
- **Items:** GX-01 to GX-06.
- **Tool:** `genomic_coord_ops`.
- **Exact inputs.** Copy each HGVS string byte-for-byte. Do not "fix" GX-01 or GX-05.
  1. GX-01: `{"operation": "parse_hgvs", "notation": "NM_000059.4:c.5946del"}`
  2. GX-02: `{"operation": "parse_hgvs", "notation": "NM_000546.6:c.743G>A"}`
  3. GX-03: `{"operation": "parse_hgvs", "notation": "NM_007294.4:c.68_69del"}`
  4. GX-04: `{"operation": "parse_hgvs", "notation": "NM_000251.3:c.1A>G"}`
  5. GX-05: `{"operation": "parse_hgvs", "notation": "NM_000548.5:1832G>A"}`
  6. GX-06: `{"operation": "parse_hgvs", "notation": "NM_004333.6:c.1799T>A"}`
- **Record:** the transcript and change exactly as the tool returns them, or the verbatim error.
- **Status effect:** none on its own. The nomenclature verdict comes only from the gate in Step 5. Neither a parse error nor a parse success replaces the gate verdict, but a parse error must be noted in the rationale.

### Step 5 — ClinVar query behind the HGVS nomenclature gate (all items)
- **Items:** GX-01 to GX-06.
- **Tool:** `query_reference_db`.
- **Exact inputs.** Use the BRIEF form, with the HGVS string verbatim in both fields:
  1. GX-01: `{"database": "clinvar", "query": "NM_000059.4:c.5946del", "variant": "NM_000059.4:c.5946del"}`
  2. GX-02: `{"database": "clinvar", "query": "NM_000546.6:c.743G>A", "variant": "NM_000546.6:c.743G>A"}`
  3. GX-03: `{"database": "clinvar", "query": "NM_007294.4:c.68_69del", "variant": "NM_007294.4:c.68_69del"}`
  4. GX-04: `{"database": "clinvar", "query": "NM_000251.3:c.1A>G", "variant": "NM_000251.3:c.1A>G"}`
  5. GX-05: `{"database": "clinvar", "query": "NM_000548.5:1832G>A", "variant": "NM_000548.5:1832G>A"}`
  6. GX-06: `{"database": "clinvar", "query": "NM_004333.6:c.1799T>A", "variant": "NM_004333.6:c.1799T>A"}`
- **Schema discrepancy** (CAPABILITIES Gap 4): the visible schema has `database`, `query` and `max_results`, with no `variant` field.
  - If the call is refused **by schema validation** because `variant` is an unknown field (as opposed to a refusal by the nomenclature gate), log the refusal verbatim. Then retry once with `{"database": "clinvar", "query": <hgvs>}`.
  - Record in `result.json.discrepancies` which form actually ran.
  - Do not invent other fields.
- **Classify each response into exactly one gate outcome**, quoting the response verbatim:
  - `rejected`: the response comes from the HGVS or nomenclature gate, or a pre-tool hook, and refuses the call because of the variant string. Quote the gate's reason verbatim. The item becomes `blocked`.
  - `cleared`: the call reached the tool, so the gate let it through. A ClinVar result (hits or zero hits) counts, and so does a network, HTTP or timeout error raised by the tool itself. A network error is **not** a rejection: record `clinvar.outcome = "network_error"` with the verbatim message.
  - `unassessed`: anything that cannot be attributed with certainty to either case above. Examples are an ambiguous error, no response, or a schema refusal on both attempts. Apply rule D2, which fails closed.
- **ClinVar content:** it never changes status. If results come back, record the variation ID or IDs, the review status as returned, and the evidence tier. The tier is "community-curated (ClinVar submission aggregate)". Use "expert-curated clinical" only if the returned review status says expert panel or practice guideline. Do not restate a clinical significance as a pathogenicity assertion. If the significance is included at all, label it "ClinVar-reported, not assessed here".

### Step 6 — Consent verification (all items) — no domain tool exists
- **Items:** GX-01 to GX-06.
- **Tool:** none. No consent or IRB tool is visible (CAPABILITIES Gap 2). Read `inputs/consent_manifest.json` with `read_file`. Protocol is `IRB-SYN-0042`.
- **Rule:** clinical return is permitted only if all of the following hold: `consent_level == "clinical_return"`, `irb_active == true`, `dua_permits == true` and `deidentified == true`. A missing field or any other value counts as not permitted.
- **Input values:**
  - GX-01 to GX-05: `clinical_return`, true, true, true.
  - GX-06: **`research_only`**, true, true, true. This is not permitted, so GX-06 is `blocked` because consent does not permit clinical return.
- **Note in `result.json`:** consent was checked against the manifest only. There was no independent verification.

### Step 7 — Optional traceability check on RESULT.md
- **Tool:** `review_artifact`.
- **Inputs:**
  - `text` = the final RESULT.md prose.
  - `traceable` = every numeric value from `run_qc.json` and `variants.json`, with `source` set to the file name.
  - `kind` = `"other"`, `domain` = `"genomics"`.
- **Status effect:** none on item statuses. Fix or remove any untraceable number it flags before finishing.

## Decision rules
Apply these to each item in order. The first rule that matches sets the status.

**D1 — blocked.** The item is `blocked` if ANY of the following holds:
- (a) Step 5 gate outcome is `rejected`.
- (b) Step 2 (or the Step 3 re-run, for GX-03) gives `validated = false`.
- (c) Step 6 shows clinical return is not permitted.

List every reason that applies in `blocking_reasons`, not just the first.

**D2 — blocked, fail-closed on missing gate evidence.** The item is `blocked` if the Step 5 gate outcome is `unassessed` or the coordinate verdict is `unassessed`.
- Use the reason text `"gate_unassessed: <which gate>"`.
- Rationale: positive statuses require the HGVS string to *clear* the gate and the coordinate to *validate*. Missing evidence is not a pass.
- This is a planner decision. Flag it in `result.json.reviewer_flags` so the lab director can review it.

**D3 — fail_qc.** The item is `fail_qc` if no D1 or D2 condition holds and at least one Step 1 metric is `fail`. List every failing metric with its value.

**D4 — report_with_caveats.** The item is `report_with_caveats` if no earlier rule holds, at least one metric is `warning`, and none is `fail`. Name **every** warning metric with its value.

**D5 — report_ready.** The item is `report_ready` if all of the following hold:
- all five metrics are `pass`;
- the gate outcome is `cleared`;
- `coordinate.validated = true`;
- consent is permitted.

**Additional rules:**
- QC failures and warnings are still recorded on blocked items, for information only.
- A ClinVar network error, a ClinVar zero-hit result, ClinVar significance, and Step 4 parse output never change status.

Expected statuses if the gates behave as the inputs suggest. **These are not results.** The Executor must derive each status from the actual tool responses.
- GX-01: D5, unless the gate rejects `c.5946del`.
- GX-02: D5.
- GX-03: D4, with warnings on coverage and duplication rate.
- GX-04: D3, because of titv.
- GX-05: likely D1(a), because `1832G>A` has no `c.` type prefix. The gate must decide this; do not pre-empt it.
- GX-06: D1(c), because of consent.

## Gates
All of the following must hold before any item gets `report_ready` or `report_with_caveats`:
1. **HGVS nomenclature gate** (runs inside `query_reference_db`): outcome must be `cleared`.
2. **GRCh38 coordinate validation** (`genomic_coord_ops` validate): `validated = true`.
3. **Consent, IRB, DUA and de-identification** (manifest): all four conditions must be met.
4. **QC**: no metric is `fail`. Any warning forces `report_with_caveats`.
5. **Governance**, which applies to the whole run:
   - `clinical_intent` is declared with a reason.
   - The precmed hand-off is recorded as pending.
   - No sign, classification or pathogenicity statement appears anywhere.
   - Every number traces to an input file or a tool response.
   - HGVS strings are verbatim.
   - Evidence citations carry a tier label.

Phenopacket v2.0 does not apply, because this is not a rare-disease cohort or phenotype-match output.

## Acceptance criteria
`result.json` is complete only if it contains all of the following.

**Top level:**
- `run_id: "RUN-2026-11-SYN"`
- `assembly: "GRCh38"`
- `clinical_intent: {"value": true, "reason": ...}`
- `precmed_handoff: {"required": true, "performed": false, "note": ...}`
- `signed: false`
- `discrepancies` (at minimum: the `variant` field missing from the schema and which call form ran; consent checked from the manifest only; no QC-grading tool)
- `reviewer_flags` (including D2 if it was applied anywhere)
- `tool_calls`: one entry per call, with the tool name, the exact input and the verbatim response or error.

**`items` object with exactly the keys GX-01 to GX-06.** Each item must contain:
- `status`: exactly one of `report_ready`, `report_with_caveats`, `fail_qc` or `blocked`.
- `decision_rule`: one of D1 to D5.
- `qc`: all five metrics, each with the exact `value` from `run_qc.json` and a `grade`. Also `warning_metrics` and `fail_metrics` arrays (each may be empty).
- `coordinate`:
  - `chromosome_input`, `position` and `assembly`;
  - `normalized_chromosome` (GX-03 only; `null` for the others);
  - `validate_response`, verbatim;
  - `validated`: `true`, `false` or `"unassessed"`.
- `hgvs`:
  - `verbatim`: identical to `variants.json`;
  - `parse_hgvs`: `{transcript, change}` or `{error}`.
- `nomenclature_gate`:
  - `outcome`: `cleared`, `rejected` or `unassessed`;
  - `reason_quote`: verbatim, and required when the outcome is `rejected` or `unassessed`.
- `clinvar`:
  - `outcome`: `result`, `no_hits`, `network_error` or `not_reached`;
  - `summary`;
  - `evidence_tier`;
  - `affects_status: false`.
- `consent`: the four manifest fields, plus `permits_clinical_return` (true or false).
- `blocking_reasons`: an array, empty unless the status is `blocked`.
- `rationale`: one or two sentences in calibrated language. Passing QC means the data is fit for review. The rationale must contain no pathogenicity claim.

**Consistency checks:**
- Each status must follow from D1 to D5 using the recorded fields alone. A second reader applying the rules to the JSON must reach the same status.
- `RESULT.md` must state the same six statuses and name every warning metric for each `report_with_caveats` item.
- `RESULT.md` must end with this structure: **finding; supporting evidence; counterevidence/limitations; unassessed checks; permitted next step and responsible reviewer.** The reviewer is the lab director or clinical sign-out with precmed review.
