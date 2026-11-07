# Battery Passport pre-publication gate report

**Domain:** `batterypass`  
**Revision execution date (UTC):** 2026-11-06; clock independently observed at 23:58:15 UTC.

All four checks were independently rerun for every passport using the unchanged payloads and exact chemistry/application keys from `inputs/`. All six original statuses were reproduced.

> Statuses reflect TOKN batterypass gate projection of EU 2023/1542; not a legal certification or publication authorization. Synthetic data. Successful `Issues: null` results are normalized to empty arrays; complete raw responses retain null.

## Decision ledger

| Passport | Gate keys | Chemistry consistent | EU | CF | DD | Status | Basis |
|---|---|---|---|---|---|---|---|
| BP-01 | NMC / EV | true | Pass | Pass | Pass | compliant | R4 |
| BP-02 | LFP / EV | false | Pass* | Pass* | Pass* | inconsistent | R1 |
| BP-03 | NMC / Industrial | true | Pass | Pass | Pass | compliant | R4 |
| BP-04 | LFP / LMT | true | Pass | Fail | Pass | non_compliant | R3 |
| BP-05 | NMC / EV | true | Pass | Pass | Fail | non_compliant | R3 |
| BP-06 | NaIon / EV | true | Matrix absent | Pass | Pass | not_assessable | R2 |

Precedence: **inconsistent > not_assessable > non_compliant > compliant**. No fallback_R5 was needed. *BP-02's other results are recorded as required but cannot be trusted to establish compliance while its chemistry contradicts the cathode.

## Verbatim issues and errors

BP-01 and BP-03 returned no gate issues. BP-02 returned no EU, CF or DD issues, but failed chemistry consistency as recorded below. All issue-array strings are reproduced verbatim:

### BP-04 — CF methodology

> primaryDataShare=0.49 is below threshold 0.50

Complete gate error:

> cf_methodology gate blocked: primaryDataShare=0.49 is below threshold 0.50

### BP-05 — due diligence

> lastAuditDate="2024-03-02" is older than 365 days

Complete gate error:

> due_diligence gate blocked: lastAuditDate="2024-03-02" is older than 365 days

The rerun also returned this remediation verbatim:

> Set lastAuditDate to an ISO-8601 date within the last 365 days (e.g. "2026-11-06") and re-run the gate.

### BP-06 — EU matrix applicability

> chemistry+application combo NAION:EV not present in mandatory-field matrix; declare it in config or extend the matrix

Complete gate error:

> eu_battery_reg_2023_1542 gate blocked: chemistry+application combo NAION:EV not present in mandatory-field matrix; declare it in config or extend the matrix

This matrix gap makes BP-06 not_assessable, not a demonstrated substantive regulatory violation. Its other passing checks cannot substitute for the missing matrix entry.

### BP-02 — complete chemistry response

```json
{
  "result": {
    "canonical_chemistry": "LFP",
    "cathode_composition": "LiNi0.6Mn0.2Co0.2O2",
    "consistent": false,
    "declared_chemistry": "LFP",
    "error": "consistency mismatch declaredChemistry=LFP cathodeActiveMaterial=LiNi0.6Mn0.2Co0.2O2 reason=chemistry element mismatch: declared=\"LFP\" cathode=\"LiNi0.6Mn0.2Co0.2O2\" missing=Fe,P forbidden=Co,Ni,Mn",
    "error_detail": {
      "fieldA": "declaredChemistry",
      "fieldB": "cathodeActiveMaterial",
      "kind": "consistency_mismatch",
      "reason": "chemistry element mismatch: declared=\"LFP\" cathode=\"LiNi0.6Mn0.2Co0.2O2\" missing=Fe,P forbidden=Co,Ni,Mn",
      "valueA": "LFP",
      "valueB": "LiNi0.6Mn0.2Co0.2O2"
    },
    "forbidden": ["Co", "Ni", "Mn"],
    "missing": ["Fe", "P"],
    "reason": "chemistry element mismatch: declared=\"LFP\" cathode=\"LiNi0.6Mn0.2Co0.2O2\" missing=Fe,P forbidden=Co,Ni,Mn"
  },
  "tool": "bp_check_chemistry"
}
```

## Cross-check and concrete residual risks

The discrepancies arrays are empty for all six items. All study methods are PEFCR. Primary-data shares are respectively 0.62, 0.71, 0.50, 0.49, 0.58 and 0.66: BP-03 passes at the inclusive threshold; only BP-04 fails it.

