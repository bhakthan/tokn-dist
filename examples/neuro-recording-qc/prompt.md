# Task: data-quality review of six recordings before a group analysis

You are a neuroimaging data steward. A lab is about to run a **group analysis** across six de-identified human recordings (three task fMRI runs and three EEG sessions). Before any recording enters the group model, they want a defensible review of signal quality, motion and artifact thresholds, and ethics/consent coverage.

The data is synthetic but realistic. Everything you need is in `demo-input/`:

| File | Contents |
|---|---|
| `demo-input/recordings.json` | Per-recording modality, file path, and QC metrics: fMRI mean framewise displacement (mm), censored-frame fraction and tSNR; EEG peak amplitude (μV) and epoch-acceptance fraction |
| `demo-input/ethics.json` | Per-recording IRB approval, protocol ID, expiry date and consented analysis scope |

The review date is **2026-11-06**. The planned analysis scope is `group_analysis`.

## Items to assess

`REC-01`, `REC-02`, `REC-03`, `REC-04`, `REC-05`, `REC-06`

## Status vocabulary (use exactly one per item)

- `ready`: passes every modality quality gate and the ethics gate.
- `ready_with_caveats`: passes every gate, but the ethics check raises a warning (for example, an IRB protocol that expires within 30 days of the review date). State the caveat.
- `exclude`: ethics gate passes, but at least one modality quality gate fails.
- `blocked`: the ethics gate fails (no IRB, expired IRB, malformed protocol ID, or the planned analysis scope is not covered by the consented scope). Do not analyse it, however good its signal looks.

## Rules

1. **The ethics gate comes first.** A `blocked` cause overrides any quality result. The IRB gate sits at `ETHICS_GATE`, before any analysis of human data.
2. fMRI gates: framewise displacement at most 0.5 mm, censored frames at most 20%, tSNR at least 40.
3. EEG gates: peak amplitude at most 150 μV, epoch acceptance at least 70%.
4. Threshold comparisons are as the TOKN neurosci validators implement them: a value exactly on a threshold passes.
5. Valid protocol IDs match `IRB-YYYY-NNN…`, `Pro########`, `STUDY######` or `H##-###`. The consented scope must contain the planned analysis scope.
6. Use the neurosci domain tools (`inspect_nwb`, `validate_bids`, `compute_quality_metrics`) on the listed files. If a tool cannot run because a dependency (pynwb, bids-validator, SpikeInterface) or the file is missing, say exactly which, and grade from the supplied metrics against the gates above. Do not invent metrics.

## Deliverable

Write `RESULT.md` with a table of item, status and the tool evidence for it, plus a short note for the reviewer. Also write `result.json` mapping each item ID to its status, for example `{"REC-01": "<status>"}`.
