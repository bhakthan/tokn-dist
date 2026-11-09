# Task: pre-publication gate check of six Battery Passport drafts

You are a product-compliance engineer at a battery pack integrator. Six draft Battery Passports (EU Battery Regulation 2023/1542, DIN DKE SPEC 99100 data model) are queued for publication. Before any of them goes live, the compliance lead wants each draft run through TOKN's batterypass gates, with a decision recorded per passport.

The data is synthetic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/passports.json` | Six drafts. Each has an `id`, the gate keys `chemistry` and `application`, and a `payload` keyed by the seven passport categories |
| `demo-input/chemistry_declarations.json` | Per passport, the label's `declared_chemistry` and the supplier's `cathode_composition`, ready for `bp_check_chemistry` |

## Items to assess

`BP-01`, `BP-02`, `BP-03`, `BP-04`, `BP-05`, `BP-06`

## Status vocabulary (use exactly one per item)

- `compliant`: the chemistry check is consistent, and the EU mandatory-attribute, carbon-footprint methodology and due-diligence gates all return no issues. This means the draft passes TOKN's gate projection of the regulation. It is not a legal certification.
- `non_compliant`: the chemistry is consistent and the combination is in the matrix, but the EU, CF methodology or due-diligence gate returns at least one issue.
- `inconsistent`: `bp_check_chemistry` returns `consistent: false`. The declared chemistry contradicts the cathode, so no other gate result can be trusted.
- `not_assessable`: the EU gate reports that the chemistry+application combination is not in the mandatory-field matrix. The passport cannot be judged against the regulation until the matrix is extended.

## Rules

1. Precedence, highest first: `inconsistent` > `not_assessable` > `non_compliant` > `compliant`. Run every check on every passport anyway, and report all the issues found.
2. For each passport, call `bp_check_compliance`, `bp_check_cf_methodology` and `bp_check_due_diligence`. Pass the `payload` as `body`, **serialized to a JSON string**, and pass the passport's `chemistry` and `application` fields exactly as given. Do not use the label variant such as `NMC811`. Then call `bp_check_chemistry` with the matching entry from `chemistry_declarations.json`.
3. A gate passes only if its `result.Issues` is empty. Quote each issue string verbatim.
4. CF methodology: the `primaryDataShare` threshold is 0.50, and a value equal to the threshold passes. The method must be PEFCR, ISO14067 or GHGProtocol.
5. Due diligence: if cobalt, lithium, nickel or natural graphite appears in the payload, there must be a policy URI and a `lastAuditDate` within 365 days.
6. Do not edit any payload to make a gate pass.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"BP-01": "<status>"}`.
