You are preparing a private-equity diligence pack for the fictional target
Quillstone Industrial Software Ltd, on behalf of the fictional sponsor
Ashgrove Capital. The asking price is $600M.

Inputs are in ./inputs:
- contracts-register.csv: the customer contract list from the data room. Each
  row has a status: executed, auto-renewed, mou, verbal, or disputed.
- data-room-summary.md: management's stated figures and the liability notes.

Produce, in ./diligence-pack:
1. arr-register.json: a row for every contract, with its status and whether it
   is authoritative. Authoritative ARR = executed or auto-renewed, undisputed.
   An MOU or verbal commitment is never authoritative.
2. valuation-memo.md: the management ARR, the authoritative ARR, the quarantined
   amount, the implied multiple of the asking price, the grounded value, and
   the gap. Show the arithmetic.
3. risk-memo.md: customer concentration, change-of-control rights, and the
   contingent liabilities. Give each liability a range and state the reserve
   that was modeled.

Default posture: do not count any commitment as ARR unless the contract is
executed or auto-renewed and undisputed. Do not invent figures. If something
is missing, record it as a gap.
