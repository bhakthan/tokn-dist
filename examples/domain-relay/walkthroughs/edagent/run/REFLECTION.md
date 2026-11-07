# REFLECTION — edagent relay: "PHI-screen and constrained-output intake QA of six synthetic ED cases"

All numbers below come from `TRACE.json`. All other claims come from `CAPABILITIES.md`, `PLAN.md`, `critique.json`, `decision.json`, `result.v1.json` and `result.json`.

## What each stage contributed

- **0-discover — claude-haiku-5-5** (25.9 s, 41,621 tokens, 8 tool calls: read_file 5, list_directory 2, write_file 1; 0 errors, 0 blocked). It wrote `CAPABILITIES.md`, which names the 4 applicable tools (`ed_triage`, `ed_phi_attest` with `sample_text` only, `ed_diagnosis_record`, `ed_clinician_review`) and records 9 gaps. Gap 3 flagged the `ICD10` system value on ED-04 before any tool had run. That item later became `code_rejected`.
- **1-plan — claude-opus-5-5** (90.6 s, 52,163 tokens, $0.5424, 8 tool calls, 0 errors, 0 blocked). It wrote `PLAN.md`: 18 conditional per-item calls plus one batch `ed_clinician_review` ("19 calls"), contingencies C1–C3, decision rules R1–R4 and 9 acceptance criteria. The plan did not call any edagent tool.
- **2-execute — Kimi-K3.1-Pro** (402.7 s, 728,981 tokens; domain calls: ed_triage 6, ed_phi_attest 6, ed_diagnosis_record 4, ed_clinician_review 1; 2 tool errors, 3 blocked/denied). It wrote `result.v1.json` and `RESULT.md`. The 17 domain calls match the plan exactly: 18 rows, minus the two diagnosis calls the plan skips for phi_blocked items, plus the review call. All six statuses were later reproduced unchanged.
- **3-critique — FW-GLM-5.3** (1,066.4 s, 1,201,775 tokens; ed_phi_attest 8, ed_diagnosis_record 4, ed_triage 6, ed_clinician_review 1, grep_search 6, read_file 13, write_file 4; 1 error, 2 blocked). It wrote `critique.json`, with 5 findings: C1 major, C2–C5 minor. No finding contested a status. Its finding text says "All six statuses reproduce exactly".
- **4-decide — Microsoft-Decision-1** (0.9 s, 2,693 input / 3 output tokens, no tools). It wrote `decision.json` with these scores: needs_revision 0.119, phi_case_admitted 0.00091, near_miss_code_accepted 0.00103. Routing was `light-revision`.
- **5-revise — gpt-6.1-sol** (268.3 s, 832,242 tokens, $0.2858; another 17 domain calls, update_plan 4; 1 error, 3 blocked). It wrote `result.json`. It reports C1, C2, C4 and C5 as fixed and C3 as rebutted, and changed no item status.

The whole relay used 2,859,478 tokens. The 3 stages that did execution or verification made 53 domain tool calls between them (17 + 19 + 17).

## What changed between the first and final answer

**Item statuses did not change.** ED-01 and ED-03 are `accepted`, ED-02 and ED-06 `phi_blocked`, and ED-04 and ED-05 `code_rejected` in both versions.

| Element | `result.v1.json` | `result.json` | Caused by |
|---|---|---|---|
| Human-review gate | "its output is quoted in RESULT.md" (no output in the JSON) | Embeds `{"clinician_reviewed": true, "phase": "RESULTS_REVIEW"}` verbatim | **C1** (major): the original failed PLAN criterion 6 |
| PHI gate name/label | "PHI gate (ed_phi_attest, gate of record)" — `pass` | "PHI control operation (not batch clearance; ED-02 and ED-06 blocked)" — `pass`, with the detail "Operational pass only" | **C2** |
| Terminology gate name/label | "Constrained-output guard on ed_diagnosis_record" — `pass` | "Terminology control operation (not batch clearance; ED-04 and ED-05 refused)" | **C2** |
| ED-01 triage evidence | `phase="TRIAGE"` stated without qualification | Raw JSON quoted, plus the note "TRIAGE independently reproduced in this revision's first triage call. Phase is a call-time observation…" | **C3**: rebutted, but annotated anyway |
| "synthetic was never passed" / "No input was corrected or retried" | Stated as fact in the gate details | Restated as "executor-attested; response fields do not echo arguments". A new limitation cites the six PHI gate events in the judgment JSONL, which carry no arguments | **C4** |
| `confidence` | `0.97`, scope not stated | `0.97`, with a new limitation scoping it to "the six intake classifications and their quoted PHI/diagnosis gate evidence" and listing what it does not cover | **C5** |
| Evidence format (all items) | Paraphrased key=value outputs | Raw JSON tool outputs, plus "Input references" pointing to `inputs/` files instead of repeating `sample_text` in full | Not tied to any finding. This came from the revision re-running every call |
| Limitations | 9 | 11: added a historical-procedure attestation and a confidence scope | C4, C5 |
| `critique_response` | `[]` | One entry for each of C1–C5 | Required by the revision stage |

