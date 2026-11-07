# CRITIQUE — RNA-seq QC gate (`result.json` / `RESULT.md`)

Critic stage. Independent re-execution: I re-ran every tool whose output decides a status —
`assess_rnaseq_quality` for all six samples, `compare_samples`, `check_batch_confound` on the
full and retained designs, `recommend_qc_thresholds(polyA)`, and `list_qc_metrics`. Every
reported verdict, per-metric result, ranking entry, confound status, and threshold value
reproduced exactly. The findings below record every remaining issue; none of them changes a
sample status or the DE-interpretability conclusion.

---

**C1 — overall — minor.** Provenance mis-attribution in RESULT.md's "Scope and evidence
basis": *"The input note describes the brief as treated and control cell lines with
poly(A)-selected, paired-end libraries."* The notes in `inputs/` say no such thing.
`inputs/qc_metrics.json`'s note reads *"Synthetic RNA-seq QC metrics for a teaching scenario;
not from any real study. Rates are percentages; nrf is a fraction; genes_detected is a count.
S05's RIN was not recorded."* and `inputs/design.json`'s note reads *"Synthetic study design
for a teaching scenario."* The cell-line / poly(A)-selected / paired-end description comes from
`BRIEF.md` ("a bulk RNA-seq study comparing treated and control cell lines (poly(A)-selected
libraries, paired-end)"). The sentence credits an input-file source with text that only
`BRIEF.md` contains, weakening the report's otherwise strict provenance index.
**Fix:** attribute the assay and study description to `BRIEF.md`, and reserve the `inputs/`
notes for what they actually state: synthetic teaching data, unit conventions (percentages /
fraction / count), and S05's unrecorded RIN.

**C2 — overall — minor.** A gate status is reported that no tool emitted. In `result.json`'s
`gates` array, `batch_confound_retained` is recorded as `status: "fail"`, and RESULT.md's
"Overall gate summary" table likewise shows "Retained-design batch confound | fail". My re-run
of `check_batch_confound` on the retained design (batches {S01:B1, S02:B2, S04:B1}; conditions
{S01:ctrl, S02:treated, S04:ctrl}) returned `status: "hard_block"`, and the adjacent
full-design entry correctly uses the tool's literal `pass`. The detail/evidence text does
disclose `hard_block`, but the status column itself carries a value outside the tool's
vocabulary — exactly the kind of silent relabelling the plan's "verbatim response" rule is
meant to prevent.
**Fix:** carry the tool's own status value in the status field of both files, e.g.
`hard_block`, or `fail (tool status: hard_block)` if a pass/fail rollup column is wanted.

**C3 — overall — minor.** Ambiguous study-level gate rollup. `result.json` marks
`required_metric_gate_DataCompleteness` as `fail`. PLAN Gates §1 defines that gate as a
precondition for granting a positive status, and it held for every sample that received one:
my re-runs show S01, S02 and S04 each returned `data_completeness: pass`. The only
`hard_block` is S05, whose outcome is correctly `cannot_certify` — no positive status was
granted on missing evidence. A reader scanning the gate table could misread the row as "a
positive status was granted despite a missing required metric", which did not happen.
**Fix:** relabel the rollup so it cannot be misread, e.g. "held for all positive statuses
(S01/S02/S04 data_completeness=pass); S05 blocked from certification and given no positive
status".

**C4 — S06 — minor.** `discrepancies` is an empty list, and it is technically compliant —
none of PLAN's triggers fired: `recommend_qc_thresholds(polyA)` matches CAPABILITIES.md's
threshold table field-for-field (rin 7/6, unique_mapping_rate 80/60, rrna_rate 10/15,
duplication_rate 20/50, nrf 0.8/0.5, exonic_rate 60/50, genes_detected 15000/10000, identical
hard-gate and required flags); S02's boundary values rin=7.0 and unique_mapping_rate=80.0
returned PASS, so no threshold-boundary discrepancy arises; and `compare_samples`' six verdicts
match all six per-sample verdicts. But two tool-internal tensions bear directly on S06's
`exclude` status and were not recorded anywhere: (a) the rrna_rate rationale string returned
with every assessment reads ">15% is a strong warning", while the band grammar
("pass<=10, warn<=15") places 22.4% beyond the warn band — that band, not the rationale, is
what made rrna_rate FAIL and drove the exclusion; (b) the protocol_consistency gate returned by
`assess_rnaseq_quality` for S06 applies a third rRNA cut, ">20%", which appears nowhere in the
metric grammar. A reviewer seeing `discrepancies: []` would conclude no such tensions exist.
**Fix:** append observational discrepancies, explicitly marked "no status change; the tool
verdict governs per PLAN", recording (a) the rrna_rate rationale-versus-band tension and (b)
the 20% protocol-consistency threshold absent from the metric grammar. Keep S06 = `exclude`.

