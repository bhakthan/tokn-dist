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
inspect_netcdf, check_cf_compliance, download_era5, download_cmip6, regrid_dataset,
preprocess_dataset, compute_trend, climsci_optimal_fingerprint.

Per-item evidence the brief needs (family count, p, term, band check) is not produced by any tool.
It is computed by reasoning from ensemble_claims.json (see Gaps).

## Gates and rules that will constrain the answer

Physical band (brief rule 2, tolerance band, not plausible range; no unit conversion):
- tas: plausible 180–340 K; tolerance band 164–356 K
- pr: plausible −1e-6–0.02 kg m-2 s-1; tolerance band −0.0020011–0.0220001
- tos: plausible 270–315 K; tolerance band 265.5–319.5 K
- Check min and max against the tolerance band. Outside it = `implausible`.

Independence (rule 3): map each source_id through model_families. A model missing from the map is its own family.
Fewer than 5 independent families = `insufficient_ensemble`.
Members of one family always agree with each other.

Likelihood term (rule 4): p = agreeing families ÷ independent families. Never use the raw model count.
Take the first row where low ≤ p ≤ high:
- virtually certain: 0.99–1.00
- very likely: 0.90–0.99
- likely: 0.66–0.90
- about as likely as not: 0.33–0.66
- unlikely: 0.10–0.33

Status precedence (brief): `implausible` > `insufficient_ensemble` > `miscalibrated` > `supported`.
Vocabulary: use exactly one status per item.

Calibrated language (rule 5): write the term with its probability range, e.g. "likely (66–100 %)".
Avoid everyday certainty words.
Note: the DOMAIN-README gives AR6 probability ranges (e.g. "very likely = 90–100%", "virtually certain = 99–100%").
These are probability statements. The rule-4 bands above are family-fraction bands. Do not mix the two.

Affect tiers (DOMAIN-README): default max tier T1; query_cmip6_catalog is T0; compute_ensemble_stats is T1. validate_physical has no documented tier (assumed T0, read-only).
Nothing in this brief needs T2 or higher.

Data layer: all inputs are CMIP6 model output (L2). No observation or reanalysis data is mixed in.

Jet-colormap block: not applicable (no figure in this brief).

## Gaps

Brief asks for, and no tool covers:
1. Rule 4 likelihood derivation (p, IPCCLikelihoodScale table). No tool exposes this. Reasoning only.
2. Rule 3 family deduplication against the brief's model_families map. compute_ensemble_stats has a deduplicate flag, but it works on the live catalog, not on this input map. Counting is by reasoning.
3. Rule 5 calibrated-language check. The DOMAIN-README IPCC language validator is not in my tool list. review_artifact checks traceable numbers and citations, not likelihood wording. Manual scan only.
4. Sign agreement (agrees_with_claimed_sign). No tool computes it. It is taken as given from ensemble_claims.json.
5. Season (JJA, DJF, ANN), baseline (1995–2014) and future windows. No tool parameters for these. Use as labels only.
6. Region boxes (box-A..box-E). compute_ensemble_stats takes a region string, but its behaviour on these boxes is not verified.

Disagreements between DOMAIN-README and my tool list (tool list wins):
- README names `read_netcdf`, `write_netcdf`, `regrid_data`, `compute_trends`, `run_wrf`, `spatial_analysis`, `validate_provenance`. None are in my list.
- My list has `inspect_netcdf`, `regrid_dataset`, `compute_trend`, which are the nearest real names. Not the same tools.
- My list has `validate_physical`, `check_cf_compliance`, `review_artifact`, `climsci_optimal_fingerprint`, `preprocess_dataset`. The README does not document them.
- README slash commands, subagents, the 12-state machine, the IPCC validator and the Jet block are not visible as tools.
- tokn-self/introspect-slice.json lists no tools. It contains only mode, domain_modes and agent_run_flags. One flag entry is corrupted ("--no-ta[REDACTED]anchor"). It is not relevant here.

Unverified:
- Live tool liveness. The catalog tools were not called at this stage. Any Python, network or dependency error must be quoted per rule 1.
- validate_physical's internal band. It is documented as "10% tolerance", but the scout did not confirm that it matches the brief's tolerance band exactly. The next stage should compare its output against the band table above.
- The model_families map was said to be copied from validation.go. This was not verified.
- KIOST-ESM (CL-05) is absent from model_families, so rule 3 makes it its own family. Only this model in the claims is absent from the map.
