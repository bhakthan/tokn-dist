# Task: supplier lot release decision for seven characteristics

You are the supplier quality engineer for a machined and welded valve body (part VB-100, synthetic). Supplier S-ALPHA (synthetic) has shipped lot LOT-2401 with a production-part data package: SPC subgroups for seven characteristics, gauge evidence, its PFMEA, and a cover letter that claims high capability. Before the lot is released to the assembly line, the plant quality manager needs a defensible release status for each characteristic.

All data are SYNTHETIC: the supplier, part, plant, gauges and values are fictitious. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/spc_data.json` | Per characteristic: `id`, `name`, `unit`, specification limits `usl` / `lsl` (CH-05 is one-sided: `usl` only) and 25 subgroups of 5 consecutive parts (`subgroups`) |
| `demo-input/msa.json` | `summaries`: gauge R&R summaries (`grr_pct`, `ndc`) for CH-01, CH-03, CH-04, CH-06, CH-07. `studies`: raw crossed gauge studies `[part][operator][trial]` (10 parts × 3 operators × 3 trials) with `tolerance` for CH-02 and CH-05 |
| `demo-input/pfmea.json` | One PFMEA row per characteristic: `severity`, `occurrence`, `detection` (1–10 scales per the AIAG-VDA FMEA Handbook), `recommended_action`, `responsible` |
| `demo-input/supplier_submission.json` | The supplier's claims (`claims`) and the control limits it uses on the shop floor (`control_limits`, with their `source`) |

## Items to assess

`CH-01`, `CH-02`, `CH-03`, `CH-04`, `CH-05`, `CH-06`, `CH-07`

## Status vocabulary (use exactly one per item)

- `release`: every gate passes, the process is in statistical control on the X̄-R chart, and Cpk and Ppk computed from the raw data are both at least 1.33, with no caveats.
- `release_with_caveats`: as `release`, but with a documented caveat, e.g. a conditionally acceptable measurement system (10% ≤ %GRR ≤ 30% with ndc ≥ 5), a normality concern or a short data set. Name the caveat.
- `hold`: gates pass, but the process shows out-of-control signals, so capability is **not assessable**. Investigate assignable causes before any capability statement.
- `reject`: in control and assessable, but Cpk or Ppk is below 1.33.
- `blocked`: a gate refuses the evidence: control limits taken from the specification, capability indices supplied instead of raw data, an unacceptable or missing measurement system analysis (%GRR > 30% or ndc < 5), or a severity 9–10 failure mode with no recorded action.

## Rules

1. Precedence is `blocked`, then `hold`, then `reject`, then `release_with_caveats`, then `release`.
2. Control limits come from the process data (voice of the process), never from the specification (voice of the customer). Pass the supplier's `control_limits` to the tools as given; do not quietly drop them.
3. Capability is computed only from raw subgroups after the control check: Cp/Cpk use within-subgroup sigma (R̄/d2) and Pp/Ppk use the overall sample standard deviation. Never accept the supplier's claimed Cpk as an input.
4. A characteristic with a raw gauge study must be judged on the study (pass `msa_study` with its `tolerance`), not on a summary.
5. Severity 9 or 10 requires a recommended action with an owner regardless of RPN or action priority.
6. Every number you report must come from a tool call or the input files. Use calibrated language: no guarantees, no "capable" claim for a process that is not in control, no "root cause confirmed" without verification. Cite standards by name and clause only (e.g. IATF 16949 clause 9.1.1.1, AIAG SPC and MSA reference manuals, AIAG-VDA FMEA Handbook).

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"CH-01": "<status>"}`.
