# Task: claims, underwriting-fairness and reserving review (synthetic)

You are the decision-support analyst for **Fictional Mutual Insurance Co. (synthetic)**. A licensed adjuster, a credentialed underwriter and a qualified actuary will make every final decision; your job is to give them a defensible, clause-cited, mechanically checked status for each item below, in decision-support language.

All data is synthetic. No real person, insurer, address or policy appears. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/policies.json` | Policy `POL-HO-100`: period, open-perils insuring agreement, limits (300,000 limit, 1,000 deductible, 1,500 jewelry sublimit), exclusions EX-1..EX-4 with the EX-2.1 ensuing-fire exception, notice and proof-of-loss conditions, and endorsements END-1 / END-2 |
| `demo-input/claims.json` | Claims CLM-2001..CLM-2007 (loss facts with fact ids, loss items, denial drafts) and two final-report drafts RPT-BAD / RPT-GOOD |
| `demo-input/underwriting.json` | Rating models UW-MODEL-A..C, cohort test UW-COHORT-D, decision batch UW-DECLINES-E |
| `demo-input/reserves.json` | Loss triangle RES-HO (with a naive LDF selection and a carried reserve), reserve figures RES-HO-FIG / RES-AUTO / RES-GL, ratio and credibility inputs |

## Items to assess

Claims `CLM-2001` … `CLM-2007`; reports `RPT-BAD`, `RPT-GOOD`; underwriting `UW-MODEL-A`, `UW-MODEL-B`, `UW-MODEL-C`, `UW-COHORT-D`, `UW-DECLINES-E`; reserving `RES-HO`, `RES-HO-FIG`, `RES-AUTO`, `RES-GL`.

## Status vocabulary (exactly one per item)

- Claims: `coverage_indicated`, `coverage_indicated_subject_to_conditions`, `coverage_not_indicated`, or `blocked` (a denial draft that cannot be issued because a reason lacks a clause or fact citation).
- Reports: `ready_for_peer_review` or `blocked`.
- Rating models: `cleared`, `review_required` (dominant proxy without justification and disparate-impact test), or `blocked` (prohibited attribute).
- Cohort tests: `four_fifths_pass` or `adverse_impact_indicated`. Decision batches: `reasons_complete` or `blocked`.
- Triangle: `below_range`, `within_range` or `above_range` for the carried reserve. Reserve figures: `documented`, `warning_no_range` or `blocked`.

## Rules

1. Use `ins_coverage_analyze` for every claim and cite the deciding clause and fact. Endorsements override the base form; exclusions are tested together with their exceptions.
2. Use `ins_payout_calc` for payable amounts: sublimits → coinsurance → deductible → limit.
3. Every denial goes through `ins_denial_explain`. A denial reason without a clause and a fact citation is blocked. Never write "the claim is denied"; write "a denial is indicated under clause X on fact Y, pending adjuster decision".
4. Screen rating models with `ins_rating_factor_screen`, test cohorts with `ins_disparate_impact` (four-fifths rule) and check declines with `ins_adverse_action_check`.
5. Reserve with `ins_chain_ladder` / `ins_reserve_range`, and pass reserve figures to `ins_reserve_report`. A figure without a method or assumptions is blocked; a point estimate without a range is a warning.
6. Never state a final coverage, legal or reserve-adequacy determination. Any final report passes `ins_report_finalize` with the decision-support disclaimer.
