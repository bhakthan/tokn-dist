# Example: Replay worlds — score exploration policies on runs you already paid for

> "Our evolve run tried twelve changes. Would a different search order have
> found the best one sooner, or is that a question this history cannot answer?"

A discovery run such as `tokn evolve` tries changes, measures each one, and
records the result with its parent. That record is a tree. `tokn worlds`
saves the tree as a **world** and replays other **exploration policies** over
it: which branch to open, which result to build on, when to stop. Each policy
gets a score, and nothing is run again.

| Step | Command | What it tells you |
|---|---|---|
| Record | `record` | Turns a saved evolve pool into a world, scored on one axis you choose |
| Inspect | `list` | Each world's shape, and whether it can tell policies apart at all |
| Replay | `replay` | One policy over one world: best result, probes spent, rounds |
| Compare | `rank` | Every policy over every world, with a verdict or an honest UNDECIDED |
| Read | `explain` | The score formula, off-record probes, degenerate worlds |

Every command here is **offline and deterministic**. No model is called and no
code is built or tested. Every score comes from a result measured during the
earlier run.

The limit is just as firm: replay only knows what the earlier run tried. A
world that cannot tell policies apart is marked **degenerate**. A comparison
the history cannot settle comes back **UNDECIDED** instead of naming a winner.

The idea is adapted from Dream-RSI (Zheng et al., Google, 2026). TOKN has not
reproduced that paper's benchmarks and claims none of its results.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.68 or later | Ships `tokn worlds` | `tokn worlds --help` |
| This folder | Three small evolve pools in `pools/` | `ls pools` |
| A model provider (step 8 only) | A real `tokn evolve --run` asks a model for changes | see [SETUP.md](../../SETUP.md) |

It runs on every tier, including the free Community tier.

### What leaves your machine

Nothing, in steps 1–7. They read local files and write JSON files under
`./worlds` and `./axis-check`. Step 8 runs `tokn evolve --run`, which sends
your package's code and the task to the model provider you configured.

## 1. Get the pools

An **evolve pool** is a JSONL file: one line per attempted change, with its
`id`, its `parentIds`, and its measured `fitness`. `tokn worlds record` reads
it; nothing else is needed.

bash:

```bash
git clone https://github.com/bhakthan/tokn-dist
cd tokn-dist/examples/replay-worlds
```

PowerShell:

```powershell
git clone https://github.com/bhakthan/tokn-dist
Set-Location tokn-dist\examples\replay-worlds
```

The folder has three **synthetic** pools. They are hand-written test data in
the real pool format, not the output of a real run. Every line says
`"detail":"synthetic fixture"`.

| File | Shape | Why it is here |
|---|---|---|
| `pools/branchy-a.jsonl` | 9 attempts, 2 starting points, 4 levels deep | A tree where order matters; one attempt has failing tests |
| `pools/branchy-b.jsonl` | 8 attempts, 2 starting points | The best result (0.80) sits in the second branch |
| `pools/chain.jsonl` | 4 attempts, one after another | A single chain: no policy has a choice to make |

Now make one **real** pool. `tokn evolve --demo` runs a fixed, offline
scenario and saves its pool:

```bash
tokn evolve --demo --pool pools/evolve-demo.jsonl
```

Expected (shortened):

```text
TOKN evolve (demo) — fail-closed fitness ratchet

  gen  candidate                          parent  child   kept      decision
  1    improver: add boundary test        0.60    0.80    0.80      SURVIVED
  2    regressor: delete an assertion     0.80    0.45    0.80      ROLLED BACK
  3    api-breaker: rename exported fn    0.80    0.90    0.80      ROLLED BACK
  4    test-breaker: introduce a bug      0.80    0.99    0.80      ROLLED BACK
  5    improver2: cover an edge case      0.80    0.92    0.92      SURVIVED
...
  Persisted to pools/evolve-demo.jsonl
```

One line of that pool:

```json
{"id":"gen-002-00","parentIds":["gen-001-00"],"generation":2,"candidate":"regressor: delete an assertion","fitness":{"mutationScore":0.45,"testsPass":true,"apiLost":0,"detail":"demo"},"survived":false,"reason":"rolled back: mutation score regressed 0.800 -\u003e 0.450","niche":"mutation/regressor"}
```

## 2. Record the pools as worlds

Worlds are stored as one JSON file per world. The default store is
`~/.tokn/worlds`. This walkthrough passes `--store worlds` so the demo worlds
stay in this folder and never mix with your own.

