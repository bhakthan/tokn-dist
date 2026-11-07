# REFLECTION — gridfm relay: trust disposition for GridSFM OPF predictions

Sources: `TRACE.json`, `CAPABILITIES.md`, `PLAN.md`, `critique.json`, `decision.json`, `result.v1.json`, `result.json`, plus the revision scripts left in the repo root (`revise_outputs.py`, `correct_revision.py`, `verify_revision.py`).

## What each stage contributed

- **0-discover, claude-haiku-5-5** (38.6 s, 65,583 tokens, 9 tool calls, 0 errors). Wrote `CAPABILITIES.md`. It mapped the six live gridfm tools to the inputs, marked `screen_n1_contingencies` as not applicable, and confirmed the tolerances (0.01 / 0 / 0.05) with one `list_verification_checks` call. It also predicted three things before any tool ran: the 3700/4000 = 92.5% OOD cap of 0.30, the missing admittance data, and the missing hooks and slash commands. It recorded 8 gaps.
- **1-plan, claude-opus-5-5** (83.5 s, 100,645 tokens, $0.7282, 10 tool calls, 0 domain tools). Wrote `PLAN.md`: 11 steps, decision rules R0–R7, gates G1–G6 and 7 acceptance criteria. Those criteria set out the per-item schema and the `deployment`, `verification_checks`, `tools_not_run` and `tool_calls` sections, and the Critic later held the result to them. It also flagged the PRED-D exact-at-limit cases.
- **2-execute, Kimi-K3.1-Pro** (status `failed`, exit_code 1, 548.6 s, tokens 0, final message `""`; retry also failed after 212.5 s with only 4 read/list calls). The trace shows `write_file` ×2 in the first attempt, and the first attempt also made every planned domain call: `list_verification_checks` 1, `select_model_tier` 1, `assess_ood` 1, `verify_surrogate_solution` 6, `evaluate_warm_start` 2. That attempt left `result.v1.json` with correct statuses for all six items (A, D `operational_advisory`; B `hold_for_review`; C, E `reject`; F `warm_start_only`). The result kept tool evidence as prose strings and did not follow the plan's schema.
- **3-critique, FW-GLM-5.3** (897.7 s, 1,031,476 tokens, 37 tool calls, 2 tool errors). Re-ran all 11 status-deciding domain calls and reproduced every number. Wrote `critique.json` with 9 findings (C1–C4 major, C5–C9 minor). None challenged a status. All 9 were schema, provenance or wording issues. The most valuable one was C5: on PRED-B the verifier returned `disposition=REVIEW` but `phase=WARM_START`.
- **4-decide, Microsoft-Decision-1** (1.4 s, 4,792 input / 3 output tokens, no tools). Wrote `decision.json` with `needs_revision` 0.060, `self_report_trusted` 0.026 and `uncapped_confidence` 0.798, and routed to `light-revision`.
- **5-revise, gpt-6.1-sol** (328.0 s, 963,831 tokens, $0.4175, 35 tool calls, 1 tool error, 4 blocked/denied; then a second successful pass of 241.7 s with 27 tool calls). Overwrote `result.json` and `RESULT.md`. The `critique_response` marks all of C1–C9 as `fixed`. The 11 domain calls were re-run in each pass and all six statuses stayed the same.

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

## Where TOKN fell short

