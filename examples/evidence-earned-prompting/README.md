# Example: Evidence-Earned Prompting on insurance claims SQL

> **[FRAME]** Evidence-Earned Prompting is design guidance that TOKN
> implements. It is not a documented vendor method.

This walkthrough turns one plain-language claims-reporting requirement into a
SQL view. Each instruction the prompt gains has to be earned first:

> *For every open claim, show the claim, the product line of its policy, and
> how much has been paid on it so far. Claims with no payments yet still
> appear, with 0 paid.*

The prompt starts small. Each time an attempt fails, TOKN sorts the failure
into one of a fixed set of classes and adds one short **patch** to the prompt.
A patch is admitted only if it cites logged evidence, such as an executor
error or a verifier result. A patch reaches the versioned **baseline** only if
it recurs across episodes, passes a regression gate and is approved by a
person. This command never promotes a patch by itself.

| Piece | In this example |
|---|---|
| **Constitution** (immutable) | `scenario.json` → `constitution`: read-only, one `CREATE VIEW`, permission `create_view` only, at most 6 iterations |
| **Baseline prompt** (versioned) | `scenario.json` → `baseline`, v1.0.0 |
| **Executor** | Every attempt runs on a fresh in-memory SQLite copy of `seed.sql` |
| **Verifier** (deterministic) | `AC-1` executes · `AC-2` non-empty · `AC-3` exactly 5 rows · `AC-4` output contract · `AC-5` required columns · `AC-6` a single statement |
| **Diagnoser** (fixed rules) | Assigns F-SCHEMA, F-LITERAL, F-GRAIN, F-FORMAT or F-SCOPE, then F-UNKNOWN, which escalates to a person |
| **Context pack** | Built from the database: the schema, distinct values of each status column, and table grain |
| **Episode log** | Optional append-only JSONL (`--log`) |

The data is fictional: five policies, ten claims (five `OPEN`) and eleven
payments. One open claim, `C-04`, has no payments yet.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| A TOKN release that includes `tokn earned-prompt run` | This walkthrough runs that command | `tokn earned-prompt run --help` |
| *Optional:* an LLM provider and key | Only for step 4, the live model | see [SETUP.md](../../SETUP.md) |
| *Optional:* `python3` (macOS / Linux, step 4 only) | `candidate.sh` reads the run log with the standard library | `python3 --version` |

Steps 1–3 need no model, no network and no key. The SQLite engine is built
into TOKN, so you don't need to install a database. The command has no
license gate, so Community and Trial both work.

> **What leaves your machine.** Steps 1–3 send nothing. In step 4, the only
> thing sent is the assembled prompt, which goes to the provider you configure.
> The SQL runs and is checked on your machine, against an in-memory database.
> The prompt does include the table schema and the distinct status values from
> `seed.sql`, because those are the evidence the patches cite. Keep that in
> mind if you adapt the example to your own data.

## 1. Open the example folder

macOS / Linux:

```bash
cd examples/evidence-earned-prompting
```

Windows PowerShell:

```powershell
Set-Location examples\evidence-earned-prompting
```

```text
evidence-earned-prompting/
  scenario.json        # constitution, baseline, task, acceptance checks
  seed.sql             # synthetic policies, claims, claim_payments
  replay.json          # four recorded attempts (offline)
  replay-unsafe.json   # one attempt that tries DROP VIEW
  candidate.sh         # live model candidate, macOS / Linux
  candidate.ps1        # live model candidate, Windows PowerShell
```

## 2. Replay four recorded attempts (offline)

```bash
tokn earned-prompt run --scenario . --replay replay.json
```

Expected output (your prompt hashes and token counts may differ):

```text
scenario: Open claims with paid-to-date (synthetic insurance data)  baseline v1.0.0  permissions=[create_view]
episode open-claims-paid-ep1: passed (all checks pass)
  iter 1  F-SCHEMA  prompt=eae1673532e6 patches=0 tokens=359  AC-1: SQL logic error: no such column: c.status (1)
  iter 2  F-LITERAL prompt=0112bf87e460 patches=1 tokens=508  AC-2: zero rows for filter value 'Open'
  iter 3  F-GRAIN   prompt=fca3b4de9ce2 patches=2 tokens=687  AC-3: row count 8 outside band 5-5
  iter 4  PASS      prompt=a382fd182528 patches=3 tokens=825
  patch open-claims-paid-ep1/p1-SCHEMA [F-SCHEMA] evidence=open-claims-paid-ep1/i1/executor: Use only the entities listed in the context pack schema; ...
  patch open-claims-paid-ep1/p2-LITERAL [F-LITERAL] evidence=open-claims-paid-ep1/i2/executor: Verify every filter literal against the value samples ...
  patch open-claims-paid-ep1/p3-GRAIN [F-GRAIN] evidence=open-claims-paid-ep1/i3/executor: State the expected output grain first and confirm no join multiplies rows; ...
```

Each line shows what went wrong, and what the loop learned from it:

