# Example: Use TOKN with Claude Code, Codex, Copilot CLI, Gemini CLI or Antigravity

TOKN works with the major coding CLIs in three ways. Pick the one you need:

| You want… | Use | Section |
|---|---|---|
| Your CLI to call TOKN's tools (domain tools, gates, memory) | `tokn serve` as an MCP server | [1](#1-your-cli-calls-tokns-tools-mcp) |
| TOKN to hand a sub-task to your CLI, under TOKN's trust rules | `/conduct` in the TOKN REPL | [2](#2-tokn-drives-your-cli-conduct) |
| TOKN to respect the rules you already wrote for your CLI | Nothing to configure: TOKN reads them | [3](#3-tokn-reads-your-clis-project-files) |

Requires TOKN v0.3.63 or later (`tokn version`).

## Before you start

- Install TOKN and **one** peer CLI; you do not need all five.
- Check the peer executable with `claude --version`, `codex --version`,
  `copilot --version`, `gemini --version` or `agy --version`.
- Complete the peer's own sign-in/setup and confirm it works on a disposable
  repo before delegating from TOKN. Model access and billing belong to the
  peer/provider you selected.
- npm-based installation below needs Node.js and npm first
  (`node --version`, `npm --version`). Install the current Node.js LTS from
  [nodejs.org](https://nodejs.org/en/download) if missing. Antigravity has
  its own installer instead.
- Install only from each publisher's official instructions. Pin an exact
  released version for npm packages and verify the package publisher and
  registry integrity metadata. For Antigravity, use its official release
  instructions and verify the downloaded version's signature or checksum
  before running it; do not pipe a mutable installer script directly to a
  shell.

MCP tool results can be sent to the calling CLI's model. `/conduct` sends the
task and accessible project context to the selected peer, and can write
local run records and repository changes. Use synthetic data for this
walkthrough; a local MCP connection does not make the peer's model local.

## 1. Your CLI calls TOKN's tools (MCP)

Register TOKN once. `--mcp-disabled` stops TOKN from starting the other MCP servers it finds in the same config files, itself included.

| CLI | Command |
|---|---|
| Claude Code | `claude mcp add --transport stdio tokn -- tokn serve --mcp-disabled` |
| Codex CLI | `codex mcp add tokn -- tokn serve --mcp-disabled` |
| Copilot CLI | `copilot mcp add tokn -- tokn serve --mcp-disabled` |
| Gemini CLI | `gemini mcp add -s user tokn tokn serve -- --mcp-disabled` |
| Antigravity | Add to `~/.gemini/config/mcp_config.json` (below), or use `/mcp` in the Antigravity CLI |

Antigravity or any JSON-based config:

```json
{
  "mcpServers": {
    "tokn": { "command": "tokn", "args": ["serve", "--mcp-disabled"] }
  }
}
```

Codex `~/.codex/config.toml` by hand:

```toml
[mcp_servers.tokn]
command = "tokn"
args = ["serve", "--mcp-disabled"]
```

Expose only some tools with `--tools`, which takes names or prefixes:

```bash
tokn serve --mcp-disabled --tools=bp_,legal_
```

**Try it:** in your CLI, ask *"List the TOKN tools you have."* Expected:
TOKN appears as an MCP server and exposes the tools allowed by your
configuration and licence. Discovery alone does not run a domain task or
prove that every tool's optional dependencies are installed.

For a minimal first check, expose only `git_status` instead of all tools.
See the [MCP walkthrough](../mcp-server/README.md) for the restricted config
and a read-only task.

TOKN uses the folder the CLI starts it in as the project root. On Windows, use `tokn.exe` or an absolute path.

## 2. TOKN drives your CLI (`/conduct`)

Inside the TOKN REPL (`tokn`), Conductor Mode hands a sub-task to another CLI and records what it did.

| Peer | What TOKN runs | Before first use |
|---|---|---|
| `claude-code` | `claude -p "<goal>"` | `npm install -g @anthropic-ai/claude-code@YOUR_VERSION` |
| `codex` | `codex exec "<goal>"` (read-only sandbox by default) | `npm install -g @openai/codex@YOUR_VERSION` |
| `copilot-cli` | `copilot --prompt "<goal>" --add-dir <dir>` | `npm install -g @github/copilot@YOUR_VERSION`; set `COPILOT_GITHUB_TOKEN` or `GH_TOKEN` (classic `ghp_` tokens are rejected) |
| `gemini-cli` | `gemini --prompt "<goal>" --approval-mode default` | `npm install -g @google/gemini-cli@YOUR_VERSION`; trust the folder in Gemini once |
| `antigravity` | `agy --prompt "<goal>"` | Follow the publisher's versioned install instructions; verify its release signature/checksum before running, then sign in |

TOKN never passes an auto-approve flag (`--yolo`, `--dangerously-skip-permissions`, `--allow-all-tools`). If a CLI isn't installed, `/conduct` tells you the install command instead of failing.

```text
/conduct list
/conduct route Explain the files in this repository without editing them
/conduct trust <available-peer> Explain the files in this repository without editing them
```

Replace `<available-peer>` with a name reported by `list`, such as `codex`.
`route` previews a recommendation without invoking a peer; `trust` invokes
the named peer and reports a trust verdict. A verdict is not a sandbox,
proof of task correctness or a promise to undo peer side effects. Inspect
the working tree and relevant tests yourself. `/conduct invoke` skips the
trust verdict and is not the path demonstrated here.

## 3. TOKN reads your CLI's project files

Open the repo with `tokn`. TOKN can import project guidance, skills and MCP
configuration from these locations; they are not all treated as executable
skills:

| CLI | Files |
|---|---|
| Claude Code | `CLAUDE.md`, `.claude/settings.json`, `.claude/memory/` |
| Codex | `AGENTS.md`; MCP servers in `.codex/config.toml` and `~/.codex/config.toml` |
| Copilot CLI | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` (honouring `applyTo`), `.github/mcp.json` |
| Gemini CLI | `GEMINI.md`, `.gemini/GEMINI.md`; MCP servers in `.gemini/settings.json` |
| Antigravity | `.agents/rules/*.md`; MCP servers in `.agents/mcp_config.json` |

In the TOKN REPL, refresh imported skills and inspect skills and MCP connections:

```text
/reload-plugins
/skill list
/mcp list
```

MCP servers found in these files still need your trust before TOKN starts them.
Read project instructions and review server commands before granting that
trust, particularly when opening an unfamiliar repository.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The CLI lists no TOKN tools | Check `tokn serve --help`, the binary path, the client's server logs and any `--tools` filter; a manual stdio server waits for input |
| `unknown flag: --repo-root` | That flag doesn't exist; start the CLI in the project folder |
| `/conduct` says a peer isn't available | Install it with the command shown, then retry |
| Gemini peer exits with an untrusted-folder error | Open the folder in Gemini once and trust it |

To undo registration, remove the TOKN MCP entry through your client's
server manager or configuration file. This does not undo repository edits
made by an earlier delegated task.

## Related

- [t3code](../t3code/README.md): drive TOKN from T3 Code over ACP.
