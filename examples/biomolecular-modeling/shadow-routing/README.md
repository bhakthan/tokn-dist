# Protein-prediction decisions without a GPU

Requires **TOKN v0.3.71 or newer**. These examples use synthetic operational
metadata, not protein sequences, scientific outputs or measured GPU performance.
No GPU, Docker, Python, weights, credentials, trial or network is needed.
Only the installed TOKN executable is required: check `Get-Command tokn` in
PowerShell or `command -v tokn` in a POSIX shell.

## 1. Run the complete worked example

```text
tokn version
tokn biomol demo
```

The JSON contains next-action recommendations and benchmark results. It
demonstrates four situations: no prediction yet, one existing prediction,
two predictors to compare, and a failed computation needing review.
Recommendations have mode `shadow`, authority `none`, acceptance
`held_unvalidated` and parity `not_verified`. **No model is executed.**

The benchmark has separate synthetic development and holdout families.
Its development-only GPU-time medians illustrate cost ordering; the numbers
are invented fixtures, not a hardware recommendation or measured speedup.
Labels are declared fixture answers, not experimentally validated biology.

## 2. Inspect and change an explicit evidence file

From this directory, run:

```powershell
tokn biomol advise --evidence (Resolve-Path .\evidence.json).Path
tokn biomol benchmark --dataset (Resolve-Path .\dataset.json).Path
```

POSIX shell:

```sh
tokn biomol advise --evidence "$PWD/evidence.json"
tokn biomol benchmark --dataset "$PWD/dataset.json"
```

The files contain only task, chain count, coarse longest-chain length band and fixed predictor
observations. `off` and `exact` are separate observations, not proof of parity.
Only Boltz-2, Chai-1 and OpenBind-0 prediction/cofolding are eligible for routing.
Band upper bounds and chain counts must fit the recommended adapter's profile;
an unknown exact length does not justify recommending a larger unsupported job.
Do not add sequences, structures, embeddings, target identities, logs, paths,
signatures or hashes: the closed schema rejects extra fields.

The `rules` policy recommends collecting missing evidence, comparing existing
predictions or considering an eligible untried predictor. It never decides that
a structure is biologically correct. `compare_existing` does not calculate
structural similarity. A recommended predictor still needs its own staged
runtime and separate external per-job review.

For a partial exercise, change the existing completed observation's
`metrics_present` to `false` and rerun `advise`. Explain why missing evidence
should not be treated as a successful scientific conclusion.

## 3. Replay a typed decision and a refusal

```powershell
tokn biomol advise --evidence (Resolve-Path .\recorded-decisions.json).Path
```

```sh
tokn biomol advise --evidence "$PWD/recorded-decisions.json"
```

These are **synthetic recorded answers**, not results from a paid model call.
The first routes a single-predictor case to `human_review`; the second records
a refusal and returns `abstain`. Deterministic evidence checks take precedence
over any recorded answer. The confidence number describes the supplied answer
distribution, not the probability that a protein structure is correct.

## 4. Read the benchmark without fooling yourself

The supplied `evaluation_only` dataset is intentionally small. Its report
states that development/holdout separation is not established.
Correctly labelled abstention counts as agreement. Missing candidate choices
are unobserved, not abstentions; missing cost is unmeasured, not zero.
Candidate-versus-baseline comparisons use the same observed holdout cases.
Impossible reference/candidate actions are rejected, including unsupported
adapter shapes, repeating a completed predictor or comparing nonexistent
results. The fixed-order and cost-order baselines may recommend a third
eligible predictor; the rules circuit instead compares two existing results.

The built-in demo additionally illustrates a structural `family_time` split
and development-only cost priors. Neither split proves biological independence:
the operator must supply appropriate family assignments and independently
reviewed labels for a real evaluation.

Try a problem-only exercise: construct a synthetic holdout case where abstaining
is the reference answer. Predict how it changes total agreement and selective
agreement, then compare the actual JSON. Do not interpret action-label agreement
as folding accuracy.

There are no live-service flags on these commands. Recorded typed circuit
answers can be replayed offline; a recommendation never becomes runtime
authority. Calibrated quality prediction, counterfactual utility, autonomous
protein design and scientific acceptance are not implemented here.
