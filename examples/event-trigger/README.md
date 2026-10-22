# Example: Start a TOKN run from a message

> "When a restock message lands in my queue, I want TOKN to read it, draft a
> summary, and stop. I want to try this on my laptop first, then point it at a
> real broker later."

TOKN can be started by events, not only by you typing a prompt. This walkthrough
uses a local directory queue first, so you can see the whole loop with no cloud
account. Azure Service Bus is an optional last step, where you supply your own
namespace.

| Capability | How this example uses it |
|---|---|
| Local directory queue | `tokn events publish` writes a message file; `peek` and `validate` inspect it |
| Event routing | A YAML config maps a message subject to an agent route |
| Dry run | `tokn events run --dry-run` shows what would dispatch, without dispatching |
| Optional broker | `tokn events run --source servicebus` with your own namespace and Entra ID auth |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | The `events` command tree is in this version line | `tokn version` |
| Licence tier: **community** for the local path | `events` has no licence gate in the source | `tokn license --help` |
| An LLM you have access to (for the live run only) | The live run calls a model; the dry run does not | See [../../SETUP.md](../../SETUP.md) |
| Azure CLI (Service Bus path only) | Signs you in with Entra ID | `az version` |
| Azure Service Bus namespace you own (Service Bus path only) | Your own broker, your own cost | Your Azure portal |

**Tier note.** The local directory queue and the Service Bus source are both
reachable in community, because the source has no licence gate on `events`. You
still need network access and RBAC for Service Bus, and an LLM for any live run.

**What leaves your machine.** The local path writes files under your workspace
only. A live run sends the prompt to the model provider you configure. The
Service Bus path sends messages to a namespace you own.

**Never put a secret in a file.** Connection strings come from environment
variables. Model keys come from environment variables. Nothing here is written to
the YAML.

## 1. Make a workspace

```bash
mkdir -p ~/tokn-demo/restock-events && cd ~/tokn-demo/restock-events
mkdir -p .nospace
```

```powershell
New-Item -ItemType Directory -Force "$HOME\tokn-demo\restock-events\.nospace" | Out-Null
Set-Location "$HOME\tokn-demo\restock-events"
```

## 2. Read the events commands

```bash
tokn events --help
tokn events publish --help
tokn events run --help
```

```powershell
tokn events --help
tokn events publish --help
tokn events run --help
```

Expected, not a recorded run: subcommands `run`, `publish`, `peek`, and
`validate`. `run` accepts `--source dir` or `--source servicebus`. Check the
help text for the exact queue-directory flag before you use it; the steps below
use `--dir` for the local queue.

## 3. Write a routing config

Create `.nospace/eventsource.yaml` by hand. It sends any message whose subject is
`restock` to one route. Strict parsing rejects unknown keys, so a typo fails
loudly.

```bash
cat > .nospace/eventsource.yaml <<'EOF'
max_concurrent: 1
max_delivery_count: 3
turn_timeout: 5m
routes:
  - name: restock-summary
    mode: default
    max_steps: 8
    token_budget: 20000
    filters:
      subject: restock
    prompt_template: "A restock message arrived with subject {{.subject}}. Summarise what it asks for and stop."
EOF
```

```powershell
@'
max_concurrent: 1
max_delivery_count: 3
turn_timeout: 5m
routes:
  - name: restock-summary
    mode: default
    max_steps: 8
    token_budget: 20000
    filters:
      subject: restock
    prompt_template: "A restock message arrived with subject {{.subject}}. Summarise what it asks for and stop."
'@ | Set-Content -Encoding utf8 .nospace\eventsource.yaml
```

What the fields mean, from source:

- `mode` must be a registered agent mode. `default` is always valid.
- `filters` must match every entry to dispatch. The last route must have
  filters, or later routes can never match.
- `token_budget` caps spend for one message. Keep it small while you learn.
- `prompt_template` is rendered with the message's envelope fields, so
  `{{.subject}}` is available.

## 4. Validate the config

```bash
tokn events validate --config .nospace/eventsource.yaml
```

```powershell
tokn events validate --config .nospace\eventsource.yaml
```

Expected, not a recorded run: a clean pass. A bad key or a route with no
filters is reported with the line that failed.

## 5. Publish a synthetic message to the local queue

Use invented data. The message body here is plain text, with no real item
codes or locations.

```bash
tokn events publish --dir .nospace/eventsource/queue --subject restock --body "Please restock 12 sample tubes and 4 gloves before Friday."
```

```powershell
tokn events publish --dir .nospace\eventsource\queue --subject restock --body "Please restock 12 sample tubes and 4 gloves before Friday."
```

Expected, not a recorded run: a message id is printed. Under the queue folder you
will find a `pending/` directory holding one JSON file for that message. The
layout also has `locked/`, `dead/`, and `tmp/` folders, created as needed.

## 6. Peek at the queue

```bash
tokn events peek --dir .nospace/eventsource/queue
```

```powershell
tokn events peek --dir .nospace\eventsource\queue
```

Expected, not a recorded run: one pending message, with its subject `restock`.
`peek` does not lock or consume the message.

## 7. Dry-run the consumer

The dry run shows which route a message would take, and skips the model call.

