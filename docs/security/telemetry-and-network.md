# Network activity and data boundaries

**A local model is one data boundary, not a blanket no-network setting.**
Review the model, tools and startup behaviour separately.

```text
                         +--> chosen model provider
Your input -> TOKN ------+--> enabled tools and external services
                         +--> local files and runtime state

Separate startup activity: install registration and update checks
Separate explicit action: feedback submission
```

## Common connections

| Activity | When it occurs | What to consider |
|---|---|---|
| Model inference | Agent turns or explicit model-backed commands | Prompts, conversation context, file excerpts and tool results may be sent to the configured endpoint |
| Install registration | Startup/trial registration when enabled | Anonymous installation and platform metadata, not your source files or prompts |
| Update checks and downloads | Startup checks or `tokn update` | Release metadata and artifacts from the public GitHub channel |
| Feedback | You invoke `tokn feedback` or `/feedback` | Your message is transmitted; review it for sensitive content |
| MCP connections | Enabled integration startup or tool use | A local subprocess or remote server can receive tool inputs |
| Search, browsers and specialist services | You enable or invoke the relevant workflow | Requests go to those services; check the walkthrough and provider policy |
| Model/package preparation | You explicitly download models or install dependencies | Requires a connected preparation step; not an offline inference operation |

This is a user-facing overview, not an exhaustive packet-level inventory.
External tools can make their own connections.
Do not assume automatic redaction makes an unapproved input safe to send.

## Disable unrelated startup activity

**PowerShell**
```powershell
$env:TOKN_NO_REGISTER = "1"
$env:TOKN_NO_UPDATE_CHECK = "1"
```

**Bash**
```bash
export TOKN_NO_REGISTER=1
export TOKN_NO_UPDATE_CHECK=1
```

`TOKN_NO_TELEMETRY=1` or `DO_NOT_TRACK=1` also opts out of anonymous
registration. **None of these is a global network kill switch.**
They do not cancel a hosted model request, an explicit update or feedback you
choose to submit. Telemetry opt-out does not make an explicit feedback message
private or local-only.

Feedback may queue locally when delivery is unavailable. Do not use it to
submit secrets, and do not assume a queued message has already arrived.

## Prepare for offline work

Stage a local runtime, suitable weights and all workflow dependencies while
connected. Select local endpoints, disable unrelated startup checks and use
the command's documented air-gap flag. Flag spelling and scope vary by command;
check its `--help`.

For a simple agent exercise, `--mcp-disabled` avoids outbound MCP connections.
It does not disable other network-capable tools or isolate subprocesses.
Use host or container network policy when no egress must be enforced, and
observe the actual process traffic in your environment.

See [model setup](../../SETUP.md), [local prediction](../../TABULAR.md) and
[the threat model](threat-model.md).
