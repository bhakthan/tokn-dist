# PLAN — pre-publication gate check of six Battery Passport drafts (batterypass)

Planner stage. This file is the only output of this stage. Nothing has been executed.
Sources read: `BRIEF.md`, `CAPABILITIES.md`, `inputs/passports.json`, `inputs/chemistry_declarations.json`, `tokn-self/DOMAIN-README.md`, `tokn-self/introspect-slice.json`.

## Objective

Run the four batterypass checks (`bp_check_compliance`, `bp_check_cf_methodology`, `bp_check_due_diligence`, `bp_check_chemistry`) on each of BP-01 to BP-06, then record exactly one status per passport (`compliant` | `non_compliant` | `inconsistent` | `not_assessable`) in `result.json` and `RESULT.md`, using the mechanical rules below.

## Ground rules for the Executor (apply to every step)

- **Do not edit any payload** (BRIEF rule 6). This includes reordering keys, fixing values, or replacing `NMC` with `NMC811`.
- **`body` serialization.** `body` is the passport's `payload` object from `inputs/passports.json`, serialized to a JSON **string** (for example `json.dumps(payload)`). Do not pass the object itself, because the batterypass parse hooks reject it. Do not include the outer `id`/`chemistry`/`application` wrapper.
- **`chemistry` / `application`.** Pass the top-level `chemistry` and `application` fields of the passport entry, character for character. Never use `Labels.declaredChemistry` or `MaterialComposition.batteryChemistry` such as `NMC811` or `NMC622`.
- **Quote every issue string verbatim**, and keep the full raw tool response for each call.
- **Run every call for every passport**, even after a higher-precedence status is already determined (BRIEF rule 1). That is 6 x 4 = 24 gate/chemistry calls, plus 6 optional parse pre-checks.
- **Retry policy.** If a call fails with a transport, tool, or parse error rather than returning a result, check that `body` is a string and retry once with an unchanged payload. If it still fails, record the error verbatim and apply the "errored" rows of the Decision rules.
- Use only the four gate tools in Steps 1-6, plus optional `bp_load_payload`. Do **not** call `bp_advance_lifecycle`, `bp_transition_state`, or any generator. No publish or state change is requested.

## Steps

Steps 1-6 use the same five calls per passport (a-e). The inputs listed for each step are copied from `inputs/`.

**Call template for passport X:**
- (a) *optional pre-check* `bp_load_payload` with `body` = stringified `payload` of X. **Status effect:** none directly. If parsing fails, the serialization is wrong. Fix the serialization only, not the payload.
- (b) `bp_check_compliance` with `body` = stringified `payload`, `chemistry` = X.chemistry, `application` = X.application. **Status effect:** non-empty `Issues` -> candidate `non_compliant`. An issue or error saying the combination is not in the matrix (signal D2) -> candidate `not_assessable`.
- (c) `bp_check_cf_methodology` with `body` = stringified `payload`. **Status effect:** non-empty `Issues` -> candidate `non_compliant`.
- (d) `bp_check_due_diligence` with `body` = stringified `payload`. **Status effect:** non-empty `Issues` -> candidate `non_compliant`.
- (e) `bp_check_chemistry` with `declared_chemistry` and `cathode_composition` taken from the X entry of `inputs/chemistry_declarations.json`. **Status effect:** `consistent: false` -> `inconsistent`, which overrides everything else.

1. **BP-01** (covers item BP-01)
   - (b) `bp_check_compliance`: `chemistry` = `"NMC"`, `application` = `"EV"`, `body` = stringified BP-01 payload.
   - (c) `bp_check_cf_methodology`: `body` = stringified BP-01 payload. Relevant payload values: `carbonFootprintStudyMethod` = `"PEFCR"`, `primaryDataShare` = `0.62`.
   - (d) `bp_check_due_diligence`: `body` = stringified BP-01 payload. Relevant values: materials include `"lithium hexafluorophosphate electrolyte"` and `"nickel manganese cobalt oxide cathode"`, `dueDiligencePolicyURI` = `"https://example.org/synthetic/dd-policy"`, `lastAuditDate` = `"2026-08-14"`.
   - (e) `bp_check_chemistry`: `declared_chemistry` = `"NMC811"`, `cathode_composition` = `"LiNi0.8Mn0.1Co0.1O2"`.

