# Example: Delegation and sign-off — decide what to automate, then sign for what you ship

> "Which of these tasks can I hand to an agent unattended, which need a human
> in the loop, and how do I record who approved the risky one?"

Not every task should be automated the same way. `tokn delegate assess` rates a
task on four axes and recommends one of four automation levels. It then lists
the TOKN controls that level calls for. When the advisor lists **sign-off**,
`tokn sign-off` writes a sealed record of what a named human approved, and
`tokn sign-off verify` tells you later whether anything changed.

| Step | Command | What it tells you |
|---|---|---|
| Assess | `tokn delegate assess "<task>"` | A level: `automate`, `automate-with-review`, `assist-only`, or `human-only` |
| | `--stakes` `--reversibility` `--ambiguity` `--frequency` | Your own ratings, instead of ratings guessed from the wording |
| | `--json` | The same assessment for scripts |
| Sign | `tokn sign-off --signer NAME` | A record of the proof, critique, and git diff, with SHA-256 hashes and a seal |
| Check | `tokn sign-off verify <record>` | Whether the record was edited, or the signed work changed, since signing |

Both commands are **offline and deterministic**. Neither calls a model. The
advisor only prints a recommendation. It does not turn any control on.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.67 or later | Ships `tokn delegate` and `tokn sign-off` | `tokn delegate --help` |
| git 2.28 or later (steps 7–10) | `sign-off` hashes a `git diff`; the setup uses `git init -b` | `git --version` |
| A git identity (steps 7–10) | The demo repo makes two commits | `git config user.name` |
| This example folder (steps 7–10) | Two small fixture files in [`fixtures/`](fixtures/) | — |

It runs on every tier, including the free Community tier. No model provider
is needed for any step.

On an expired trial, every command first prints a "trial has ended — running
the free community tier" notice to stderr. The outputs below leave it out. Add
`2>/dev/null` (bash) or `2>$null` (PowerShell) to hide it too.

### What leaves your machine

Nothing from these two commands. `delegate assess` reads only its arguments.
`sign-off` reads local files and runs `git`. TOKN's own once-a-day "update
available" check can still go out; pass `--no-update-check` or set
`TOKN_NO_UPDATE_CHECK=1` to turn it off.

## 1. The four ratings

```text
tokn delegate assess --help
```

| Flag | Values | Question it answers |
|---|---|---|
| `--stakes` | `low` \| `moderate` \| `high` | How costly is a wrong outcome? |
| `--reversibility` | `reversible` \| `partly-reversible` \| `irreversible` | Can the effect be undone? |
| `--reversible` | `--reversible=true` \| `--reversible=false` | Shorthand for the two ends of `--reversibility` |
| `--ambiguity` | `low` \| `medium` \| `high` | How under-specified is the task? |
| `--frequency` | `rare` \| `occasional` \| `frequent` | How often does it recur? |

Any rating you leave out is inferred from the task wording and labelled
`(inferred ...)`. The rules are fixed, so the same input always gives the same
answer.

## 2. Task 1 — the formatter: `automate`

A low-stakes, reversible, well-specified task that runs on every commit. Give
all four ratings.

```bash
tokn delegate assess "run the formatter on every commit" \
  --stakes low --reversibility reversible --ambiguity low --frequency frequent
```

PowerShell:

```powershell
tokn delegate assess "run the formatter on every commit" `
  --stakes low --reversibility reversible --ambiguity low --frequency frequent
```

Expected:

```text
task:  run the formatter on every commit
level: automate

ratings
  stakes         low
  reversibility  reversible
  ambiguity      low
  frequency      frequent

why
  - the task is frequent, low-stakes, reversible and well-specified — the clearest case for unattended automation

controls
  - run log review       unattended runs still need an after-the-fact record someone actually reads

This is an automation RECOMMENDATION, not a permission grant. ...
```

No rating says `(inferred)`, so the result rests only on your input. Even at
`automate`, one control remains: someone should read the run log.

Frequency matters. Change `--frequency frequent` to `--frequency rare` and the
level drops:

```text
level: automate-with-review
...
why
  - the task is rare, so the setup cost of unattended automation is not repaid; run it attended