**C5 — overall — minor.** PLAN's Optional Step 10 — call `explain_qc_metric` once for each
metric key that returned WARN or FAIL (duplication_rate, nrf, rin, rrna_rate) — was not
executed, and no record of the skip appears in `result.json` or RESULT.md. The step is
explicitly labelled optional, so this is not a rule violation, and the explanatory text
RESULT.md does carry is drawn from `assess_rnaseq_quality`'s per-metric `rationale` strings
rather than invented; but the report never states that the plan's dedicated explanation tool
went unused, so a reader cannot tell which tool the explanatory language came from.
**Fix:** either call `explain_qc_metric` for the four WARN/FAIL keys and cite those responses,
or add one line under limitations recording that Optional Step 10 was skipped and that metric
explanations are taken from `assess_rnaseq_quality` rationale strings.

**C6 — overall — minor.** Structural deviation from PLAN acceptance criterion 1, which
specifies `items`: "exactly six entries, keys S01-S06". `result.json` implements `items` as a
six-element JSON array whose entries carry an `id` field rather than as an object keyed by
sample id. The content is complete — all six entries are present with `status`, `overall`,
`phase`, `blockers`, `per_metric`, `input_metrics`, plus `warn_metrics` (S04), `fail_metrics`
and `hard_gate_failure` (S03, S06) and `missing_required` (S05) where the plan requires them —
so this is a shape difference only, not missing content.
**Fix:** either emit `items` as an object keyed S01-S06, or add a line to provenance noting
that the array-with-id form is a deliberate equivalent of the criterion's wording.

