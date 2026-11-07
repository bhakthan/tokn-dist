# CAPABILITIES — SCOUT stage, genomics mode, run RUN-2026-11-SYN

Scope: read-only reconnaissance for items GX-01 to GX-06. No item is assessed here.

Inputs read: `BRIEF.md`, `inputs/run_qc.json`, `inputs/variants.json`, `inputs/consent_manifest.json`, `tokn-self/introspect-slice.json`, `tokn-self/DOMAIN-README.md`. The tool list visible to this session is treated as ground truth.

Input facts (recorded, not graded):
- Assembly is GRCh38 for all variants and QC values (`variants.json`, `run_qc.json`).
- Chromosome naming is not uniform: GX-01, GX-02, GX-04, GX-05, GX-06 are `chr`-prefixed; GX-03 is `17`.
- HGVS strings are verbatim as exported. GX-05 (`NM_000548.5:1832G>A`) has no HGVS type prefix (`c.`), and GX-01 (`c.5946del`) has no deleted sequence. Both are for the nomenclature gate, not for this scout.
- Boundary values present in the input: GX-02 `wgs_mean_coverage` 30.0 and `wgs_duplication_rate` 15.0; both sit exactly on inclusive thresholds.
- Consent manifest: GX-06 has `consent_level` `research_only`. The other five have `clinical_return`. All samples have `irb_active`, `dua_permits` and `deidentified` true under protocol IRB-SYN-0042.

## Domain tools that apply

| tool (exact name) | Items / input file it applies to | Input fields needed (present in `inputs/`?) |
|---|---|---|
| `genomic_coord_ops` (operation `validate`) | GX-01 to GX-06, coordinate check on GRCh38 | `chromosome`, `position`, `assembly` (all present in `variants.json`; assembly = GRCh38) |
| `genomic_coord_ops` (operation `normalize`, convention `chr`) | GX-03 only (chromosome `17` is not `chr`-prefixed) | `chromosome` = `17` (present) |
| `genomic_coord_ops` (operation `parse_hgvs`) | GX-01 to GX-06, transcript and change report | `notation` = `hgvs` string (present in `variants.json`) |
| `query_reference_db` (database `clinvar`) | GX-01 to GX-06, the ClinVar call the HGVS gate sits in front of | `query` = `hgvs` string (present). The brief also passes the string in a `variant` field; see Gaps. |
| `search_literature` | Not required by the brief. Needed only if a gene–disease statement is made. | Not applicable to these inputs as written |
| `run_bioinformatics_tool` | Not required. QC values come from `run_qc.json` and must not be re-derived. | Not applicable |
| `submit_hpc_job` | Not required. No pipeline re-run is in scope. | Not applicable |
| `review_artifact` (generic, not genomics-specific) | Optional check of the final `RESULT.md` for untraceable numbers | Prose plus declared values; the `traceable` list would come from `run_qc.json` |
| `grounding_check_citations` (generic) | Optional check of cited sources in `RESULT.md` | Answer text plus the tool outputs seen this turn |

Not present in the tool list, so not usable: a QC-grading tool, a consent or IRB verification tool, an HGVS nomenclature gate tool, a provenance tool, an ACMG classifier, a `/report` sign tool, a `/consent` command, a gnomAD query, a precmed tool.

## Gates and rules that will constrain the answer

QC thresholds (from `BRIEF.md`, inclusive, use `run_qc.json` values as given with no rounding or imputation):
- `wgs_mean_coverage` (higher is better): pass `≥ 30`; warning `≥ 20 and < 30`; fail `< 20`.
- `wgs_bases_gt10x` (higher is better): pass `≥ 95`; warning `≥ 90 and < 95`; fail `< 90`.
- `wgs_mapping_rate` (higher is better): pass `≥ 98`; warning `≥ 95 and < 98`; fail `< 95`.
- `wgs_duplication_rate` (lower is better): pass `≤ 15`; warning `> 15 and ≤ 25`; fail `> 25`.
- `wgs_titv_ratio` (higher is better): pass `≥ 2.0`; warning `≥ 1.9 and < 2.0`; fail `< 1.9`.