```bash
tokn worlds record --from-evolve pools/evolve-demo.jsonl --id evolve-demo --store worlds
tokn worlds record --from-evolve pools/branchy-a.jsonl --id branchy-a --store worlds
tokn worlds record --from-evolve pools/branchy-b.jsonl --id branchy-b --store worlds
tokn worlds record --from-evolve pools/chain.jsonl --id chain --store worlds
```

Expected:

```text
recorded world "evolve-demo" from pools/evolve-demo.jsonl (5 nodes) into …/replay-worlds/worlds
shape: roots=1 max-depth=2 mean-branching=4.00 distinct-scores=4
recorded world "branchy-a" from pools/branchy-a.jsonl (9 nodes) into …/replay-worlds/worlds
shape: roots=2 max-depth=4 mean-branching=1.75 distinct-scores=8
recorded world "branchy-b" from pools/branchy-b.jsonl (8 nodes) into …/replay-worlds/worlds
shape: roots=2 max-depth=3 mean-branching=1.50 distinct-scores=7
recorded world "chain" from pools/chain.jsonl (4 nodes) into …/replay-worlds/worlds
warning: this world is degenerate and cannot separate exploration policies: world is a single chain: every policy must walk the same nodes in the same order, so branch selection and ordering are unobservable
```

- Each attempt becomes a **node**. If an attempt has several parents, only
  the first one is kept, so the pool becomes a tree.
- `--axis` picks the score. The default is `mutation` (higher is better).
  `perf` and `security` are recorded as costs, so TOKN flips their sign. Step
  6 shows why the choice matters.
- `chain` is still stored, with a warning. It is kept so later commands can
  report it, not so it can decide anything.
- Recording again with the same `--id` is refused (`world "chain" already
  exists …`). Pass `--force` to replace it.

## 3. List: which worlds can tell policies apart?

```bash
tokn worlds list --store worlds
```

Expected:

```text
Replay is exact over recorded history and blind outside it. No LLM, no builds and no discovery calls are made: every score comes from outcomes already measured during an earlier online run.

4 world(s) in …/replay-worlds/worlds

  branchy-a                   9 nodes  roots=2 depth=4 branching=1.75 scores=8
  branchy-b                   8 nodes  roots=2 depth=3 branching=1.50 scores=7
  chain                       4 nodes  DEGENERATE — world is a single chain: every policy must walk the same nodes in the same order, so branch selection and ordering are unobservable
  evolve-demo                 5 nodes  roots=1 depth=2 branching=4.00 scores=4

1 of 4 world(s) cannot separate exploration policies.
```

Three worlds are **separable**: they branch, and their scores differ, so two
policies can take different paths and reach different results. A world is
**degenerate** when it has fewer than two nodes, is a single chain, or has
fewer than two distinct scores among usable attempts. Add `--json` for a
machine-readable list; the one-line limit notice then goes to stderr.

## 4. Replay one policy

A policy is data, not code. You pick one of four rules and a few settings:

| Rule | What it expands next |
|---|---|
| `greedy` (default) | The revealed attempt with the highest score |
| `ucb` | Highest score plus a bonus for attempts expanded less often (`--beta` sets the bonus) |
| `threshold` | Only attempts within `--beta` of the best score so far; stops when none are left |
| `roundrobin` | The attempt expanded least often |

Replay `greedy` over `branchy-a`:

```bash
tokn worlds replay --world branchy-a --store worlds
```

Expected:

```text
policy "greedy" over world "branchy-a"
  value=0.7400 best=0.7800 probes=9 rounds=9 seq-rounds=9 revealed=100%
```

| Field | Meaning |
|---|---|
| `best` | Highest score among revealed attempts whose tests passed |
| `probes` | Attempts revealed: what the policy would have paid to run |
| `rounds` | Decision rounds; `seq-rounds` charges each round by `--workers` |
| `revealed` | Share of the recorded tree the policy looked at |
| `value` | `best − 0.01 × probes + 0.05 × (probes ÷ rounds)` |

Here `0.78 − 0.09 + 0.05 = 0.74`. `branchy-a` also has an attempt scoring
0.95, but its tests failed, so it never counts as `best`. The two weights are
TOKN's defaults, not values from the paper.

Replay over the degenerate world:

```bash
tokn worlds replay --world chain --store worlds
```

Expected:

```text
policy "greedy" over world "chain"
  value=0.7200 best=0.7100 probes=4 rounds=4 seq-rounds=4 revealed=100%
  warning: this world is degenerate; every policy scores alike here.
```

`value` can be higher than `best`: with one probe per round, the last term is
a fixed `+0.05`.

### A cheap policy that misses

