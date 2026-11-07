# WGS readiness review — revised DRAFT

**Run:** `RUN-2026-11-SYN`; **assembly:** GRCh38, patch not supplied. No classification, signature or patient return.

## Question, scope and QC-gate DAG

Assess mechanical readiness per synthetic sample and its exported candidate variant, not pathogenicity. Sources: inputs/run_qc.json, inputs/variants.json and inputs/consent_manifest.json [tier: synthetic observations/administrative assertions, not independent clinical evidence]. Positions are 1-based; transcripts retain their supplied versions. No independent biological replication is claimed.

DAG: preserve inputs → consent eligibility hold → parallel QC threshold grading and GRCh38 bounds checks → informational HGVS parsing → runtime database screening plus mandatory structural-policy check → blocked > fail_qc > report_with_caveats > report_ready → qualified precision-medicine review. Audit-only checks on blocked samples do not advance clinical analysis or authorize return.

Thresholds are inclusive local BRIEF.md policy, not evidence of call correctness. Clinical intent is declared (`GenomicsContext.ClinicalIntent=true`) because this concerns possible clinical return. Explicit precmed referral is recorded; execution and VUS/PHI/CLIA/PGx validation remain pending. No authorized sign-out occurs here.

**Missing prerequisites:** reference patch, locus callability, allele concordance, transcript/genomic correspondence, independent identity and consent verification, and completed precmed review.

**Schema notice to lab director:** result.json retains an `items` array under the reviser same-shape instruction, whereas PLAN.md requested a keyed object. Consumers must use each item’s `id`; no ID is omitted or duplicated.

## Per-sample results

| Sample | Status | Mean coverage (x) | Bases >10x (%) | Mapping (%) | Duplication (%) | Ti/Tv |
|---|---|---:|---:|---:|---:|---:|
| GX-01 | `report_ready` | 36.2 (pass) | 97.1 (pass) | 99.2 (pass) | 9.8 (pass) | 2.05 (pass) |
| GX-02 | `report_ready` | 30.0 (pass) | 96.4 (pass) | 98.9 (pass) | 15.0 (pass) | 2.04 (pass) |
| GX-03 | `report_with_caveats` | 27.4 (warning) | 95.8 (pass) | 98.6 (pass) | 18.6 (warning) | 2.03 (pass) |
| GX-04 | `fail_qc` | 41.0 (pass) | 98.0 (pass) | 99.0 (pass) | 8.9 (pass) | 1.84 (fail) |
| GX-05 | `blocked` | 44.8 (pass) | 98.7 (pass) | 99.4 (pass) | 7.2 (pass) | 2.07 (pass) |
| GX-06 | `blocked` | 38.5 (pass) | 97.6 (pass) | 99.1 (pass) | 10.4 (pass) | 2.06 (pass) |

QC table source: inputs/run_qc.json; grades independently recomputed from unchanged values [tier: synthetic observations/local policy]. GX-02 inclusive boundary values pass.

### GX-01 — `report_ready`

**Variant:** `NM_000059.4:c.5946del` (unchanged). Parse returns transcript `NM_000059.4`, change `c.5946del`, type `coding`. [tier: computational informational parse].

**Coordinate:** `chr13:32340300` on GRCh38 returned `valid=true` [tier: computational bounds check].

**Consent:** `clinical_return`; IRB active, DUA permits and deidentified all true. Permits clinical return: true [tier: synthetic manifest assertion; not independently verified].

**Runtime screening/ClinVar:** {"count": "1", "database": "clinvar", "ids": ["9325"], "provenance": "NCBI ClinVar via E-utilities", "query": "NM_000059.4:c.5946del", "query_date": "2026-11-07T03:11:57Z"}; review status, significance and database release not returned. Search IDs are not confirmed matched variation records. [tier: community-curated ClinVar submission aggregate; expert-curated status not established]. Database content never changes status.

All supplied coordinates validated for GRCh38 bounds only; QC grades use exact input values and consent is manifest-only. All mechanical brief gates pass; readiness is only for qualified review, not clinical authorization.

### GX-02 — `report_ready`

**Variant:** `NM_000546.6:c.743G>A` (unchanged). Parse returns transcript `NM_000546.6`, change `c.743G>A`, type `coding`. [tier: computational informational parse].

**Coordinate:** `chr17:7674220` on GRCh38 returned `valid=true` [tier: computational bounds check].