```bash
tokn events run --config .nospace/eventsource.yaml --source dir --dir .nospace/eventsource/queue --dry-run
```

```powershell
tokn events run --config .nospace\eventsource.yaml --source dir --dir .nospace\eventsource\queue --dry-run
```

Expected, not a recorded run: the message matches the `restock-summary` route,
and nothing is dispatched to a model. The message stays in `pending/` because a
dry run does not complete it.

## 8. Live run on the local queue (uses your model)

Only do this once you have an LLM configured. Set placeholders in your shell.
Replace them with your own values. See [../../SETUP.md](../../SETUP.md).

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
tokn events run --config .nospace/eventsource.yaml --source dir --dir .nospace/eventsource/queue
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<a model you have access to>"
$env:ANTHROPIC_API_KEY = "<your key>"
tokn events run --config .nospace\eventsource.yaml --source dir --dir .nospace\eventsource\queue
```

Expected, not a recorded run: the consumer locks the message, runs the route,
and completes it. The message moves out of `pending/`. The run prints a summary
of received, completed, and dead-lettered counts. A message that fails
`max_delivery_count` times is moved to `dead/` with a reason file.

Clear the placeholder values from your shell when you are done.

## 9. Optional: Azure Service Bus with your own namespace

Only do this if you have a namespace you own. The local path above is complete
without it.

### 9a. Preflight

| Tool | Why | Check | Install (Windows) | Install (macOS) | Install (Linux) |
|---|---|---|---|---|---|
| Azure CLI | Signs you in with Entra ID | `az version` | `winget install -e --id Microsoft.AzureCLI` | `brew install azure-cli` | `curl -sL https://aka.ms/InstallAzureCLIDeb \| sudo bash` |
| Network to the broker | Messages travel over AMQP/TLS | `az servicebus namespace show --name <your-namespace> --resource-group <your-resource-group>` | Same | Same | Same |

If `az` is not found after install, open a new terminal.

### 9b. Sign in and grant yourself a role

Entra ID auth is preferred. It needs no connection string. Your identity needs a
Service Bus data role on the namespace. Ask your admin, or grant it yourself if
you own the namespace.

- To receive: **Azure Service Bus Data Receiver**
- To publish: **Azure Service Bus Data Sender**

```bash
az login
az account show --query name -o tsv
```

```powershell
az login
az account show --query name -o tsv
```

Expected, not a recorded run: your subscription name prints. Nothing is written
to the YAML.

### 9c. Point the config at your namespace

The source comes from the command line, not the YAML, so the config stays
unchanged. Keep the namespace as a fully qualified host.

```bash
tokn events run --source servicebus --namespace <your-namespace>.servicebus.windows.net --queue <your-queue> --config .nospace/eventsource.yaml
```

```powershell
tokn events run --source servicebus --namespace <your-namespace>.servicebus.windows.net --queue <your-queue> --config .nospace\eventsource.yaml
```

Expected, not a recorded run: the consumer connects with your Entra ID
identity and starts receiving. Live broker behaviour is not covered by the
released tests, so treat the first run as a trial. Keep `--dry-run` off for
Service Bus: the source refuses it.

### 9d. Connection string instead (key-based, use only if you must)

Entra ID is the default. If you cannot use it, pass a connection string from an
environment variable. Never paste the value into a file or a command you share.

```bash
export YOUR_SB_CONNECTION_STRING=<your connection string>
tokn events run --source servicebus --connection-string "$YOUR_SB_CONNECTION_STRING" --queue <your-queue> --config .nospace/eventsource.yaml
unset YOUR_SB_CONNECTION_STRING
```

```powershell
$env:YOUR_SB_CONNECTION_STRING = "<your connection string>"
tokn events run --source servicebus --connection-string $env:YOUR_SB_CONNECTION_STRING --queue <your-queue> --config .nospace\eventsource.yaml
Remove-Item Env:YOUR_SB_CONNECTION_STRING
```

Set `--namespace` or `--connection-string`, not both. The source rejects both
at once.

## What to look for

- `validate` passes before any run, and the config names the failing field when it does not.
- `publish` writes one JSON file under `pending/`. `peek` shows it without consuming it.
- A dry run matches the route and dispatches nothing.
- A live run moves the message out of `pending/`.
- A message that keeps failing lands in `dead/`, with a reason file beside it.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `validate` says unknown field | A typo in the YAML (strict parsing) | Fix the key name shown in the error |
| Route never matches | Subject filter does not equal the published subject | Publish with `--subject restock`, or match your filter |
| `unsupported agent mode` | Mode name not registered | Use `mode: default` |
| Dry run refused for servicebus | Dry run is local-only | Drop `--dry-run` for Service Bus |
| `az: command not found` | Azure CLI not installed | Use the install line in step 9a, then open a new terminal |
| Auth or 403 on Service Bus | Missing data role | Grant Data Receiver (or Sender) on the namespace |
| Message in `dead/` | Failed `max_delivery_count` times | Read the reason file, fix the route or prompt, then republish |
| Model error on live run | Placeholder not replaced | Set the three environment variables in step 8 |

## Related

- [../../SETUP.md](../../SETUP.md): install, model configuration, and licence activation
- [../domain-plugin/README.md](../domain-plugin/README.md): a plugin you author yourself