2. **BP-02** (covers item BP-02)
   - (b) `bp_check_compliance`: `chemistry` = `"LFP"`, `application` = `"EV"`, `body` = stringified BP-02 payload.
   - (c) `bp_check_cf_methodology`: `body` = stringified BP-02 payload (`PEFCR`, `primaryDataShare` = `0.71`).
   - (d) `bp_check_due_diligence`: `body` = stringified BP-02 payload (lithium materials, policy URI present, `lastAuditDate` = `"2026-09-03"`).
   - (e) `bp_check_chemistry`: `declared_chemistry` = `"LFP"`, `cathode_composition` = `"LiNi0.6Mn0.2Co0.2O2"`.

3. **BP-03** (covers item BP-03)
   - (b) `bp_check_compliance`: `chemistry` = `"NMC"`, `application` = `"Industrial"`, `body` = stringified BP-03 payload.
   - (c) `bp_check_cf_methodology`: `body` = stringified BP-03 payload (`PEFCR`, `primaryDataShare` = `0.5`, exactly the threshold; per BRIEF rule 4 this should pass).
   - (d) `bp_check_due_diligence`: `body` = stringified BP-03 payload (lithium/nickel/cobalt materials, policy URI present, `lastAuditDate` = `"2026-07-22"`).
   - (e) `bp_check_chemistry`: `declared_chemistry` = `"NMC622"`, `cathode_composition` = `"LiNi0.6Mn0.2Co0.2O2"`.

4. **BP-04** (covers item BP-04)
   - (b) `bp_check_compliance`: `chemistry` = `"LFP"`, `application` = `"LMT"`, `body` = stringified BP-04 payload.
   - (c) `bp_check_cf_methodology`: `body` = stringified BP-04 payload (`PEFCR`, `primaryDataShare` = `0.49`, below the 0.50 threshold).
   - (d) `bp_check_due_diligence`: `body` = stringified BP-04 payload (lithium materials, policy URI present, `lastAuditDate` = `"2026-08-30"`).
   - (e) `bp_check_chemistry`: `declared_chemistry` = `"LFP"`, `cathode_composition` = `"LiFePO4"`.

5. **BP-05** (covers item BP-05)
   - (b) `bp_check_compliance`: `chemistry` = `"NMC"`, `application` = `"EV"`, `body` = stringified BP-05 payload.
   - (c) `bp_check_cf_methodology`: `body` = stringified BP-05 payload (`PEFCR`, `primaryDataShare` = `0.58`).
   - (d) `bp_check_due_diligence`: `body` = stringified BP-05 payload (lithium/nickel/cobalt materials, policy URI present, `lastAuditDate` = `"2024-03-02"`).
   - (e) `bp_check_chemistry`: `declared_chemistry` = `"NMC811"`, `cathode_composition` = `"LiNi0.8Mn0.1Co0.1O2"`.

6. **BP-06** (covers item BP-06)
   - (b) `bp_check_compliance`: `chemistry` = `"NaIon"`, `application` = `"EV"`, `body` = stringified BP-06 payload.
   - (c) `bp_check_cf_methodology`: `body` = stringified BP-06 payload (`PEFCR`, `primaryDataShare` = `0.66`).
   - (d) `bp_check_due_diligence`: `body` = stringified BP-06 payload. Materials are `"sodium hexafluorophosphate electrolyte"`, `"layered sodium transition-metal oxide cathode"` and `"hard carbon anode"`; `cathodeActiveMaterial` contains `Ni` but not the word "nickel"; `lastAuditDate` = `"2026-09-10"`.
   - (e) `bp_check_chemistry`: `declared_chemistry` = `"NaIon"`, `cathode_composition` = `"NaNi0.33Fe0.33Mn0.33O2"`.