**Consent:** `clinical_return`; IRB active, DUA permits and deidentified all true. Permits clinical return: true [tier: synthetic manifest assertion; not independently verified].

**Runtime screening/ClinVar:** {"count": "3", "database": "clinvar", "ids": ["230253", "12356", "12347"], "provenance": "NCBI ClinVar via E-utilities", "query": "NM_000546.6:c.743G>A", "query_date": "2026-11-07T03:11:57Z"}; review status, significance and database release not returned. Search IDs are not confirmed matched variation records. [tier: community-curated ClinVar submission aggregate; expert-curated status not established]. Database content never changes status.

All supplied coordinates validated for GRCh38 bounds only; QC grades use exact input values and consent is manifest-only. All mechanical brief gates pass; readiness is only for qualified review, not clinical authorization.

### GX-03 — `report_with_caveats`

**Variant:** `NM_007294.4:c.68_69del` (unchanged). Parse returns transcript `NM_007294.4`, change `c.68_69del`, type `coding`. [tier: computational informational parse].

**Coordinate:** `17:43124027` on GRCh38 returned `valid=true` [tier: computational bounds check]. Naming normalization returned `chr17`; no liftover.

**Consent:** `clinical_return`; IRB active, DUA permits and deidentified all true. Permits clinical return: true [tier: synthetic manifest assertion; not independently verified].

**Runtime screening/ClinVar:** {"count": "2", "database": "clinvar", "ids": ["54425", "17662"], "provenance": "NCBI ClinVar via E-utilities", "query": "NM_007294.4:c.68_69del", "query_date": "2026-11-07T03:11:57Z"}; review status, significance and database release not returned. Search IDs are not confirmed matched variation records. [tier: community-curated ClinVar submission aggregate; expert-curated status not established]. Database content never changes status.

All supplied coordinates validated for GRCh38 bounds only; QC grades use exact input values and consent is manifest-only. Review hand-off carries warnings: wgs_mean_coverage=27.4, wgs_duplication_rate=18.6.

### GX-04 — `fail_qc`

**Variant:** `NM_000251.3:c.1A>G` (unchanged). Parse returns transcript `NM_000251.3`, change `c.1A>G`, type `coding`. [tier: computational informational parse].

**Coordinate:** `chr2:47403191` on GRCh38 returned `valid=true` [tier: computational bounds check].

**Consent:** `clinical_return`; IRB active, DUA permits and deidentified all true. Permits clinical return: true [tier: synthetic manifest assertion; not independently verified].

**Runtime screening/ClinVar:** ClinVar query failed: HTTP 429; API rate limit exceeded. No record content returned; not a negative finding or nomenclature rejection. [tier: community-curated source unavailable; no record evidence]. Database content never changes status.

All supplied coordinates validated for GRCh38 bounds only; QC grades use exact input values and consent is manifest-only. Failing wgs_titv_ratio=1.84 requires re-analysis or re-sequencing under local policy.

### GX-05 — `blocked`

**Variant:** `NM_000548.5:1832G>A` (unchanged). Parse returns transcript `NM_000548.5`, change `1832G>A`; no type returned. [tier: computational informational parse].

**Coordinate:** `chr16:2081000` on GRCh38 returned `valid=true` [tier: computational bounds check].

**Consent:** `clinical_return`; IRB active, DUA permits and deidentified all true. Permits clinical return: true [tier: synthetic manifest assertion; not independently verified].

**Runtime screening/ClinVar:** ClinVar query failed: HTTP 429; API rate limit exceeded. No record content returned; not a negative finding or nomenclature rejection. [tier: community-curated source unavailable; no record evidence]. Database content never changes status.

All supplied coordinates validated for GRCh38 bounds only; QC grades use exact input values and consent is manifest-only. Runtime screening cleared to a ClinVar rate-limit error, but mandatory structural policy blocks the unchanged string; the earlier alleged tool rejection was removed. D1 is extended to explicit policy rejection, not a fabricated runtime rejection.

**Policy/runtime discrepancy:** The former alleged tool rejection is not reproduced and has been removed. The observed lookup reached the tool; this does not establish structural HGVS compliance. Mandatory rule: HGVS structural nomenclature: `reference_seq:type.position_change`. The unchanged string lacks the type prefix. This is an explicit policy-based rejection, not a verbatim runtime rejection. D1 is extended to the mandatory policy block; a qualified reviewer must resolve the enforcement discrepancy. Do not adopt the critic’s suggested readiness upgrade or silently repair the string.

