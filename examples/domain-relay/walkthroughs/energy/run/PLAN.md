# PLAN — Q3 2026 energy & carbon board pack release gate (energy relay, Planner stage)

Sources read: `BRIEF.md`, `inputs/analysis_requests.json`, `inputs/release_policy.json`,
`CAPABILITIES.md`, `tokn-self/DOMAIN-README.md`, `tokn-self/introspect-slice.json`.

> **Correction to CAPABILITIES.md (Gap 2), checked directly in the files on disk:** the "ri[REDACTED]free" text is
> a display artefact of the Scout's viewer. `grep` of the raw files shows:
> - `inputs/analysis_requests.json` line 40 (EN-3 `assumptions`): `"Cash flows discounted at the risk-free rate plus a 350 bp project spread; ..."`
> - `tokn-self/DOMAIN-README.md` line 58: blocked certainty terms include `"guaranteed return", "risk-free", "will definitely", etc.`
>
> So the EN-3 payload **does** contain a README-listed blocked term (`risk-free`). This is a prediction about the gate, not a finding. The Executor must still submit the payload and record what the tool actually returns.

## Objective
Submit each of the six analysis payloads (EN-1…EN-6) to its named `en_` tool exactly once and unchanged, then give each item exactly one status (`release`, `release_with_caveat`, `blocked`) by the mechanical rules below, with evidence quoted from the tool output.

## Steps

General instructions for every step:
- Pass the payload **byte-for-byte as in `inputs/analysis_requests.json`**. Do not add, remove, rename, retype or "fix" fields. In particular, do **not** add `provenance`, `disclaimer_acknowledged`, `candidates`, `carbon_price`, etc. where they are absent, and do **not** change `0.0`.
- Call each tool **once**. A gate refusal is the finding. Do not retry with a changed payload. Retry only if the call failed for a transport reason (timeout or connection error, not a gate message), at most once, with the identical payload. Record the retry.
- For every call, capture the raw response verbatim into the evidence record:
  - (a) whether it completed or was refused;
  - (b) the refusal/gate message text, if any;
  - (c) the returned `provenance`, if any;
  - (d) the returned `confidence`, if any;
  - (e) any numeric results.
- The six calls are independent and may be issued in parallel.

### Step 1 — EN-1 (Site-north multi-carrier energy balance, Q3)
- Tool: `en_energy_balance`
- Input (exact):
  ```json
  {"carriers": ["electricity", "natural_gas", "heat"], "period": "2026-Q3", "provenance": "metered", "meter_id": "AMI-HQ-0042", "region": "site-north"}
  ```
- Data layer: `metered` (payload field, BRIEF rule 3).
- Status-changing outcomes:
  - provenance gate refusal (e.g. metered without meter ID) → `blocked`;
  - completes → `release` (metered layer);
  - completes but the returned confidence is above 0.95 → still `release`, plus the confidence-cap flag (see Decision rules R7).

### Step 2 — EN-2 (20-year on-site generation & storage capacity expansion)
- Tool: `en_capacity_expansion`
- Input (exact):
  ```json
  {"horizon_years": 20, "discount_rate": 0.0, "assumptions": "Rooftop PV and 4-hour storage candidates; real 2026 prices; demand growth 1.8%/yr; grid import tariff escalates with CPI"}
  ```
- Data layer: no payload provenance. Use the tool-returned `provenance` (BRIEF rule 3).
- Status-changing outcomes:
  - scenario-disclosure gate refusal → `blocked`;
  - completes → **still `blocked`**, by BRIEF rule 4 (`discount_rate` 0.0 = undisclosed). See R2.
  - Record whether the gate actually fired, because a non-firing gate is itself a finding to report.
- Expected (prediction only): `blocked`.

### Step 3 — EN-3 (12-year virtual PPA valuation)
- Tool: `en_ppa_valuate`
- Input (exact):
  ```json
  {"contract_type": "virtual/cfd", "tenor_years": 12, "strike_price": 41.5, "volume_mwh": 180000, "discount_rate": 0.07, "assumptions": "Cash flows discounted at the risk-free rate plus a 350 bp project spread; P50 volume; hub-to-node basis held at the 3-year average", "disclaimer_acknowledged": true}
  ```
  (Use the raw file text. The word is `risk-free`, not a redaction token.)
- Data layer: no payload provenance. Use the tool-returned `provenance`.
- Status-changing outcomes:
  - market-disclaimer / blocked-term gate refusal → `blocked`;
  - completes but the payload contains the README-listed blocked term `risk-free` → **still `blocked`** per BRIEF's blocked definition ("a blocked certainty term in the payload"). See R3. Record that the gate did not fire.
  - completes with no blocked-term issue → layer rule R5/R6.
