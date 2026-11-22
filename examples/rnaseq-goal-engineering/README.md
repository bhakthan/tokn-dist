# Goal engineering: a reviewer's correction becomes a lesson for every later run

This example shows **goal scopes** in TOKN. Goal engineering, as described in
LangChain's [Goal Engineering](https://www.langchain.com/blog/goal-engineering) post,
means defining the goal once for a *type* of task, not once per instance. A goal
scope does this: you describe the task type, TOKN queues every run of that type for
human review, and when a reviewer corrects a run, the correction is saved as a
verified lesson. TOKN applies that lesson to every later run in the same scope
without anyone rewriting the prompt.

The demo task type is **bulk RNA-seq differential expression with a batch
covariate**, starting from raw integer count matrices. Each instance ships its own
brief, counts and sample sheet. The designs differ in replicate number, so a method
that is correct on one design can be wrong on another.

## What you will do

1. Create a goal scope and lint it.
2. Run the agent on the shipped case with `--goal-scope`.
3. Grade the result against a separate answer key.
4. Review the run and correct it. The correction becomes a lesson.
5. Generate a new instance with a different seed and run it. The lesson applies.
6. Accept the run and inspect the scope's review history.

## Prerequisites

- TOKN installed and on your `PATH` (`tokn version` should print).
- Python 3.9 or newer with `numpy` (`pip install numpy`). The grader needs it too.
- A model provider that can make tool calls. The live runs below used Anthropic;
  `.env.example` lists the names. Use a model capable of the required tool calls;
  provider charges and number of turns depend on the run. A missing/failed tool
  result is unassessed, not a pass. Check static configuration with
  `tokn doctor --provider anthropic` (it does not prove the key works).

## Setup

Build a run-owned scratch root **outside this repository**, and a separate grading
root the agent never gets. Both must be new; `mkdir` fails if they exist, which is
what you want. The goal scope store is pointed into the run root too, so lessons
from this exercise do not leak into your other scopes (`~/.tokn/goalscopes/`).

```bash
RUN=~/rnaseq-goal-run; GRADE=~/rnaseq-goal-grading
EX=examples/rnaseq-goal-engineering          # from the tokn-dist root
mkdir "$RUN" "$GRADE"
cp -r "$EX/case" "$EX/checks" "$EX/make_case.py" "$RUN/"
cp -r "$EX/answer_key/." "$GRADE/"
export TOKN_GOALSCOPE_DIR="$RUN/scopes"
export NOSPACE_MODEL_PROVIDER='anthropic'
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
cd "$RUN"
```

```powershell
$RUN = "$HOME\rnaseq-goal-run"; $GRADE = "$HOME\rnaseq-goal-grading"
$EX = "examples\rnaseq-goal-engineering"     # from the tokn-dist root
New-Item -ItemType Directory $RUN, $GRADE | Out-Null
Copy-Item -Recurse "$EX\case", "$EX\checks", "$EX\make_case.py" $RUN
Copy-Item -Recurse "$EX\answer_key\*" $GRADE
$env:TOKN_GOALSCOPE_DIR = "$RUN\scopes"
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "YOUR_MODEL_ID"
# Supply ANTHROPIC_API_KEY from a trusted secret store or session, not a command containing the key.
Set-Location $RUN
```

If you use an Anthropic-compatible gateway, set `ANTHROPIC_BASE_URL` in the same
trusted shell. Do not source `.env.example` or commit a populated `.env`. Keep
`TOKN_GOALSCOPE_DIR` set in every shell you use for steps 1 to 6. All commands
below run from `$RUN` unless they say otherwise.

## 1. Create the scope

```bash
tokn goal scope create bulk-rnaseq-de-batch \
  --task-type "bulk RNA-seq differential expression between two conditions with a batch covariate, starting from raw integer count matrices" \
  --goal "produce a per-gene results table and a QC report that meet every acceptance criterion in the case brief, using a batch-aware test with Benjamini-Hochberg FDR" \
  --context "Each instance ships its own brief, counts matrix and sample sheet; designs differ in replicate number." \
  --context "Only numpy and the standard library are allowed; statistics are implemented by hand."
```

A scope describes the *kind* of task. It must not name one instance. To see the
linter at work, try a draft that does:

```bash
tokn goal scope create draft-with-path --task-type "analyse data/counts_s7.tsv" --goal "analyse sample S07"
```

The linter refuses this draft: `GS001` flags the file path and `GS002` flags the
sample identifier. Rewrite the text so it describes the task type, not the
instance. If you really need the literal text, add `--force-lint`.

Check the scope and list it:

```bash
tokn goal scope lint bulk-rnaseq-de-batch
tokn goal scope list
```

Scopes are stored under `~/.tokn/goalscopes/<name>/` by default; with the setup
above they go to `$RUN/scopes/<name>/` instead, and you delete them with the run root.

## 2. Run the agent

Give the solver a fresh `work/` that holds only the case. The answer key is in
`$GRADE`, outside the solver's repository root:

```bash
mkdir work && cp -r case work/case
```

