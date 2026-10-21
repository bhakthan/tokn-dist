You are preparing a synthetic Phase 3 trial analysis package for the sponsor's
go/no-go review of compound VTX-417 (fictional) in the fictional indication
"chronic rhinitis with eosinophilic phenotype".

Inputs are in ./inputs:
- sap-excerpt.md: the pre-specified statistical analysis plan (SAP).
- phase2-locked-summary.md: the locked Phase 2 summary.

Produce, in ./analysis-package:
1. endpoint-register.json: one entry per statistical claim you intend to
   make. Each entry must have: id, endpoint, p_value, is_primary,
   population ("ITT" or other), blinded (true/false), sdv ("full" or
   "partial"), sap_prespecified (true/false), posthoc (true/false),
   assay_qualified (true/false), and a source reference to the SAP or
   Phase 2 section it comes from.
2. decision-memo.md: a recommendation (proceed, adaptive-redesign, or kill)
   with the reason for each claim. Do NOT green-light any claim that fails
   the SAP rules. Mark each claim LAWFUL or QUARANTINED.

Default posture: deny green-light unless every eligibility rule is met.
Do not invent data. If something is missing, record it as a gap.
