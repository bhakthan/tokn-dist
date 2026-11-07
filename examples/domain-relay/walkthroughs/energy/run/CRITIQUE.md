# CRITIQUE — Q3 2026 energy & carbon board pack release gate (Critic stage, energy relay)

Evidence base: `BRIEF.md`, `inputs/analysis_requests.json`, `inputs/release_policy.json`, `PLAN.md`, `CAPABILITIES.md`, `tokn-self/DOMAIN-README.md`, `tokn-self/introspect-slice.json`, `result.json`, `RESULT.md`, plus independent re-runs of all six domain tools and two further tool runs (`en_ppa_valuate` with the file's true payload text; `en_carbon_report` as a cross-check).

## Method

I re-ran every tool whose output decides a status, with each payload copied from `inputs/analysis_requests.json`:

| Item | Tool | Re-run result |
|---|---|---|
| EN-1 | `en_energy_balance` | completes; `balance_computed`, provenance=metered, period=2026-Q3, region=site-north, unit=MWh, no confidence — identical to the recorded response |
| EN-2 | `en_capacity_expansion` | REFUSED: "[ENERGY] energy: scenario missing discount rate — projections are meaningless without a stated discount rate" — identical to the recorded reason |
| EN-3 | `en_ppa_valuate` | see C1 — the recorded response does not correspond to the payload in `inputs/` |
| EN-4 | `en_carbon_inventory` | REFUSED: "[ENERGY] energy: data provenance layer required — declare whether data is metered, estimated, modeled, or assumed" — identical to the recorded reason |
| EN-5 | `en_scenario_model` | completes; `scenario_modeled`, provenance=modeled, confidence=0.45 — identical to the recorded response |
| EN-6 | `en_demand_forecast` | completes; `forecast_generated`, carrier=electricity, sector=commercial, unit=MWh — identical to the recorded response |

I also used `grep_search` (raw file text, no viewer redaction) against `inputs/`, `result.json` and `RESULT.md`, which is what exposed C1/C2. `read_file` renders the phrase in question as `ri[REDACTED]free`; the raw bytes are `risk-free`.

## Findings

### C1 — EN-3 payload was not submitted as given; the recorded status-bearing fields are contradicted by the tool (blocking)

Raw-text search shows `inputs/analysis_requests.json` line 40 reads "Cash flows discounted at the **risk-free** rate plus a 350 bp project spread; ..." and `tokn-self/DOMAIN-README.md` line 58 lists the blocked term as "risk-free"; PLAN.md line 60 states explicitly "Use the raw file text. The word is `risk-free`, not a redaction token."

I ran `en_ppa_valuate` as a metamorphic pair:

- with the file's actual text ("risk-free rate") the call is **refused**: `[ENERGY] energy: blocked term detected — terms like 'guaranteed return', 'risk-free', 'will definitely' are prohibited in market analysis: risk-free`
- with the corrupted string `ri[REDACTED]free` the call **completes** with status=`ppa_valued`

`result.json` records the second outcome: `call_completed=true`, `gate_fired=false`, `rule_applied=R3`, flag `gate_did_not_fire_policy_block`, and a "raw result" quoting strike_price=41.5 / tenor_years=12. Since the file's text is `risk-free`, the only way to obtain the recorded completed response is to have submitted a string that is not in `inputs/`. That violates BRIEF rule 1 ("Submit each payload exactly as given") and the release_policy `submission` rule.

The correct record: the market-disclaimer gate (`enforce_market_disclaimer`, blocked-term check) **fires** on the true payload, so R1 applies, `call_completed=false`, `gate_fired=true`, there is no `gate_did_not_fire_policy_block` flag, and no `ppa_valued` response exists to quote. The final label `blocked` is unchanged, but the recorded rule, gate outcome, completion flag, reason and evidence are all wrong.

**Fix:** re-run `en_ppa_valuate` once with the payload copied byte-for-byte from `inputs/analysis_requests.json` line 40; record status=blocked, rule_applied=R1, call_completed=false, gate_fired=true, the refusal verbatim, flags=[]; delete the `ppa_valued` response values from the evidence.

### C2 — EN-3 evidence quotes a payload that does not exist in `inputs/` (major)

`result.json` (lines 30, 33, 91) and `RESULT.md` (line 54) write the blocked term and the submitted assumptions as `ri[REDACTED]free` — a viewer redaction artefact, not file text. The evidence line "submitted assumptions=\"Cash flows discounted at the ri[REDACTED]free rate ...\"" quotes a payload absent from `inputs/`, breaking the verbatim-evidence requirement (BRIEF rule 5, PLAN acceptance criterion 5).

**Fix:** replace every `ri[REDACTED]free` with `risk-free` in both files and quote the assumptions exactly as they appear at `inputs/analysis_requests.json` line 40.

### C3 — Missing top-level `board_pack` field (major)

PLAN acceptance criterion 1 requires `board_pack: "Q3 2026 energy & carbon board pack"`. A repository-wide search for `board_pack` finds it only in PLAN.md and `inputs/analysis_requests.json` line 3 — never in `result.json`, whose top-level keys are domain, objective, items, gates, overall_verdict, confidence, limitations, critique_response. The value supplied in `inputs/` was ignored.

**Fix:** add `"board_pack": "Q3 2026 energy & carbon board pack"` to `result.json`, copied from `inputs/analysis_requests.json` line 3.

### C4 — Missing `payload_submitted` on every item (major)

PLAN acceptance criterion 2 requires a `payload_submitted` field per item, "identical to the input payload; must diff-equal inputs/analysis_requests.json". A search for `payload_submitted` matches only PLAN.md. No item carries its payload; payloads appear only in prose. The deliverable contains no checkable evidence that payloads were submitted unchanged — the exact property that failed for EN-3 (C1) and that this field would have caught.

**Fix:** add `payload_submitted` to each of EN-1…EN-6, copied byte-for-byte from the corresponding `payload` object.

### C5 — Missing `summary` object (major)

PLAN acceptance criterion 3 requires a `summary` object with counts per status "taken by counting the `items` array. No other derived numbers." `result.json` has no `summary` key; the counts appear only as prose inside `overall_verdict`.

**Fix:** add `{"release": 2, "release_with_caveat": 1, "blocked": 3}` — EN-1 and EN-6 release, EN-5 release_with_caveat, EN-2/EN-3/EN-4 blocked. Unaffected by C1, since EN-3 is blocked either way.

### C6 — `gates` does not meet the required structure and three per-item values are wrong (major)

PLAN acceptance criterion 4 requires a `gates` object with, per item, `passed` | `refused` | `not_applicable`, and lifecycle gates as `not_verifiable`. `result.json` supplies an array of `{name, status, detail}` entries using "fail" and "n/a" — neither value is in the required vocabulary — with no per-item breakdown. Three per-item values are also wrong:

- `enforce_scenario_disclosure` is marked "fail" because EN-2 was refused, but EN-3 and EN-5 were **not** refused by that gate (my re-runs of both completed; EN-3's true refusal comes from the blocked-term check, not scenario disclosure).
- `enforce_market_disclaimer` is reported as a policy failure with `gate_did_not_fire_policy_block`, but per C1 the hook **does** refuse the true payload, so EN-3 is `refused`.
- the lifecycle entry uses status "n/a" and relegates "not_verifiable" to the detail text.

**Fix:** restructure `gates` as an object keyed by gate name with per-item values from {passed, refused, not_applicable} — validate_data_provenance: EN-1/EN-5/EN-6 passed, EN-4 refused, EN-2/EN-3 not_applicable; enforce_scenario_disclosure: EN-2 refused, EN-3/EN-5 passed, others not_applicable; enforce_carbon_boundary: not established for EN-4 (refused upstream), not_applicable elsewhere; enforce_market_disclaimer: EN-3 refused, others not_applicable; lifecycle_gates: `not_verifiable` as the status value.

### C7 — `confidence_cap` never stated for any released item (major)

PLAN acceptance criterion 2 requires `confidence_cap` "for the layer" on every released item. No cap value appears anywhere in `result.json` or `RESULT.md`; a search for `confidence_cap` matches only PLAN.md. Caps (DOMAIN-README.md, Four-Layer Data Hierarchy): metered 0.95, estimated 0.75, modeled 0.55. EN-5's confidence is 0.45 (confirmed by my re-run), and RESULT.md concludes "the returned value does not exceed R7's modeled-layer cap" without stating that the cap is 0.55 — so the R7 no-flag conclusion cannot be audited from the deliverable. The same omission affects EN-1 (metered, 0.95) and EN-6 (estimated, 0.75).

**Fix:** add `confidence_cap` to each released item: EN-1 → 0.95, EN-5 → 0.55, EN-6 → 0.75; state EN-5's check explicitly as 0.45 ≤ 0.55.

### C8 — False statements about observed tool behavior for EN-3 (major)

RESULT.md's "Predictions versus observed outcomes" says EN-3 "matched the final predicted blocked outcome, but not the predicted mechanism: the plan named ErrBlockedTerm as the expected refusal; instead, the tool completed ... The harness gate did not fire." `result.json`'s limitations repeat it. Both are false for the payload in `inputs/`: the harness gate **did** fire and returned exactly the predicted blocked-term refusal. The predicted mechanism matched; the divergence was an artefact of the corrupted input (C1).

**Fix:** rewrite the EN-3 prediction-reconciliation entry to state that outcome and mechanism both matched the plan's prediction, and remove or correct the corresponding limitation line.

### C9 — Decision-record values buried in prose, `provenance_source` unstated for EN-1/EN-5 (minor)

The required per-item fields (`call_completed`, `gate_fired`, `rule_applied`, `flags`, `provenance`, `provenance_source`, `confidence`, `caveat`, `reason`) exist only as free text inside `rationale`/`evidence` strings, not as named machine-checkable fields. `provenance_source` is additionally unstated for EN-1 and EN-5 in `result.json` (only EN-6 has it, as "payload").

**Fix:** promote these to named fields. Apart from EN-3 (C1), the values are correct against my independent re-runs of all six tools (EN-1: true/false/R5; EN-2: false/true/R1; EN-4: false/true/R1; EN-5: true/false/R6; EN-6: true/false/R5) — only the structure is missing. Set provenance_source explicitly: EN-1 "payload", EN-5 "tool", EN-6 "payload".

### C10 — Top-level `confidence: 0.93` is broader than the evidence supports (minor)

The six status labels are reproduced exactly by my independent re-runs (EN-1, EN-2, EN-4, EN-5, EN-6 byte-identical; EN-3 blocked either way), so 0.93 is defensible for the status labels alone. Presented as confidence in the deliverable as a whole it exceeds what the artifact supports: `result.json` does not meet PLAN acceptance criteria 1–4 (C3–C6), omits the confidence caps (C7), and its EN-3 evidence chain is broken (C1, C2).

**Fix:** scope the confidence claim to the per-item statuses, or lower and qualify the 0.93 to reflect C1–C7.

## What I checked and found correct

For completeness, the following were verified and are **not** findings:

- **EN-1**: re-run output byte-identical to the recorded response; `release` under R5 is correct (metered layer declared in payload, meter_id AMI-HQ-0042 supplied, no refusal); the honesty about no returned confidence or balance figures is appropriate.
- **EN-2**: re-run refusal byte-identical; `blocked` under R1 is correct (and R2 independently, discount_rate=0.0); gate_fired=true, no retry, no payload mutation — all consistent.
- **EN-4**: re-run refusal byte-identical; `blocked` under R1 is correct; the refusal is genuinely from the data-provenance gate, and the caution that a passed carbon-boundary hook "cannot be asserted from the response" is the right call.
- **EN-5**: re-run output byte-identical (provenance=modeled, confidence=0.45); `release_with_caveat` under R6 is correct; caveat wording matches `release_policy.caveat_wording` verbatim; the 0.45-vs-cap comparison, had the cap been stated, yields no flag.
- **EN-6**: re-run output byte-identical; `release` under R5 is correct (payload declares provenance=estimated); no confidence returned, no cap flag — correctly reported.
- **Status precedence** (blocked > release_with_caveat > release) applied correctly on all six items.
- **No mental arithmetic**: no figure appears in either file that is not present verbatim in a tool output or in `inputs/`.
- **Lifecycle gates** correctly recorded as not_verifiable with no tool response citing a lifecycle error.

## Overall assessment

The five items other than EN-3 are reproduced exactly by independent re-runs of their tools, and their statuses follow correctly from the plan's decision rules; the report's discipline about not inventing confidence or numerical figures is genuine and welcome. The deliverable fails on two fronts, however. First and most seriously, EN-3's evidence chain is broken at the root: the payload in `inputs/analysis_requests.json` reads "risk-free", the tool refuses exactly that term, and yet `result.json` records a completed `ppa_valued` call obtained only by submitting a different string — a redaction artefact propagated from the viewer into the actual tool call. This violates the brief's central instruction (payloads submitted exactly as given), inverts every status-bearing field for that item (`call_completed`, `gate_fired`, `rule_applied`, the flag), and leads the report to make affirmatively false claims in its prediction-reconciliation section about what the harness gate did. Second, `result.json` does not satisfy the plan's own acceptance criteria: it lacks the `board_pack` field, per-item `payload_submitted`, the `summary` object, the confidence caps, and a `gates` structure in the required per-item vocabulary — omissions whose practical effect is precisely to make the EN-3 payload substitution invisible. The status labels themselves are all six correct, which makes the defects easy to miss but no less material: this is a board audit & risk committee deliverable whose stated evidence does not support its own quoted gate behavior, and it should not be released until EN-3 is re-run with the true payload text and the structural fields are filled in.
