# DRAFT — revised ADAS mechanical release-gate review

## Evidence and decision basis

Every supplied function record was freshly checked with `asil_decompose_verify`, `fmea_fta_engine`, and `safety_validation_report`. The explicit FN-LKA decomposition rejection and FN-APA V&V rejection were retried with identical complete inputs and repeated. Two separate negative probes contrasted ACC’s supplied no-error responses with rejection when only its child ASILs changed to A/A or only coverage changed to 94%.

**Basis: BRIEF’s rejection-based mechanical definitions.** Non-error decomposition and V&V responses expose action/instruction, not explicit positive verdict fields. The observed rejection channel is `error`. No-error is interpreted as mechanical acceptance under BRIEF, not proof of compliance or functional safety.

**Blocking clarification for human release:** PLAN R1/R3 really require explicit positive verdict fields in addition to no error. Contrary to critique C3’s quotation, literal PLAN does not equate no error alone with PASS. Literal PLAN would leave all five `decomposition_invalid`. The differentiated BRIEF classifications below do not satisfy that literal requirement. The safety manager must clarify or obtain structured verdicts before release use. Decision-1 requested full revision; its routing is not engineering evidence.

## Ordered outcomes

| Function | Decomposition | Hardware | V&V | First failing check | Status |
|---|---|---|---|---|---|
| FN-AEB | PASS under BRIEF | PASS | PASS under BRIEF | none | `release_candidate` |
| FN-LKA | FAIL | PASS | PASS under BRIEF | decomposition | `decomposition_invalid` |
| FN-ACC | PASS under BRIEF | PASS | PASS under BRIEF | none | `release_candidate` |
| FN-TJA | PASS under BRIEF | FAIL | PASS under BRIEF | hardware | `hw_metrics_fail` |
| FN-APA | PASS under BRIEF | PASS | FAIL | V&V | `vv_incomplete` |

All items are DRAFT. Later checks cannot override the first failure. Candidate counts describe mechanical classification, not authorized release or a complete PLAN-compliant evidence package.

## Hardware evidence

All five fresh hardware calls returned PMHF target **10 FIT**, SPFM target **99%**, LFM target **90%**. ACC (ASIL C) and APA (ASIL B) returned exactly the same targets as AEB/LKA/TJA (ASIL D). Programme-wide targets apply uniformly. PMHF passes at or below its target; SPFM and LFM pass at or above theirs.

The values below come from `inputs/fmeda_metrics.json`. The tool returned targets only, not recomputed metrics, detailed FMEA or a fault tree.

| Function | asil_req | PMHF FIT (≤10) | SPFM % (≥99) | LFM % (≥90) |
|---|---|---:|---:|---:|
| FN-AEB | D | 6.2 | 99.4 | 92.1 |
| FN-LKA | D | 3.1 | 99.7 | 96.0 |
| FN-ACC | C | 8.0 | 99.0 | 90.4 |
| FN-TJA | D | 7.5 | **98.9 — FAIL** | 91.0 |
| FN-APA | B | 4.0 | 99.2 | 93.5 |

ACC SPFM passes at equality. TJA SPFM is not rounded up.

## Per-function rationale and V&V

- **FN-AEB:** Supplied D → (B,C) decomposition returns no error. All hardware comparisons pass. Supplied V&V coverage 97.4%, zero open defects and zero open goals returns no error. BRIEF-based DRAFT candidate, pending contract clarification.
- **FN-LKA:** Supplied D → (B,A) is explicitly rejected: `child ASILs [B A] (sum 3) do not cover parent D (4) per ISO 26262-9 §5`. Identical retry repeats rejection. Hardware and V&V pass later checks but cannot override decomposition failure. V&V input is 99.1% coverage with zero defects/goals.
- **FN-ACC:** Supplied C → (B,A) returns no error. The generic instruction’s omission of this pair is not a verdict. All hardware comparisons pass, including SPFM 99.0%. Supplied V&V coverage exactly 95.0%, zero defects/goals returns no error. Negative probes reject C → (A,A) and coverage 94%; these demonstrate contrasting rejection behavior, not explicit positive fields. BRIEF-based DRAFT candidate, pending clarification.
- **FN-TJA:** Supplied D → (C,B) returns no error. Hardware first fails because SPFM 98.9% < 99%; PMHF and LFM pass. V&V coverage 96.8%, zero defects/goals returns no error but cannot override hardware failure.
- **FN-APA:** Supplied B → (A,A) returns no error; hardware passes. V&V rejects: `1 open defects remain — all safety-critical defects must be resolved before V&V completion`. Identical complete-input retry repeats rejection. Input coverage is 98.0%, defects_open is 1, and open_goals is 1. The open goal is a separate unresolved observation; the explicit rejection cites the defect, not the goal.

## Gate summary