Independently calculated audit ages on the observed date, 2026-11-06, are BP-01: 84 days; BP-02: 64; BP-03: 107; BP-04: 68; BP-05: 979; BP-06: 57. The first five material lists explicitly include lithium and contain policy URIs; only BP-05 exceeds 365 days. BP-06's material list names none of cobalt, lithium, nickel or natural graphite, although its formula contains Ni. These manual cross-checks agree with gate outcomes but do not replace them or establish general trigger-matching semantics.

**Concrete unassessed physical-consistency risk:** BP-04 combines batteryWeight `9.6`, ratedCapacity `87.0` and absoluteCarbonFootprint `5160.0`. The other five have weight `412.0` with the same capacity and absolute footprint. BP-03 is Industrial, not EV. This warrants review; the four requested checks do not establish physical plausibility or perform cross-category mass reconciliation.

For every draft, independent Decimal arithmetic verifies `59.2 × 87.0 = 5150.40`, versus reported absoluteCarbonFootprint `5160.0`: difference `9.60`, approximately `0.186%` of 5160.0. **ASSUMPTION needed to interpret this as a defect:** ratedCapacity must be a compatible energy denominator, and the equality must respect lifetime-energy normalization and rounding tolerances. The inputs do not supply ratedCapacity units, while the functional unit refers to energy over service life. The arithmetic difference is verified, but a dimensional inconsistency or regulatory defect is not established. No rerun CF issue addresses this difference; compliant does not imply complete numeric consistency.

## Overall verdict

BP-01 and BP-03 pass TOKN's configured gate projection. BP-04 and BP-05 are non_compliant; BP-02 is inconsistent; BP-06 is not_assessable until the NaIon/EV mandatory-field matrix is extended. No result is legal certification or publication authorization.

## Limitations and confidence

- Cross-category mass reconciliation and physical plausibility remain outside the tested four-gate scope; concrete suspect values are identified above.
- The DD gate exposes no reference-date field or exact reference instant. Its BP-05 remediation names `2026-11-06` as an example in-window date, corroborating the observed execution date without establishing an exact instant. Age findings are accepted verbatim.
- Free-text material-trigger matching is undocumented. No general parser semantics are inferred for synthetic graphite or formula-only Ni.
- Original relay fields are retained in JSON as requested, with all missing PLAN audit fields added. The populated critique_response is appropriate to this reviser stage.

**Status confidence: 0.95.** This estimate concerns only the six classifications under the configured tools, not legal compliance or complete physical/numeric correctness. Deliverable conformance is assessed separately through structural verification and exact input comparisons.

## Grounding summary

Twenty-four independent domain-tool calls support the classifications. `result.json` preserves exact arguments, including serialized payload bodies, and complete observed raw response wrappers for each check. Normalized issues, status bases, discrepancies arrays and unchanged-payload attestations are explicit. Independent Decimal and date calculations verify the numeric cross-checks. No input payload was edited.

## Response to critique

- **C1 — fixed:** Independently confirmed missing fields and added all PLAN audit fields, preserving the original relay fields under the user's same-shape instruction. All 24 reruns reproduce the statuses.
- **C2 — fixed:** Stored exact call arguments, including each serialized body, and complete raw responses. Parsed bodies are checked against the input payloads.
- **C3 — fixed:** BP-02 rerun confirmed the complete mismatch error and error_detail; both appear in JSON and the full chemistry response above.
- **C4 — fixed:** Populated critique_response with one resolved entry per finding at this reviser stage; it is no longer an empty placeholder. Existing relay fields remain.
- **C5 — fixed:** Reduced confidence to 0.95 and limited it to configured-gate statuses. Structural conformance is separately verified; legal and physical correctness are not claimed.
- **C6 — fixed:** Independently confirmed BP-05's remediation example date and acknowledged its corroboration, while distinguishing it from an exposed reference-date field or exact instant.
- **C7 — fixed:** Verified the input values and independently computed 5150.40 and the approximately 0.186% difference. Added concrete residual risks, qualified the dimensional-equality assumption, and corrected the critic's characterization of BP-03 as an EV pack. No gate status changed.
- **C8 — fixed:** Added discrepancies: [] to every item and explicitly stated that all arrays are empty. Independent threshold and audit-age comparisons agree with the reruns, subject to trigger semantics.
