# REFLECTION: batterypass relay, "Pre-publication gate check of six Battery Passport drafts"

Sources: `TRACE.json`, `CAPABILITIES.md`, `PLAN.md`, `critique.json`, `decision.json`, `result.v1.json`, `result.json`. `steps` is `null` for every stage in TRACE.json, so this file gives tool counts, tokens and durations, not step counts.

## What each stage contributed

- **0-discover, claude-haiku-5-5** (36.6 s, 47,511 tokens, 7 tool calls: read_file 5, list_directory 1, write_file 1; 0 errors). Wrote `CAPABILITIES.md`. It mapped the four gate tools to their input fields, quoted the status precedence and the 0.50 / 365-day rules, and listed 6 gaps. Those gaps were: no aggregation tool, an unknown matrix, an unknown reference date, undocumented material matching, no mass reconciliation, and an unverified mode. It also flagged conflicts between the README and the live tool list.
- **1-plan, claude-opus-5-5** (157.5 s, 152,623 tokens, $1.1161; read_file 6, list_directory 2, write_file 2, git_status 1; 0 errors, 1 blocked/denied). Wrote `PLAN.md`. It specified 24 calls with exact inputs and a decision table (R1–R5 plus the D2 "not in matrix" test). It also defined the `result.json` acceptance shape and listed hypotheses the Executor must not use as results.
- **2-execute, Kimi-K3.1-Pro** (430.5 s, 447,840 tokens; each of the 4 bp_check tools called 9×, so 36 gate calls; run_command 4, write_file 2; **23 tool errors, 13 blocked/denied**). Wrote `result.v1.json`. All six statuses were correct and were kept unchanged to the end: BP-01 compliant, BP-02 inconsistent, BP-03 compliant, BP-04 non_compliant, BP-05 non_compliant, BP-06 not_assessable. The file did not follow PLAN's schema, and it claimed confidence 0.99.
- **3-critique, FW-GLM-5.3** (289.2 s, 480,499 tokens; each bp_check tool 6×, so 24 gate calls; **20 tool errors, 3 blocked/denied**). Wrote `critique.json` with 8 findings: C1 blocking, C2 major, C3–C8 minor. It re-ran all 24 gate calls and reproduced every outcome. None of the findings challenged a status.
- **4-decide, Microsoft-Decision-1** (1.0 s; 2,390 input and 3 output tokens; no tools). Wrote `decision.json` with needs_revision = 0.0260, mislabelled_chemistry_passed = 0.0059 and overclaimed_compliance = 0.0028, but routed to `"full-revision"`.
- **5-revise, gpt-6.1-sol** (627.9 s, **832,115 tokens**, $0.3978; each bp_check tool 6×, so 24 gate calls; run_command 13, read_file 8; **19 tool errors, 8 blocked/denied**). Overwrote `result.json`, marking all of C1–C8 as `fixed`. All six statuses stayed the same, and confidence was lowered to 0.95.

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

## Where TOKN fell short

- **Tool error and denial noise is high and not explained.** TRACE.json records 23 errors and 13 blocked/denied calls (execute), 20 and 3 (critique), and 19 and 8 (revise), for 62 tool errors in total. At most 4 gate calls per 24-call pass could be explained by gates that block by design: BP-02 chemistry, BP-04 CF, BP-05 DD and BP-06 EU all return an `error` string in `result.json`. TRACE.json does not say which calls errored, so this reflection cannot tell real harness faults apart from gates working as designed. That gap in the trace is itself a shortcoming.
- **Wasted calls:** the Executor made 9 calls per gate tool, 36 in total, against PLAN's 24. That is 12 surplus calls, consistent with PLAN's "retry once" policy being used heavily.
- **Planned but never called:** `bp_load_payload` was listed in CAPABILITIES as an optional pre-check and was step (a) in PLAN's call template. No stage called it, even though PLAN warned that "the batterypass parse hooks reject" object bodies. No stage called `abstention_gate` or `grounding_check_citations` either, although the result makes calibrated confidence claims (0.99, then 0.95).
- **The decision stage disagreed with its own numbers.** `needs_revision` = 0.026, yet routing was `"full-revision"`. That triggered the most expensive stage (832,115 tokens, 627.9 s), which by its own account changed no status. The C1–C8 fixes were mostly structural, so a lighter revision would likely have done the job.
- **The Executor ignored the planned schema.** `result.v1.json` did not follow PLAN's acceptance shape (C1 blocking, C2 major). No harness check validated `result.json` against PLAN's schema before critique, so a mechanical problem used up a critique round.
- **The Reviser made an unrequested edit:** it rewrote `gates[].status` from `"fail"` to status-vocabulary values, which no finding asked for. It also kept a hybrid schema instead of C1's "exact shape".
- **Gaps CAPABILITIES recorded that stayed unresolved:**
  - No aggregation tool (Gap 1). The precedence rule was applied by reasoning in every stage.
  - No mass-reconciliation tool (Gap 5). BP-04's 9.6 kg weight with an EV-scale footprint was found only by the critic reading the inputs by hand (C7).
  - The DD gate exposes no reference-date field (Gap 3).
  - Free-text material matching is undocumented (Gap 4).
  - The batterypass mode was never verified (Gap 6).
  - README vs live tool list drift remains: `bp_refresh_model` vs `bp_refresh_snapshot`, 18 vs 23 tools, and no Turtle loader.
- **Trace completeness:** `steps` is `null` for all stages, and `cost_usd` is 0 for four stages, so step efficiency and cost cannot be compared.

## Proposed /teach rule

/teach In batterypass gate-check briefs, the Executor must write result.json in the exact PLAN acceptance shape on the first pass (checks.{chemistry,eu_compliance,cf_methodology,due_diligence} with called, input incl. serialized body, raw, issues, error; status_basis; all_issues; discrepancies:[]; payload_modified:false), and must treat a gate's "gate blocked" error string as a recorded failing result rather than a tool fault to retry.

## Next run

1. **Plan:** add a post-execute step that mechanically validates `result.json` against PLAN's acceptance shape and `inputs/` before critique. This should stop C1/C2/C8-type findings from using up the critique and revision rounds. Also make the `bp_load_payload` pre-check mandatory and drop its "optional" label, so serialization errors surface once and early instead of as retries.
2. **Roster / routing:** make DECIDE's routing follow its probabilities. With needs_revision ≈ 0.03 and no status-level findings, route to a light "evidence-only" revision instead of `full-revision`. Also tell the Reviser not to change fields that no finding names, such as `gates[].status`.
3. **Prompts and trace:** have the relay driver record a per-call error list with tool name and message, plus non-null `steps`, in TRACE.json. That would separate designed gate blocks from real harness errors and denials across the 62 errors. In Executor and Critic prompts, state that issues outside the gates' scope, such as BP-04's mass/footprint implausibility, must be listed as residual risks (CAPABILITIES Gap 5).
