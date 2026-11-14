# Example: drive `tokn serve` from an MCP client

This walkthrough starts TOKN as a Model Context Protocol (MCP) server, connects
to it the way a desktop or IDE client does, and calls one harmless tool. It
then shows the same steps from a short Python script, which prints a
summary of each reply.

> *Start TOKN as a tool server on this machine, list the tools it exposes, and
> call `git_status` on a local repository.*

| Feature | What it does here |
|---|---|
| **`tokn serve`** (MCP over stdio) | Runs TOKN as a tool server. The client starts it as a child process and talks over stdin/stdout. |
| **Tool filter** (`--tools`) | Limits which tools the server exposes. Optional, shown in step 3. |
| **MCP config** | A common server block, with a separate VS Code form below. |
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

No trial is required for this core-tool example.

> **What leaves your machine.** The MCP exchange uses local stdio, not a
> listening network port. Calling `git_status` does not need a model. This
> is not a guarantee of zero startup traffic: disable registration and
> update checks with `TOKN_NO_REGISTER=1` and `TOKN_NO_UPDATE_CHECK=1` when
> needed. `--mcp-disabled` prevents TOKN from connecting to other discovered
> MCP servers. The calling client can send tool results to its own model.

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
      "args": ["serve", "--mcp-disabled", "--tools=git_status"]
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
      "args": ["serve", "--mcp-disabled", "--tools=git_status"]
    }
  }
}
```

Restart the client after saving. It should list `tokn` among its servers.
Use a full binary path if the client's environment does not include TOKN
on `PATH`. Start it in the repository you intend to inspect; `git_status`
uses the server's working directory.

## 3. (Optional) Expose only some tools

Pass a prefix list to limit what the client sees. `--tools` takes names or
prefixes, separated by commas:

```json
{
  "mcpServers": {
    "tokn": {
      "command": "tokn",
      "args": ["serve", "--mcp-disabled", "--tools=git_,read_file"]
    }
  }
}
```

## 4. Run the stdlib client

`client.py` is in this folder. It starts `tokn serve` as a child process,
performs the MCP handshake, lists the tools, and calls `git_status` on a
repository you choose. Run it from the `tokn-dist` root.

Unlike the restricted config above, this script launches plain `tokn serve`.
It calls only `git_status`, but does not restrict the advertised tools or
disable discovered outbound MCP connections. Review your configuration
before running it. TOKN may also write local session logs; this is not a
zero-artifact probe.

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
- **Check both kinds of failure.** Request errors can be JSON-RPC errors;
  tool execution failures can instead return a tool result marked `isError`.
  The script reports the latter as `tools/call git_status -> error`.
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

## Stateless clients (cold probes)

TOKN also supports clients that probe availability before completing a
handshake. For this walkthrough, keep the normal initialization sequence
used by `client.py`; do not treat successful discovery as proof that a
particular tool is licensed or that its dependencies are installed.

After the Python example exits it stops its child server. Remove the
throwaway repository when you no longer need it. GUI/IDE clients manage
their own server lifetime; disable or remove the server entry there.
