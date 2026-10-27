# Example: Decision circuits — replace keyword `if`s with typed, testable decisions

> "Our refund bot decides with keyword lists and regexes. How do we turn that
> into something we can test, reason about, and ship as plain code?"

A **decision circuit** is a JSON file that asks a model a few typed questions
(`choice`, `score` or `noul`, a yes/no probability) and wires the answers into
fixed logic. Each answer becomes `true`, `false` or `unknown`, using explicit
thresholds. An ordered switch then picks one label from a closed list.
`unknown` never falls through to a later arm: it goes to `on_unknown`, usually
a human.

Circuit outputs are **advisory labels** for your own code to act on. They are
never permissions, approvals or safety gates. Your application still enforces
its own rules.

This walkthrough uses only the offline subcommands of `tokn circuit`:

| Step | Command | What it does |
|---|---|---|
| 2 | `packs` | Lists and exports built-in starter circuits |
| 3 | `validate`, `analyze` | Strict parse; unreachable arms, abstain paths, noise margins |
| 4–6 | `test` | Replays recorded answers (test vectors) and checks the label |
| 7 | `gen` | Compiles a circuit into a dependency-free Python or TypeScript module with tests |
| 8 | `detect`, `draft` | Finds fuzzy decisions in code and drafts a circuit from them |
| 9 | `profile` | Maps table columns to decision candidates |
| 10 | `threshold` | Proposes a yes/no cutoff from the cost of each mistake |
| 11 | `explain`, `ledger` | Explains a saved trace; reviews and overrides logged decisions |

`run`, `batch` and `eval` call a model. Step 12 covers them briefly.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.68 or later | Ships `tokn circuit` | `tokn circuit --help` |
| This folder | Fixture circuit, vectors, code, table, trace and ledger | — |
| Python 3.9 or later (step 7 only) | Runs the generated module's tests | `python --version` (or `python3 --version`) |

It runs on every tier, including the free Community tier. No credentials are
needed. On an expired trial TOKN prints a "community tier" banner to stderr;
it does not affect these commands.

### What leaves your machine

Nothing, in steps 1–11. Every command reads local files and prints a report.
TOKN writes session logs under `.tokn/logs/` in the current folder. Only
`run`, `batch` and `eval` (step 12) send data to a model backend, and
`--air-gap` blocks all three.

## 1. Copy the example to a working folder

Some steps write files, and step 11 appends to a ledger. Work on a copy.

bash:

```bash
cp -r examples/decision-circuits "$HOME/tokn-circuits"
cd "$HOME/tokn-circuits"
```

PowerShell:

```powershell
Copy-Item -Recurse examples\decision-circuits "$HOME\tokn-circuits"
Set-Location "$HOME\tokn-circuits"
```

| File | What it is |
|---|---|
| `refund-triage.v1.circuit.json` | A first draft of a refund triage circuit, with three mistakes |
| `refund-triage.circuit.json` | The fixed circuit |
| `refund-triage.vectors.json` | Seven test vectors: recorded answers and the expected label |
| `app/refund_handler.py` | A small handler that decides with keyword lists and regexes |
| `tickets.csv` | Twelve synthetic refund tickets |
| `sample-trace.json` | A hand-written trace in the shape `circuit run` prints |
| `sample-ledger.jsonl` | Three hand-written ledger records in the shape `circuit run --ledger` writes |

The commands below are the same in bash and PowerShell unless both are shown.

## 2. Start from a built-in starter pack

```bash
tokn circuit packs list
```

Expected:

```text
DOMAIN       ID                               VERSION  GATES  VECTORS  OUTPUTS
batterypass  supplier-due-diligence-evidence  1.1.0    8      21       sufficient_evidence, request_more_evidence, red_flag_review, human_review
finrisk      aml-alert-disposition            1.1.0    7      23       close_documented_false_positive, enhanced_review, escalate_investigation, human_review
finrisk      complaint-regulatory-routing     1.1.0    7      21       compliance_review, fraud_ops, priority_servicing, standard_servicing, human_review
geospatial   scene-quality-triage             1.1.0    6      19       usable_scene, usable_with_masking, remask_required, reject_scene, human_review
legalai      contract-clause-risk             1.1.0    8      22       standard_accept, negotiate, counsel_review, human_review
legalai      privilege-triage                 1.1.0    7      20       not_privileged_release_candidate, privilege_hold, counsel_review, human_review

Show: tokn circuit packs show <id>   Compile: tokn circuit gen --pack <id> --lang python --out <dir>
```