- Expected (prediction only): `blocked` (`ErrBlockedTerm`).

### Step 4 — EN-4 (2025 Scope 1+2 GHG inventory)
- Tool: `en_carbon_inventory`
- Input (exact):
  ```json
  {"ghg_scope": "scope1+2", "accounting_method": "market-based", "reporting_year": "2025", "organization": "operational_control"}
  ```
- Data layer: no payload provenance. Use the tool-returned `provenance`.
- Status-changing outcomes:
  - carbon-boundary gate refusal → `blocked`;
  - completes → `release` if the returned provenance is metered or estimated; `release_with_caveat` if it is modeled, assumed, or absent (R6).

### Step 5 — EN-5 (Fleet-electrification transition scenario to 2040)
- Tool: `en_scenario_model`
- Input (exact):
  ```json
  {"scenario_name": "electrify-fleet-2040", "horizon_years": 15, "discount_rate": 0.06, "assumptions": "Light-duty fleet fully battery-electric by 2035; depot charging on managed tariff; carbon price starts at 85 per tCO2e", "demand_growth": 0.021}
  ```
  (Do not add `carbon_price`. The value 85 stays inside `assumptions` only.)
- Data layer: no payload provenance. Use the tool-returned `provenance`.
- Status-changing outcomes:
  - scenario-disclosure gate refusal → `blocked`;
  - completes → `release` if the returned provenance is metered or estimated; `release_with_caveat` if it is modeled, assumed, or absent.

### Step 6 — EN-6 (Five-year monthly commercial electricity demand forecast)
- Tool: `en_demand_forecast`
- Input (exact):
  ```json
  {"carrier": "electricity", "sector": "commercial", "horizon_years": 5, "granularity": "monthly", "provenance": "estimated"}
  ```
- Data layer: `estimated` (payload field).
- Status-changing outcomes:
  - provenance gate refusal → `blocked`;
  - completes → `release` (estimated layer);
  - returned confidence above 0.75 → still `release`, plus the R7 flag.

### Step 7 — Assemble outputs (no domain tool exists for this; see CAPABILITIES gaps 5–6)
- Apply the Decision rules to each evidence record. Write `result.json` and `RESULT.md` per the Acceptance criteria.
- Do **not** compute totals or derived figures by hand. Report only numbers that appear verbatim in tool outputs or in `inputs/`.
- Caveat text for `release_with_caveat` items is copied verbatim from `inputs/release_policy.json` → `release_policy.caveat_wording`.

## Decision rules
Apply in order. The first rule that matches sets the status (this implements precedence `blocked` > `release_with_caveat` > `release`).

- **R1 — Gate refusal.** The tool response is a refusal or error from a domain gate. Examples: any of `ErrDataProvenanceRequired`, `ErrMeteredClaimWithoutSource`, `ErrScenarioDisclosureRequired`, `ErrMissingDiscountRate`, `ErrMissingTimeHorizon`, `ErrMissingKeyAssumptions`, `ErrCarbonBoundaryRequired`, `ErrScopeBoundaryUndeclared`, `ErrAccountingMethodUndeclared`, `ErrMarketDisclaimerRequired`, `ErrBlockedTerm`, or any response saying the call was blocked or refused by `validate_data_provenance` / `enforce_scenario_disclosure` / `enforce_carbon_boundary` / `enforce_market_disclaimer`.
  - → `blocked`. Quote the reason verbatim. Set `gate_fired: true`.
- **R2 — Zero discount rate.** The payload has `discount_rate` equal to `0` / `0.0` (BRIEF rule 4).
  - → `blocked`, even if the tool completed.
  - Reason: `"discount_rate 0.0 treated as undisclosed (BRIEF rule 4); scenario disclosure gate"`, plus the tool's own message if one exists.
  - Set `gate_fired` to whatever actually happened.
- **R3 — Blocked certainty term.** Any payload string field contains a blocked certainty term known from the repo (`"guaranteed return"`, `"risk-free"`, `"will definitely"`, matched case-insensitively as a substring).
  - → `blocked`, even if the tool completed.
  - Reason: the tool's message if one exists; otherwise `"payload contains blocked certainty term '<term>' (DOMAIN-README.md line 58; BRIEF blocked definition)"`.
  - Set `gate_fired` to whatever actually happened.