Run TOKN on the brief. `--auto-route` sends each step to the cheapest model that can
handle it, and `--goal-scope` attaches the scope to the run. `--permission-mode
default` asks before each edit or mutating command, so you approve the analysis code
the agent writes and runs:

```bash
tokn agent-run --goal-scope bulk-rnaseq-de-batch --auto-route \
  --repo-root work \
  --prompt-file work/case/TASK.md \
  --max-steps 40 --permission-mode default
```

Do not add `--no-confirm` here: it auto-approves every tool call. Setting
`TOKN_GOAL_SCOPE=bulk-rnaseq-de-batch` has the same effect as `--goal-scope`. The
agent writes its outputs to `work/solution/`. Raise `--max-steps` if the run stops
early.

## 3. Grade

Grade from outside `work/`, with the grader and truth from `$GRADE`:

```bash
python "$GRADE/grade.py" work/solution/results.tsv \
  --truth "$GRADE/truth.tsv" --counts case/counts.tsv --report work/solution/report.md
```

The grader checks precision, FDR, recall, the log2 fold-change correlation, the
call count, the low-count share, coverage, the QC section and the QC word count.
The thresholds are the criteria in `case/TASK.md`. The grader prints PASS or FAIL
for each check.

## 4. Review and correct

Each run of a scope is queued for review:

```bash
tokn review --scope bulk-rnaseq-de-batch
```

Run IDs restart at `R001` in each scope, so name the scope with `--scope` or use
`<scope>/R002`. Suppose a run uses a normal (z) reference for its batch-aware test,
which is a poor fit when each cell has only a few replicates. Its empirical FDR
comes out at 0.101, just above the brief's 0.10 bound. Record the correction:

```bash
tokn review correct --scope bulk-rnaseq-de-batch R002 --category calibration \
  --note "With few replicates per condition-by-batch cell, never use a normal (z) reference. Use a Student t with residual degrees of freedom (or a likelihood-ratio test with a small-sample correction), and state the reference and df in the QC section."
```

`tokn review correct` takes the lesson text in `--note`. The lesson is saved as a
verified lesson and injected into **every** later run of the scope, so write only a
rule that holds for the task type. Keep case-specific observations (this run's FDR,
a sample that looked odd) out of lessons: `tokn review accept --note` and
`tokn review reject --note` record a note on the run without creating a lesson. Add
a lesson by hand with `tokn goal scope lesson add` if you prefer.

Other review decisions:

```bash
tokn review accept --scope bulk-rnaseq-de-batch R003 --note "FDR and recall within the brief's bounds; QC states the reference and df."
tokn review reject --scope bulk-rnaseq-de-batch R005
```

## 5. Run a new instance

Generate a different instance. The seed and the replicate count change the design.
Generate it inside the grading root, because it writes its own answer key, then
give the solver only its case:

```bash
python make_case.py --seed 7 --replicates 4 --out "$GRADE/instance-s7"
mkdir work-s7 && cp -r "$GRADE/instance-s7/case" work-s7/case
tokn agent-run --goal-scope bulk-rnaseq-de-batch --auto-route \
  --repo-root work-s7 --prompt-file work-s7/case/TASK.md \
  --max-steps 40 --permission-mode default
```

`make_case.py` writes `instance-s7/case/` (counts, sample sheet, brief) and
`instance-s7/answer_key/truth.tsv`. The scope lesson is applied automatically;
`tokn goal scope preamble bulk-rnaseq-de-batch` prints exactly what is injected.

Grade the new run against its own truth and counts:

```bash
python "$GRADE/grade.py" work-s7/solution/results.tsv \
  --truth "$GRADE/instance-s7/answer_key/truth.tsv" \
  --counts work-s7/case/counts.tsv \
  --report work-s7/solution/report.md
```

Review it with `tokn review --scope bulk-rnaseq-de-batch`, then accept it.

## 6. Inspect the scope

```bash
tokn goal scope show bulk-rnaseq-de-batch
```

The output includes the accept rate for runs before and after the lesson. This
example's live runs are below.

## Results from the live runs

Historical observed live runs (Claude models through TOKN with auto-routing), recorded
when this example was written; they are not re-run by this guide and your models,
versions and numbers will differ. The scope had no lessons until R002 was corrected.

| Run | Instance | Lesson applied | Reference used | Empirical FDR | Precision | Recall | Outcome |
|-----|----------|----------------|----------------|---------------|-----------|--------|---------|
| R002 | 12 samples (shipped case) | no | normal (z) | 0.101 | — | — | corrected by reviewer |
| R003 | 16 samples (new seed) | L001 | Student t, 13 df | 0.031 | 0.969 | 0.900 | accepted |
| R004 | 12 samples (shipped case, re-run) | L001 | Student t, 9 df | 0.057 | — | 0.821 | accepted |

`tokn goal scope show bulk-rnaseq-de-batch` reported an accept rate of 0% before the
lesson (2 reviewed runs) and 100% after it (2 reviewed runs). Treat that as an
illustration, not proof. Two reviewed runs per side can differ by chance. Judge the
effect over more runs.

The lesson, saved as L001 in category `calibration`:

> With few replicates per condition-by-batch cell, never use a normal (z) reference.
> Use a Student t with residual degrees of freedom (or a likelihood-ratio test with a
> small-sample correction), and state the reference and df in the QC section.

In R003 the agent also added its own permutation check on the null distribution,
which the lesson did not ask for.

The shipped case uses seed 20240607 with 3 replicates per cell (12 samples). The
16-sample instance in the table came from a different seed, so `make_case.py` with
the defaults reproduces the 12-sample case, not that instance.

## Stress gaps: turn lessons into a pre-review check

Step 3 grades against hidden truth and reports numerical margins.
`checks/lagarias_stress_gate.py` adds a different, truth-free check. It borrows a framing from Lagarias's reformulation of the Riemann hypothesis,
where the margin of an inequality at each n, not just its sign, says how close a case
is to a counterexample. It's an analogy for gate design; nothing here is derived from
the Riemann hypothesis.

The check reads only the run's outputs and the case files, and scores each lesson as a
relative gap (binary checks, including zero invalid tokens, use +1/−1). A gated gap of 0 or less is a counterexample and the check fails. A gap between
0 and 0.05 is a near miss: the check passes but prints a warning for the reviewer.

| Check | Lesson category | What it catches |
|---|---|---|
| `bh_consistent` | (integrity) | `padj` isn't Benjamini–Hochberg of `pvalue` |
| `reference_stated`, `residual_df` | `calibration` | no recognised test name or matching residual df in the report; this checks wording, not the p-value calculation |
| `lfc_agreement_r` | `off-line-zero` | advisory: correlation with batch-adjusted log2(CPM+1) OLS on tested genes with mean count ≥ 10. Different normalisation, shrinkage or count models can disagree without batch leakage |
| `c2s_invalid_token_rate`, `c2s_euler_discrepancy` | `analytic-continuation` | only with `--c2s-audit`: unknown gene tokens or labels marked unverified by the supplied audit (not independently recomputed); use only with a matching gene index |

Record the check command on a new scope. Run it from `$RUN` before review; recording `--check` alone is not evidence that it ran:

```bash
tokn goal scope create bulk-rnaseq-de-batch-stress \
  --task-type "bulk RNA-seq differential expression between two conditions with a batch covariate, starting from raw integer count matrices" \
  --goal "produce a per-gene results table and a QC report that meet every acceptance criterion in the case brief, with every stress gap positive" \
  --check "python checks/lagarias_stress_gate.py --results work/solution/results.tsv --counts work/case/counts.tsv"
```

Record lessons about the task type, not one instance. The scope linter checks task and goal text, not the statistical validity of a lesson:

```bash
tokn goal scope lesson add bulk-rnaseq-de-batch-stress --category calibration \
  --text "For a small-sample linear model, use a Student t reference with the residual degrees of freedom. For a count-model likelihood-ratio test, document its reference distribution and limitations."
tokn goal scope lesson add bulk-rnaseq-de-batch-stress --category off-line-zero \
  --text "Fit expression ~ condition + batch. If error stops shrinking, investigate batch imbalance and other error floors; check log2FC against an independent batch-adjusted fit."
tokn goal scope lesson add bulk-rnaseq-de-batch-stress --category analytic-continuation \
  --text "When a model labels cells, keep a label only if the cell's own marker genes support it, and reject gene tokens outside the panel."
```

Run the check by hand at any time:

```bash
python checks/lagarias_stress_gate.py --results work/solution/results.tsv --counts work/case/counts.tsv
```

**Observed** on the shipped 12-sample case, with two hand-built solutions that use the
same batch-adjusted linear model: the one that reports "Student t with 9 residual df"
passes (log2FC r = 1.0, advisory margin 0.11). With `--require-lfc-agreement`, that margin is also the minimum gated gap. Pearson correlation alone does not validate log units or offsets. The one that uses a normal reference
fails on `reference_stated` and `residual_df`, before any reviewer or answer key is
involved. The answer-key grader now also prints each criterion's relative margin and
the minimum, flagging near misses below 0.05. The margins never change its verdict.

These paths assume the layout from Setup and step 2. Keep `checks/` outside the solver's `work/` directory and retain the check output with the review. The check cannot establish whether the report describes the analysis that actually ran.

## What to try next

- Generate more seeds and replicate counts. Check whether the lesson holds across
  designs, not just on the one you corrected.
- Write your own `--check` for another lesson, in the style of
  `checks/lagarias_stress_gate.py`. Keep the answer key out of the solver's working
  tree when you do this.
- Write a second lesson in another category and see how the scope's history
  changes.

## Notes

- With the Setup above, run state, scopes and generated outputs live in `$RUN` and
  answer keys in `$GRADE`, outside this repository. Delete both folders when you are
  done; that also removes the isolated scope and its lessons.
- If you do run inside the checkout, `.nospace/`, `.tokn/`, `solution/`, `work/`,
  `instance-*/` and `solve-*/` are git-ignored.
- The case files are synthetic. The example shows how a scope improves a method. It
  does not show that the method works on real assays.