7. **Aggregate (all items; reasoning step, no domain tool exists for it, see CAPABILITIES Gap 1).** Apply the Decision rules to the 24 recorded results. Fill the per-gate pass/fail fields and the final status for each item.

8. **Discrepancy cross-check (all items; reasoning only, never changes a status).** For each passport, compare the gate result against BRIEF rules 4 and 5 applied by hand to the payload values listed above. Rule 4: method in {PEFCR, ISO14067, GHGProtocol} and `primaryDataShare` >= 0.50. Rule 5: trigger material present -> URI present and audit within 365 days of the execution date. If the gate result and the hand evaluation disagree, add a `discrepancies` entry. An example would be the CF gate flagging BP-03's `0.5`. The status still follows the gate's `Issues` (BRIEF rule 3).

9. **Write deliverables** `result.json` and `RESULT.md` (see Acceptance criteria). Writing them is a later stage's job. Nothing else is written.

### Hypotheses the Executor must NOT use as results

These are planner observations from reading the inputs. They are only for spotting anomalies. Statuses come from tool output only.
- BP-02 declares `LFP` but its cathode `LiNi0.6Mn0.2Co0.2O2` is an NMC formula, so `consistent: false` is likely.
- Matrix membership of `NMC x Industrial`, `LFP x LMT` and `NaIon x EV` is unknown. Only `bp_check_compliance` output decides it (CAPABILITIES Gap 2).
- BP-04's `0.49` is below the CF threshold. BP-05's audit date `2024-03-02` is likely outside a 365-day window.
- The gate's reference date ("today") is unknown (CAPABILITIES Gap 3). Audit dates in 2026 may be future-dated relative to the gate's clock. Report any such issue verbatim and do not reinterpret it.
- How the DD gate matches trigger materials in free text is undocumented (CAPABILITIES Gap 4). For example, it is unknown whether "synthetic graphite" counts as graphite, or whether `Ni` in BP-06's cathode counts as nickel. Use the tool result as given.

## Decision rules

Definitions (apply literally):
- **Issues list of a gate** = the `Issues` array in the tool result (also accept lowercase `issues`). Treat `null`/missing as empty **only if** the call returned a result object without error.
- **Gate passes** iff the call returned a result and its Issues list has length 0. **Gate fails** iff the Issues list has length >= 1. **Gate errored** iff the call returned no result object after one retry.
- **Chemistry consistent** iff `bp_check_chemistry` returned the boolean `consistent: true`. **Chemistry inconsistent** iff it returned `consistent: false`. Any other outcome (error, missing field, non-boolean) = **chemistry undetermined**.
- **Not-in-matrix signal (D2)**: the `bp_check_compliance` response says the chemistry+application combination is absent from the mandatory-field matrix, either in an Issues string or in an error message. Test it mechanically: some Issues string or error text, lowercased, contains `matrix`, **or** contains the chemistry value and the application value together with one of `unknown`, `unsupported`, `not found`, `no entry`, `not in`. Record the exact string that triggered D2.

Apply this ordered table per passport. The first matching row gives the status:

| # | Condition | Status |
|---|---|---|
| R1 | Chemistry inconsistent (`consistent: false`) | `inconsistent` |
| R2 | Not R1, and D2 is true for `bp_check_compliance` | `not_assessable` |
| R3 | Chemistry consistent, D2 false, and at least one of {EU, CF, DD} **fails** (>= 1 issue) | `non_compliant` |
| R4 | Chemistry consistent, D2 false, and EU, CF and DD all **pass** | `compliant` |
| R5 | None of the above. This covers chemistry undetermined, or any of EU/CF/DD errored with no failing gate. | `not_assessable`, with `status_basis` = `fallback_R5` and the reason stated. This is a planner fallback because the BRIEF defines no status for tool failure. It must be flagged as such in RESULT.md and never presented as a matrix gap. |