| Gate | Independent check outcomes |
|---|---|
| G1 decomposition | 4 satisfied / 1 not satisfied — FN-LKA, under BRIEF |
| G2 hardware metrics | 4 satisfied / 1 not satisfied — FN-TJA |
| G3 V&V | 4 satisfied / 1 not satisfied — FN-APA, under BRIEF |
| G4 evidence integrity | **Not satisfied:** selective evidence, not a complete raw-response audit log |
| G5 human release | Not assessed; DRAFT only, clarification pending |
| HARA | Not assessed |
| Safety Concept | Not independently assessed beyond decomposition records |

Gate vocabulary is separately defined in JSON: satisfied, not satisfied, mixed, not assessed. A mixed summary does not mean all items fail. First-failure precedence still controls individual status.

## Discrepancies and limitations

1. **D1 — BRIEF versus literal PLAN/tool contract:** Non-error responses lack the explicit positive fields PLAN requires. This remains a blocking human clarification, not silently resolved by probes. BRIEF-based candidate classifications are conditional and do not establish literal PLAN compliance.
2. **D2 — Generic instruction versus actual outcome:** The four non-error decomposition calls return identical help text. ACC’s non-enumeration carries no verdict weight. Error responses observed here have null results, not the instruction text alleged in part of C6.
3. **D3 — Threshold wording:** Independently read `tokn-self/DOMAIN-README.md`: its domain-gate and Safety & Compliance sections specify PMHF <10 FIT for ASIL-D, versus BRIEF ≤ returned target 10 FIT. No supplied PMHF equals 10, so it changes none of these comparisons. BRIEF’s inclusive comparison governs.
4. **D4 — Audit-log completeness:** A comprehensive write containing the full raw response envelopes was blocked first by the command guard and then by the file-content scanner. Neither blocked write changed the files. These final files preserve selective evidence and structured outcomes, not the required complete tool_log. G4 and full PLAN schema completeness are therefore not satisfied. No scanner bypass was attempted.

Independence and DFA completion claims were taken as supplied; supporting artefacts were not independently evaluated. Evidence names and report paths are illustrative. Not assessed: HARA, Safety Concept, supporting DFA/independence evidence, SOTIF/ODD coverage, cybersecurity, underlying evidence-document quality, and the human Release gate.

## Grounding and confidence

**Assessed confidence: 0.85 in BRIEF-based mechanical classification**, not in functional safety, release readiness or audit-package completeness. Evidence consists of fresh supplied-record tool calls, identical rejection retries, contrasting negative probes, input metrics and returned targets. Identical retries establish repeatability, not independent engineering assurance. The previous unsupported JSON/decision-comparison validation claim is withdrawn. Structural verification of the revised files is distinct from domain certification.

Synthetic teaching data. All statuses are a DRAFT mechanical gate review for safety-manager review. Passing these gates is evidence for a release decision, not proof that a function is safe, and is not release approval. Resolve the contract conflict and incomplete raw audit log before release use.

## Response to critique

- **C1 — fixed:** Independently reran all supplied records and corrected BRIEF statuses: AEB/ACC release_candidate (DRAFT), LKA decomposition_invalid, TJA hw_metrics_fail, APA vv_incomplete. Updated gates and overall verdict; retained the literal PLAN conflict explicitly.
- **C2 — fixed, partial correction with remaining blocker:** Added structured item outcomes, first failures, draft flags, metrics, observations, targets provenance, discrepancies, not_assessed, counts and disclaimer while preserving original fields. Complete raw tool_log and full PLAN schema remain unavailable after scanner-blocked writes; not claimed fully resolved. G4 and overall verdict now expose the incompleteness.
- **C3 — fixed:** Recorded observed rejection channel and ran negative probes C → (A,A) and coverage 94%, contrasted with supplied ACC no-error results including coverage 95.0%. The critic misquotes PLAN’s actual explicit-positive-field rule; D1 retains that conflict for human clarification.
- **C4 — fixed:** Used the finding’s fallback: G4 marked not satisfied; selective quotations explicitly distinguished from full raw-log preservation. No false preservation claim.
- **C5 — fixed:** Removed unsupported prior validation claim, lowered assessed confidence to 0.85 for BRIEF classification, and exposed contract and completeness limitations. Retries described as repeatability only.
- **C6 — fixed:** Removed instruction enumeration as verdict evidence. Fresh calls independently show identical generic help on non-error responses and null error results; part of the critic’s error-string assertion is not reproduced.
- **C7 — fixed:** Recorded asil_req per function and confirmed identical targets across D/C/B calls. Independently verified README strict PMHF wording and recorded D3; no PMHF boundary input exists.
- **C8 — fixed:** Added not_assessed and observations, including APA open_goals=1 separately from its explicit defect rejection and unverified DFA assertions.
- **C9 — fixed:** Replaced blanket gate failures with counts: G1/G2/G3 each four satisfied, one not satisfied, respectively LKA/TJA/APA. First-failure precedence retained.
- **C10 — fixed:** Performed APA V&V identical complete-input retry; repeated the one-open-defect rejection. LKA decomposition was also retried. Evidence is selectively recorded, not a full audit log.
- **C11 — fixed:** Current REVISER instructions explicitly require critique_response; populated once per finding. Gate vocabulary separately defined; only the four permitted item statuses used.