Status vocabulary and precedence: exactly one of `report_ready`, `report_with_caveats`, `fail_qc`, `blocked`. Precedence is `blocked` > `fail_qc` > `report_with_caveats` > `report_ready`. `report_with_caveats` must name every warning metric.

Blocking gates (any one forces `blocked`):
- HGVS nomenclature gate runs before `query_reference_db`. A rejection blocks the sample; quote the gate's reason. A network error is not a nomenclature rejection.
- Coordinate must validate on GRCh38.
- Consent must be `clinical_return`, with `irb_active`, `dua_permits` and `deidentified` all true, for clinical return.

Governance and language:
- This session does not classify, sign or return results. `report_ready` means ready for hand-off to clinical sign-out, not signed.
- Do not assert pathogenicity. Passing QC means fit for review, not that a call is correct.
- Affect tiers: `query_reference_db` T0, `genomic_coord_ops` T1, `run_bioinformatics_tool` and `submit_hpc_job` T2, draft report T3, sign and deliver T4 (not available in this session).
- Clinical intent: a readiness review for clinical return is clinical intent under the genomics rules. `GenomicsContext.ClinicalIntent = true` must be recorded with a written reason. Clinical handoff goes to precmed for VUS, PHI, CLIA and PGx validation. Do not sign inside genomics mode.
- Four-layer hierarchy, cite the tier on every evidence citation: expert-curated clinical > population frequency > community-curated > computational prediction. ClinVar is cited as a database query result; state its tier explicitly and do not treat it as expert-panel review without checking review status.
- Every number reported must come from a tool call or an input file. HGVS strings are reported verbatim.
- Phenopacket v2.0 compliance applies only to rare-disease cohort or phenotype-match output. Not triggered by this brief.

## Gaps

1. QC grading: no domain tool grades the five metrics. The grading is done by reasoning against the table above. Boundary cases are handled inclusively.
2. Consent, IRB and DUA: `/consent` is listed in the DOMAIN-README but is not in the tool list. Consent is checked by reading `consent_manifest.json` only, and no independent verification occurs.
3. HGVS nomenclature gate: no visible tool exposes it. Its verdict is known only from the runtime response to `query_reference_db`. If the gate does not run, the nomenclature status is unassessed, not passed.
4. `query_reference_db` schema: the schema exposes `database`, `query` and `max_results`. It has no `variant` parameter, although the brief asks for one. Log this discrepancy; do not invent the field. Also, the tool description does not list gnomAD, so allele-frequency claims have no visible tool.
5. `genomic_coord_ops` operations: the schema takes a free-text `operation`. `parse_hgvs` and `normalize` are used by the brief but not enumerated. Their support must be confirmed at runtime from the response.
6. ClinicalIntent and precmed handoff: no tool sets `GenomicsContext.ClinicalIntent`. The precmed mode is listed in the introspect slice, but no precmed tool is visible here. The handoff must be recorded by reasoning and left for review.
7. Signing and T4: no sign tool is available. This is correct by policy, but the README's T4 ceremony cannot be exercised.
8. README vs tool list: the README lists 10 slash commands, 8 playground modes, a 13-state workflow, 6 skills, and a `.nospace/genomics.yaml` threshold config. None of these appear as tools in the visible list. The README also says QC thresholds are configurable in `.nospace/genomics.yaml`, but the brief fixes them explicitly. Use the brief values. The five domain tools in the README match the visible list.
9. Introspect slice: `introspect-slice.json` lists the domain modes and run flags but no genomics tool or gate inventory. It cannot be used to confirm the tool set.
10. Input naming and format: `chromosome` is `17` for GX-03 (not prefixed), and the HGVS forms in GX-01 and GX-05 may not clear the nomenclature gate. These are for the gate to decide, not for this scout.