Filter with `--domain finrisk`. Save the complaint-routing pack and its test
vectors so you can edit them:

```bash
tokn circuit packs export complaint-regulatory-routing --out pack
```

Expected:

```text
wrote pack/complaint-regulatory-routing.circuit.json
wrote pack/complaint-regulatory-routing.vectors.json
```

Open the circuit. It has seven gates (one `choice`, one `score`, five `noul`),
one signal, six ordered arms, and `"on_unknown": "human_review"`. Its
`excluded_uses` say what it must not be used for, for example "Not a
determination that a UDAAP, fair-lending ... violation occurred".

`--out` is relative to `--root` (default `.`), and output cannot escape the
root. It refuses to overwrite existing files unless you pass `--force`.

## 3. Validate and analyze

```bash
tokn circuit validate pack/complaint-regulatory-routing.circuit.json
```

Expected:

```text
valid tokn.decision-circuit/1 complaint-regulatory-routing@1.1.0
  hash: sha256:8b80e14794310b19d5bb9edf8e0c749e6b9c918913f3741d75281263611dec15
  gates: 7 in 1 stage(s)  signals: 1  arms: 6
  outputs: compliance_review, fraud_ops, priority_servicing, standard_servicing, human_review
  default: human_review  on_unknown: human_review
```

The parse is strict: unknown fields, duplicate keys and nulls are errors. The
hash identifies this exact circuit in traces and ledgers.

```bash
tokn circuit analyze pack/complaint-regulatory-routing.circuit.json
```

Expected:

```text
complaint-regulatory-routing@1.1.0: 11664 abstract state(s), exhaustive
reachable outputs:
  compliance_review                yes
  fraud_ops                        yes
  human_review                     yes
  priority_servicing               yes
  standard_servicing               yes
findings:
  info  ABSTAIN_REACHABLE  switch.on_unknown  circuit abstains to "human_review" in 46.3% of all 11664 abstract states
  info  NO_GOVERNANCE      governance         circuit declares no governance (owner, risk tier, safe default); outcomes have no accountable owner on record
```

`analyze` makes no model call. It enumerates every combination of
`true` / `false` / `unknown` per gate (and each option of a `choice`). The
46.3% is a share of those combinations, not a forecast of how often a model
will abstain. Add `--json` to either command for machine-readable output.

## 4. Test the pack with its vectors

A vector is a set of recorded answers and the label you expect. `test`
replays them through the same engine `run` uses, with no network.

```bash
tokn circuit test pack/complaint-regulatory-routing.circuit.json --vectors pack/complaint-regulatory-routing.vectors.json
```

Expected (shortened):

```text
PASS  routine_fee_dispute_to_standard_servicing -> standard_servicing (standard)
PASS  product_inquiry_to_standard_servicing -> standard_servicing (standard)
PASS  fair_lending_allegation_to_compliance -> compliance_review (fair_lending)
...
PASS  udaap_noise_band_abstains -> human_review
PASS  fraud_noise_band_abstains -> human_review
PASS  category_low_margin_abstains -> human_review
...
21 passed, 0 failed
```

The name in brackets is the arm that fired. Lines with no arm went to
`default` or `on_unknown`. `test` exits 1 if any vector fails, so it works as a
CI check.

## 5. Your own circuit: let `analyze` find the mistakes

`refund-triage.v1.circuit.json` routes a refund request with two gates:
`reason` (a `choice`: damaged, late, changed_mind, other) and `threat` (a
`noul`: does the customer threaten a chargeback or legal action?).

```bash
tokn circuit analyze refund-triage.v1.circuit.json
```

Expected:

```text
refund-triage@0.1.0: 15 abstract state(s), exhaustive
reachable outputs:
  auto_refund                      yes
  human_review                     yes
  partial_refund                   NO
  store_credit                     yes
findings:
  warning  NO_NOISE_MARGIN        gates.threat                   noul gate has no noise band (false_at == true_at == 0.5): borderline answers flip between true and false instead of reading unknown
  warning  OUTPUT_NEVER_PRODUCED  switch.outputs.partial_refund  output is never produced in any abstract state
  warning  UNREACHABLE_ARM        switch.arms.late_only          arm never fires in any abstract state; an earlier arm always decides first or its condition is never true
  info     ABSTAIN_REACHABLE      switch.on_unknown              circuit abstains to "human_review" in 40.0% of all 15 abstract states
  info     NO_GOVERNANCE          governance                     circuit declares no governance (owner, risk tier, safe default); outcomes have no accountable owner on record
```

What went wrong:

- **No noise margin.** With `true_at` and `false_at` both 0.5, an answer of
  0.49 reads as a confident "no". There is no room for "not sure".
- **Unreachable arm.** `late_only` comes after `damaged_or_late`, which
  already handles every `late` case, so `partial_refund` can never happen.
- **No governance.** Nobody owns the outcome.

`refund-triage.circuit.json` fixes all three. Diff the two files to see how:

- `threat` now has a noise band (`true_at` 0.6, `false_at` 0.3).
- `late_only` and `partial_refund` are gone.
- A `governance` block names an owner, `risk_tier` 2 and a `safe_default`.
  The tier fills in any threshold a gate leaves unset. Here that gives `reason`
  a confidence floor of 0.70 and a margin of 0.25.
- A `pre_guard` sends orders of 500 or more to `manager_review` before any
  model is asked. Exact rules stay deterministic code.

```bash
tokn circuit analyze refund-triage.circuit.json
```

Expected:

```text
refund-triage@1.0.0: 15 abstract state(s), exhaustive
reachable outputs:
  auto_refund                      yes
  human_review                     yes
  manager_review                   yes
  store_credit                     yes
findings:
  info  ABSTAIN_REACHABLE  switch.on_unknown  circuit abstains to "human_review" in 40.0% of all 15 abstract states
```

`analyze` exits 0 even with warnings. In CI, add `--fail-on-warn` to exit 1
when any warning is reported; the draft above would fail, the fixed circuit
passes.

## 6. Test both versions with the same vectors

```bash
tokn circuit test refund-triage.circuit.json --vectors refund-triage.vectors.json
```

Expected:

```text
PASS  damaged_item_auto_refund -> auto_refund (damaged_or_late)
PASS  changed_mind_store_credit -> store_credit (changed_mind)
PASS  chargeback_threat_to_human -> human_review (threat)
PASS  borderline_threat_abstains -> human_review
PASS  unclear_reason_abstains -> human_review
PASS  other_reason_defaults_to_human -> human_review
PASS  large_order_forced_to_manager -> manager_review
7 passed, 0 failed
```

Now run the same vectors against the draft:

```bash
tokn circuit test refund-triage.v1.circuit.json --vectors refund-triage.vectors.json
```

Expected (exit status 1):

```text
PASS  damaged_item_auto_refund -> auto_refund (damaged_or_late)
PASS  changed_mind_store_credit -> store_credit (changed_mind)
PASS  chargeback_threat_to_human -> human_review (threat)
FAIL  borderline_threat_abstains -> auto_refund (damaged_or_late)
FAIL  unclear_reason_abstains -> auto_refund (damaged_or_late)
PASS  other_reason_defaults_to_human -> human_review
FAIL  large_order_forced_to_manager -> human_review
4 passed, 3 failed
```

Each failure maps to a fix from step 5:

- A threat score of 0.45 counted as "no threat", because there was no noise
  band.
- A `damaged` 0.45 vs `late` 0.40 split was trusted, because there was no
  margin check.
- The 900-dollar order was not forced to a manager, because there was no
  pre-guard.

Open `refund-triage.vectors.json` to see the answer format. A `choice` answer
needs `probabilities` over every option when a margin applies.

## 7. Generate an embeddable Python module

`gen` compiles the circuit into one standard-library-only module, a test file
that replays your vectors, and a README.

```bash
tokn circuit gen refund-triage.circuit.json --lang python --out gen --vectors refund-triage.vectors.json
```

Expected:

```text
wrote …/gen/refund_triage.py
wrote …/gen/test_refund_triage.py
wrote …/gen/README.md
```