**C7 — S06 — minor.** Unexplained phase/hard-gate tension for S06. My re-run of
`assess_rnaseq_quality(S06)` returned `phase: QUARANTINED` while the same response's only FAIL
metric (rrna_rate) has `hardGate: false`, and `result.json` records `hard_gate_failure: false`
for S06. PLAN's decision table for FAIL reads "phase (QUARANTINED if a hard gate failed,
otherwise as returned)", so keeping the tool's phase is defensible — but the combination
"phase=QUARANTINED with hard_gate_failure=false" is stated in both files without any note that
the plan's parenthetical would lead a reader to expect a non-hard-gate FAIL not to be labelled
QUARANTINED. The S06 rationale in `result.json` also asserts the FAIL "is not a hard-gate
metric, so hard_gate_failure=false" without addressing why the phase is still QUARANTINED.
**Fix:** add one sentence to the S06 entry (and/or a discrepancy entry marked "no status
change") noting that the tool returned phase=QUARANTINED for a non-hard-gate FAIL, that the
plan's rule says to keep the returned phase, and that the status remains `exclude` either way.

**C8 — overall — minor.** Inconsistent field naming for gate records across the same file.
Per-sample gate objects in `result.json`'s `items` use a `gate` key (e.g. `{"gate":
"data_completeness", ...}`), while the study-level `gates` array uses a `name` key (e.g.
`{"name": "protocol_context", ...}`). Both are unambiguous in context and the content is
correct, but a consumer parsing gate records uniformly would need to handle two schemas in one
document. Verified by grep: no top-level gate record uses the `gate` key, and no per-sample
gate record uses `name`.
**Fix:** use one key (either `gate` or `name`) for gate records at both levels, or document the
two-level naming convention in the provenance block.

---

## Checks that came back clean

- **Per-sample statuses (all six).** Every status follows its own tool verdict exactly as the
  plan's decision table requires: S01 `include` ← `PASS`/`ANALYSIS_READY`; S02 `include` ←
  `PASS`/`ANALYSIS_READY` with rin=7.0 and unique_mapping_rate=80.0 returned PASS at the
  inclusive boundaries; S03 `exclude` ← `FAIL`/`QUARANTINED`, sole FAIL metric `rin` (hard
  gate), `hard_gate_failure=true`; S04 `flag_for_review` ← `WARN`/`FLAGGED`, WARN metrics
  `duplication_rate` (34) and `nrf` (0.71), both named; S05 `cannot_certify` ←
  `INCOMPLETE`/`QUARANTINED`, `missing=[rin]`, no imputation; S06 `exclude` ←
  `FAIL`/`QUARANTINED`, sole FAIL metric `rrna_rate` (22.4), `hard_gate_failure=false`.
- **No input value was ignored or altered.** All six `input_metrics` maps are byte-identical
  to `inputs/qc_metrics.json`, including S05's absent `rin` key, and the one value the brief
  singles out — S05's unrecorded RIN — is handled exactly as required (INCOMPLETE, no guess).
- **`compare_samples`.** Re-ran with the full unchanged six-sample map; the worst-first
  ranking (S05 INCOMPLETE, S03 FAIL, S06 FAIL, S04 WARN, S01 PASS, S02 PASS) is verbatim, and
  its verdicts agree with all six per-sample verdicts, so the empty cross-check discrepancy is
  correct.
- **Both confound checks.** Full design → `pass` ("batch and condition are not perfectly
  confounded"); retained design R = {S01, S02, S04} → `hard_block`. R equals
  `include` ∪ `flag_for_review` exactly.
- **`de_interpretable_as_is=false`** is derived exactly as PLAN Step 9 specifies, from
  `batch_confound_retained.response.status = hard_block` and nothing else.
- **`replicate_counts`** (per condition: ctrl 2, treated 1; per batch × condition: B1 2
  ctrl / 0 treated, B2 0 ctrl / 1 treated) re-derived by hand from `inputs/design.json`
  restricted to R, and labelled `source: "derived from design.json"`, not tool-computed.
- **Retained-set caveat honestly stated.** Both files carry the fact that treated libraries
  exist only in B2 and ctrl only in B1, so treatment and batch are inseparable in the retained
  design — the strongest remaining risk in the whole study, and it is stated rather than
  buried.
- **Gates §6 / `unassessed_checks`.** All four items PLAN forbids claiming (DownstreamGate /
  PreToolUse DE block, compbio multiple-testing gate, paired-end layout check, confidence-tier
  caps) are present and explicitly not claimed as passed.
- **Language calibration.** "Include" is framed as fitness for analysis under local policy,
  not biological signal; synthetic-data status is stated in both files; per-sample
  `confidence=1` is identified as a tool output rather than biological certainty.
- **Protocol context.** `recommend_qc_thresholds(polyA)` and `list_qc_metrics` both reproduce
  the recorded grammar exactly, and the two are consistent with each other, so the empty
  threshold discrepancy is correct.
- **No skipped hard gate.** PLAN Gates 1-4 are all addressed with tool evidence; nothing was
  marked pass without a re-runnable output behind it.

---

## Overall assessment

On the substantive question this relay stage was asked to answer, `result.json` and
`RESULT.md` are correct and fully reproducible: I re-ran all nine tool calls that decide a
status and every verdict, per-metric result, ranking entry, confound status, and threshold
value came back identical, so the six sample statuses, the retained set {S01, S02, S04}, and
the headline conclusion that a treated-versus-control DE contrast on the retained design is
not interpretable as-is all stand on solid evidence. The strongest remaining risk — that
treated libraries exist only in B2 and controls only in B1, making treatment and batch
inseparable — is stated plainly rather than buried, which is the right behaviour. What I found
is confined to the presentation and traceability layer, not the analysis: a provenance sentence
credits `inputs/` with text that only `BRIEF.md` contains (C1), one gate-status field relabels
the tool's `hard_block` as `fail` (C2), the DataCompleteness gate rollup could be misread as
though a positive status had been granted on missing evidence when it had not (C3), an empty
`discrepancies` list omits two tool-internal threshold tensions that bear on S06's exclusion
(C4), an optional explanation step went unrun and unrecorded (C5), `items` is shaped as an
array where the plan's acceptance criterion asks for keys (C6), S06's QUARANTINED phase is
left unexplained next to its `hard_gate_failure=false` (C7), and gate records use two different
field names for the same concept in one document (C8). None of these changes a status or the
interpretability verdict, and none is blocking — a downstream reader who applies the C1-C4
fixes would gain a report whose every field is traceable to its actual source.
**Responsible reviewer for the fixes:** the bioinformatics QC lead, per the report's own
escalation line.
