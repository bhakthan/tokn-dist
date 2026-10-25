# Example: Use TOKN from T3 Code

> "I like T3 Code's interface. I want TOKN's harness, local models and gates behind it."

[T3 Code](https://github.com/pingdotgg/t3code) is an open-source (MIT) web, desktop and mobile app for coding agents. It can run any agent that speaks the [Agent Client Protocol](https://agentclientprotocol.com) (ACP), and `tokn acp` is one. You add TOKN once as a **Local ACP command**, and nothing in T3 Code needs to change.

| What you get in T3 Code | How TOKN provides it |
|---|---|
| Mode selector and Plan toggle | Modes `default`, `accept_edits`, `plan` and `autopilot` |
| Model picker | `--available-models` |
| Inline diffs for every edit | Diff content on file-edit tool calls |
| Approve or deny prompts | Tools TOKN gates become permission requests; anything but an explicit allow denies |
| T3 Code's own tools inside the agent | TOKN starts T3 Code's MCP bridge for each session |
| Threads that survive a restart | `session/load` replays a bounded transcript |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.62 or later | The T3 Code compatibility in `tokn acp` | `tokn version` |
| T3 Code (desktop app, or `npx t3`) | The user interface | its install guide |
| A model: cloud key, or a local Ollama or llama.cpp server | Every prompt runs a TOKN turn | `tokn acp --help` |

### What leaves your machine

- `tokn acp` sends prompts and the files the agent reads to the model provider you choose. With `--provider ollama` or `--provider gguf`, that is a server on your own network, so nothing leaves the machine.
- Resumable transcripts stay in `~/.tokn/acp-sessions`: at most 200 sessions, each capped at 20 turns or 48 KiB. Pass `--no-session-store` to keep none.
- What T3 Code itself sends (for example remote pairing) is governed by T3 Code, not TOKN.

## 1. Check TOKN on its own

`tokn acp` writes protocol frames to stdout, so a healthy start prints nothing. Stop it with Ctrl+C.

bash:

```bash
export OPENAI_API_KEY=sk-...
tokn acp --provider openai --model gpt-5.6-sol
```

PowerShell:

```powershell
$env:OPENAI_API_KEY = "sk-..."
tokn acp --provider openai --model gpt-5.6-sol
```

Air-gapped, with a local Ollama model instead:

```bash
tokn acp --provider ollama --model qwen3-coder
```

## 2. Add TOKN to T3 Code

In T3 Code, open **Settings → Providers → Add provider → Local ACP command** and fill in:

| Field | Value |
|---|---|
| Command path | `tokn`, or its absolute path (for example `C:\tools\tokn.exe`) |
| Arguments, one per row | `acp` · `--provider` · `openai` · `--model` · `gpt-5.6-sol` |
| Environment overrides | `OPENAI_API_KEY` (or the key for your provider) |
| Auth method | leave empty |

T3 Code does **not** use a shell, so `~`, `$VAR` and quotes are passed literally. Put every flag and every value in its own row.

Useful extra arguments:

| Arguments | Effect |
|---|---|
| `--permission-mode` `accept_edits` | Start new threads with edits auto-approved |
| `--available-models` `gpt-5.6-sol,gpt-5.6-luna` | Models listed in T3 Code's picker |
| `--max-steps` `80` | A longer budget per prompt (default 50) |
| `--no-session-store` | Keep no transcripts (threads cannot resume after a restart) |

When you save, T3 Code checks the agent by opening a session. A missing key shows up there as TOKN's error message.

## 3. Try it on a project

Open a folder in T3 Code, start a thread with the TOKN provider, and try three prompts:

1. **Plan first.** Turn on Plan, then ask: *"How would you add input validation to this project?"* TOKN blocks write tools in `plan` mode, so you get a design and no edits.
2. **Build with approvals.** Turn Plan off, keep the `default` mode, and ask: *"Implement that validation and add tests."* Every edit asks first, and each approval shows its diff inline.
3. **Let it run.** Switch the mode to `accept_edits`, or to `autopilot` if you trust the task. Edits stop asking, but domain safety hooks still apply in `autopilot`.

Expected, not a recorded run: tool calls appear as they happen, edits show diffs with file locations, and the final answer streams into the thread.

## 4. Resume after a restart

Close and reopen T3 Code, then open the same thread. T3 Code calls `session/load`, and TOKN replays the saved transcript so the conversation continues. It holds the last 20 turns or 48 KiB; tool traces are not replayed.

## What to look for

| Check | Expected |
|---|---|
| Provider saves without error | The `initialize` and `session/new` probe passed |
| Mode menu | Default, Accept edits, Plan, Autopilot |
| Plan toggle on | No file changes, only a plan |
| An edit in `default` mode | An approval prompt with an inline diff |
| Thread after a restart | Earlier messages are back |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Provider fails to save | `tokn` is not on T3 Code's PATH | Use the absolute path |
| "no model provider configured" | No key in T3 Code's environment | Add it under Environment overrides |
| Arguments ignored | Several on one row | One flag or value per row |
| A turn with an image fails | TOKN accepts no image input over ACP | Describe the image, or paste the text |
| "cannot load or resume session" | Started with `--no-session-store` | Remove the flag |
| Local model never answers | Ollama or llama-server not running, or wrong model name | `ollama list`, or check `GGUF_SERVER_URL` |

## Related

- [agent-organization](../agent-organization/README.md): `tokn acp` also serves as an Agensh worker.
- [loops-and-ship-ready](../loops-and-ship-ready/README.md): the same agent from TOKN's own REPL.
