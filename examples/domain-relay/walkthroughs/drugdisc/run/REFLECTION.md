# REFLECTION — drugdisc relay: "Hit-to-lead advancement triage for a kinase series"

## What changed between the first and final answer

Item statuses did not change. CMP-01 and CMP-02 are `advance` (D4), CMP-03 is `hold` (D1), CMP-04 is `reject` (D2), CMP-05 is `advance_with_caveats` (D3) and CMP-06 is `hold` (D1) in both versions. Everything that changed is about evidence, calibration and bookkeeping:

| Item / field | result.v1.json | result.json | Caused by |
|---|---|---|---|
| CMP-03 evidence | One logged hERG refusal; no reproduction note | Limitation added: "Reviser reproduced this exact complete-record gate response through the batch interface. Software rule reproduction is not independent biological validation." | C1 (rebutted rather than accepted: the reviser says the complete-record call reproduced the hold; the critic had only been able to make reduced-field calls) |
| CMP-06 evidence | Gate refusal plus ddi_analyze refusal | Says the CYP450 refusal was reproduced by both the complete-record gate and ddi_analyze | C2 (rebutted: "Gate-specific reproducibility gap closed") |
| `confidence` | `0.99` | `null`; limitation "Former 0.99 confidence withdrawn" | C3 |
| `run_disposition` | `answer`, `human_reviewer: null` | `defer`, with "Senior medicinal-chemistry reviewer, with safety-pharmacology and qualified DDI reviewers" | C3 |
| tool_log step 8 | Missing (log ended at step 7) | grounding_check_citations entry with raw output: 10 verified, 1 unchecked, 0 mismatched | C4 |
| Mistyped predict_admet call and stray execute_domain_script call | Mentioned in prose only | Arguments recovered from `.nospace/runs/...jsonl` and logged (SMILES `CC(=O)Nc1ccc(cc1)C(=O)NC2CCO`; `{"script":"noop"}`) | C5 |
| CMP-03 `raw_output` | Contained the executor-added `observed_wrapper` key | Annotation moved to a sibling field; every item's gate_response now carries the full wrapper | C6 |
| `gates` array | Used undefined `warn`/`fail`/`n/a`/`pass` labels; MW>1200 labelled `pass` | Only the brief's four tokens; scale defined in provenance; MW>1200 described as "Not triggered (supplied values)" | C7 |
| `gates.Ames` | "the other four scored responses" | "The other three scored responses (CMP-01, CMP-02, CMP-05)" | C8 |
| `unassessed_checks` | Only on CMP-01 and CMP-02 | On all six items | C9 |

**Open inconsistency.** The final answer contradicts itself on C5. `result.json` `critique_response` C5 and RESULT.md line 119 say the calls were "Recovered ... from the local executor run log". The C5 bullet inside the RESULT.md text stored in the step-8 grounding_check_citations log says the opposite: "original arguments, mistyped SMILES and raw responses were not retained in supplied artifacts".

`provenance.citation_check_scope` admits the order of events: the C5 prose was corrected after the citation check ran. That means the grounding check verified an earlier draft of RESULT.md, not the final one.

The `gates` array also now labels `PAINS`, `MW_gt_1200_validation` and `context_tools` as `hold`. These are item-status tokens applied to unassessed checks. This was the reviser's response to C7, and a reader could easily take those entries for item outcomes.

## Where TOKN's harness helped

- **`check_advancement_gate`** decided every status. It returned scored eight-criterion results for CMP-01, CMP-02, CMP-04 and CMP-05. It hard-blocked CMP-04 with `hard_blocked: true` and the note "HARD BLOCK: Ames-positive compounds cannot advance". It marked CMP-05 failures on MW 548.6 against "≤ 500 (Lipinski)" and cLogP 5.6 against "≤ 5". It also reported the QED ≥ 0.3 and LogS ≥ -6 thresholds that CAPABILITIES Gap 3 had listed as undefined. Those thresholds are what overturned the planner's CMP-02 expectation.
- **The drugdisc PreToolUse safety hooks** refused CMP-03 ("[DRUGDISC] hERG HARD BLOCK: predicted hERG IC50 = 0.620 μM < 1.00 μM") and CMP-06 ("[DRUGDISC] CYP450 HARD BLOCK: CYP3A4 IC50 0.450 μM < 1.00 μM ... no DDI analysis on file"). Neither hold was cleared by fabrication. Both `fabrication_check` and RESULT.md say no `mitigation`, `pains_justified` or `ddi_analysis_done: true` was added, and `decision.json` puts `positive_despite_block` at 0.020.
- **`ddi_analyze`** did not produce an analysis. It returned the same CYP450 refusal, and that gave the critic independent proof that the CYP hook exists (C2).
- **`abstention_gate`** worked as designed once it was used honestly. Called with 0.99 it returned `answer`. Called fail-closed (confidence omitted) it returned `defer` with the reason "no confidence estimate available and stakes are high — escalate rather than guess", and that drove the C3 fix.
- **`grounding_check_citations`** checked 11 citations in the revised RESULT.md: 10 verified, 1 unchecked because the quote was too short, 0 mismatched.
- **Microsoft-Decision-1** routed correctly to `full-revision` in 1.0 s on 3,263 tokens.

## Proposed /teach rule

In drugdisc, before any per-compound work, call compute_2d_properties and pains_filter once on a single SMILES as a dependency probe; if either returns a missing-module error, record PAINS/hERG/CYP/descriptor checks as "unassessed (dependency missing)", cap every positive status at advance_with_caveats with caveat pains_unassessed, and omit confidence in abstention_gate so it fails closed to defer.