| Iteration | What the SQL did | Class | What gets added |
|---|---|---|---|
| 1 | Used `c.status`, a column that doesn't exist (the real one is `claim_status`) | F-SCHEMA | The real schema goes into the context pack, plus a patch: "use only the listed entities" |
| 2 | Filtered on `'Open'`, but the data stores `'OPEN'`. SQLite compares strings case-sensitively, so it returned 0 rows | F-LITERAL | The distinct values of `claim_status` (`CLOSED, DENIED, OPEN`), plus a patch: "verify every filter literal" |
| 3 | Inner join to `claim_payments`: 8 rows, one per payment. The task wants 5, one per open claim. `C-04` also disappeared, because it has no payments | F-GRAIN | Table row counts and keys, plus a patch: "state the grain first" |
| 4 | Pre-aggregated payments with `LEFT JOIN` and `COALESCE(..., 0)` | PASS | — |

Every patch cites an evidence ID such as `.../i1/executor`. If a patch has no
evidence, or its evidence can't be found, the patch is rejected. Patches are
also rejected if they name or weaken an acceptance check, or try to edit the
constitution or the baseline. At most 5 patches can be active at once. When
the limit is reached, the patch that has fired least is retired first.

> **Be honest about replay.** A replay doesn't read the prompt. It only shows
> the loop's mechanics: diagnosis, admission, context and stop rules. To see a
> model actually respond to the patches, use step 4.

## 3. See the guardrails

**An action outside the permission list hard-stops before anything runs.**
Models often write `DROP VIEW IF EXISTS ...;` before a `CREATE VIEW`. The
constitution permits only `create_view`:

```bash
tokn earned-prompt run --scenario . --replay replay-unsafe.json
```

```text
episode open-claims-paid-ep1: permission_denied (action "drop_view" is outside the permission list)
  iter 1  BLOCKED   prompt=eae1673532e6 patches=0 tokens=354
```

**Recurrence makes a patch a candidate, not part of the baseline.** Run three
episodes:

```bash
tokn earned-prompt run --scenario . --replay replay.json --episodes 3
```

```text
promotion candidates (recurred in >= 3 episodes):
  F-GRAIN  "State the expected output grain first and confirm no join multiplies rows; ..."  (3 evidence refs)
  F-LITERAL  "Verify every filter literal against the value samples in the context pack before using it; ..."  (3 evidence refs)
  F-SCHEMA  "Use only the entities listed in the context pack schema; ..."  (3 evidence refs)
not promoted: promotion requires a regression gate and human approval.
```

Recurring three times only makes a patch a *candidate*. To get into the
baseline, it must also pass a regression gate on held-out tasks, with no drop
in pass rate and token cost within tolerance. Then a person must review the
diff. Only then does the baseline version go up, with a changelog entry that
records the evidence IDs. Patches that don't recur are discarded.

The other stop rules work the same way. If all checks pass, the loop stops.
If it reaches `max_iter` or the token budget, it stops and reports the best
attempt. If the same failure class happens three iterations in a row, or any
F-UNKNOWN appears, it escalates to a person instead of looping forever.

Add `--json` to any command for the full report. It includes the per-iteration
prompt hash, patch IDs, evidence IDs, verifier results, tokens and latency.
Add `--log scratch/episodes.jsonl` to keep the append-only episode log. The
`scratch/` folder must exist first.

## 4. Let a real model earn its patches (optional)

Configure a provider as in [SETUP.md](../../SETUP.md), then:

macOS / Linux:

```bash
export NOSPACE_MODEL_PROVIDER=<provider>   # e.g. openai, anthropic, azure-openai
export NOSPACE_MODEL_NAME=<model>
mkdir -p scratch
tokn earned-prompt run --scenario . --candidate-cmd "bash candidate.sh" --log scratch/episodes.jsonl
```

Windows PowerShell:

```powershell
$env:NOSPACE_MODEL_PROVIDER = '<provider>'
$env:NOSPACE_MODEL_NAME     = '<model>'
New-Item -ItemType Directory -Force scratch | Out-Null
tokn earned-prompt run --scenario . `
  --candidate-cmd "powershell -NoProfile -ExecutionPolicy Bypass -File candidate.ps1" `
  --log scratch\episodes.jsonl
```

Now the model reads the seven-section prompt:

1. constitution
2. baseline
3. active patches
4. context pack
5. prior-attempt summary
6. task input
7. output contract

What happens next is not fixed. A strong model may pass on iteration 1, and
then no patch is earned. That is the point: an instruction that wasn't needed
is never added. A weaker model may go through the same F-SCHEMA → F-LITERAL →
F-GRAIN sequence as the replay. If the model keeps making the same mistake
three times, the run escalates instead of spending your budget.

If the model wraps its answer in a ```` ```sql ```` fence, TOKN strips it. If
it adds a `DROP VIEW` line, the run hard-stops, as in step 3.

## Adapt it to your own task

Copy the folder and edit:

* `seed.sql`: your schema plus a small, non-sensitive sample.
* `scenario.json` → `task`: your requirement and output contract.
* `scenario.json` → `checks`: one of `executes`, `non_empty`, `single_statement`,
  `row_band:MIN-MAX`, `contract:REGEX` or `columns:a,b,c`. Use opaque IDs such
  as `AC-1`, so that patches can't name them.

Token counts are estimates (characters ÷ 4), because TOKN does not ship a
tokenizer.
