# Example: teach TOKN a preference once, and have a new session recall it

This walkthrough follows one preference from the moment you state it to the
moment a fresh session uses it, without being told again:

> *Next time, give me status updates as three bullet points or fewer. Then, in
> a new session, ask for a status update and check that TOKN uses bullets
> without being reminded.*

It uses two sessions. Session 1 teaches the preference. Session 2 starts from
nothing and recalls it.

| Feature | What it does here |
|---|---|
| **Automatic write-back** | A message that starts with "next time", "remember to", "from now on" and similar phrases is saved as a durable preference, with no confirmation step. |
| **`/recall`** | Searches the memory stores and prints the matches. |
| **`memory_search`** tool | The same search, called by the agent during a run. |
| **`remember`** tool | Saves a fact or preference explicitly, when you ask for it. |
| **`/memory`** | Shows the memory state and turns automatic write-back on or off. |
| **Trust levels** | Every entry carries a trust level. Your own corrections are stored as `verified`. |

All text in this example is synthetic.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with this walkthrough's commands | `tokn version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |
| Write access to `~/.tokn/memories/` | Where TOKN keeps memory | `ls ~/.tokn` (macOS / Linux) or `dir $HOME\.tokn` (PowerShell) |

Memory is a **Community** feature, so the free tier runs this example. Model
calls are billed by your own provider.

> **What leaves your machine.** Each run sends your prompt, and any memory
> entries TOKN places in the system prompt, to your model provider. The memory
> files themselves stay on your disk. TOKN removes credentials and personal
> data from a correction before it saves it.

## 1. Create a scratch repository

Memory is scoped to a repository root, so the demo needs one. Use a folder
outside this repo.

macOS / Linux:

```bash
mkdir -p ~/tokn-memory-demo && cd ~/tokn-memory-demo
git init -q
echo "Demo project: a small inventory service." > README.md
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-memory-demo | Out-Null
Set-Location $HOME\tokn-memory-demo
git init -q
"Demo project: a small inventory service." | Set-Content README.md
```

## 2. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a Claude model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a Claude model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Keep keys in your shell or in `~/.tokn/config/credentials.env`. Never commit a
key to a repo.

## 3. Check that memory is on

Open the REPL in the scratch repo and look at the memory state:

```bash
tokn agent-repl --repo-root ~/tokn-memory-demo
```

```text
/memory show
```

If it reports memory as off, run `/memory on`, then `/exit`.

## 4. Session 1: teach the preference

Put the teaching message in a file, so the quoting is simple. The message must
**start** with the trigger phrase, because detection looks at the start of the
message.

macOS / Linux:

```bash
cat > ~/session1.txt <<'EOF'
Next time, give me status updates as three bullet points or fewer. Then tell me what this project is in one sentence.
EOF
tokn agent-run --repo-root ~/tokn-memory-demo --prompt-file ~/session1.txt
```

Windows PowerShell:

```powershell
Set-Content $HOME\session1.txt "Next time, give me status updates as three bullet points or fewer. Then tell me what this project is in one sentence."
tokn agent-run --repo-root $HOME\tokn-memory-demo --prompt-file $HOME\session1.txt
```

TOKN answers the question. It also saves the preference. The save happens during
the run, not as a separate step.

## 5. Session 2: recall it in a new session

This is a new process with no shared chat history. Ask for a status update
and say nothing about format:

macOS / Linux:

```bash
tokn agent-run --repo-root ~/tokn-memory-demo --prompt "Give me a status update on this project."
```

Windows PowerShell:

```powershell
tokn agent-run --repo-root $HOME\tokn-memory-demo --prompt "Give me a status update on this project."
```

Then check the recall directly in the REPL:

```text
/recall bullet
```

## 6. Look at the stored memory

Both files live in your user profile, not in the repo:

| File | What it holds |
|---|---|
| `~/.tokn/memories/memory.json` | Cross-session entries. Each auto-saved correction has `"trust": "verified"`, `"pattern_type": "preference"` and `"auto": "true"`, plus a `"repo"` tag. |
| `~/.tokn/memories/context.md` | The project-memory file. Each correction is one line, marked with the repo it came from. |

macOS / Linux: `cat ~/.tokn/memories/context.md`

Windows PowerShell: `Get-Content $HOME\.tokn\memories\context.md`

## 7. Optional: save a fact explicitly

In the REPL, phrase a fact as a direct request. This uses the `remember` path,
and it also stores the entry as `verified`:

```text
Remember that I prefer British spelling in summaries.
```

Then run `/recall spelling`.

## What to look for

- **Session 2 uses bullets** without being told, and the answer has three or
  fewer. That is the proof of recall across sessions.
- **Repo scope.** Each entry carries a repo tag. Running the same recall from a
  different repo root should not show this preference. Only a message that says
  "in all repos" or "globally" is stored for every repo.
- **Only strong phrasings are saved.** "Next time", "remember to",
  "from now on" and "remember that" are saved. A bare "Always ..." or
  "Never ..." is treated as a one-off task rule and is **not** saved unless
  you add a durable phrase.
- **Credentials and personal data are removed** before anything is written.
  Try a correction that includes a fake token. The stored text should not
  contain it.
- **Turning memory off stops write-back.** After `/memory off`, a "next time"
  message is not saved.
- **Trust levels.** Entries are tagged `verified` (your own instructions),
  `internal` (generated during a run), `external` (web or API results) or
  `untrusted`. Trust is kept with each entry, so a reader can tell where it
  came from.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Session 2 ignores the preference | Memory was off during session 1 | `/memory show`, then `/memory on` and run session 1 again |
| `/recall` finds nothing | Ran from a different repo root | Use the same `--repo-root` as session 1 |
| Nothing was written | Message did not start with a trigger phrase | Start the message with "Next time," or "Remember to" |
| A bare "always ..." was not saved | Bare "always" and "never" are task-scoped by design | Phrase it as "from now on, ..." |
| `memory.json` is missing | No correction has been saved yet | Run session 1 first; the file is created on first write |

Expected outcomes above are based on the source code and tests. They are
**expected, not a recorded run.**