`threshold` with the default `--beta 0` only builds on the best result so far.
On `branchy-b` it is cheap, and it misses:

```bash
tokn worlds replay --world branchy-b --rule threshold --store worlds
```

Expected:

```text
policy "threshold" over world "branchy-b"
  value=0.5800 best=0.5700 probes=4 rounds=4 seq-rounds=4 revealed=50%
```

It followed the first branch to 0.57, glanced at the second branch's first
attempt (0.45), and stopped. The 0.80 result is deeper in that second branch.
Tell it to open another branch while the best frontier score is below 0.6:

```bash
tokn worlds replay --world branchy-b --rule threshold --open-root-if 0.6 --store worlds
```

Expected:

```text
policy "threshold" over world "branchy-b"
  value=0.8100 best=0.8000 probes=4 rounds=4 seq-rounds=4 revealed=50%
```

Same cost, and it found the best result.

### Stopping and batching

Stop `greedy` after two rounds without improvement:

```bash
tokn worlds replay --world branchy-a --stop-no-gain 2 --store worlds
```

Expected:

```text
policy "greedy" over world "branchy-a"
  value=0.7700 best=0.7800 probes=6 rounds=6 seq-rounds=6 revealed=67%
```

It reached the same 0.78 with 6 probes instead of 9. Allow up to 3 probes
per round, charged against 2 workers:

```bash
tokn worlds replay --world branchy-a --max-parallel 3 --workers 2 --store worlds
```

Expected:

```text
policy "greedy" over world "branchy-a"
  value=0.7543 best=0.7800 probes=9 rounds=7 seq-rounds=7 revealed=100%
```

Nine probes in 7 rounds: this tree was rarely wide enough to fill a batch.
Other settings: `--max-rounds N` (the policy stops after N rounds),
`--replay-rounds N` (hard cap, default 64), and `--json`.

## 5. Rank: does any policy win?

```bash
tokn worlds rank --store worlds
```

Expected:

```text
POLICY              VALUE       BEST     PROBES   OFF-RECORD DISCRIMINATING
greedy             0.8100     0.8333        7.3            0          3/4  
roundrobin         0.8100     0.8333        7.3            0          3/4  
ucb                0.8100     0.8333        7.3            0          3/4  
threshold          0.7567     0.7500        4.3            0          3/4  

verdict: UNDECIDED — the recorded history cannot separate these policies.
  - Excluded 1 distinct degenerate worlds from scoring and verdict evidence; row Worlds retains their count.
  - Leader advantage 0 is within coverage-induced tolerance 0.17999999999999994 (leader's per-world value spread).
```

How to read it:

- **Means use separable worlds only.** `DISCRIMINATING 3/4` means `chain` was
  left out of the averages. It is still counted, so you can see it was there.
- **Three rules tie.** With no stopping settings, `greedy`, `ucb` and
  `roundrobin` all reveal every attempt and reach the same score. Order only
  matters when a policy stops early. `rank` accepts `--stop-no-gain`,
  `--max-rounds` and `--open-root-if`, applied to every rule. With
  `--stop-no-gain 2` here, `threshold` leads by 0.003, still UNDECIDED.
- **UNDECIDED is an answer.** The leader must beat the runner-up by more than
  the spread of its own value across worlds. `greedy` scored 0.74, 0.77 and
  0.92 on the three worlds, a spread of 0.18. A gap of 0 is inside it.

Compare just two rules, with `--beta 0.15` for each:

```bash
tokn worlds rank --rules greedy,threshold --beta 0.15 --store worlds
```

Expected:

```text
POLICY              VALUE       BEST     PROBES   OFF-RECORD DISCRIMINATING
threshold          0.8200     0.8333        6.3            0          3/4  
greedy             0.8100     0.8333        7.3            0          3/4  

verdict: UNDECIDED — the recorded history cannot separate these policies.
  - Excluded 1 distinct degenerate worlds from scoring and verdict evidence; row Worlds retains their count.
  - Leader advantage 0.010000000000000009 is within coverage-induced tolerance 0.16000000000000003 (leader's per-world value spread).
```

`threshold` now leads by 0.01, with one probe fewer on average. That is far
smaller than its own 0.16 spread across worlds, so there is still no winner.
A verdict needs all of these:

| Condition | Finding when it fails |
|---|---|
| At least 2 policies | `Fewer than 2 policies were evaluated` |
| At least 2 separable worlds per policy | `has 1 discriminating worlds; at least 2 are required` |
| A lead larger than the leader's spread across worlds | `Leader advantage … is within coverage-induced tolerance …` |
| The leader stayed on the record, if the runner-up did | `Leader used off-record probing …` |