- **The Executor failed twice.** `exit_code` 1, `tokens` 0, empty `final`, 548.6 s plus a 212.5 s retry that made only 4 read/list calls. The first attempt did write `result.v1.json`, so the harness logged a failure for a stage whose artifact was usable. The token accounting (0) and the missing final message mean the trace cannot show why it failed.
- **The Executor ignored the plan's output schema.** PLAN.md's acceptance criteria 1–7 listed every field, yet v1 put tool values in prose `evidence` strings. Findings C1–C4 and C9 (5 of the 9) only restate acceptance criteria. Nothing checked the result's structure before the Critic, so the most expensive stage (1,031,476 tokens, 897.7 s) went largely on schema conformance.
- **Expensive duplicate work.** The 11 domain calls were run 4 times: Execute, Critique, Revise pass 1 and Revise pass 2. Revise pass 1 had already succeeded (exit 0) when the retry ran them all again. Critique plus Revise used about 2.0 M tokens to produce zero status changes.
- **Tool errors and denials with no recorded cause.** Critique had 2 tool errors. Revise had 1 tool error and 4 blocked/denied calls, during a pass that also used `execute_domain_script` ×4 and `run_command` ×3. TRACE.json records only the counts, not which calls failed or why.
- **The Reviser left ad-hoc files behind.** `revise_outputs.py`, `correct_revision.py` and `verify_revision.py` remain in the repo root. `revise_outputs.py` writes the `deployment` block as hard-coded literals (0.925, 0.3, 4000) instead of copying them from the stored tool outputs. They match the tool outputs, but the provenance is a script constant. `correct_revision.py` patches PRED-C's violation kind to `power_balance` and replaces `| violation: 1 |` in RESULT.md. This suggests (ASSUMPTION, inferred from the script, not shown in TRACE) that the first scripted rewrite mislabelled the kind. Also, every violation's `value_limit_source` carries the same power-balance sentence, including the thermal, voltage and reactive ones.
- **The decision signal was never acted on.** `uncapped_confidence` was 0.798, which says the result probably describes something above the 0.30 cap. The router still chose `light-revision` (keyed on the low `needs_revision`). The Critic raised nothing about it, and `result.json` still carries `prediction_cap` 0.9 values and surrogate confidences up to 0.97 (marked `evidence: false`). No stage resolved whether these count as uncapped language.
- **Capability gaps recorded in CAPABILITIES.md and still open:**
  - The two DOMAIN-README hooks (block actuation on non-OPERATIONAL predictions; flag unbacked feasibility claims) and the `/gridfm` and `/tier` slash commands are not in the tool list, so human-gated actuation was only asserted (G6), never enforced.
  - No tool computes a per-prediction cap independent of the surrogate.
  - No tool certifies that the 3-bus pocket represents the 3700-bus network.
  - The verifier does not report whether `flow_voltage_consistency` ran. The Critic confirmed its output has no such field.
  - No tool estimates timing variance.
  - The verifier returns `detail`/`margin` rather than `value`/`limit`, and its `phase` disagrees with `disposition` on PRED-B (C5). Both are verifier-schema issues, not relay errors.
- **Planned but not called:** only `screen_n1_contingencies`, which was correctly excluded (no contingency cases). Every other planned domain call ran. `steps` is `null` for every stage in TRACE.json, so step efficiency cannot be measured.

## Proposed /teach rule

In gridfm, the Executor must write result.json directly in PLAN.md's acceptance-criteria schema (structured per-item fields incl. disposition, phase, surrogate_self_report with evidence:false, violations as [] not null, plus deployment, verification_checks, tools_not_run and a tool_calls input ledger) and must copy every number from a stored tool output, never from a hard-coded script literal.

## Next run

1. **Plan / harness:** add a schema check between Execute and Critique that validates `result.json` against PLAN.md's acceptance criteria. Then the Critic (and its ~1 M tokens) can spend its effort on physics and status questions instead of missing fields. Also record each tool error's and each blocked call's name and reason in TRACE.json, not just counts.
2. **Roster / routing:** swap or harden the Executor. Kimi-K3.1-Pro failed twice with 0 tokens reported. Don't retry a Revise pass that already exited 0, which would have saved the third full set of 11 domain calls and about 241.7 s. Let the Reviser reuse the Critic's re-run outputs unless the Critic disputes a number.
3. **Prompts:** feed `decision.json` into the Reviser prompt, and make any probability ≥ 0.5 (here `uncapped_confidence` 0.798) a required item to resolve explicitly, for example by stating whether `prediction_cap` 0.9 and surrogate confidences break the 0.30 cap. Also tell the Reviser to delete any temporary scripts it creates before it finishes.
