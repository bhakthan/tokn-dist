# Example: block writes to a protected folder with a PreToolUse hook

This walkthrough adds two lifecycle hooks to a small repo and shows one of them
blocking a write during a real `tokn agent-run`:

> *Write a status note to two places, one of them a protected folder, and
> report which write succeeded.*

| Feature | What it does here |
|---|---|
| **PreToolUse command hook** | Runs before each file-write tool call. Exit code `2` refuses the call, and the hook's stderr becomes the reason the model sees. |
| **PostToolUse command hook** | Runs after each file-write tool call and appends one line to a local audit file. |
| **Workspace trust** (`tokn trust`) | Repo-local hooks only run in a workspace you have trusted. |

TOKN supports 26 lifecycle phases and four handler types: `command`, `http`,
`prompt` and `agent`. This example uses only `command` hooks on the two
tool-call phases. The `http` handler is omitted on purpose, so nothing in
this example sends data over the network. The phase names are in
`environment-manager/internal/agent/hooks/hooks.go`, and the config keys map
to them in `hooks/configurable.go`: `PreToolUse` maps to `before_tool_call`,
and `PostToolUse` maps to `after_tool_call`.

All paths and content in `repo/` are synthetic.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with the hook behaviour shown here | `tokn version` |
| A shell for the hook scripts | `sh` on macOS / Linux, PowerShell 5.1+ on Windows | `sh -c "echo ok"` / `$PSVersionTable.PSVersion` |
| `git` (optional) | Only if you want to commit the example repo | `git --version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |

Trial and Community tiers both run this example. I did not find a license gate
on hooks or `agent-run` in source, but the Community feature list only names
`core:*` and `workflow:*`, so confirm with `tokn version` before you start.
Model calls are billed by your own provider, not by TOKN.

> **What leaves your machine.** The model provider receives the task and the
> files the agent reads or writes. The hook scripts run locally and write only
> to `.tokn-audit/` inside the example repo. Nothing else is sent.

## 1. Copy the example repo

macOS / Linux:

```bash
cp -r examples/custom-hooks/repo ~/tokn-hooks-demo
cd ~/tokn-hooks-demo
mkdir -p protected notes
```

Windows PowerShell:

```powershell
Copy-Item examples\custom-hooks\repo $HOME\tokn-hooks-demo -Recurse
Set-Location $HOME\tokn-hooks-demo
New-Item -ItemType Directory -Force protected, notes | Out-Null
```

You now have:

```text
tokn-hooks-demo/
  task.md                       # the task
  .claude/settings.json         # hook config (bash)
  .claude/settings.powershell.json  # the same hooks, for Windows cmd
  hooks/block_protected.sh/.ps1 # PreToolUse: refuse writes under protected/
  hooks/audit_write.sh/.ps1     # PostToolUse: append to .tokn-audit/hook-audit.log
  protected/                    # empty; writes here should be blocked
  notes/                        # empty; writes here should succeed
```

**Windows only:** TOKN runs command hooks with `cmd /c`, so use the PowerShell
config. Replace the bash file with it:

```powershell
Copy-Item .claude\settings.powershell.json .claude\settings.json -Force
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

Use your shell or `~/.tokn/config/credentials.env` for keys. Never commit a
key to the repo.

## 3. Trust the workspace so hooks load

TOKN treats an unknown repo as untrusted and ignores `.claude/settings.json`,
so the hooks would silently not run. Trust the repo once you have read the
hook scripts, which is the case here:

macOS / Linux / Windows PowerShell:

```bash
tokn trust . --capability hooks -y
tokn trust status .
```

The grant is pinned to the current contents of the settings file. If you edit
`.claude/settings.json` later, run the `tokn trust` command again.

## 4. Run the agent

`--no-confirm` auto-approves tool calls, which is acceptable in this scratch
repo. Leave it off if you want to approve each edit.

macOS / Linux / Windows PowerShell:

```bash
tokn agent-run --repo-root . --prompt-file task.md --no-confirm --max-steps 8
```

## 5. See the hook block the write

Expected behaviour, from the code paths in `loop/realworld.go` and
`hooks/configurable.go`:

| Step | What you should see |
|---|---|
| Write to `protected/status.md` | The `PreToolUse` script exits `2`. The file is **not** created. The agent receives the error `blocked: writes under protected/ are not allowed (protected/status.md)` and does not retry the same path. |
| Write to `notes/status.md` | The `PreToolUse` script exits `0`. The file is created. `PostToolUse` appends one audit line. |
| Final answer | The agent says which write succeeded and which was blocked, as `task.md` asks. |

Check the results on disk:

macOS / Linux:

```bash
ls protected/          # empty
cat notes/status.md
cat .tokn-audit/hook-audit.log
```

Windows PowerShell:

```powershell
Get-ChildItem protected                  # empty
Get-Content notes\status.md
Get-Content .tokn-audit\hook-audit.log
```

The audit log should have one line for the allowed write, for example:

```text
2025-01-01T12:00:00Z tool=write_file path=notes/status.md
```

The run log records the blocked call as an event named `hook-blocked`. Find it
in `.tokn/logs/` under the repo (the default is `session-<stamp>.log`, per
`tokn agent-run --help`). Use `--log-file` to choose a different path.

### What to look for

- **The file is absent, not just empty.** A blocked call never reaches the
  tool, so `protected/status.md` should not exist.
- **The reason reaches the model.** The agent's next message should mention
  the protected path, which shows the stderr from the hook was used.
- **Only allowed writes are audited.** The audit file is local and has no file
  contents in it.
- **Trust is pinned.** Change `settings.json` and the hooks stop until you
  run `tokn trust` again.

## 6. Clean up

```bash
rm -rf .tokn-audit
```

```powershell
Remove-Item -Recurse -Force .tokn-audit
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| The write to `protected/` succeeds and no block appears | Check trust: `tokn trust status .`. Hooks are ignored in an untrusted repo |
| Hooks not running | Run `tokn trust . --capability hooks -y`, then `tokn trust status .` to confirm. Re-grant after editing `settings.json` |
| No `.tokn-audit/hook-audit.log` after the run | Check that `notes/status.md` was written, and that `PostToolUse` matches `write_file` in your run. Check the run log in `.tokn/logs/` |
| `sh: command not found` on Windows | Use `.claude/settings.powershell.json` (step 1). Command hooks run through `cmd /c` on Windows |
| `execution of scripts is disabled` | The PowerShell config already passes `-ExecutionPolicy Bypass`. Check that you copied the right file |
| The agent uses a tool name other than `write_file`, `edit_file` or `create_file` | The matcher only covers those three. Add the tool name to `matcher` in the settings file |
| The model call fails | The LLM is not configured. Re-check step 2 |