**Off-record.** A probe is off-record when a policy asks for a continuation
the recording does not have. It is counted, never answered. In every run in
this walkthrough the `OFF-RECORD` column is 0: none of the four built-in rules
asked beyond these recordings. `replay` prints an `off-record=` line only
when the count is above zero.

`--json` prints the ranking as JSON on stdout and the limit notice on stderr.

## 6. Pick the axis on purpose

The demo pool only measured mutation score. Record it on the `perf` axis, in
a separate store so it does not join the ranking above:

```bash
tokn worlds record --from-evolve pools/evolve-demo.jsonl --id evolve-demo-perf --axis perf --store axis-check
```

Expected:

```text
recorded world "evolve-demo-perf" from pools/evolve-demo.jsonl (5 nodes) into …/replay-worlds/axis-check
warning: this world is degenerate and cannot separate exploration policies: world has fewer than two distinct scores among usable attempts: every trajectory attains the same quality, so the quality term cannot separate policies
```

No attempt has a perf number, so every score is the same. TOKN says so instead
of ranking policies on a question the run never measured. Record each world on
the axis its run actually optimised.

## 7. Explain

```bash
tokn worlds explain
```

Expected (shortened):

```text
THE REPLAY SCORE
  value = best - beta1*probes + beta2*(probes / rounds)
Quality reached, minus the execution cost a policy would have incurred, plus a
bonus for batching independent probes instead of serializing them. beta1 and
beta2 are TOKN's chosen defaults, not values taken from the source paper.
...
UNDECIDED
An undecided verdict is an answer, not a failure to retry. It means one of:
every world was degenerate; fewer than two policies were compared; the margin
between the top two was inside the leader's own variability across worlds; or
the leader's advantage depended on off-record probing.
...
```

The full text also covers what a world is, off-record probes, degenerate
worlds, and what replay does **not** show.

## 8. Optional: record a world from your own evolve run

A real pool comes from `tokn evolve --run`, which asks a model for changes to
a package, measures each one, and keeps or rolls it back. Run it from the
root of a git repo with a clean working tree:

```bash
tokn evolve --run ./yourpkg --task "cover error paths" --generations 3 --isolate --pool pool.jsonl
tokn worlds record --from-evolve pool.jsonl --id my-run-1 --axis mutation
tokn worlds list
```

This step needs a model provider. Without one, `tokn evolve --run` stops with
`No model provider is configured` and lists the keys it can use. `--isolate`
makes the changes in a temporary git worktree; kept changes come back as
uncommitted edits for you to review.

Without `--store`, worlds go to `~/.tokn/worlds`. Use a new `--id` for each
run. A ranking needs at least two separable worlds, recorded on the same axis.

## What to look for

- **Degenerate before ranked.** Check `list` first. A world marked DEGENERATE
  is stored and counted, but never used as evidence.
- **Cheap is not the same as good.** `threshold` spent 4 probes on `branchy-b`
  and missed the best result; `--open-root-if 0.6` fixed that at the same cost.
- **UNDECIDED is the common case.** Worlds with different score ranges give
  the leader a wide spread, so only a large, consistent lead earns a verdict.
- **Only failing tests mark an attempt failed.** In `evolve-demo`, the
  `api-breaker` attempt (0.90) was rolled back for losing exported API, but it
  still counts as a usable score in replay.
- **Replay is not an online result.** A policy that does well on recorded
  history has only been tested where an earlier policy chose to look.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `--from-evolve …: file not found; pass a saved evolve pool JSONL file` | The `--from-evolve` path is wrong. Check the path. |
| `dream: evolve pool is empty` | The file has no lines. |
| `evolve pool: parse line` | The pool is JSONL: one JSON object per line. A pretty-printed JSON file or a comment line will not load. |
| `--world is required` | Pass `--world <id>`. `tokn worlds list` shows the recorded ids. |
| `world "<id>" already exists in …` | `record` will not overwrite a world. Choose another `--id`, or pass `--force` to replace it. |
| `dream: read world "<id>": …` | No world has that id in this store. Run `tokn worlds list` with the same `--store`. |
| `no worlds recorded in …` | The store is empty or does not exist. Record a pool first, or pass the right `--store`. `list`, `replay` and `rank` never create the store folder. |
| Every rank is UNDECIDED | Expected with few or very different worlds. Record more separable runs on the same axis, and read each finding. |
| Your demo worlds show up in your real rankings | You left out `--store worlds`. Delete the demo files from `~/.tokn/worlds`. |
| `invalid --axis` | Use `mutation`, `perf` or `security`. |
