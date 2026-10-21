# Example: let TOKN choose which skills to use, how many, and in what order

This walkthrough gives TOKN a small library of five skills and one task. TOKN
has to decide which skills apply, how many to use, and the order to apply them in.

> *Find every river gauge reading that reached flood stage, check the detections
> against the regression cases, and write the confirmed breaches to a report.*

| Feature | What it does here |
|---|---|
| **Skill composition** (on by default) | Selects an ordered, bounded sequence of skills from the library, instead of loading every matching skill. |
| **Composition log line** | Each run logs which skills were chosen, how many matched, and their order. You can grep for it. |
| **Flat fallback** (`--no-skill-compose`) | Turns composition off and loads every matching skill, so you can compare the two. |

The library has five skills. Four are relevant to the task. The fifth,
`deploy-alert`, is a distractor: its triggers do not match the task, so a
correct run leaves it out.

All data in `data/` is synthetic.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with the composition log line and the flags used here | `tokn version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |
| Tier: **trial or Community** | `tokn license features` on the Community tier lists `core:*` and `workflow:*`, which cover the agent loop used here. Community is enough. The 14-day trial (`tokn license trial`) is not required. | `tokn license` |

> **What leaves your machine.** The model provider receives the task, the
> skill text that TOKN selects, and the files the agent reads. Nothing else is
> sent. The `data/` files are synthetic.

## 1. Make a scratch repo

Composition looks for skills in the repository you run TOKN in. Use a scratch
folder so the example does not touch your own projects.

macOS / Linux:

```bash
mkdir -p ~/tokn-skills/data && cd ~/tokn-skills
cp -r path/to/examples/skill-compose/data/* data/
cp path/to/examples/skill-compose/task.md .
git init -q && git add -A && git commit -qm "skill compose example"
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-skills\data | Out-Null
Set-Location $HOME\tokn-skills
Copy-Item path\to\examples\skill-compose\data\* data\
Copy-Item path\to\examples\skill-compose\task.md .
git init -q; git add -A; git commit -qm "skill compose example"
```

Replace `path/to` with the location of your `tokn-dist` checkout.

## 2. Place the skills where TOKN discovers them

TOKN scans these folders in the repository root, in this order:

| Folder | Typical use |
|---|---|
| `.nospace/skills/` | TOKN's own project skills (used here) |
| `.github/skills/` | Skills shared with GitHub Copilot |
| `.agents/skills/` | Generic agent skills |
| `.claude/skills/` | Skills shared with Claude Code |

Each skill is a folder containing a `SKILL.md` file with frontmatter (`name`,
`description`, `triggers`, `category`).

macOS / Linux:

```bash
mkdir -p .nospace/skills
cp -r path/to/examples/skill-compose/skills/* .nospace/skills/
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force .nospace\skills | Out-Null
Copy-Item path\to\examples\skill-compose\skills\* .nospace\skills\ -Recurse
```

Commit the copied skills, or add them to `.gitignore`, so they are not mixed
with your own skills by accident.

> **Name collisions.** TOKN also reads skills from your home folder. If you
> already have a skill called `detect-flood` or `deploy-alert`, rename one of
> them before you run this example.

## 3. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For example:

```bash
export NOSPACE_MODEL_PROVIDER=<your provider>
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "<your provider>"
$env:NOSPACE_MODEL_NAME     = "<a model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Use your shell or `~/.tokn/config/credentials.env` for keys. Never commit a
key to the repo.

## 4. Run the task

Read the task from its file, skip confirmations, write the log to a known
file, and capture the final result as JSON:

macOS / Linux:

```bash
tokn agent-run --prompt-file task.md --no-confirm --headless \
  --max-steps 12 --log-file skills-run.log --output-format json > result.json
```

Windows PowerShell:

```powershell
tokn agent-run --prompt-file task.md --no-confirm --headless `
  --max-steps 12 --log-file skills-run.log --output-format json > result.json
```

`--headless` exits `0` on success, `1` on task failure, `2` on a usage error
and `3` if an action was denied or blocked.

## 5. See which skills were composed

TOKN writes one line per run to its log. Search for it:

macOS / Linux:

```bash
grep "skills.Compose" skills-run.log
```

Windows PowerShell:

```powershell
Select-String "skills.Compose" skills-run.log
```

You should see a line like this (your counts may differ):

```text
skills.Compose: selected 4 skill(s) (of 5 candidate matches), order=[fetch-gauge-data > flood-thresholds > detect-flood > verify-regression]
```

`(of N candidate matches)` is how many skills matched the prompt before
composition trimmed the list.

## 6. Compare with flat activation

Run the same task with composition turned off. TOKN then loads every matching
skill, in no particular order:

macOS / Linux:

```bash
tokn agent-run --prompt-file task.md --no-confirm --headless \
  --max-steps 12 --no-skill-compose --log-file flat-run.log --output-format json > flat.json
```

Windows PowerShell:

```powershell
tokn agent-run --prompt-file task.md --no-confirm --headless `
  --max-steps 12 --no-skill-compose --log-file flat-run.log --output-format json > flat.json
```

If `flat-run.log` has no `skills.Compose` line, composition was off for that run.
Compare the two `result.json` files to see the difference in steps and usage.

## 7. Cap how many skills are used (optional)

`--max-skills` limits the length of the sequence. The default is 8. Set it to
2 and the composer stops after two skills:

macOS / Linux:

```bash
tokn agent-run --prompt-file task.md --no-confirm --headless \
  --max-steps 12 --max-skills 2 --log-file capped-run.log --output-format json > capped.json
```

Windows PowerShell:

```powershell
tokn agent-run --prompt-file task.md --no-confirm --headless `
  --max-steps 12 --max-skills 2 --log-file capped-run.log --output-format json > capped.json
```

`--skill-token-budget <n>` does the same with a limit on prompt tokens instead of skill count.

## 8. Read the result

| File | Read it for |
|---|---|
| `result.json` | The final status, answer, step count and usage |
| `skills-run.log` | The `skills.Compose` line and the regime and dataflow lines that follow it |
| `report.md` | The confirmed breaches, written by the agent |

### What to look for

- **Which skills.** `deploy-alert` should be absent from the selected list. Its
  triggers do not match a flood-analysis task.
- **How many.** Four skills should be selected from five candidates.
- **In what order.** Gauge data first, then thresholds, then detection, then
  verification. A step that needs data from an earlier step should come after it.
- **Composition vs flat.** Compare `flat-run.log` with `skills-run.log`. The
  flat run loads more skill text into the prompt, which is why composition
  exists.

The expected breaches, from the synthetic data and the flood stages in
`flood-thresholds`, are RIV-01 at 02:00 (3.6 m), RIV-02 at 01:00 (2.8 m, equal
to flood stage, which counts) and RIV-03 at 02:00 (4.7 m). RIV-03 at 01:00
(4.4 m) is below flood stage. The regression file expects that reading to be
`ok`, which is a deliberate check. Check that the report agrees
with the rules in `detect-flood`, and that `verify-regression` reports any case
it disagrees with.

### What one of our runs looked like (your numbers will differ)

Our committed matrix ran this task with three models from two providers. In all
three, composition selected four skills in the expected order and left
`deploy-alert` out. Every run passed the regression check.

## Troubleshooting

| Symptom | Fix |
|---|---|
| No `skills.Compose` line in the log | No skill matched. Check that `.nospace/skills/` exists in the folder you run from, and that each `SKILL.md` has frontmatter. |
| `deploy-alert` was selected | Check the `triggers` line in its `SKILL.md`, and whether an older skill with the same name exists in your home folder. |
| Only one skill selected | Check `--max-skills` and `--skill-token-budget`. Unset them to use the defaults. |
| `Unknown flag` error | Run `tokn agent-run --help` and check the flag name. |
| Every step fails or stops early | The LLM is not configured. Re-check step 3. |
| `result.json` is empty | Check `skills-run.log` for the error. `--output-format json` writes to stdout and logs go to stderr. |