Add `--dry-run` to list the files first, or `--lang typescript` for a `.ts`
module. To compile a pack directly, use `--pack complaint-regulatory-routing`
in place of the file; its vectors are included automatically. `--out` must be
a new folder: `gen` refuses to write into an existing one.

Run the generated tests. They use fake clients, so no network or key is
needed:

bash:

```bash
cd gen
python3 -m unittest
```

PowerShell:

```powershell
Set-Location gen
python -m unittest
```

Expected (shortened):

```text
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
```

That is your seven vectors plus six built-in checks, such as "a pre-guard
forces an output without a model call" and "unsure cannot be ignored".

You can also replay answers from your own code, still offline. Save this as
`replay.py` in `gen/` and run it:

```python
from refund_triage import evaluate_answers, explain

d = evaluate_answers({
    "reason": {"type": "choice", "choice": "late", "confidence": 0.9,
               "probabilities": {"damaged": 0.05, "late": 0.85, "changed_mind": 0.05, "other": 0.05}},
    "threat": {"type": "noul", "noul": 0.1},
})
print(d.status, d.output.value, d.unsure)
d = evaluate_answers({}, state={"order_total": 750})
print(d.status, d.output.value, d.pre_guard)
d = evaluate_answers({"threat": {"type": "noul", "noul": 0.45}})
print(d.status, d.output.value, d.unsure)
print(explain(d))
```

Expected:

```text
AUTO auto_refund False
FORCED manager_review large_order
ABSTAIN human_review True
Advisory output=human_review; reason=UNKNOWN_ABSTAIN; arm=(none); abstained=true; requests=0
```

In production you call `decide(state)`, which asks a System One backend. The
generated `gen/README.md` lists the environment variables for each backend.
When the circuit abstains, `d.label` is an `Unsure` value, not an `Output`, so
your code must handle that case explicitly. Go back up with `cd ..`.

## 8. Find fuzzy decisions in existing code

`detect` scans Python, TypeScript/JavaScript and Go for decisions that are
really judgments about meaning. It only reads files.

```bash
tokn circuit detect app
```

Expected:

```text
app/refund_handler.py:15  KEYWORD_LIST  [medium, suggest choice]
    if any(word in text for word in ANGRY_WORDS):
    why: Several natural-language words are matched against free text; lexical membership may stand in for a judgment about meaning.
app/refund_handler.py:17  REGEX_ON_TEXT  [low, suggest noul]
    if DAMAGE_PATTERN.search(message):
    why: A regular expression is applied to a text-like value; check whether it recognizes exact syntax or approximates meaning.
app/refund_handler.py:20  LLM_OUTPUT_PARSE  [high, suggest noul]
    if "yes" in reply.lower():
    why: A likely language-model answer is interpreted with a string comparison; a typed question avoids prose parsing and makes abstention explicit.
app/refund_handler.py:23  SCORE_THRESHOLD  [medium, suggest score]
    if sentiment < 0.35:
    why: A fuzzy score is compared with a numeric cutoff; use an explicit ordered rubric and measure the threshold on held-out examples.
4 decision point(s). Draft a circuit: tokn circuit draft <dir> --id <circuit-id>
```

The exact rule `order_total >= 500` is not flagged. It should stay ordinary
code, or become a `pre_guard` as in step 5. Test files are skipped unless you
pass `--include-tests`.

`draft` turns the findings into a starting circuit. It prints JSON to stdout;
save it to a file:

bash:

```bash
tokn circuit draft app --id refund-draft > refund-draft.circuit.json
tokn circuit validate refund-draft.circuit.json
```

PowerShell:

```powershell
tokn circuit draft app --id refund-draft > refund-draft.circuit.json
tokn circuit validate refund-draft.circuit.json
```

Windows PowerShell 5.1 writes `>` as UTF-16, and `Out-File -Encoding utf8`
adds a BOM. Circuit commands accept both, so no workaround is needed.

Expected from `validate`:

```text
valid tokn.decision-circuit/1 refund-draft@0.1.0
  hash: sha256:3a1f24b00773d3e57d0438202088d0eb58b68fd4def9b0532d3670f24cf4eaa1
  gates: 4 in 1 stage(s)  signals: 0  arms: 4
  outputs: refund_handler_keyword_list_15, refund_handler_regex_on_text_17, refund_handler_llm_output_parse_20, refund_handler_score_threshold_23, no_match, human_review
  default: no_match  on_unknown: human_review
```