The first answer was already correct on substance. Every change made the claims more precise, better scoped, or easier to verify from the structured file alone.

## Where TOKN's harness helped

- **`ed_phi_attest` (fail-closed PHI gate)** blocked ED-02 (`MRN 00482913`) and ED-06 (`triage.desk@sandbox-ed.example`) with `residual_phi=true, phi_cleared=false`. It did not block ED-03's look-alike lot string `404-17-882` (`residual_phi=false`). Three stages got the same result from 20 calls in total (6 + 8 + 6). `decision.json` scores phi_case_admitted at 0.00091.
- **`constrained_output` guard on `ed_diagnosis_record`** refused the near-miss codes with the verbatim text `"emitted 1 uncoded value(s): order=ICD10:J44.1"` and `order=ICD-10:R07.90`. It accepted `ICD-10:I21.4` and `ICD-10:K35.80`. No stage "corrected" a code, and near_miss_code_accepted scores 0.00103.
- **Status precedence and conditional calls:** in all three runs, `ed_diagnosis_record` was called exactly 4 times, never for the PHI-blocked items.
- **`ed_clinician_review` / `RequireHumanReviewBeforeClose`:** every stage recorded the batch as awaiting sign-off. No stage called `ed_disposition`.
- **Tool determinism made independent verification possible:** the critic and the reviser each re-ran the domain calls and got identical refusal strings. This is how C3 was settled.
- **The decision stage** cost 0.9 s and 2,696 tokens. It turned five findings into three calibrated probabilities and a `light-revision` route. It correctly saw that no status was at risk.

## Where TOKN fell short

- **Errors and denials are not explained.** TRACE.json records 4 tool errors (execute 2, critique 1, revise 1) and 8 blocked or denied calls (3, 2, 3) but does not say which tool or which input caused them. None of the result artifacts mentions them. The relay cannot learn from failures it does not identify, and this reflection cannot attribute them either.
- **Tool arguments are not logged.** C4 exists because `ed_phi_attest` does not echo its arguments. According to the revised limitations, the judgment JSONL records PHI gate events "but no arguments or diagnosis retry history". As a result, "synthetic never passed" and "no retries" can only be attested, not proven. This is a harness gap, not a model failure.
- **The encounter state machine is session-global and forward-only.** Six `ed_triage` calls each returned `opened=true`, but phases 2–6 came back `RESULTS_REVIEW`. C3 arose because the critic called `ed_triage` only after its session had already advanced the phase. Encounter isolation is still listed as "unverified" in the final answer. The tool set has no way to reset or scope encounters per item.
- **A critic probe violated the brief's prohibition.** The critic called `ed_phi_attest` with `synthetic: true` ("critic-side probe", C4), which brings its count to 8 instead of 6. `CAPABILITIES.md` says `synthetic` "must not" be passed, and `PLAN.md` says "Never pass `synthetic`… in any form". Nothing in the record shows the harness blocking that call, and the PHI gate is the gate of record. The probe was informative (the output does not change with the flag), but the guarantee depended on the model's discipline rather than on a gate.
- **Verification was expensive.** The critique used 1,201,775 tokens over 1,066.4 s, which is 42% of all tokens. The light revision used 832,242 tokens and re-ran all 17 domain calls even though decision.json put needs_revision at only 0.119 and no status changed. Most of that re-verification was needed only because `result.v1.json` paraphrased its evidence and the run had no argument log. The critic also wrote 4 files where its deliverables needed fewer.
- **CAPABILITIES gaps that no stage closed:** no case-bank write tool (gap 1), no terminology lookup (gap 2), chief complaints passed to `ed_triage` without a PHI screen (gap 4), and the unresolved `phi_input_screen` hook-scope ambiguity (carried as a limitation in both answers). "Terminology files are illustrative" (gap 8) means enrolment ≠ clinical correctness.
- **No tools were planned and then skipped.** The plan named 4 tools and all 4 were called as specified. Every other `ed_*` tool was excluded on purpose, so this was not a failure.

## Proposed /teach rule

`/teach In edagent batch runs, the Executor must embed every ed_* call's exact input arguments and raw verbatim output (including ed_clinician_review) directly in result.json, with ed_triage called first in a fresh session, so later stages verify from the artifact instead of re-running the domain tools.`

## Next run

1. **Plan/prompt:** add an acceptance criterion that `result.json` records an `args` and `raw_output` pair for each domain call, and that its gate labels describe per-item outcomes (for example "control operated; blocked ED-02, ED-06"). This would have prevented C1, C2 and C4 up front.
2. **Critic prompt:** forbid domain calls that the brief or plan prohibits (no `synthetic` flag, even as a probe). Allow re-running a domain call only for a specific suspect claim, in a fresh session, instead of re-running all 19 calls. Have the driver write the cause of every tool error and denial into TRACE.json.
3. **Roster/routing:** when decision.json gives needs_revision < 0.2 and no status-level probability is raised, the light-revision stage should edit the artifact only, without re-running the domain tools. Use a cheaper model for that stage than the one that spent 832,242 tokens here.
