# Example: Use TOKN with Claude Code, Codex, Copilot CLI, Gemini CLI or Antigravity

TOKN works with the major coding CLIs in three ways. Pick the one you need:

| You want… | Use | Section |
|---|---|---|
| Your CLI to call TOKN's tools (domain tools, gates, memory) | `tokn serve` as an MCP server | [1](#1-your-cli-calls-tokns-tools-mcp) |
| TOKN to hand a sub-task to your CLI, under TOKN's trust rules | `/conduct` in the TOKN REPL | [2](#2-tokn-drives-your-cli-conduct) |
| TOKN to respect the rules you already wrote for your CLI | Nothing to configure: TOKN reads them | [3](#3-tokn-reads-your-clis-project-files) |

Requires TOKN v0.3.63 or later (`tokn version`).

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

**Try it:** in your CLI, ask *"List the TOKN tools you have."*

TOKN uses the folder the CLI starts it in as the project root. On Windows, use `tokn.exe` or an absolute path.

## 2. TOKN drives your CLI (`/conduct`)

Inside the TOKN REPL (`tokn`), Conductor Mode hands a sub-task to another CLI and records what it did.

| Peer | What TOKN runs | Before first use |
|---|---|---|
| `claude-code` | `claude -p "<goal>"` | `npm install -g @anthropic-ai/claude-code` |
| `codex` | `codex exec "<goal>"` (read-only sandbox by default) | `npm install -g @openai/codex` |
| `copilot-cli` | `copilot --prompt "<goal>" --add-dir <dir>` | `npm install -g @github/copilot`; set `COPILOT_GITHUB_TOKEN` or `GH_TOKEN` (classic `ghp_` tokens are rejected) |
| `gemini-cli` | `gemini --prompt "<goal>" --approval-mode default` | `npm install -g @google/gemini-cli`; trust the folder in Gemini once |
| `antigravity` | `agy --prompt "<goal>"` | macOS/Linux: `curl -fsSL https://antigravity.google/cli/install.sh \| bash`; Windows: `irm https://antigravity.google/cli/install.ps1 \| iex`; then run `agy` once to sign in |

TOKN never passes an auto-approve flag (`--yolo`, `--dangerously-skip-permissions`, `--allow-all-tools`). If a CLI isn't installed, `/conduct` tells you the install command instead of failing.

```text
/conduct list
```

## 3. TOKN reads your CLI's project files

Open the repo with `tokn`, and these are picked up as skills automatically:

| CLI | Files |
|---|---|
| Claude Code | `CLAUDE.md`, `.claude/settings.json`, `.claude/memory/` |
| Codex | `AGENTS.md`; MCP servers in `.codex/config.toml` and `~/.codex/config.toml` |
| Copilot CLI | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` (honouring `applyTo`), `.github/mcp.json` |
| Gemini CLI | `GEMINI.md`, `.gemini/GEMINI.md`; MCP servers in `.gemini/settings.json` |
| Antigravity | `.agents/rules/*.md`; MCP servers in `.agents/mcp_config.json` |

See what was imported:

```text
/skill rescan
/mcp list
```

MCP servers found in these files still need your trust before TOKN starts them.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The CLI lists no TOKN tools | Run `tokn serve --mcp-disabled` in a terminal; it should wait silently on stdin |
| `unknown flag: --repo-root` | That flag doesn't exist; start the CLI in the project folder |
| `/conduct` says a peer isn't available | Install it with the command shown, then retry |
| Gemini peer exits with an untrusted-folder error | Open the folder in Gemini once and trust it |

## Related

- [t3code](../t3code/README.md): drive TOKN from T3 Code over ACP.