The draft is valid but generic. Its description starts with `DRAFT: edit
questions, categories, evidence, thresholds, arm priority and test vectors
before integration`. The gate names come from file and line numbers, and the
keyword list becomes a `choice` over the words themselves. Compare it with the
hand-written `refund-triage.circuit.json`. That is the kind of edit a person
still has to make.

## 9. Profile a table for decision candidates

`profile` looks at each column of a CSV or JSONL table. It suggests which
columns could be a model's decision and which should stay deterministic.

```bash
tokn circuit profile tickets.csv
```

Expected:

```text
Decision Map  tickets.csv  (12 rows, 7 columns)

COLUMN         SEMANTIC          PRIMITIVE      FITNESS  BAND     PAIRED TEXT  SENSITIVITY
ticket_id      identifier        deterministic  0.00     exclude  -            none
created_at     timestamp         deterministic  0.00     exclude  -            none
order_total    numeric_measure   deterministic  0.00     exclude  -            none
channel        system_attribute  deterministic  0.00     exclude  -            none
refund_reason  category          route          0.74     propose  message      none
is_escalated   boolean_flag      gate           0.89     propose  message      none
message        free_text         none           0.00     exclude  -            none

Candidates: is_escalated, refund_reason
Next: tokn circuit profile tickets.csv --draft is_escalated > circuit.json
```

This is a heuristic, and a person reviews it. `refund_reason` is a real
judgment over `message`. `is_escalated` is a yes/no flag a person set, so it
is a `gate` candidate: a model could learn to make that call from `message`.
`channel` is a `system_attribute`: it is recorded when the ticket arrives, so it
stays deterministic.

`--draft refund_reason` prints a one-gate starter circuit with placeholder
text (`DRAFT: define evidence for this option`) and an added `cannot_tell`
option. `--template refund_reason` prints a state template, which `batch` uses
to turn rows into model input.

## 10. Pick a threshold from the cost of mistakes

Suppose wrongly sending a customer to a human costs 1, and missing a real
chargeback threat costs 4:

```bash
tokn circuit threshold --cost-fp 1 --cost-fn 4
```

Expected:

```text
proposed noul true_at = 0.2000  (Cfp 1, Cfn 4)
valid only if the noul is calibrated on your data; check Brier/ECE with `tokn circuit eval` first

risk-tier defaults (governance.risk_tier; a gate's own knobs always win):
TIER  NOUL TRUE_AT  CHOICE MIN_CONFIDENCE  CHOICE MIN_MARGIN
1     0.70          0.60                   0.15
2     0.80          0.70                   0.25
3     0.85          0.80                   0.30
4     0.90          0.85                   0.35
```

The formula is `Cfp / (Cfp + Cfn)`. TOKN never applies the number for you. If
you use it, copy it into the gate's `true_at`, keep a `false_at` below it, and
re-run `analyze` and `test`.

## 11. Explain a trace and review the ledger

`circuit run` prints a JSON trace of each decision. `sample-trace.json` is a
hand-written trace in that shape: the borderline-threat case from step 6.

```bash
tokn circuit explain sample-trace.json
```

Expected:

```text
Circuit "refund-triage@1.0.0" abstained with "human_review" (reason UNKNOWN_ABSTAIN): arm "threat" read unknown before any arm fired, and unknown never falls through. Gates: reason=damaged, threat=unknown (noise_band). Requests: 1. Advisory: the caller decides; this is not a permission.
```

`explain -` reads the trace from stdin.

`circuit run --ledger` and `circuit batch --ledger` append each decision to a
JSONL ledger. Each record holds hashes and a row pointer, never the raw input.
`sample-ledger.jsonl` holds three hand-written records: one `AUTO`, one
`FORCED` by the pre-guard, one `ABSTAIN`.

```bash
tokn circuit ledger stats --ledger sample-ledger.jsonl
```

Expected:

```text
CIRCUIT              DECISIONS  AUTO  ABSTAIN  FORCED  ERROR  OVERRIDES
refund-triage@1.0.0  3          1     1        1       0      0
```

A reviewer looks at the abstained ticket and records the right answer:

bash:

```bash
tokn circuit ledger feedback dl_0003 --ledger sample-ledger.jsonl \
  --circuit refund-triage.circuit.json --reviewer alice --reason "Late parcel, no threat: seller fault" \
  --correct-output auto_refund
tokn circuit ledger show dl_0003 --ledger sample-ledger.jsonl
```

PowerShell:

```powershell
tokn circuit ledger feedback dl_0003 --ledger sample-ledger.jsonl `
  --circuit refund-triage.circuit.json --reviewer alice --reason "Late parcel, no threat: seller fault" `
  --correct-output auto_refund
tokn circuit ledger show dl_0003 --ledger sample-ledger.jsonl
```

Expected (shortened):

```text
recorded override on dl_0003
{
  "record": {
    "kind": "decision",
    "ledger_id": "dl_0003",
    ...
    "output": "human_review",
    "reason_code": "UNKNOWN_ABSTAIN",
    "status": "ABSTAIN",
    ...
  },
  "feedback": [
    {
      "reviewer": "alice",
      "correct_output": "auto_refund",
      "reason": "Late parcel, no threat: seller fault",
      "ts": "…"
    }
  ]
}
```

`ledger stats` now shows `OVERRIDES 1`. Feedback is appended as a new line,
and earlier lines are never rewritten. These overrides become labels for
`circuit eval`. `--circuit` checks that `--correct-output` is one of the circuit's
outputs and that the circuit's hash matches the decision; a typo such as
`partial_refund` is refused. Without `--circuit`, `feedback` records the label
unchecked and prints a `note: … was not checked` line to stderr.

## 12. Going live: `run`, `batch` and `eval`

These three call a System One backend and need credentials:

| Command | What it does |
|---|---|
| `run <circuit> --state <state.json>` | Decides one state; prints a trace, or a sentence with `--explain` |
| `batch <circuit> --table … --template … --out …` | Adds decision columns to every row of a table |
| `eval <circuit> --dataset <examples.jsonl>` | Accuracy, calibration (Brier/ECE), robustness and release gates on labelled examples |

Without a key, `run` stops with
`backend not configured: no API key: set JEV_API_KEY (or TYPESAFE_API_KEY)`.
With `--air-gap`, all three refuse before any call:

```text
Error: circuit run makes an external System One call and is disabled by --air-gap; use `tokn circuit test` with vectors for offline checks
```

To set up a backend and see live decisions, continue with
[decision-council](../decision-council/README.md) and
[decisions-api](../decisions-api/README.md).

## What to look for

- **Unknown is a first-class answer.** Borderline and low-margin answers read
  `unknown` and go to `on_unknown`. They never slip into a later arm.
- **`analyze` finds logic bugs before any model call.** It found an
  unreachable arm, a missing noise band and an output that is never produced.
- **Vectors pin behaviour.** The same seven vectors pass on the fixed circuit
  and fail on the draft, one failure per bug.
- **Exact rules stay code.** The 500-dollar rule is a `pre_guard` and needs no
  model call. `detect` did not flag it.
- **Generated code has no dependencies,** and its tests run offline.
- **Everything is advisory.** Every trace and generated module says so. Your
  application decides what a label allows.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `JSON is not valid UTF-8` or `malformed JSON` on a file you saved in PowerShell | UTF-16 and UTF-8-with-BOM files are accepted since v0.3.68, so upgrade. If it persists, the file is not valid JSON. |
| `circuitgen: destination already exists; choose a new directory` | `gen --out` needs a folder that does not exist yet. Delete it or pick another name. |
| `test` reports `FAIL` with an unexpected `human_review` | A gate read `unknown`. Check thresholds, and that `choice` answers include `probabilities` for every option. |
| `run` says `backend not configured: no API key` | Expected offline. Use `test` with vectors, or configure a backend (step 12). |
| `… is disabled by --air-gap` | `run`, `batch` and `eval` make external calls. Remove `--air-gap`, or stay with the offline commands. |
| `--correct-output … is not an output of …` or `--circuit is not the circuit that made decision …` | Check the label against `outputs` in the circuit, and pass the circuit version that made the decision. |
| `ledger: unknown decision "dl_…"` | The ID is not in that ledger file. Run `ledger stats` and check `--ledger`. |
| A "trial has ended — running the free community tier" banner | Printed to stderr; every command here works on the Community tier. |