### GX-06 — `blocked`

**Variant:** `NM_004333.6:c.1799T>A` (unchanged). Parse returns transcript `NM_004333.6`, change `c.1799T>A`, type `coding`. [tier: computational informational parse].

**Coordinate:** `chr7:140753336` on GRCh38 returned `valid=true` [tier: computational bounds check].

**Consent:** `research_only`; IRB active, DUA permits and deidentified all true. Permits clinical return: false [tier: synthetic manifest assertion; not independently verified].

**Runtime screening/ClinVar:** ClinVar query failed: HTTP 429; API rate limit exceeded. No record content returned; not a negative finding or nomenclature rejection. [tier: community-curated source unavailable; no record evidence]. Database content never changes status.

All supplied coordinates validated for GRCh38 bounds only; QC grades use exact input values and consent is manifest-only. Clinical-return consent is absent; blocked regardless of passing QC.

## Limitations and permitted routing

Passing these supplied QC thresholds means fit for review only. GRCh38 checks establish bounds, not allele or transcript concordance. No rarity, gene–disease validity, pathogenicity, or absent-call claim is made; population and gene–disease lookups are outside this mechanical audit. Phenopacket v2.0 is inapplicable: no rare-disease cohort or phenotype-match output.

Rate-limit responses are unavailable evidence, not negative findings. Search IDs lack record-level verification, review status and database release. Identifying response fields are redacted in the evidence log. No unsupported runtime version or numeric confidence is reported. This is an LLM-authored TOKN genomics artifact, with tool versions unavailable. The full report’s deterministic artifact-review response is recorded in result.json; software checks do not establish biological validity or compliance.

Route GX-01/GX-02 to qualified review and GX-03 with both warnings (`wgs_mean_coverage=27.4`, `wgs_duplication_rate=18.6`). Route GX-04 for re-analysis/re-sequencing. Hold GX-05 for approved nomenclature correction and enforcement-discrepancy review; hold GX-06 unless valid clinical-return authorization is independently established.

## Response to critique

- **C1 — fixed:** Independently reran GX-05 validate, parse and ClinVar. Bounds valid; parser omits type; ClinVar reached tool but returned HTTP 429, not claimed rejection. Removed unsupported quote and not_reached claim. Kept blocked by mandatory structural policy; runtime cleared is explicit. Critic recommendation to upgrade cannot override policy.
- **C2 — fixed:** Removed unsupported Python/Windows envelope and its claims. Provenance is LLM-authored TOKN genomics revision; implementation versions unavailable.
- **C3 — fixed:** Replaced unsourced confidence with null to preserve field shape; no probability is estimated.
- **C4 — fixed:** Re-read all supplied inputs; evidence log contains exact input file content plus revision domain calls. Removed unverified historical artifact-review claims; actual final review recorded separately.
- **C5 — fixed:** Removed stale historical counts and blocked-checker language. Full final RESULT.md is rerun through review_artifact; exact scope, response and advisory adjudication stored in artifact_review and tool_calls.
- **C6 — fixed:** Verified six unique IDs and all fields. Retained items array under user same-shape requirement; prominently disclose keyed-object plan deviation to lab director in RESULT.md.
- **C7 — fixed:** No claim of variant-field acceptance remains. Revision uses schema-defined database/query only; prior field forwarding cannot be verified.

**Finding:** Mechanical statuses remain as listed; GX-05’s block now rests transparently on mandatory policy, not an unsupported runtime rejection.

**Supporting evidence:** Re-read synthetic inputs and rerun domain checks for every sample; exact evidence is in result.json. QC caveats and consent block reproduce; all GRCh38 bounds checks return valid [tier: synthetic observations and computational checks].

**Counterevidence/limitations:** GX-05 runtime clears despite malformed structure; ClinVar rate limiting and missing review status preclude record interpretation. Neither runtime clearance nor QC proves variant correctness.

**Unassessed checks:** Locus coverage/callability, contamination, identity, relatedness, ploidy, mosaicism, variant-class limitations, reference patch/allele concordance, transcript/genomic mapping, independent consent/IRB/DUA verification, and precision-medicine validation.

**Permitted next step and responsible reviewer:** Lab director/clinical sign-out with precision-medicine review owns final authorization, QC remediation, nomenclature-policy reconciliation and consent verification. This DRAFT cannot sign, diagnose, prescribe or return results.
