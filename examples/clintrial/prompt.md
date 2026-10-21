# Task: emulate a synthetic target trial (decision support only)

You are helping a research team specify and check an emulation of a
**synthetic** two-arm trial. Every input is fabricated. Do not treat any output
as clinical evidence or as a substitute for a randomised trial.

Inputs are in `inputs/`: `target-trial-spec.json` (the estimand and validation
plan) and `synthetic-cohort.json` (8 synthetic patients).

Do the following, in order:

1. Read `inputs/target-trial-spec.json`. Restate the estimand in your own words:
   population, intervention, comparator, outcome, time zero, and summary
   measure. If any element is missing or ambiguous, stop and say so.
2. Confirm that the cohort is synthetic and that no real patient data is
   present. Read `inputs/synthetic-cohort.json`.
3. Check the treatment assignment for confounding. Name the confounders the spec
   lists and say which of them are visibly unbalanced between arms.
4. Estimate the treatment effect on the outcome. Report the naive estimate and
   the estimate after adjusting for the listed confounders. Use calibrated
   language: state the uncertainty and that eight records are illustrative only.
5. Run the validation the spec asks for: a placebo (null) check and the
   negative-control outcome. Report the E-value against the threshold in the
   spec.
6. Prepare the evidence summary, but **do not emit it as a final artifact**. Stop
   before any emit step so a human reviewer can decide.

End with a list of the validation hooks that were exercised and a list of the
ones that were not. Make clear which parts were blocked for human review.
