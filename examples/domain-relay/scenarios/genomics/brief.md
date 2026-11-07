# Brief — WGS run QC and report-readiness review

You are the QA lead for a clinical sequencing lab. Six de-identified whole-genome samples from run `RUN-2026-11-SYN` each have one candidate variant queued for a report. Before anything goes to sign-out, the lab director needs a mechanical readiness decision for every sample, covering coverage and call quality, variant nomenclature and coordinates, and consent.

The data is synthetic but realistic. Everything you need is in `inputs/`:

| File | Contents |
|---|---|
| `inputs/run_qc.json` | Per-sample WGS QC metrics: `wgs_mean_coverage` (x), `wgs_bases_gt10x` (%), `wgs_mapping_rate` (%), `wgs_duplication_rate` (%), `wgs_titv_ratio` |
| `inputs/variants.json` | Per-sample candidate variant: `hgvs`, `chromosome`, `position` (GRCh38), exactly as exported by the pipeline |
| `inputs/consent_manifest.json` | Per-sample `consent_level`, `irb_active`, `dua_permits`, `deidentified` |

## Items to assess

`GX-01`, `GX-02`, `GX-03`, `GX-04`, `GX-05`, `GX-06`

## Status vocabulary (use exactly one per item)

- `report_ready`: every QC metric is `pass`, the coordinate validates, the HGVS string clears the nomenclature gate, and consent permits clinical return.
- `report_with_caveats`: same as `report_ready`, except at least one QC metric is `warning` and none is `fail`. Name every warning metric.
- `fail_qc`: at least one QC metric is `fail`. The sample needs re-sequencing or re-analysis.
- `blocked`: a gate stops the sample regardless of its QC numbers: the HGVS nomenclature gate rejects the variant string, the coordinate does not validate on GRCh38, or consent, IRB, DUA or de-identification does not permit a clinical return.

Precedence when more than one applies: `blocked` > `fail_qc` > `report_with_caveats` > `report_ready`.

## QC rules (the genomics plug's WGS thresholds)

Each metric is graded `pass`, `warning` or `fail`. Thresholds are **inclusive**: a value exactly on the pass threshold passes.

| Metric | Direction | Pass | Warning | Fail |
|---|---|---|---|---|
| `wgs_mean_coverage` | higher is better | ≥ 30 | ≥ 20 and < 30 | < 20 |
| `wgs_bases_gt10x` | higher is better | ≥ 95 | ≥ 90 and < 95 | < 90 |
| `wgs_mapping_rate` | higher is better | ≥ 98 | ≥ 95 and < 98 | < 95 |
| `wgs_duplication_rate` | lower is better | ≤ 15 | > 15 and ≤ 25 | > 25 |
| `wgs_titv_ratio` | higher is better | ≥ 2.0 | ≥ 1.9 and < 2.0 | < 1.9 |

Use the values in `run_qc.json` exactly as given. Do not round, impute or re-derive them.

## Rules

1. For each sample, call `genomic_coord_ops` with `{"operation": "validate", "chromosome": ..., "position": ..., "assembly": "GRCh38"}`. If a chromosome is not `chr`-prefixed, also call it with `{"operation": "normalize", "chromosome": ..., "convention": "chr"}` and report the normalized name.
2. For each sample, call `genomic_coord_ops` with `{"operation": "parse_hgvs", "notation": <hgvs>}` to report transcript and change.
3. For each sample, call `query_reference_db` with `{"database": "clinvar", "query": <hgvs>, "variant": <hgvs>}`, passing the HGVS string unchanged in the `variant` field. The genomics HGVS nomenclature gate runs before this tool. If the gate rejects the call, the sample is `blocked`; quote the gate's reason. If the call goes through, the ClinVar result does not change the status, and a network error is not a nomenclature rejection; report it as such.
4. Check consent from `consent_manifest.json`. Analysis toward a clinical report must not proceed if any consent verification fails.
5. This genomics session does not classify, sign or return results. `report_ready` means ready for hand-off to clinical sign-out, not signed. Do not assert pathogenicity.
6. Every number you report must come from a tool call or the input files. Use calibrated language: passing QC means the data is fit for review, not that a call is correct.

## Deliverable

`result.json` and `RESULT.md`, as described in your stage instructions.
