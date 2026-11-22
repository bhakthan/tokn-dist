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

Recall is not the same as resuming. `/recall` and the `memory_search` tool read saved
preferences and facts. `tokn list-sessions` lists past chat sessions, and
`tokn agent-repl -c` resumes an unfinished run from its checkpoint. Neither is a memory
check. This walkthrough uses a throwaway TOKN profile (step 1) and a non-personal
preference, and deletes that profile at the end (step 8).

All text in this example is synthetic.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with this walkthrough's commands | `tokn version` |
| An LLM provider and key | Runs the agent. Use a model capable of the required tool calls; provider charges and number of turns depend on the run. A missing/failed tool result is unassessed, not a pass. | `tokn doctor --provider anthropic` (static; does not prove the key works) |
| A throwaway TOKN profile | Keeps the demo memory out of your real `~/.tokn/memories/` | set `TOKN_HOME` in step 1 |

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
export TOKN_HOME="$HOME/tokn-memory-demo-home"   # throwaway profile; same shell for every step
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-memory-demo | Out-Null
Set-Location $HOME\tokn-memory-demo
git init -q
"Demo project: a small inventory service." | Set-Content README.md
$env:TOKN_HOME = "$HOME\tokn-memory-demo-home"   # throwaway profile; same shell for every step
```

`TOKN_HOME` moves TOKN's whole profile (memory, sessions, config) for this shell only.
Run every later step in the same shell, or set it again. On first use, v0.3.118 copies (never moves)
any legacy `~/.nospace` data into the new profile. If you have old memory there, it may
appear in `/recall`; deleting the throwaway profile does not touch the original.

## 2. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "YOUR_MODEL_ID"
$env:ANTHROPIC_API_KEY      = Read-Host 'Anthropic key' -MaskInput   # pwsh 7.1+; or read it from your secret store
```

Keep keys in your shell session. Never commit a key to a repo. A key file under your
normal `~/.tokn/config/` is not read while `TOKN_HOME` points at the throwaway profile.

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

Both files live in the TOKN profile (normally `~/.tokn`; here the throwaway `$TOKN_HOME`), not in the repo:

| File | What it holds |
|---|---|
| `$TOKN_HOME/memories/memory.json` | Cross-session entries. Each auto-saved correction has `"trust": "verified"`, `"pattern_type": "preference"` and `"auto": "true"`, plus a `"repo"` tag. |
| `$TOKN_HOME/memories/context.md` | The project-memory file. Each correction is one line, marked with the repo it came from. |

macOS / Linux: `cat "$TOKN_HOME/memories/context.md"`

Windows PowerShell: `Get-Content "$env:TOKN_HOME\memories\context.md"`

## 7. Optional: save a fact explicitly

In the REPL, phrase a fact as a direct request. This uses the `remember` path,
and it also stores the entry as `verified`:

```text
Remember that I prefer British spelling in summaries.
```

Then run `/recall spelling`.

## 8. Clean up

Delete the throwaway profile and scratch repo, then clear the variable. Your real
`~/.tokn` is untouched.

```bash
rm -rf "$HOME/tokn-memory-demo-home" "$HOME/tokn-memory-demo" "$HOME/session1.txt"; unset TOKN_HOME
```

```powershell
Remove-Item -Recurse -Force "$HOME\tokn-memory-demo-home", "$HOME\tokn-memory-demo", "$HOME\session1.txt"; Remove-Item Env:TOKN_HOME
```

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
