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
- An Anthropic API key, or access to an Anthropic-compatible gateway.

## Setup

```powershell
cd examples\rnaseq-goal-engineering
copy .env.example .env
# edit .env: set ANTHROPIC_API_KEY (and ANTHROPIC_BASE_URL if you use a gateway)
```

Make these values available to TOKN in your shell before running it (for example,
set them as environment variables). Never commit `.env`.

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

Scopes are stored under `~/.tokn/goalscopes/<name>/` (override with
`TOKN_GOALSCOPE_DIR`).

## 2. Run the agent

Work in a fresh copy of the case so the solver never sees the answer key:

```bash
mkdir work
cp -r case work/case
```

Run TOKN on the brief. `--auto-route` sends each step to the cheapest model that can
handle it, and `--goal-scope` attaches the scope to the run:

```bash
tokn agent-run --goal-scope bulk-rnaseq-de-batch --auto-route \
  --repo-root work \
  --prompt-file work/case/TASK.md \
  --no-confirm
```

Setting `TOKN_GOAL_SCOPE=bulk-rnaseq-de-batch` has the same effect as `--goal-scope`.
The agent writes its outputs to `work/solution/`. Copy `solution/results.tsv` and
`solution/report.md` back into this folder, or grade them from `work/`.

## 3. Grade

Move the answer key out of the working tree first. Only the grader should read it:

```bash
mv answer_key ../answer_key-rnaseq
python ../answer_key-rnaseq/grade.py work/solution/results.tsv \
  --counts case/counts.tsv --report work/solution/report.md
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
verified lesson for the scope. Add a lesson by hand with `tokn goal scope lesson add`
if you prefer.

Other review decisions:

```bash
tokn review accept --scope bulk-rnaseq-de-batch R003 --note "FDR and recall within the brief's bounds; QC states the reference and df."
tokn review reject --scope bulk-rnaseq-de-batch R005
```

## 5. Run a new instance

Generate a different instance. The seed and the replicate count change the design.
Put it in its own folder, outside `case/`:

```bash
python make_case.py --seed 7 --replicates 4 --out instance-s7
```

This writes `instance-s7/case/` (counts, sample sheet, brief) and
`instance-s7/answer_key/truth.tsv`. Run the agent on the new brief, the same way
as in step 2, with a new working folder. The scope lesson is applied automatically.

Grade the new run against its own truth and counts:

```bash
python ../answer_key-rnaseq/grade.py work-s7/solution/results.tsv \
  --truth instance-s7/answer_key/truth.tsv \
  --counts instance-s7/case/counts.tsv \
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

Live runs used Claude models through TOKN with auto-routing. The scope had no lessons
until R002 was corrected.

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

## What to try next

- Generate more seeds and replicate counts. Check whether the lesson holds across
  designs, not just on the one you corrected.
- Add a `--check` command to the scope (`tokn goal scope create ... --check "<cmd>"`)
  to run a script on each run before the reviewer sees it. Keep the answer key out of
  the solver's working tree when you do this.
- Write a second lesson in another category and see how the scope's history
  changes.

## Notes

- `.nospace/` and `.tokn/` hold local run state. They are git-ignored.
- `solution/`, `work/`, `instance-*/` and `solve-*/` are generated outputs. They are
  git-ignored too.
- The case files are synthetic. The example shows how a scope improves a method. It
  does not show that the method works on real assays.
