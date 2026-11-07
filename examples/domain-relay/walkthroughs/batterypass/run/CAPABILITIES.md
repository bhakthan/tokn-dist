# CAPABILITIES — SCOUT stage, batterypass pre-publication gate check

Scope: items BP-01 to BP-06 in `inputs/passports.json` and `inputs/chemistry_declarations.json`.
Evidence: BRIEF.md, both inputs, `tokn-self/introspect-slice.json`, `tokn-self/DOMAIN-README.md`, and the live tool list. Where these disagree, the live tool list governs (see Gaps).

## Domain tools that apply

Every passport (BP-01 to BP-06) needs the same four gate calls plus one chemistry call. The payload is passed as `body`, serialized to a JSON string.

| tool (exact name) | Items / input | Input fields needed (present in `inputs/`) |
|---|---|---|
| `bp_check_compliance` | BP-01 to BP-06, `passports.json` | `body` ← `payload` (stringified); `chemistry` ← `chemistry`; `application` ← `application` |
| `bp_check_cf_methodology` | BP-01 to BP-06 | `body` ← `payload`. Reads `payload.CarbonFootprint`: `carbonFootprintStudyMethod`, `primaryDataShare`, `systemBoundary`, `functionalUnit` (all present) |
| `bp_check_due_diligence` | BP-01 to BP-06 | `body` ← `payload`. Reads `payload.MaterialComposition.batteryMaterials` and `payload.SupplyChainDueDiligence`: `dueDiligencePolicyURI`, `lastAuditDate` (all present) |
| `bp_check_chemistry` | BP-01 to BP-06, `chemistry_declarations.json` | `declared_chemistry` ← `declared_chemistry`; `cathode_composition` ← `cathode_composition` (matched by `passport`) |
| `bp_load_payload` (optional pre-check) | BP-01 to BP-06 | `body` ← stringified `payload`. Confirms the payload parses before gating. Not required by the brief. |

Tools in my list that this brief does not need: `bp_advance_lifecycle`, `bp_transition_state` (no publish or state change is requested), and the generator, ingest and diff tools.

## Gates and rules that will constrain the answer

From BRIEF.md (quoted exactly):
- Status vocabulary, one per item: `compliant`, `non_compliant`, `inconsistent`, `not_assessable`.
- Precedence, highest first: `inconsistent` > `not_assessable` > `non_compliant` > `compliant`. Run every check on every passport and report all issues.
- `compliant` means "the draft passes TOKN's gate projection of the regulation. It is not a legal certification." Use this calibrated wording; do not present any status as legal certification.
- `inconsistent`: `bp_check_chemistry` returns `consistent: false`. Other gate results then cannot be trusted.
- `not_assessable`: the EU gate reports the chemistry+application combination is not in the mandatory-field matrix.
- `non_compliant`: chemistry is consistent and the combination is in the matrix, but the EU, CF or due-diligence gate returns at least one issue.
- A gate passes only if `result.Issues` is empty. Quote each issue string verbatim.
- CF: `primaryDataShare` threshold is `0.50`, and a value equal to the threshold passes. Method must be `PEFCR`, `ISO14067` or `GHGProtocol`.
- Due diligence: if cobalt, lithium, nickel or natural graphite appears in the payload, there must be a policy URI and a `lastAuditDate` within `365` days.
- Do not edit any payload to make a gate pass.
- Pass `chemistry` and `application` exactly as given (e.g. `NMC`, not `NMC811`).

From DOMAIN-README.md (regulatory anchor, not a number I can verify in code):
- EU 2023/1542 gate blocks `compliance_checked -> published` on any missing Annex VI / VIII / XIII attribute for the chemistry x application combination.
- CF gate blocks on missing functional unit, system boundary, PEFCR flag, or primary-data share "above threshold" (wording differs from the brief; see Gaps).
- Cross-category consistency gate is described as reconciling material mass with CF mass intensity and checking chemistry across categories (see Gaps: no tool covers the mass part).

## Gaps

Brief asks for, but no tool covers it. These are handled by reasoning and must be stated as such:
1. Status aggregation with the precedence rule. No tool combines gate results into one status; I must do this by reasoning and show the mapping.
2. EU matrix membership. The matrix is not in `inputs/` and no tool lists it. Whether NaIon x EV, NMC x Industrial and LFP x LMT are in the matrix is known only from `bp_check_compliance`'s output. Do not pre-judge `not_assessable`.
3. Reference date for the 365-day audit window. No input or tool states "today". Results that depend on the window are date-dependent, and the reference date used by the gate is unknown to me.
4. Material trigger matching. The brief says cobalt, lithium, nickel or natural graphite trigger DD. How the gate matches these terms in free-text `batteryMaterials` (substring, case, "synthetic" vs "natural") is not documented. I will report the tool result verbatim and not infer the trigger myself.
5. Mass reconciliation (cross-category consistency). No tool here checks material mass totals against CF intensity. The brief does not ask for it, so it is not assessed.
6. Active mode. I have not verified the harness is in `batterypass` mode. ASSUMPTION: the gates run as the tools expose them.

Disagreements between DOMAIN-README.md / introspect and my tool list (live list governs):
- README names `bp_refresh_model`; my list has `bp_refresh_snapshot`. Not used here.
- Counts: README says 18 tools, 14 commands, 6 hooks, 12-state lifecycle. Introspect says 23 tools, 19 commands, 9 hooks. My list has 23 `bp_` tools, matching introspect.
- `primaryDataShare`: brief says equal to 0.50 passes. README says "above threshold". The brief's rule is used; the README wording is flagged.
- README ingest lists RDF/Turtle. My list has no Turtle loader (only jsonld, jsonschema, openapi, payload). Not needed for this brief.
- Lifecycle: README lists 11 named states plus `revised`. Not needed for this brief.