```

## 3. The same task, with inferred ratings

Now give only the frequency. This is the example from `--help`.

```bash
tokn delegate assess "run the formatter on every commit" --frequency frequent
```

Expected:

```text
task:  run the formatter on every commit
level: automate-with-review

ratings
  stakes         moderate  (inferred: default)
  reversibility  reversible  (inferred from "format")
  ambiguity      medium  (inferred: default)
  frequency      frequent

why
  - a wrong outcome carries moderate cost, so a review step is warranted
  - the task is partly under-specified, so the result should be reviewed against the actual intent

controls
  - HITL checkpoint      pause before effects land so a human can approve or reject them
  - clarify scope first  resolve the under-specified parts with the requester before executing
  - plan mode            state the intended changes before making them, so the review has something to review

This is an automation RECOMMENDATION, not a permission grant. ...

note: at least one rating was inferred from the task wording. Supply --stakes / --reversibility / --ambiguity / --frequency to remove the guess.
```

There are two kinds of label:

- `(inferred from "format")` — a word in the task matched a rule.
- `(inferred: default)` — nothing matched, so a middle value was used.

The defaults (`moderate` stakes, `medium` ambiguity) lean cautious. The same
task got `automate` in step 2 only because you said it was low-stakes and
well-specified. When the answer matters, give all four ratings.

A word can also lower a rating. Here "draft" was read as low stakes:

```bash
tokn delegate assess "rename a local variable in a draft branch"
```

Expected (shortened):

```text
task:  rename a local variable in a draft branch
level: automate-with-review

ratings
  stakes         low  (inferred from "draft")
  reversibility  partly-reversible  (inferred: default)
  ambiguity      medium  (inferred: default)
  frequency      occasional  (inferred: default)
...
```

## 4. Task 2 — rotating staging keys: `assist-only`

Reversible and clear, but a mistake is expensive.

```bash
tokn delegate assess "rotate the staging API keys" \
  --stakes high --reversibility reversible --ambiguity low --frequency occasional
```

PowerShell:

```powershell
tokn delegate assess "rotate the staging API keys" `
  --stakes high --reversibility reversible --ambiguity low --frequency occasional
```

Expected:

```text
task:  rotate the staging API keys
level: assist-only

ratings
  stakes         high
  reversibility  reversible
  ambiguity      low
  frequency      occasional

why
  - a wrong outcome carries high cost, so the agent should prepare the work and a human should execute it

controls
  - HITL checkpoint      no effect lands without an explicit human action
  - independent review   a second pass by a reviewer who did not author the work
  - plan mode            produce the plan and the diff; let the human apply them
  - sign-off             record who approved the work and on what basis
...
```

Without ratings, the same wording gets every rating from defaults and comes
out as `automate-with-review`. Nothing in "rotate the staging API keys" tells
TOKN the stakes are high. Only you know that.

## 5. Task 3 — deleting production backups: `human-only`

Run it with no ratings first:

```bash
tokn delegate assess "delete the production database backups"
```

Expected:

```text
task:  delete the production database backups
level: human-only

ratings
  stakes         high  (inferred from "production")
  reversibility  irreversible  (inferred from "delete")
  ambiguity      medium  (inferred: default)
  frequency      occasional  (inferred: default)

why
  - the task is irreversible, so its effects must pass a human before they land
  - a wrong outcome carries high cost, so the agent should prepare the work and a human should execute it
  - high stakes combined with irreversibility leaves no recovery path, so a human must drive the task
  - the task is partly under-specified, so the result should be reviewed against the actual intent

controls
  - clarify scope first  resolve the under-specified parts with the requester before executing
  - human ownership      the agent advises; a named human makes and owns the decision
  - independent review   a second pass by a reviewer who did not author the work
  - rollback plan        an irreversible step needs a documented recovery path before, not after
  - sandbox / dry-run    exercise the operation where its effects can be discarded before running it for real
  - sign-off             record the accountable decision-maker
...
note: at least one rating was inferred from the task wording. ...
```

Here the words did the work. "production" and "delete" were enough for
`human-only`. Give the ratings anyway, so the record does not rest on a guess:

```bash
tokn delegate assess "delete the production database backups" --stakes high --reversible=false
```

Expected (shortened):

```text
ratings
  stakes         high
  reversibility  irreversible
  ambiguity      medium  (inferred: default)
  frequency      occasional  (inferred: default)
```

