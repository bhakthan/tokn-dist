# Task: pre-release export compliance review of seven shipments

You are the trade-compliance analyst for Halvorsen Precision Devices Inc., a fictional US manufacturer of instruments and electronic components. Seven export shipments are waiting in the pre-release queue on **2026-11-09**. Before the warehouse releases anything, the compliance officer needs a defensible, decision-support disposition for each one.

All data is synthetic. Every company, person, address and country code (`XN`, `XS`, `XM`, `XQ`, `XR`) is fictional. The screening list, the country chart and the control criteria are **synthetic stand-ins** that look like the real reference data: a restricted-party list, the Commerce Country Chart (EAR Part 738) and the technical parameters of CCL / USML entries. They are not real list entries or regulatory text. Use only the files supplied here.

| File | Contents |
|---|---|
| `demo-input/shipments.json` | Seven shipments. Each has `shipment_id`, `exporter`, `destination_country` and `parties` (role, name, address, country, `is_freight_forwarder`, `business_type`, `owners` with percentages). It also has `items` (product type, declared ECCN/USML, `classification_basis`, technical `specs`, HS code and schedule, origin, quantity, value, reference unit-value range, expected business types), `end_use`, `payment` and `routing`. |
| `demo-input/screening_list.json` | A synthetic restricted-party list: entry ID, name, aliases, addresses, country and program. |
| `demo-input/country_chart.json` | A synthetic country chart. It gives the reason-for-control columns per destination (NS1, NS2, MT1, NP1, CB1, RS1, AT1), embargo and military-end-use flags, reasons for control per ECCN, and advisory license-exception rules. |
| `demo-input/control_criteria.json` | Synthetic technical criteria. Each one places an item in a USML category or an ECCN when every condition on its specs holds. |

Pass the reference files to the tools by path, for example `screening_list_path: "tests/domain-relay-live/scenarios/tradecomp/inputs/screening_list.json"`. The paths are relative to the repository root.

## Items to assess

`SHP-001`, `SHP-002`, `SHP-003`, `SHP-004`, `SHP-005`, `SHP-006`, `SHP-007`

## Status vocabulary (use exactly one per item)

- `ready_for_officer_review`: every check ran and no automated check blocks the shipment: parties, ownership, classification, jurisdiction, license, red flags and documentation. This is **not** a legal clearance. Release still needs a human compliance officer's attestation.
- `hold_sanctions`: a party is a confirmed match to the screening list, or is owned 50% or more in aggregate by listed parties.
- `hold_screening_review`: a party is a potential match that a human analyst has not yet dispositioned (false positive with rationale, or escalate).
- `hold_jurisdiction`: the specs meet a USML criterion but the item was routed under the EAR (or the reverse). Jurisdiction must be resolved first, if necessary by a commodity jurisdiction request.
- `hold_classification`: the classification is undetermined, malformed, or contradicted by the technical criteria (for example, EAR99 declared for an item whose specs meet a CCL entry).
- `hold_license`: a license is required and none is on file, or the requirement cannot be determined from the chart.
- `hold_red_flag`: a "Know Your Customer" style red flag has no human resolution.
- `correct_documentation`: the export checks pass, but the HS code, value, currency or origin data is wrong and must be corrected.

## Rules

1. Precedence is `hold_sanctions`, then `hold_screening_review`, `hold_jurisdiction`, `hold_classification`, `hold_license`, `hold_red_flag`, `correct_documentation` and finally `ready_for_officer_review`.
2. Screening is fuzzy. Transliteration variants, reordered tokens and legal-form suffixes (LLC, Ltd) do not make a name "different". A potential match is never cleared by the agent; only a named human analyst can disposition it.
3. Apply the 50% rule in aggregate. Add up the ownership held by all listed parties; an entity owned 50% or more in total is treated as blocked even though no single owner reaches 50%.
4. Review the USML before the CCL (order of review). EAR99 is available only after every applicable entry has been excluded, so a "sales team assumption" is not a classification basis.
5. A freight forwarder is not an end user. A shipment whose only consignee is a forwarder, with no ultimate consignee or end user, has an unresolved red flag.
6. HS codes must be structurally valid: 2/4/6 digits internationally, with 8/10-digit national extensions. Chapter 77 is reserved, and no heading ends in 00.
7. Use `trade_party_screen`, `trade_ownership_aggregate`, `trade_classification_check`, `trade_jurisdiction_review`, `trade_license_determination`, `trade_red_flag_check` and `trade_hs_validate`, or `trade_shipment_review`, which runs them together. Every number you report must come from a tool call or the input files.
8. Use calibrated language. These are decision-support results, not legal determinations. Never write that a shipment is cleared or approved for export. A screening hit or red flag is a risk signal for the compliance officer, never an accusation.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"SHP-001": "<status>"}`.