Notes:
- R3 needs **consistent: true**. Undetermined chemistry with a failing gate falls to R5, because BRIEF defines `non_compliant` as "the chemistry is consistent and...".
- Under R1 and R2, still record every issue from every gate. They are reported but do not change the status.
- An EU issue that triggers D2 counts toward D2. If the EU gate also has other, non-matrix issues, list them all. The status is still `not_assessable` by precedence.
- The gate result is authoritative over the planner's manual reading (BRIEF rule 3). Disagreements go in `discrepancies` (Step 8) and do not change the status.

## Gates

A positive status (`compliant`) requires **all** of these, on the same unmodified payload:
1. **Chemistry consistency:** `bp_check_chemistry` returns `consistent: true`.
2. **EU 2023/1542 mandatory-attribute gate:** `bp_check_compliance` returns empty Issues and no D2 signal.
3. **Carbon-footprint methodology gate:** `bp_check_cf_methodology` returns empty Issues.
4. **Supply-chain due-diligence gate:** `bp_check_due_diligence` returns empty Issues.

If any of these is missing, errored, or failing, `compliant` is forbidden. `compliant` means "passes TOKN's gate projection of the regulation", **not** legal certification, and must be worded that way in RESULT.md. The mass-reconciliation part of the cross-category consistency gate has no tool here and is **not assessed** (CAPABILITIES Gap 5). Say so in RESULT.md.

## Acceptance criteria

`result.json` is complete only if it is valid JSON with this shape (key `called` = the exact tool name invoked):

```json
{
  "brief": "BRIEF.md",
  "disclaimer": "Statuses reflect TOKN batterypass gate projection of EU 2023/1542; not a legal certification. Synthetic data.",
  "execution_date": "<ISO date the checks were run>",
  "items": [
    {
      "id": "BP-01",
      "chemistry": "NMC",
      "application": "EV",
      "status": "compliant | non_compliant | inconsistent | not_assessable",
      "status_basis": "R1 | R2 | R3 | R4 | fallback_R5",
      "checks": {
        "chemistry":      {"called": "bp_check_chemistry", "input": {"declared_chemistry": "...", "cathode_composition": "..."}, "consistent": true, "raw": {}},
        "eu_compliance":  {"called": "bp_check_compliance", "input": {"chemistry": "...", "application": "..."}, "passed": true, "not_in_matrix": false, "issues": [], "error": null, "raw": {}},
        "cf_methodology": {"called": "bp_check_cf_methodology", "passed": true, "issues": [], "error": null, "raw": {}},
        "due_diligence":  {"called": "bp_check_due_diligence", "passed": true, "issues": [], "error": null, "raw": {}}
      },
      "all_issues": ["<every issue string from every gate, verbatim>"],
      "discrepancies": [],
      "payload_modified": false
    }
  ]
}
```

Checklist:
1. Exactly six entries in `items`, with ids `BP-01` to `BP-06`, each appearing once.
2. Each `status` is one of the four vocabulary strings, and `status_basis` names the decision-table row that produced it.
3. All four `checks` are present for every item, 24 in total, each with its tool name, exact inputs, raw response, and verbatim `issues` (or `error`).
4. `chemistry`/`application` equal the top-level passport values from `inputs/passports.json`, with no label variants.
5. `all_issues` is the concatenation of every gate's issues, copied verbatim with nothing paraphrased.
6. `payload_modified` is `false` for every item.
7. Any `fallback_R5` status and any `discrepancies` are explicitly called out in RESULT.md.
8. RESULT.md includes a per-passport table (id, status, basis, issues) plus the disclaimer, and states the unassessed scope: mass reconciliation, the unknown gate reference date for the 365-day window, and the undocumented material-trigger matching.
