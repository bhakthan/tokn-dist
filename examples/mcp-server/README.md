# Example: drive `tokn serve` from an MCP client

This walkthrough starts TOKN as a Model Context Protocol (MCP) server, connects
to it the way a desktop or IDE client does, and calls one harmless tool. It
then shows the same exchange from a short Python script, so you can see every
message.

> *Start TOKN as a tool server on this machine, list the tools it exposes, and
> call `git_status` on a local repository.*

| Feature | What it does here |
|---|---|
| **`tokn serve`** (MCP over stdio) | Runs TOKN as a tool server. The client starts it as a child process and talks over stdin/stdout. |
| **Tool filter** (`--tools`) | Limits which tools the server exposes. Optional, shown in step 3. |
| **Generic MCP config** | One JSON block that works in Claude Desktop, VS Code, Cursor and Copilot CLI. |
| **Stdlib client** (`client.py`) | A short Python script that speaks JSON-RPC and nothing else. |

Everything runs over stdio. The example opens no network port, so there is
nothing to bind and nothing to expose.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Current `serve` flags | `tokn version` |
| `git` | `git_status` runs against a local repository | `git --version` |
| Python 3.10+ (optional) | Runs `client.py` | `python --version` |

**Tier.** Trial or Community both work. The tools in this example fall under
`core:*`, which the Community tier grants. Check with:

```bash
tokn license features
```

If the output does not list `core:*`, start a 14-day trial with `tokn license trial`.

> **What leaves your machine.** Nothing. `tokn serve` in stdio mode talks only
> to the process that started it. No model is called in this example.

## 1. Check the server starts

bash or PowerShell (same command):

```bash
tokn serve --help
```

Expected: a list of modes that begins with `mcp  Model Context Protocol over stdio (default)`.

Do not run `tokn serve` by hand in a terminal. Your MCP client starts it for
you, and a bare run would just sit waiting for input.

## 2. Register TOKN with an MCP client

Most clients accept the same server block. Add this under the `mcpServers`
key of your client's config file.

```json
{
  "mcpServers": {
    "tokn": {
      "command": "tokn",
      "args": ["serve"]
    }
  }
}
```

Where the file lives:

| Client | Config file |
|---|---|
| Claude Desktop | `claude_desktop_config.json` (Settings → Developer → Edit Config) |
| VS Code | `.vscode/mcp.json` in your workspace. Use the `servers` key instead of `mcpServers`. |
| Cursor | `.cursor/mcp.json` in your project |
| GitHub Copilot CLI | `~/.copilot/mcp-config.json` |

For VS Code, the block is:

```json
{
  "servers": {
    "tokn": {
      "type": "stdio",
      "command": "tokn",
      "args": ["serve"]
    }
  }
}
```

Restart the client after saving. It will list `tokn` among its servers.

## 3. (Optional) Expose only some tools

Pass a prefix list to limit what the client sees. `--tools` takes names or
prefixes, separated by commas:

```json
{
  "mcpServers": {
    "tokn": {
      "command": "tokn",
      "args": ["serve", "--tools=git_,read_file"]
    }
  }
}
```

## 4. Run the stdlib client

`client.py` is in this folder. It starts `tokn serve` as a child process,
performs the MCP handshake, lists the tools, and calls `git_status` on a
repository you choose. Run it from the `tokn-dist` root.

Make a throwaway repository to point it at:

macOS / Linux:

```bash
mkdir -p ~/tokn-mcp-demo && git -C ~/tokn-mcp-demo init -q && echo "hello" > ~/tokn-mcp-demo/notes.txt
python examples/mcp-server/client.py ~/tokn-mcp-demo
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-mcp-demo | Out-Null
git -C $HOME\tokn-mcp-demo init -q; Set-Content $HOME\tokn-mcp-demo\notes.txt "hello"
python examples\mcp-server\client.py $HOME\tokn-mcp-demo
```

The script prints each step as it runs (sample output; the counts and branch name will differ):

```text
[client] started: tokn serve
[client] initialize -> protocol 2025-03-26, server "tokn"
[client] tools/list -> N tools (first: ...)
[client] tools/call git_status -> ok
  ## No commits yet on main
  ?? notes.txt
```

## 5. Check the result

- The `initialize` line names a protocol version and a server.
- `tools/list` returns more than zero tools.
- `tools/call git_status` returns text that includes `notes.txt` as untracked (`??`).

## What to look for

- **The handshake comes first.** Clients send `initialize`, then
  `notifications/initialized`, before any other request. `client.py` does this.
- **Tool calls are plain JSON.** `tools/call` takes a `name` and an `arguments`
  object. `git_status` takes no arguments, so `arguments` is `{}`.
- **Failures are JSON-RPC errors.** A tool that cannot run returns an `error`
  object with a message, not a crash.
- **Tiers do not change the protocol.** Community and Trial expose the same
  MCP surface. Only the set of licensed features differs.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `tokn: command not found` | The binary is not on `PATH` | Add the folder that contains `tokn` to `PATH`, or put the full path in `"command"` |
| The client shows `tokn` as failed | The config JSON is invalid, or the client was not restarted | Validate the file with `python -m json.tool <file>` and restart the client |
| `client.py` hangs | The handshake was skipped or the reply was not read | Use the script as written. It reads each reply before sending the next request |
| `git_status` says "not a git repository" | The path is not a repo | Run `git init` in the folder you passed on the command line |
| The client lists no tools | `--tools` filter matches nothing | Remove `--tools` or check the prefix spelling |
| Licence message at start | Trial ended, running Community | Informational. Community runs this example. |
