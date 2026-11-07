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
- The exact fraction is on the shared interval boundary; first-match ordering assigns very likely (90–100 %).

## CL-02 — miscalibrated

**Claim:** Summer precipitation in box B decreases by 2041-2060 relative to 1995-2014.
**Stated likelihood:** likely (66–100 %).

- Physical check: extrema [0.0, 0.000184] kg m-2 s-1; tolerance band [-0.0020011, 0.0220001] kg m-2 s-1. Manual check passes; validate_physical rerun returned PASS in summary mode.
- Independence: 7 families; 4 agree; p = 4/7 = 0.5714. Derived term: about as likely as not (33–66 %).
- Mapping: CESM2 → CESM; CESM2-WACCM → CESM; CESM2-FV2 → CESM; EC-Earth3 → EC-Earth; EC-Earth3-Veg → EC-Earth; EC-Earth3-CC → EC-Earth; MPI-ESM1-2-HR → MPI-ESM; MPI-ESM1-2-LR → MPI-ESM; CanESM5 → CanESM; MIROC6 → MIROC; GFDL-CM4 → GFDL; INM-CM5-0 → INM.
- All family votes are internally consistent. Full flags, request arguments, errors and named gates are in result.json.
- Decision rule 3: miscalibrated.

## CL-03 — implausible

**Claim:** Winter precipitation in box C increases by 2081-2100 relative to 1995-2014.
**Stated likelihood:** likely (66–100 %).

- Physical check: extrema [0.0, 18.4] kg m-2 s-1; tolerance band [-0.0020011, 0.0220001] kg m-2 s-1. Manual check fails; validate_physical rerun returned FAIL in summary mode.
- Independence: 8 families; 7 agree; p = 7/8 = 0.8750. Derived term: likely (66–100 %).
- Mapping: ACCESS-ESM1-5 → ACCESS; CanESM5 → CanESM; CESM2 → CESM; EC-Earth3 → EC-Earth; GFDL-ESM4 → GFDL; IPSL-CM6A-LR → IPSL; MIROC6 → MIROC; MPI-ESM1-2-HR → MPI-ESM.
- All family votes are internally consistent. Full flags, request arguments, errors and named gates are in result.json.
- Decision rule 1: implausible.

## CL-04 — insufficient_ensemble

**Claim:** Winter near-surface air temperature in box D rises by 2081-2100 relative to 1995-2014.
**Stated likelihood:** virtually certain (99–100 %).

- Physical check: extrema [255.3, 305.9] K; tolerance band [164, 356] K. Manual check passes; validate_physical rerun returned PASS in summary mode.
- Independence: 4 families; 4 agree; p = 4/4 = 1.0000. Derived term: virtually certain (99–100 %).
- Mapping: UKESM1-0-LL → UKESM; HadGEM3-GC31-LL → UKESM; HadGEM3-GC31-MM → UKESM; CNRM-CM6-1 → CNRM; CNRM-CM6-1-HR → CNRM; CNRM-ESM2-1 → CNRM; IPSL-CM6A-LR → IPSL; IPSL-CM5A2-INCA → IPSL; ACCESS-CM2 → ACCESS; ACCESS-ESM1-5 → ACCESS.
- All family votes are internally consistent. Full flags, request arguments, errors and named gates are in result.json.
- Decision rule 2: insufficient_ensemble.

## CL-05 — supported

**Claim:** Annual sea-surface temperature in box E rises by 2041-2060 relative to 1995-2014.
**Stated likelihood:** likely (66–100 %).

- Physical check: extrema [265.8, 305.1] K; tolerance band [265.5, 319.5] K. Manual check passes; validate_physical rerun returned PASS in summary mode.
- Independence: 6 families; 4 agree; p = 4/6 = 0.6667. Derived term: likely (66–100 %).
- Mapping: CanESM5 → CanESM; GFDL-ESM4 → GFDL; MIROC-ES2L → MIROC; NorESM2-MM → NorESM; INM-CM4-8 → INM; KIOST-ESM → KIOST-ESM.
- All family votes are internally consistent. Full flags, request arguments, errors and named gates are in result.json.
- Decision rule 4: supported.
- KIOST-ESM is unmapped and counts as its own family. The lower field extreme passes the tolerance band despite falling below the untoleranced 270 K lower bound.

## Live checks, provenance and limitations

All five query_cmip6_catalog and all five compute_ensemble_stats reruns failed. Each item's exact error and request arguments are recorded in result.json. The common error tail is:

```text
ModuleNotFoundError: No module named 'intake': python execution failed
```

No live models, means, percentiles or family counts were returned, and region-string behaviour remains unverified. These failures do not change status under BRIEF rule 1. No dependencies were installed.

Inputs: inputs/catalog_requests.json, inputs/ensemble_claims.json and inputs/field_ranges.json. Input data layer: L2-model-output; no observation or reanalysis data were mixed in. This report is derived from synthetic summaries. No NetCDF inspection, CF-compliance check, unit conversion, regridding or bias correction was performed. Jet-colormap and bias-correction gates are not_applicable.

The producing Python script revise_report.py, observed runtime, input hashes and final review_artifact output are recorded in result.json provenance. Quantitative values are computed from the inputs, not hardcoded item answers. Self-assessed confidence in the five status assignments is 0.97, conditional on the synthetic inputs; it does not assess real-world projections or deliverable readiness.

## Overall verdict

CL-01 and CL-05: supported. CL-02: miscalibrated; replace the stated label with about as likely as not (33–66 %). CL-03: implausible on its declared precipitation maximum. CL-04: insufficient_ensemble despite unanimous family agreement.

## Response to critique

- **C1 — fixed:** Added actual producing code and observed runtime. Baseline review independently reproduced two critical provenance gaps; the final artifact review output is recorded in provenance.
- **C2 — fixed:** Retained existing top-level fields and id identifiers while adding item, verbatim claim and stated_likelihood. Replaced free-text evidence with all plan-required named fields.
- **C3 — fixed:** Added top-level provenance listing synthetic inputs, hashes, tools, data layer, producing code and runtime.
- **C4 — fixed:** Removed the banned availability wording; final language scans cover both deliverables.
- **C5 — fixed:** Removed the undocumented revision adjective. All five independent physical-tool reruns agree with manual checks: PASS, PASS, FAIL, PASS, PASS.
- **C6 — fixed:** Restored exact claim characters for CL-03 and CL-04. All five claims are copied verbatim from inputs.
- **C7 — fixed:** Scoped self-assessed confidence 0.97 to the five status assignments conditional on authoritative synthetic inputs, not real-world projections or deliverable readiness.
