# REFLECTION: batterypass relay, "Pre-publication gate check of six Battery Passport drafts"

## What changed between the first and final answer

None of the six `status` values changed between v1 and the final answer. All changes are to evidence, structure and how claims are calibrated.

| Change (v1 → final) | Caused by |
|---|---|
| Added top-level `brief`, `disclaimer`, `execution_date: "2026-11-06"` | C1 |
| Each item gained `chemistry`, `application`, `status_basis` (R4, R1, R4, R3, R3, R2), `checks`, `all_issues`, `payload_modified: false` | C1 |
| `checks.*.input` now holds the exact serialized `body` and the chemistry pair; `checks.*.raw` holds the full tool response | C2 |
| BP-02 chemistry check now keeps the full `error` string and the `error_detail` object (`kind: consistency_mismatch`, fieldA/fieldB, valueA/valueB) | C3 |
| `critique_response` went from `[]` to 8 entries (C1–C8). The critic's fix allowed this ("populated only after a critique has actually been returned") | C4 |
| `confidence` went from 0.99 to 0.95 and now applies only to "the six statuses under the configured gates" | C5 |
| The DD reference-date limitation now cites the BP-05 remediation example date 2026-11-06 as corroboration | C6 |
| New limitations name BP-04 (weight 9.6, capacity 87.0, footprint 5160.0) and 59.2 × 87.0 = 5150.40 vs 5160.0 (≈0.186%) | C7 |
| Every item now has an explicit `discrepancies: []` | C8 |
| `gates[].status` values went from `"fail"` to the status vocabulary (`inconsistent`, `not_assessable`, `non_compliant`, `non_compliant`) | **No finding asked for this.** It is an unrequested change by the Reviser. |
| v1 fields (`domain`, `objective`, `rationale`, `evidence`, `tools_used`, `gates`, `overall_verdict`) were kept alongside the PLAN shape | Partly against C1, which asked for "the exact shape". The Reviser's C1 note cites "the user instruction to keep the existing shape". |

## Where TOKN's harness helped

- **`bp_check_chemistry`** caught BP-02. It returned `consistent=false` with "declared=\"LFP\" cathode=\"LiNi0.6Mn0.2Co0.2O2\" missing=Fe,P forbidden=Co,Ni,Mn". Under R1 that made BP-02 `inconsistent`, even though its EU, CF and DD gates all passed. It also accepted NMC811/NMC622 as canonical `NMC` for BP-01, BP-03 and BP-05.
- **`bp_check_compliance`** (EU 2023/1542 matrix gate) caught BP-06: "chemistry+application combo NAION:EV not present in mandatory-field matrix; declare it in config or extend the matrix". This settled CAPABILITIES Gap 2, so matrix membership came from the tool and nobody had to guess it. It passed NMC×Industrial and LFP×LMT.
- **`bp_check_cf_methodology`** caught BP-04 ("primaryDataShare=0.49 is below threshold 0.50"). It passed BP-03 at exactly 0.50, which resolved the "equal passes" versus README "above threshold" wording conflict that CAPABILITIES had flagged.
- **`bp_check_due_diligence`** caught BP-05 ('lastAuditDate="2024-03-02" is older than 365 days'). Its remediation text named 2026-11-06, the only evidence anywhere of the gate's reference date (C6).
- **Reproducibility:** three separate models ran the same gates (Executor 36 calls, Critic 24, Reviser 24) and got identical outcomes. Because of that, the decision stage's low `mislabelled_chemistry_passed` (0.0059) and `overclaimed_compliance` (0.0028) are backed by repeated tool output, not by a single model's word.

## Proposed /teach rule

/teach In batterypass gate-check briefs, the Executor must write result.json in the exact PLAN acceptance shape on the first pass (checks.{chemistry,eu_compliance,cf_methodology,due_diligence} with called, input incl. serialized body, raw, issues, error; status_basis; all_issues; discrepancies:[]; payload_modified:false), and must treat a gate's "gate blocked" error string as a recorded failing result rather than a tool fault to retry.