Write `--reversible=false` with the `=`. See [Troubleshooting](#troubleshooting).

## 6. JSON for scripts

`--json` prints the same assessment as one JSON object on stdout. Each rating
carries an `inferred` flag.

```bash
tokn delegate assess "run the formatter on every commit" \
  --stakes low --reversibility reversible --ambiguity low --frequency frequent --json 2>/dev/null
```

Expected (shortened):

```json
{
  "task": "run the formatter on every commit",
  "level": "automate",
  "ratings": [
    { "name": "stakes", "value": "low", "inferred": false },
    ...
  ],
  "reasons": [ "the task is frequent, low-stakes, reversible and well-specified — ..." ],
  "controls": [ { "name": "run log review", "why": "unattended runs still need ..." } ],
  "guidance": "This is an automation RECOMMENDATION, not a permission grant. ..."
}
```

PowerShell, listing which ratings were guessed:

```powershell
$a = tokn delegate assess "run the formatter on every commit" --frequency frequent --json 2>$null |
  Out-String | ConvertFrom-Json
$a.level
($a.ratings | Where-Object inferred).name -join ','
```

Expected:

```text
automate-with-review
stakes,reversibility,ambiguity
```

### Levels and controls, side by side

What the four runs above returned:

| Level | Meaning (from the tool's own guidance) | Controls listed |
|---|---|---|
| `automate` | runs unattended | run log review |
| `automate-with-review` | the work runs but its effects wait for a human | HITL checkpoint, plan mode; plus clarify scope first when ambiguity is not low; plus rollback plan and sandbox / dry-run when only partly reversible |
| `assist-only` | the agent prepares and the human executes | HITL checkpoint, independent review, plan mode, sign-off |
| `human-only` | the agent should not drive the task at all | clarify scope first, human ownership, independent review, rollback plan, sandbox / dry-run, sign-off |

The controls are a checklist for you. The advisor does not turn on plan mode,
checkpoints, or a sandbox. Both the `assist-only` and the `human-only` task
list **sign-off**. The rest of this walkthrough does that step.

## 7. Set up a change to sign off

The demo change shortens log retention from 30 days to 7. Logs already deleted
cannot be brought back, so this is the kind of change a named human should
approve. Work on a branch so you can sign against `main`.

Set `EX` to this folder in your copy of `tokn-dist`.

bash:

```bash
EX="/path/to/tokn-dist/examples/delegation-and-signoff"
DEMO="$HOME/tokn-signoff-demo"
mkdir -p "$DEMO" && cd "$DEMO"
git init -q -b main
printf '.nospace/\n' > .gitignore
printf 'retention_days = 30\n' > app.txt
git add . && git commit -qm "initial config"
git switch -q -c shorten-retention
printf 'retention_days = 7\n' > app.txt
mkdir -p .nospace/runs && cp "$EX/fixtures/PROOF.md" .nospace/runs/PROOF.md
```

PowerShell:

```powershell
$EX   = "C:\path\to\tokn-dist\examples\delegation-and-signoff"
$DEMO = "$HOME\tokn-signoff-demo"
New-Item -ItemType Directory $DEMO -Force | Out-Null
Set-Location $DEMO
git init -q -b main
Set-Content .gitignore ".nospace/"
Set-Content app.txt "retention_days = 30"
git add .
git commit -qm "initial config"
git switch -q -c shorten-retention
Set-Content app.txt "retention_days = 7"
New-Item -ItemType Directory .nospace\runs -Force | Out-Null
Copy-Item "$EX\fixtures\PROOF.md" .nospace\runs\PROOF.md
```

| File | What it is |
|---|---|
| `fixtures/PROOF.md` | A hand-written proof-of-work note: what changed, the dry run, the rollback. `sign-off` looks for it at `.nospace/runs/PROOF.md` by default. |
| `fixtures/critique-verdict.json` | A hand-written reviewer verdict, passed with `--critique`. |

Both are samples written for this example, not TOKN output. `sign-off` hashes
whatever file you give it.

`.nospace/` goes in `.gitignore` so the sign-off records do not show up as
untracked files in your own diff.

## 8. Sign off

In a terminal, run without `--yes`. Per `tokn sign-off --help`, TOKN then
asks you to type `yes`:

```bash
tokn sign-off --signer "Ada Reviewer" --base main --critique "$EX/fixtures/critique-verdict.json"
```

The run recorded below used `--yes` instead, because it was not a terminal.
Use `--yes` only when you are the signer and mean it.

bash:

```bash
tokn sign-off --signer "Ada Reviewer" --base main --critique "$EX/fixtures/critique-verdict.json" --yes
```

PowerShell:

```powershell
tokn sign-off --signer "Ada Reviewer" --base main --critique "$EX\fixtures\critique-verdict.json" --yes
```

Expected:

```text
Sign-off for …\tokn-signoff-demo
  proof    present sha256 c9908fdbcf79… (353 bytes)
  critique present sha256 dd48733451c7… (172 bytes)
  diff     present sha256 c9094cda2a7c… (142 bytes)

Signed off by Ada Reviewer.
  …\tokn-signoff-demo\.nospace\signoff\20261027T134232Z.md
  …\tokn-signoff-demo\.nospace\signoff\20261027T134232Z.json
  seal bc60376b8c487b073378f7e7c78dd52d5c7451565d1aab6c5b494a8dcd34f07a
```

Your hashes, timestamp, and seal will differ. Line endings alone change the
hashes.

TOKN refuses to sign without a name, and refuses a non-interactive stdin
without `--yes`. Piping `yes` into it is refused too:

```text
Error: --signer "<your name>" is required: a sign-off must name the human who confirmed it
```

```text
Error: refusing to sign off: stdin is not an interactive terminal and --yes was not given.
Run in a terminal to confirm interactively, or pass --yes if you are the signer confirming deliberately
```

A missing component is recorded as `absent` with a reason, never skipped.
Without `.nospace/runs/PROOF.md` and `--critique`, the summary reads:

```text
  proof    absent  file not found: …\.nospace\runs\PROOF.md (no proof-of-work ledger at the default location; run the agent with proof-of-work enabled or pass --proof <path>)
  critique absent  no critique verdict supplied — TOKN's critique mode does not persist a verdict file; pass --critique <path> to include one
  diff     present sha256 c9094cda2a7c… (142 bytes)
```

## 9. Read the record

Each sign-off writes a `.md` for people and a `.json` for `verify`.

bash:

```bash
cat "$(ls -t .nospace/signoff/*.md | head -1)"
```

PowerShell:

```powershell
Get-Content (Get-ChildItem .nospace\signoff\*.md | Sort-Object Name | Select-Object -Last 1)
```

Expected (shortened):

```text
# Sign-off record

- **Signer:** Ada Reviewer
- **Confirmation:** flag --yes
- **Signed at:** 2026-10-27T13:42:32Z
- **Repository:** `…\tokn-signoff-demo`
- **Diff base:** `main`
- **Seal (SHA-256 of JSON record):** `bc60376b8c48…`

The seal detects edits and drift; it is not a cryptographic signature. Verify with `tokn sign-off verify <record.json>`.

## Components

| component | status | sha256 | bytes | source | note |
|---|---|---|---|---|---|
| proof | **present** | `c9908fdbcf79…` | 353 | `…\.nospace\runs\PROOF.md` |  |
| critique | **present** | `dd48733451c7…` | 172 | `…\fixtures\critique-verdict.json` |  |
| diff | **present** | `c9094cda2a7c…` | 142 | `git diff main (working tree vs base)` |  |
...
```

The record also embeds each component in full, including the diff itself.
Note `Confirmation: flag --yes`: the record says how you confirmed.

## 10. Verify, commit, and catch drift

Save the record path, then verify.

bash:

```bash
RECORD=$(ls -t .nospace/signoff/*.json | head -1)
tokn sign-off verify "$RECORD"
```

PowerShell:

```powershell
$RECORD = (Get-ChildItem .nospace\signoff\*.json | Sort-Object Name | Select-Object -Last 1).FullName
tokn sign-off verify $RECORD
```

Expected:

```text
sign-off verify: OK — no drift since signing
  record: …\.nospace\signoff\20261027T134232Z.json
  signer: Ada Reviewer
  seal:   intact
  ✓ proof    unchanged
  ✓ critique unchanged
  ✓ diff     unchanged
```

Commit the change and verify again:

```bash
git commit -qam "shorten log retention to 7 days"
tokn sign-off verify "$RECORD"
```

Expected (first line):

```text
sign-off verify: OK — no drift since signing
```

It still passes because you signed against `main`, and the branch still
differs from `main` by the same diff. Signed against the default (`HEAD`), the
same commit reports drift, because the working tree then matches `HEAD` and
the diff is empty.

Now change the file after signing:

bash:

```bash
printf 'retention_days = 1\n' > app.txt
tokn sign-off verify "$RECORD"; echo "exit $?"
```

PowerShell:

```powershell
Set-Content app.txt "retention_days = 1"
tokn sign-off verify $RECORD; "exit $LASTEXITCODE"
```

Expected:

```text
sign-off verify: DRIFT — the signed state no longer matches
  record: …\.nospace\signoff\20261027T134232Z.json
  signer: Ada Reviewer
  seal:   intact
  ✓ proof    unchanged
  ✓ critique unchanged
  ✗ diff     content changed since signing
exit 1
```

Undo it with `git checkout -- app.txt` and `verify` passes again.

Editing the record itself breaks the seal. Here a copy of the record had its
signer changed to `Mallory`:

```text
sign-off verify: DRIFT — the signed state no longer matches
  record: tampered.json
  signer: Mallory
  seal:   BROKEN — the record file was edited after signing
  ✓ proof    unchanged
  ✓ critique unchanged
  ✓ diff     unchanged
```

`verify` exits 1 on any drift or a broken seal, so you can use it as a CI gate.
`verify --json` prints `ok`, `seal_valid`, and a per-component `checks` list
with the signed and current hashes.

When you are done, delete the demo folder (`$DEMO`).

## What to look for

- **`(inferred ...)` labels.** They are the weakest part of a result. Defaults
  lean cautious, but a word like "draft" can lower a rating.
- **Stakes the wording cannot show.** "rotate the staging API keys" gets
  `automate-with-review` from defaults and `assist-only` once you say the
  stakes are high.
- **Irreversibility.** Every high-stakes irreversible case above came out
  `human-only`. The tool's own guidance says irreversibility dominates every
  other factor.
- **`absent` components.** A sign-off with only a diff is still valid. The
  record says plainly what was not there.
- **The untracked-files note.** `git diff` ignores untracked files. When any
  exist, `sign-off` prints `note: N untracked file(s) are NOT in the diff`.
  Use `git add -N <file>` to include them.
- **The seal is not a signature.** It detects edits and drift. It does not
  prove who ran the command.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Error: accepts 1 arg(s), received 2` | You wrote `--reversible false`. A boolean flag takes no separate value; write `--reversible=false`. Also quote the task as one argument. |
| `Error: --reversibility=reversible conflicts with --reversible=false` | Use one of `--reversible` or `--reversibility`, not both. |
| `Error: invalid stakes "extreme" (want low\|moderate\|high)` | Use one of the listed values. Each rating flag says which values it accepts. |
| `refusing to sign off: stdin is not an interactive terminal` | Run in a terminal and type `yes`, or pass `--yes` if you are the signer. Piped input is refused on purpose. |
| `--signer "<your name>" is required` | Add `--signer "Your Name"`. Quote names with spaces. |
| `not inside a git repository` | `cd` into a git repo, or pass `--repo <dir>`. |
| `verify` reports diff drift right after you commit | You signed against the default `HEAD`. Sign with `--base <branch>` (step 10). |
| Each error message prints twice | Both copies are the same error. Nothing else went wrong. |
| `--json` output is mixed with the trial notice | The notice goes to stderr. Add `2>/dev/null` (bash) or `2>$null` (PowerShell). In PowerShell, do not use `2>&1` before `ConvertFrom-Json`. |
| `sign-off --json` output does not parse as JSON | In v0.3.67 the human summary (`Sign-off for …`) is printed before the JSON on stdout. Read the written `.json` record instead, or use `verify --json`, which is pure JSON. |
| A task with `$` in it changes in PowerShell | Double quotes expand `$name` (`"reset $HOME/cache"` becomes `reset C:\Users\…/cache`). Use single quotes: `'reset $HOME/cache'`. |
| `/delegate` in a REPL session does something else | That slash command hands a task to a peer agent. The advisor is the `tokn delegate assess` CLI command. |
