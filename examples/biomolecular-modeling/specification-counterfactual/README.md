# Specification counterfactuals: is it the question, or the predictor?

Requires **TOKN v0.3.75+**. This is an end-to-end, **GPU-free research
exercise**. It does not predict a structure, run a model or validate biology.

When two structure predictors disagree, the usual reaction is to run a third.
This assay tests a different explanation: **the folding question itself may be
underdetermined.** Stoichiometry, binding partner, ligand, conformational state
or construct boundaries are often unstated. If changing one of those choices
flips the answer you care about more than changing the predictor does, the
defensible next step is to **settle the question before choosing a predictor.**

TOKN makes that an executable test over a panel you declare:

```text
question facets (binary)  x  predictors (2-4)  x  family/lineage blocks
             |                     |
  same predictor, one facet   same question,
  differs -> question effect  different predictor -> predictor effect
```

Factorial designs and minimum hitting sets are established methods. Applying
them to decide *whether to review the question before predictor choice* is our
framing; its worldwide novelty is unverified.

## 1. Dependencies and a first run

Only **TOKN** is needed. No GPU, Docker, Python, credentials, internet,
weights or model is used, and no file is written.

```powershell
Get-Command tokn -ErrorAction Stop
tokn version          # must report 0.3.75 or later
tokn biomol research --help
tokn biomol research demo
```

```sh
command -v tokn && tokn version
tokn biomol research --help
tokn biomol research demo
```

If TOKN is missing, follow the [installation guide](../../../GETTING_STARTED.md).

## 2. Read the input before running it

`question-underdetermined.json` declares one facet, two predictors and two
families:

| Field | Meaning |
|---|---|
| `basis` | `synthetic` (invented) or `externally_declared` (your own records) |
| `facets` | 1-5 of `stoichiometry`, `partner_context`, `ligand_context`, `state_context`, `construct_context` |
| `specifications` | Every `a`/`b` combination of the facets exactly once (2^facets), with numeric IDs |
| `predictors` | 2-4 numeric IDs. Names stay outside TOKN |
| `blocks` | One per `(family, lineage)`, each holding a full specification x predictor grid |
| `predicate` | Your decision-relevant yes/no: `present`, `absent` or `unresolved` |
| `global_class` | 1-16 label for "which overall structural answer", used only as context |
| `max_comparisons` | 1-200000 in-memory comparisons reserved before work starts |

Inputs are **target-free by design**: no sequences, names, files or
coordinates. The `a`/`b` alternatives are opaque; your notebook maps them to
"homodimer vs monomer", "apo vs holo" and so on. Unknown, missing, `null` or
mis-cased fields are rejected without echoing their content.

The predicate is the important design choice. Pick the structural fact that
would change your next decision, e.g. "is the pocket open?" or "is the
interface helix buried?" Full-structure agreement is shown separately in
`global_class` because two predictions can disagree globally yet agree on
the fact you need.

## 3. Run the supported case end to end

From this directory:

```powershell
$report = tokn biomol research analyze --input (Resolve-Path .\question-underdetermined.json).Path | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Panel not analyzed: $($report.stop_reason)" }
$report | Select-Object status, question_status, next_step, stop_reason
$report.specification; $report.predictor
$report.best_resolutions | ConvertTo-Json
```

```sh
tokn biomol research analyze --input "$PWD/question-underdetermined.json"
```

Expected key fields:

```json
"status": "supported_in_declared_panel",
"question_status": "underdetermined_within_declared_blocks",
"next_step": "review_question_facets_before_predictor_choice",
"specification": {"pairs": 4, "predicate_flips": 4, "global_disagreements": 0},
"predictor":     {"pairs": 4, "predicate_flips": 0, "global_disagreements": 4},
"best_resolutions": [{"facets": ["stoichiometry"], "remaining_conflict_pairs": 0}],
"comparisons": 14, "model_calls": 0, "authority": "none"
```

**Think-aloud reading.** Changing the stoichiometry flipped the predicate in
4 of 4 same-predictor pairs. Swapping predictors flipped it 0 of 4 times,
even though the predictors disagreed on the *global* answer every time. So
the predictors disagree in a way that does not matter for this decision, while
the unstated stoichiometry does. Both families point the same way. Resolving
`stoichiometry` alone removes every question-driven conflict. Running a third
predictor would not answer the question that actually decides the outcome.

`conflict_pairs` (8) counts every disagreeing pair. `question_conflict_pairs`
(4) counts the subset with the same predictor and a different question; only
these can certify a facet. `confounded_conflict_pairs` (4) differ in both
question and predictor, so they deliberately cannot. `irreducible_conflict_pairs`
are same-question predictor disagreements. `question_resolution_possible` is
true only on a supported result with no irreducible conflicts. On abstaining
reports, `best_resolutions` is a diagnostic, never an instruction; a listed
facet with leftover conflicts means "settle this, then still review the
predictors".

## 4. The full fixture set

Run them all and compare with the table:

```powershell
foreach ($f in Get-ChildItem *.json) {
  $r = tokn biomol research analyze --input $f.FullName 2>$null | ConvertFrom-Json
  '{0,-30} exit={1} {2,-32} {3}' -f $f.Name, $LASTEXITCODE, $r.status, $r.stop_reason
}
```

```sh
for f in *.json; do
  tokn biomol research analyze --input "$PWD/$f" >/dev/null 2>&1; echo "$f exit=$?"
done
```