- **R4 — Non-gate failure.** The call failed for a non-gate reason (transport error, schema error) after one identical retry.
  - → `blocked`, with `reason` = verbatim error and `gate_fired: false`, flagged as an execution failure. Fail closed: nothing ships without a completed call.
- **R5 — Completed on a high-certainty layer.** The call completed and the data layer (payload `provenance` if present, else returned `provenance`) is `metered` or `estimated`.
  - → `release`.
- **R6 — Completed on a caveat layer.** The call completed and the data layer is `modeled` or `assumed`, **or no provenance is available from either payload or response** (fail-closed: treat as `assumed`, and flag `provenance_source: "none — defaulted to assumed"`).
  - → `release_with_caveat`.
- **R7 — Confidence-cap check.** This adds a flag only and never changes the status. If the returned confidence exceeds the cap for the layer (metered 0.95, estimated 0.75, modeled 0.55, assumed 0.35), set `flags: ["confidence_exceeds_layer_cap"]`. Report the returned value unmodified.

Gate-mismatch reporting: if R2 or R3 sets `blocked` while the tool completed, record `gate_fired: false` and add flag `gate_did_not_fire_policy_block`. That way the reviewer sees the divergence between the harness and the brief.

## Gates
No positive status (`release` / `release_with_caveat`) may be given unless **all** of these hold for that item:
1. **Data provenance gate** (`validate_data_provenance`). The call was not refused. A data layer is determined (payload or returned, or fail-closed default per R6). A metered claim carries `meter_id`. Applies to EN-1 and EN-6 directly, and to all items for layer determination.
2. **Scenario disclosure gate** (`enforce_scenario_disclosure`). For projection tools (EN-2 `en_capacity_expansion`, EN-3 `en_ppa_valuate`, EN-5 `en_scenario_model`), the call was not refused **and** the payload has a non-zero `discount_rate`, a `horizon_years`/`tenor_years`, and non-empty `assumptions`.
3. **Carbon boundary gate** (`enforce_carbon_boundary`). For EN-4, the call was not refused and the payload declares `ghg_scope`, `accounting_method` and `organization`.
4. **Market disclaimer gate** (`enforce_market_disclaimer`). For EN-3, the call was not refused, `disclaimer_acknowledged` is `true`, and no blocked certainty term appears in the payload.
5. **Completion.** The tool call returned a non-error result.

Lifecycle gates (BALANCE_SIMULATION←DATA_COLLECTION, etc.) cannot be read or advanced with any available tool (CAPABILITIES gap 4). Record them as `not_verifiable` in `result.json`. They do not change status unless a tool response cites a lifecycle error (`ErrInvalidTransition`, `Err*GateFailed`), in which case R1 applies.

## Acceptance criteria
`result.json` is complete only if:
1. It contains a top-level `board_pack` field set to `"Q3 2026 energy & carbon board pack"`.
2. It contains an `items` array with **exactly six** entries, `EN-1`…`EN-6`, each having:
   - `id`, `tool` (exact `en_` name), and `payload_submitted` (identical to the input payload; must diff-equal `inputs/analysis_requests.json`);
   - `call_completed` (bool) and `gate_fired` (bool);
   - `status`: exactly one of `release` | `release_with_caveat` | `blocked`;
   - `rule_applied` (R1–R6);
   - for `blocked`: `reason`, a verbatim quote of the gate/tool message, or the R2/R3 policy reason text when the gate did not fire;
   - for `release` / `release_with_caveat`:
     - `provenance` and `provenance_source` (`payload` | `tool` | `none — defaulted to assumed`);
     - `confidence` (the tool-returned value, or `null` if none was returned);
     - `confidence_cap` for the layer;
     - key result figures copied verbatim from the tool output;
   - for `release_with_caveat`: a `caveat` equal to `release_policy.caveat_wording` verbatim, and the payload `assumptions` (if any) restated;
   - `flags` (array, possibly empty).
3. A `summary` object with counts per status, taken by counting the `items` array. No other derived numbers.
4. A `gates` object listing the four domain gates with, per item, `passed` | `refused` | `not_applicable`, and lifecycle gates as `not_verifiable`.
5. An `evidence` section (or a per-item `raw_response`) holding the verbatim tool responses, so every reported number traces to a tool call (BRIEF rule 6).
6. `RESULT.md` mirrors `result.json` in prose. It includes:
   - the per-item status table;
   - quoted block reasons;
   - provenance and confidence for released items;
   - the caveat wording;
   - an explicit list of predictions that did **not** match outcomes (e.g. EN-2 or EN-3 completing despite the expected gate refusal).
