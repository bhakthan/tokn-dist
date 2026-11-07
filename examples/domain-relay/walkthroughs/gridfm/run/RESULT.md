# GridFM final trust-disposition report

## Deployment evidence and confidence

Independent reruns selected GridSFM-Open for the full 3700-bus deployment (maxBuses=4000; scaleHeadroom=0.925). assess_ood was called without independently_verified and returned outOfDist=true, confidenceCap=0.3. Every applied confidence cap is 0.3; the cap does not change status. These are reduced-pocket dispositions, not full-network assurance.

list_verification_checks returned voltage_bound, generator_active_limit, generator_reactive_limit, thermal_limit, power_balance and flow_voltage_consistency. Tolerances: powerBalancePU=0.01, thermalSlack=0, consistencyPU=0.05. The stated balance/thermal tolerances match the brief.

## Independent-verifier results

| Item | Status | Disposition | Violations by kind | Residual (pu) | Speedup |
|---|---|---|---|---|---|
| PRED-A | operational_advisory | OPERATIONAL | none listed | 2.498001805406602e-16 | not run |
| PRED-B | hold_for_review | REVIEW | none listed | 2.498001805406602e-16 | not run |
| PRED-C | reject | REJECTED | power_balance: 1 | -0.1500000000000001 | not run |
| PRED-D | operational_advisory | OPERATIONAL | none listed | 2.498001805406602e-16 | not run |
| PRED-E | reject | WARM_START | thermal_limit: 1, voltage_bound: 1 | -1.942890293094024e-16 | 0.9130434782608696 |
| PRED-F | warm_start_only | WARM_START | generator_reactive_limit: 1 | 2.498001805406602e-16 | 1.75 |

The independent verifier found no listed violations for A, B or D; raw null is normalized to [] in JSON. A and D are advisory only: any actuation remains human-approved. B is held for review because disposition=REVIEW, despite phase=WARM_START. Status and timing eligibility use disposition under R3/Step 10, not phase. This is a fail-closed disagreement, not operational clearance.

D exact-limit input comparisons: B1 vMagPU=vMaxPU=1.05; G2 pgPU=pMaxPU=1.0; L23 sFlowPU=ratingPU=0.4. The rerun listed no violations, consistent with the strict-outside rule.

## Violation and timing evidence

- PRED-C: power_balance at system; verifier detail: power-balance residual -0.1500 pu exceeds tolerance 0.0100 (gen=1.8800 load=2.0000 losses=0.0300); returned margin=0.1400000000000001.
- PRED-E: thermal_limit at L13; verifier detail: |S|=1.0600 pu exceeds rating 1.0000; returned margin=0.06000000000000005.
- PRED-E: voltage_bound at B3; verifier detail: |V|=0.9300 pu below lower bound 0.9500; returned margin=0.019999999999999907.
- PRED-E timing rerun: baselineSeconds=4.2, warmSeconds=4.6, speedup=0.9130434782608696; within_expected=false. Point-of-use caveat: single synthetic sample, no variance estimate. seed_hurt_convergence=true.
- PRED-F: generator_reactive_limit at G2; verifier detail: Qg=0.6200 above Qmax=0.5000; returned margin=0.12.
- PRED-F timing rerun: baselineSeconds=6.3, warmSeconds=3.6, speedup=1.75; within_expected=true. Point-of-use caveat: single synthetic sample, no variance estimate. seed_hurt_convergence=false.

C is rejected for the independent power-balance breach under R1. E is rejected under R2 because its WARM_START seed was slower than cold start (speedup below 1.0). F meets the timing gate under R2 but remains a classical-solver seed only, not an operational advisory. A/B/C/D did not qualify for timing evaluation.

## Surrogate self-reports — not evidence

| Item | Self-reported feasibility | Self-reported confidence |
|---|---|---|
| PRED-A | feasible | 0.94 |
| PRED-B | infeasible | 0.41 |
| PRED-C | feasible | 0.97 |
| PRED-D | feasible | 0.88 |
| PRED-E | feasible | 0.9 |
| PRED-F | feasible | 0.86 |

C self-reported feasible at confidence 0.97, yet the independent verifier returned REJECTED. These raw self-scores never upgrade status and are not this report confidence; applied confidence remains capped at 0.3.

## Plan-defined gates

- G1 scale: pass for every item; no refusal or tier mismatch.
- G2 verification ran: pass for every item; valid dispositions do not imply all predictions are feasible.
- G3 trust: pass for A/D; not applicable to B/C/E/F.
- G4 timing: E fails; F passes; not applicable to A/B/C/D.
- G5 no false all-clear: no strict-outside discrepancy identified in exact inputs and reruns.
- G6 human approval: required operating condition; enforcement not technically tested.

## Additional reported checks and limitations

- OOD finding is non-blocking for status but caps confidence at 0.3. The 3-bus pocket is not certified representative of the 3700-bus network.
- Every item records flow_voltage_consistency=not_reported_by_verifier. Inputs have no admittance data and reruns expose no execution metadata. No run/not_run, pass, or unused-tolerance assertion is made.
- Native violation entries supply detail/margin rather than value/limit. Structured value/limit fields in JSON have explicit provenance from residual/tolerance or returned detail and exact input fields; empty raw null is normalized to [].
- Timing observations are single synthetic samples; no repeated-solve or variance evidence.
- screen_n1_contingencies not run: no contingency cases in inputs. No N-1 assurance.
- No classical AC-OPF re-solve or optimality proof, and no observed hook/slash-command enforcement.

## Response to critique

- **C1 — fixed:** Independently reran deployment and tolerance tools: GridSFM-Open, scaleHeadroom=0.925, OOD cap=0.3, powerBalancePU=0.01, thermalSlack=0, consistencyPU=0.05 reproduced. Added deployment, verification_checks, tools_not_run and full domain input ledger. assess_ood input omits independently_verified; six exact prediction objects included.
- **C2 — fixed:** All exact-object verifier reruns reproduce dispositions, residuals, caps and violation detail/margin. Added structured item fields and counts; normalized null to []. Added value/limit provenance rather than presenting these as native fields.
- **C3 — fixed:** Read all input self-reports and recorded feasibility/confidence with evidence=false. Exact-object rerun rejects PRED-C despite feasible/0.97 self-report.
- **C4 — fixed:** All reruns omit consistency execution metadata. Added not_reported_by_verifier per item. Did not adopt unsupported suggested assertion that consistencyPU=0.05 was unused; tool reports neither execution nor tolerance use.
- **C5 — fixed:** Independent B rerun confirms disposition=REVIEW, phase=WARM_START. Recorded every phase and B mismatch; R3/Step 10 use disposition, preserving hold_for_review and no timing evaluation.
- **C6 — fixed:** Added consolidated report table with independently reproduced dispositions, violation counts, residuals and timing speedups.
- **C7 — fixed:** Compared existing report with rerun rationale; rephrased unquoted safe-leaning wording as fail-closed disagreement. No prediction called safe.
- **C8 — fixed:** Verified PLAN defines G1-G6 only. Moved former G7-G10 content to additional reported checks; independently reproduced OOD/tolerance facts retained.
- **C9 — fixed:** Independent timing reruns reproduce E speedup=0.9130434782608696 and F=1.75. Added point-of-use within_expected, synthetic, single_sample, variance_not_estimated and slower-seed flags.