| Fixture | Exit | Status / stop | What it teaches |
|---|---|---|---|
| `question-underdetermined.json` | 0 | supported / `question_review_required` | Question drives the flip; review `stoichiometry` first |
| `multi-facet-resolution.json` | 0 | supported / `question_review_required` | Three facets; only `ligand_context` must be settled |
| `predictor-dominant.json` | 0 | not supported / `predictor_variation_dominates` | Predictor choice drives the flip; no facet is credited |
| `heterogeneous-blocks.json` | 0 | abstained / `heterogeneous_block_effects` | Families disagree on the direction; no claim |
| `single-family.json` | 0 | abstained / `insufficient_declared_families` | One family cannot support a direction |
| `incomplete-panel.json` | 1 | abstained / `incomplete_factorial_panel` | Missing cell; nothing is inferred |
| `budget-stop.json` | 1 | abstained / `comparison_budget_insufficient` | 14 comparisons needed, 3 allowed; stops before work |

Exit 0 means **the analysis completed**, including complete abstentions. Exit
1 means it could not be analyzed; the abstaining report still prints so you can
see why. Scripts should check both the exit code and `status`.

### Multi-facet: find the smallest question to settle

```powershell
$m = tokn biomol research analyze --input (Resolve-Path .\multi-facet-resolution.json).Path | ConvertFrom-Json
$m.facet_effects | Format-Table
$m.best_resolutions | ConvertTo-Json
```

| Facet | Same-predictor pairs | Predicate flips | Global disagreements |
|---|---|---|---|
| `stoichiometry` | 16 | 0 | 0 |
| `ligand_context` | 16 | 16 | 0 |
| `state_context` | 16 | 0 | 16 |

`state_context` changes the global structure every time but never the
decision predicate. `ligand_context` is the only facet worth resolving, and
`best_resolutions` reports exactly `["ligand_context"]` from the eight-subset
search (248 comparisons). Without the predicate/global split, the larger
global change would have drawn attention to the wrong facet.

### Predictor-dominant: an honest refutation

Here the predicate follows the predictor, not the question. `status` is
`not_supported_in_declared_panel`, `question_conflict_pairs` is 0 and
`best_resolutions` is `[{"facets": [], "remaining_conflict_pairs": 8}]`:
no question facet would remove any conflict. The four
`irreducible_conflict_pairs` are same-question predictor disagreements. TOKN's
`next_step` stays the generic `review_declared_panel`; deciding to examine
predictor evidence is your follow-up, not an instruction from the assay.

### Heterogeneous and single-family: why it abstains

`heterogeneous-blocks.json` contains one question-dominant family and one
predictor-dominant family. Pooling them would hide the disagreement, so TOKN
abstains and `question_status` stays `not_established`. A single family
likewise cannot separate a question effect from that family's quirks.

A direction needs **concordant dominant blocks in at least two distinct
families**. Extra lineages within one family, or a second family whose rates
tie, add no support and abstain with `insufficient_concordant_families`.
A tied third family does not veto two concordant families either.
If every block ties with real flips, the result is `tied_block_effects`.

## 5. Three ways to work through it

The same assay serves different experience levels. Choose your path.

### Beginner: worked -> partial -> problem-only

1. **Worked.** Run section 3 and read the think-aloud aloud. Answer: why does
   4/4 global disagreement between predictors *not* mean "run a third one"?
2. **Partial.** Copy `question-underdetermined.json` to `my-panel.json` and in
   block 2 change every `"present"` to `"absent"`. Predict the status before
   running. (Block 2 becomes stable and ties, so only one family points in a
   direction: TOKN abstains with `insufficient_concordant_families`.) Then
   run it with an absolute path, and explain why that abstention is correct.
3. **Problem only.** Make a panel that returns
   `predictor_variation_dominates` without looking at `predictor-dominant.json`.
   Then diff against it.

### Intermediate: design the predicate

1. For a system you know, write three candidate predicates and say which
   decision each one would change. Keep the mapping outside TOKN.
2. Reproduce the multi-facet result, then edit observations so
   `state_context` also flips the predicate. Predict `best_resolutions` before
   running. (Expect two facets to be needed.)
3. Use `tokn biomol uncertainty compile` from the
   [uncertainty compiler](../uncertainty-compiler/README.md) to plan which
   missing evidence to collect *after* the question is settled.

### Research: falsify the hypothesis on your own records

1. Switch `basis` to `externally_declared` and encode your recorded
   predictions as opaque IDs. Use different `family` values only for genuinely
   different target families, and give runs sharing MSAs, templates or training
   lineage the same `lineage` label. TOKN cannot verify independence.
2. Pre-register which predicate and facets you will test, then run once.
   Report abstentions and refutations as readily as support.
3. Stress it: duplicate a family under a new label and confirm that the result
   could look stronger. That is why family/lineage labels are assertions
   you must justify, not evidence.
4. Use the [adaptive research journey](../adaptive-journeys/README.md) to
   practise transfer to novel evidence afterwards.

## 6. Limits you must keep

- Every observation, alternative and label is **your assertion**. Support is
  descriptive for this declared panel, not biological validation, statistical
  significance or population generalization.
- Binary alternatives do not exhaust real questions; omitted factors and
  shared training or inputs can confound results.
- Resolutions are combinatorial certificates within each block, not
  probabilities or a promise that settling the question improves biology.
- `authority: none`, `runtime_approval: separate_admission_required` and
  `model_calls: 0` are fixed. Nothing here approves or launches a job.
- Comparisons count in-memory pairs, not money, tokens or model calls.

Related: [biomolecular overview](../README.md) ·
[uncertainty compiler](../uncertainty-compiler/README.md) ·
[adaptive journeys](../adaptive-journeys/README.md) ·
[shadow routing](../shadow-routing/README.md)
