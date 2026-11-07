# REFLECTION — gridfm relay: trust disposition for GridSFM OPF predictions

## What changed between the first and final answer

No status changed. All six items have the same status and `confidence` is 0.3 in both versions. Every change is structural, provenance or wording:

| Item / section | `result.v1.json` | `result.json` | Caused by |
|---|---|---|---|
| Top level | keys: domain, objective, items, gates, overall_verdict, confidence, limitations, critique_response (`[]`) | adds `deployment` (bus_count 3700, GridSFM-Open, maxBuses 4000, refused false, outOfDist true, ood_cap 0.3, tier_mismatch false), `verification_checks`, `tools_not_run` {screen_n1_contingencies: "no contingency cases in inputs"}, `tool_calls` (11 entries) | C1 |
| Every item | `id`, `status`, `rationale`, `evidence` strings, `tools_used` | adds `label`, `disposition`, `independently_feasible`, `power_balance_residual_pu`, `prediction_cap` (0.9/0.9/0.5/0.9/0.5/0.5), `confidence_cap_applied`, `decision_rule` (R4/R3/R1/R4/R2/R2), `discrepancies`, `violations` (null → `[]` for A/B/D), `violations_by_kind`, `violation_schema_note` | C2 |
| PRED-C, E, F violations | detail/margin only, inside prose | structured `{kind, element, value, limit, detail, margin, value_limit_source}`; for example C: power_balance, value −0.15, limit 0.01 | C2 (C's kind was corrected afterwards by `correct_revision.py`; see below) |
| Every item | no surrogate self-report; PRED-C's feasible/0.97 not recorded | `surrogate_self_report` {feasibility, confidence, evidence: false}; for example PRED-C feasible / 0.97 | C3 |
| Every item | flow-voltage consistency only in global G9 / limitation 3 | per-item `flow_voltage_consistency: not_reported_by_verifier` plus note. The Reviser did **not** adopt the Critic's suggested wording "consistencyPU tolerance 0.05 unused", because no tool shows it | C4 |
| Every item, PRED-B | `phase` not recorded | `phase` recorded; PRED-B shows `REVIEW` / `WARM_START`, and the mismatch is noted | C5 |
| `RESULT.md` | no six-row summary table | consolidated table added (per `critique_response`) | C6 |
| `RESULT.md` PRED-B | "safe-leaning disagreement" in the report's own voice | rephrased as fail-closed disagreement (per `critique_response`) | C7 |
| `gates` | G1–G10 | G1–G6 only; old G7–G10 moved to `additional_reported_checks` | C8 |
| PRED-E, PRED-F | no structured `warm_start`; single-sample caveat only in the global limitations | `warm_start` objects with `flags` {within_expected, seed_hurt_convergence, single_sample, synthetic, variance_not_estimated}; other items get `warm_start: null` + `not_run` | C9 (and C2) |

No change traces to `decision.json`'s `uncapped_confidence` = 0.798. No critique finding or revision addressed it (see below).

## Where TOKN's harness helped

- **`verify_surrogate_solution`** (6 calls in each of Execute, Critique and both Revise passes) did the core work. It returned `REJECTED` on PRED-C: power_balance residual −0.15 pu against tolerance 0.01, while the surrogate self-reported "feasible" at 0.97 confidence. That is the confident-but-infeasible case the domain exists to catch. It caught the PRED-E thermal (L13) and voltage (B3) violations and the PRED-F reactive-limit violation (G2 Qg 0.62 > 0.50). It also respected the brief's strict-outside rule on PRED-D's three exact-at-limit values (`violations=null`, so no R6 discrepancy). On PRED-B it put a surrogate that the physics checks passed into `REVIEW`, because the surrogate's own self-report disagreed.
- **`evaluate_warm_start`** (2 calls per stage) supplied the speedups: 0.9130434782608696 on PRED-E, with `withinExpected=false` and the note "seed hurt convergence", which forced `reject`; and 1.75 on PRED-F, inside the 1.5–2.0× band. No one divided by hand.
- **`select_model_tier` / `assess_ood`** turned the README's predicted OOD condition into a tool-backed cap: GridSFM-Open, scaleHeadroom 0.925, outOfDist true, confidenceCap 0.3. Both versions apply this 0.3 instead of the verifier's per-prediction caps of 0.9 / 0.5.
- **`list_verification_checks`** let Discover pin the tolerances before planning, and the Critic confirmed them.
- **Independent re-verification across stages.** The Critic and the Reviser both re-ran all 11 domain calls and reproduced every value. That makes the statuses reproducible across three different models.
- **The decision gate** (`self_report_trusted` 0.026, `needs_revision` 0.060) independently agreed that no status relied on the surrogate's self-report.

## Proposed /teach rule

In gridfm, the Executor must write result.json directly in PLAN.md's acceptance-criteria schema (structured per-item fields incl. disposition, phase, surrogate_self_report with evidence:false, violations as [] not null, plus deployment, verification_checks, tools_not_run and a tool_calls input ledger) and must copy every number from a stored tool output, never from a hard-coded script literal.
