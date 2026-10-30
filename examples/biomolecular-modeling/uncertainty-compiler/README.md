# Uncertainty compiler: investigate the decision before spending on a fold

Requires **TOKN v0.3.73+**. This is an end-to-end, **GPU-free operational
reasoning exercise**. It does not predict a structure, generate biological
hypotheses or establish that an objective truly does not need a structure.

The unconventional move is to ask: **what evidence would change the next
decision?** TOKN compiles a closed objective and existing observations into
operational explanations, evidence gaps, a next step and an explicit stop.
Then it checks whether irrelevant changes can disturb that reasoning.

## 1. Dependencies and a complete first run

Offline commands need **only TOKN**. No GPU, Docker, Python, Node, credentials,
internet, weights or scientific model is required. PowerShell's JSON tools are
built in; POSIX users can read the emitted JSON directly.

```powershell
Get-Command tokn -ErrorAction Stop
tokn version
tokn biomol uncertainty --help
tokn biomol uncertainty demo
```

```sh
command -v tokn
tokn version
tokn biomol uncertainty --help
tokn biomol uncertainty demo
```

If TOKN is missing, follow the [installation guide](../../../GETTING_STARTED.md).
The demo emits a synthetic plan and its reasoning-check report. No file is
created and no model is called. A passing check validates tested software
properties, **not folding accuracy or scientific truth**.

## 2. Begin with the evidence gap, not a third predictor

From this directory:

```powershell
$inputFile = (Resolve-Path .\evidence-gap.json).Path
$plan = tokn biomol uncertainty compile --input $inputFile | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Uncertainty compilation failed" }
$plan | ConvertTo-Json -Depth 12
$plan | Select-Object rules_decision, decision, next_step, stop_reason, cost_status
```

```sh
tokn biomol uncertainty compile --input "$PWD/evidence-gap.json"
```

Our invented observations say Boltz-2 and Chai-1 completed, but Boltz-2's
metrics are absent. The observer declares 90% confidence; that declaration is
**not evidence that the structure or decision is correct**.

| Possible operational explanation | Evidence that distinguishes it |
|---|---|
| A computation failed | Recorded outcome, rather than observer confidence |
| Required metric evidence is missing | `metrics_present` on completed observations |
| Existing predictions need comparison | At least two usable completed observations |
| An untried predictor might be considered | Existing eligibility rules and unresolved evidence |

These explanations are not necessarily mutually exclusive. They are not
biological mechanism hypotheses, probabilities or diagnostic labels.
The defensible immediate action is **collect missing evidence**, not compare
incomplete results or automatically launch another predictor.
`explanations` contains the record-status alternatives; `rules_decision`
preserves the original adviser choice, while `decision` and `next_step` describe
the immediate evidence-first response. `stop_reason` identifies its boundary.

“Cheapest” here means an evidence/review step with **no model call** before
new computation. TOKN does not claim measured value of information, global
cost optimality or an inferred GPU speedup. All runtime approvals and
scientific acceptance remain separate.

## 3. Test the reasoning without a GPU

```powershell
$check = tokn biomol uncertainty check-reasoning --input $inputFile |
    ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Reasoning checks failed or were incomplete" }
$check | Select-Object passed, complete, checks, failures
```

```sh
tokn biomol uncertainty check-reasoning --input "$PWD/evidence-gap.json"
```

The checker applies bounded deterministic variants:

- Reorder predictor observations: a list's presentation must not change the
  decision.
- Vary declared observer confidence: confidence must not fill an evidence gap.
- Vary valid reported costs or provenance: these must not manufacture
  acceptance or override missing evidence.
- Probe meaningful evidence boundaries, such as missing metrics and failure,
  where applicable to the objective.

It compares decision and authority properties, not byte-for-byte explanation
text. **Allowed-adapter ordering is a real policy preference**, so changing it
is not falsely treated as an irrelevant perturbation.
`results` distinguishes executed passes, failures, inapplicable transformations
and budget-skipped cases. The evidence-gap fixture executes 12 compiler
evaluations including baseline; the structure-not-required fixture executes
three, with observation-dependent checks honestly inapplicable.

The implementation tests also inject deliberately brittle compiler behavior
to establish that the checker detects drift. This CLI tests the built-in
offline compiler, **not arbitrary live models or external agents**.

### An honest incomplete result

```powershell
tokn biomol uncertainty check-reasoning --input (Resolve-Path .\budget-stop.json).Path
if ($LASTEXITCODE -eq 0) { throw "Expected incomplete-check failure" }
```

```sh
if tokn biomol uncertainty check-reasoning --input "$PWD/budget-stop.json"; then
  echo "Expected incomplete-check failure" >&2
  exit 1
fi
```

This input permits only one check. The report is incomplete, cannot claim
`passed: true`, and the CLI exits nonzero. `max_checks` is a count of offline
check cases—not a currency, token or time estimate.

## 4. Stop if the declared decision does not need a structure

```powershell
tokn biomol uncertainty compile --input (Resolve-Path .\structure-not-required.json).Path
```

```sh
tokn biomol uncertainty compile --input "$PWD/structure-not-required.json"
```

This uses `objective: structure_necessity` and explicitly declares
`decision_requires_structure: false`. TOKN produces the evidence-led stop
`structure_not_required_by_declared_objective`.

**The distinction matters:** the operator declared this requirement. TOKN did
not infer biological irrelevance or prove a fold unnecessary. Review the real
objective with an appropriate expert before relying on that declaration.
If it is true instead, compilation may plan evidence checks, but cannot mint
permission to run a model.

## 5. Intermediate: audit what already exists

```powershell
tokn biomol uncertainty compile --input (Resolve-Path .\audit-existing.json).Path
tokn biomol uncertainty check-reasoning --input (Resolve-Path .\audit-existing.json).Path
```

```sh
tokn biomol uncertainty compile --input "$PWD/audit-existing.json"
tokn biomol uncertainty check-reasoning --input "$PWD/audit-existing.json"
```

Both recorded predictors completed with metrics. This objective audits
existing prediction evidence: comparison/inspection precedes unnecessary new
compute. A recommendation to compare **does not actually compute structural
agreement**, validate the metrics or establish which prediction is correct.

## 6. Research-level use: challenge the plan

Before reading a report, write down which operational observation should
change the next step. In a caller-owned copy outside the repository:

1. Replace one completed observation's metric-presence flag with false.
2. Predict the collection hold before replaying.
3. Record which independently reviewed evidence would actually resolve the
   scientific uncertainty, rather than merely completing this software test.

Do not turn the compiler's own recommendation into an “independent” scientific
reference. Combine these exercises with the
[adaptive journeys](../adaptive-journeys/README.md) for skill-specific support,
confidence-error remediation and independent-fixture disagreements.

The schema is `tokn.biomol-uncertainty/1`. Objectives are closed:
`next_action`, `structure_necessity`, `audit_prediction_evidence`.
No biological target, arbitrary question, sequence, coordinate, identifier,
path, raw log or free-text note is accepted. Uploaded observations remain
assertions; completed processes and matching opinions do not establish
acceptance. Compilation is offline, target-free and advisory only.
