# REFLECTION — energy relay: "Release gate for a quarterly energy & carbon board pack"

## What changed between the first and final answer

None of the status labels changed. In both files EN-1 and EN-6 are `release`, EN-5 is `release_with_caveat`, and EN-2, EN-3 and EN-4 are `blocked`. Everything else changed:

- **EN-3 (C1, C2, C8).**
  - v1 recorded the call as completed, `ppa_valued`, `rule_applied=R3`, `gate_fired=false`, with the flag `gate_did_not_fire_policy_block`, and quoted strike_price=41.5 and tenor_years=12 from the response.
  - Final records `call_completed=false`, `gate_fired=true`, `R1` and `flags=[]`, with the verbatim reason "[ENERGY] energy: blocked term detected …". The `ppa_valued` evidence is gone.
  - The v1 limitation that the gate did not fire was removed (C8).
  - The assumptions are now quoted from the raw file (C2). The final evidence line says this was confirmed by "Python raw-file JSON and character-codepoint inspection".
- **Top level (C3).** Added `board_pack: "Q3 2026 energy & carbon board pack"`.
- **All items (C4).** Added `payload_submitted` to each item, copied from the inputs.
- **Top level (C5).** Added `summary: {release: 2, release_with_caveat: 1, blocked: 3}`. In v1 these counts appeared only in prose.
- **Gates (C6).**
  - The v1 `gates` array used "fail" and "n/a". Final replaces it with a per-item object using passed/refused/not_applicable, and sets `lifecycle_gates: "not_verifiable"`.
  - `enforce_market_disclaimer` for EN-3 changed from a policy failure to `refused`.
  - `enforce_scenario_disclosure` now shows EN-3 and EN-5 as `passed`.
- **EN-1, EN-5, EN-6 (C7).** Added `confidence_cap` values of 0.95, 0.55 and 0.75. EN-5's confidence of 0.45 is now shown next to its 0.55 cap.
- **All items (C9).** `call_completed`, `gate_fired`, `rule_applied`, `flags`, `provenance`, `provenance_source`, `reason` and `caveat` were prose inside `evidence` strings. They are now named fields.
- **Overall confidence (C10).** The top-level `confidence` went from 0.93 to `null`. A new `confidence_basis` limits the claim to per-item classification.
- **New in final, not tied to a specific finding.** A `gate_interpretation` note, a `verification` block, and a limitation that says unchanged submission is asserted only for the reviser stage.

## Where TOKN's harness helped

- **`enforce_scenario_disclosure`, via `en_capacity_expansion` (EN-2).** Refused discount_rate 0.0 with "[ENERGY] energy: scenario missing discount rate — projections are meaningless without a stated discount rate". Critique and Revise reproduced the refusal exactly, and it matched PLAN's prediction.
- **`validate_data_provenance`, via `en_carbon_inventory` (EN-4).** Refused with "[ENERGY] energy: data provenance layer required …". PLAN had not predicted this: it expected EN-4 to complete and planned R5/R6 for it.
- **Market blocked-term check (`enforce_market_disclaimer`), via `en_ppa_valuate` (EN-3).**
  - It fired on the true payload, and it was the gate that exposed the v1 defect.
  - Critique's metamorphic pair showed the tool refuses "ri[REDACTED]free" as it appears in the file, but completes `ppa_valued` on the corrupted string.
  - This makes the gate useful as a test of whether a payload is byte-faithful, and not only as a policy check.
- **Four-layer confidence caps.** `en_scenario_model` returned provenance=modeled and confidence=0.45. That value let R6 and R7 be applied mechanically and audited against the 0.55 cap.
- **Re-runnable, deterministic tools.** Critique reports five of six outputs as "byte-identical" to v1. That made the independent re-runs in Critique and Revise cheap and decisive.
- **Market disclaimer.** The v1 `ppa_valued` response carried "PPA valuation is analytical modeling, not financial advice". The disclaimer path works, but the response it appeared in should not have existed.

## Proposed /teach rule

`/teach Before any en_ tool call, load the payload from inputs/ with a raw-byte JSON read (never from displayed or redacted text), submit it unchanged, and record its sha256 next to the raw response; if displayed text contains "[REDACTED]", stop and resolve it from the raw bytes first.`
