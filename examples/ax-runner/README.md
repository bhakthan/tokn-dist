# Example: AX runner — run TOKN inside Google's AX agent control plane

> "AX can schedule and sandbox our agents. Who counts what each task spends,
> and who stops it?"

[AX](https://github.com/google/ax) is Google's open, declarative control plane
for agent workloads. It has four resource kinds in `ax.io/v1alpha1`: **Task**,
**Workspace**, **Gateway** and **Model**. AX does not run the agent itself.
It starts a *runner* as PID 1 in every task container, and the runner does the
work inside the sandbox. `tokn ax` makes TOKN one of those runners:

| Step | Command | What it does |
|---|---|---|
| Understand | `explain` | What the integration does, and what it does not |
| Check | `preflight` | Which tools an AX workflow needs, with install commands |
| Generate | `gen` | Task, Workspace, Gateway and Model manifests for a TOKN run |
| Package | `dockerfile` | A Dockerfile that turns TOKN into a runner image |
| Run | `runner` | The runner contract: health, metadata, workspace setup, the task command |
| Account | `report-usage` | Report one model call's tokens; the runner prices them and checks a ceiling |

AX declares a place for token usage (`TaskStatus.usage`) but nothing in AX
fills it, and AX removed its budget settings. TOKN counts its own spend and
enforces a ceiling inside the sandbox. It cannot write the number back into
AX, because AX has no channel for that. Step 1 shows exactly where the line
falls.

**AX is pre-stable.** Its `v1alpha1` API may change without notice. TOKN
speaks the wire format directly and pins it with a test against AX's own
example manifests.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.68 or later, on your `PATH` | Ships `tokn ax`; the local task command calls `tokn` | `tokn ax --help` |
| `git` | The runner clones `spec.git` repositories into the workspace | `git --version` |
| `curl` (bash) or PowerShell | Probe the runner's endpoints in steps 5–7 | `curl --version` |
| Docker (step 4, optional) | Build the runner image | `docker version` |
| `ax`, `kubectl`, a cluster (step 8, optional) | Deploy to a real AX control plane | `tokn ax preflight` |

Steps 1–7 need no model, no API key and no cluster. Every command ran on the
free Community tier; none was gated.

TOKN prints a trial or license banner on stderr. It is harmless and is left
out of the output below.

### What leaves your machine

Nothing in steps 1–4. Step 5 clones one small public repository
(`github.com/octocat/Hello-World`) from GitHub. The runner serves HTTP on the
port you choose, and `report-usage` only talks to that local runner. No model
is called anywhere in this example. Steps 4 and 8, if you run them, pull a
base image and talk to your registry and cluster.

## 1. Explain: what TOKN does inside AX, and what it does not

```bash
tokn ax explain
```

Expected (shortened):

```text
AX orchestrates. TOKN is what runs inside.

What TOKN does
--------------
  * Implements AX's task-runner contract, so a TOKN image is a drop-in
    spec.image for any AX Task: ...
  * Generates Task, Workspace, Gateway and Model manifests from a TOKN run,
    validated against AX's own rules before they are written.
  * Accounts for its own token usage and cost, and enforces a spend ceiling
    inside the sandbox.
...
What TOKN does NOT do
---------------------
  * It does not serve Agent Substrate guest services. spec.debug turns those on
    in AX's default runner and is what 'ax ssh' attaches to. ...
  * It does not resolve MCP or skill registry queries. ...
  * It does not execute a WorkspaceRef goal. ...

The usage gap, precisely
------------------------
AX declares TaskStatus.usage (prompt and completion tokens) and
TaskStatus.pendingApproval. Nothing in AX writes either. TaskSpec.policies,
which carried budget and approval configuration, is reserved and removed. ...

  CAN   account for its own usage and cost, and serve it at the sandbox
        boundary on /metadata/v1alpha1/tokn/usage, readable by 'ax ssh' and
        any in-cluster client.
  CAN   enforce a spend ceiling locally, which is what TaskSpec.policies would
        have done; enforcement inside the sandbox needs no control plane.
  CANNOT set TaskStatus.usage in the control plane. No channel exists for a
        runner to report one. When AX adds one, the number is already computed
        and waiting.

An unpriced model reports costKnown:false rather than a cost of zero, and a
ceiling is never enforced against a cost that is not known.
```

The last paragraph matters later: a ceiling only works when the runner knows
the model's price (step 6).

## 2. Preflight: which tools are missing?

```bash
tokn ax preflight
```

Expected (on a Windows machine without `ax` and `ko`, with Docker Desktop
stopped; exit status 1):

```text
TOOL     STATUS                     NEEDED FOR
git      found                      cloning spec.git repositories during workspace preparation
docker   found, daemon NOT running  building and pushing a TOKN runner image
ax       MISSING                    applying manifests and inspecting tasks
kubectl  found                      operating the cluster AX's control plane runs on
ko       MISSING                    deploying the AX control plane itself (make deploy)

The docker CLI is installed but cannot reach a daemon. Start Docker Desktop (Windows/macOS) or 'sudo systemctl start docker' (Linux), then re-run.

2 missing. Install on windows:

  ax         go install github.com/google/ax/cmd/ax@latest
  ko         go install github.com/google/ko@latest
...
```

It lists every tool at once and installs nothing. Only `git` and `docker`
matter for building a runner image. The rest are for running an AX cluster.
When any tool is missing, `preflight` exits 1 and prints
`Error: 2 AX workflow dependencies missing` to stderr, so a script can stop
there. For Docker it also checks the daemon, not just the `PATH`.

## 3. Gen: write the manifests for a TOKN task

```bash
tokn ax gen --name fix-flake --image ghcr.io/me/tokn-runner:latest \
  --repo https://github.com/me/app.git --branch main \
  --egress api.anthropic.com --egress github.com:443 \
  --provider anthropic --model claude-opus-5 \
  --secret-name llm-keys --secret-key ANTHROPIC_API_KEY \
  --budget-usd 5 -o fix-flake.yaml
```

PowerShell:

```powershell
tokn ax gen --name fix-flake --image ghcr.io/me/tokn-runner:latest `
  --repo https://github.com/me/app.git --branch main `
  --egress api.anthropic.com --egress github.com:443 `
  --provider anthropic --model claude-opus-5 `
  --secret-name llm-keys --secret-key ANTHROPIC_API_KEY `
  --budget-usd 5 -o fix-flake.yaml
```

It writes four documents in apply order. The result is checked in here as
[fix-flake.yaml](fix-flake.yaml). The Task, at the end:

```yaml
apiVersion: ax.io/v1alpha1
kind: Task
metadata:
    name: fix-flake
    atespace: default
spec:
    image: ghcr.io/me/tokn-runner:latest
    env:
        - name: TOKN_AX_BUDGET_USD
          value: "5"
        - name: TOKN_AX_PROVIDER
          value: anthropic
        - name: TOKN_AX_MODEL
          value: claude-opus-5
    workspaces:
        - name: fix-flake-workspace
          path: /workspace
    gateway:
        name: fix-flake-gateway
```

| Document | Key fields | From flag |
|---|---|---|
| Workspace `fix-flake-workspace` | `spec.git[]`: `repo`, `branch` | `--repo`, `--branch`, `--depth`, `--skills-path` |
| Gateway `fix-flake-gateway` | `spec.egress.allowlist.hosts[]`; listeners on 8494 (gRPC) and 8080 (HTTP) | `--egress` (port defaults to 443) |
| Model `fix-flake-model` | `provider`, `model`, `secretKey.name` / `.key` | `--provider`, `--model`, `--secret-name`, `--secret-key` |
| Task `fix-flake` | `image`, `env` (`TOKN_AX_BUDGET_USD`, `TOKN_AX_PROVIDER`, `TOKN_AX_MODEL`), workspace mount at `/workspace`, gateway | `--image`, `--budget-usd`, `--provider`, `--model`, `--command`, `--cpu`, `--memory`, `--debug` |

Notes:

- **`atespace` is not a typo in TOKN.** AX itself spells its namespace field
  `atespace` in its API and example manifests. TOKN matches what AX parses.
  You still pass `--namespace` to `gen`.
- `--provider` and `--model` also go into the Task's `env`, so the runner
  can price usage and the ceiling can trip (step 6). Without them there is no
  Model document and no price. Without `--command` the Task has no `command`.
- `--image` is required, and there is no published TOKN runner image. Without
  it, `gen` exits 1 and tells you to build one (step 4).
- Bad input fails before anything is written. For example
  `--egress "bad host:99999"` exits 1 with
  `invalid egress host "bad host:99999": invalid port "99999"`. A name that is
  not a DNS-1123 label, such as `--name Bad_Name`, is refused the same way.

Apply the file with `ax apply -f fix-flake.yaml` (step 8, not verified here).

## 4. Dockerfile: package TOKN as a runner image (optional)

AX ignores an image's entrypoint. It always runs
`/usr/local/bin/ax-task-runner`. The generated Dockerfile installs TOKN and
makes that path a small shell script that runs `tokn ax runner`.

An AX sandbox is always Linux, so the image needs the Linux binary. Download
`tokn_linux_amd64` from the
[latest release](https://github.com/bhakthan/tokn-dist/releases/latest) into
an empty folder (`tokn ax dockerfile --help` shows the same steps), then:

```bash
gh release download --repo bhakthan/tokn-dist --pattern tokn_linux_amd64
tokn ax dockerfile --binary tokn_linux_amd64 -o Dockerfile.ax
```

Expected (`Dockerfile.ax`, shortened):

```dockerfile
FROM debian:stable-slim
...
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY tokn_linux_amd64 /usr/local/bin/tokn
RUN chmod +x /usr/local/bin/tokn

# The shim AX actually executes.
RUN printf '#!/bin/sh\nexec /usr/local/bin/tokn ax runner "$@"\n' > /usr/local/bin/ax-task-runner \
    && chmod +x /usr/local/bin/ax-task-runner

# /workspace is the durable volume AX mounts and snapshots on suspend.
WORKDIR /workspace

EXPOSE 80
ENTRYPOINT ["/usr/local/bin/ax-task-runner"]
```

`--base` changes the base image. `--with-git=false` leaves git out; the
runner will then refuse to clone `spec.git` repositories.

Build it with:

```bash
docker build -f Dockerfile.ax -t ghcr.io/me/tokn-runner:latest .
```

**This build was not run for this example** (no Docker daemon was running).
Check `docker version` first: it must print a `Server:` section. If it shows
`failed to connect to the docker API`, start Docker Desktop (Windows, macOS)
or `sudo systemctl start docker` (Linux). To install Docker, see
<https://docs.docker.com/get-docker/>.

## 5. Run the runner locally

`tokn ax runner` is what AX starts in the container. With `--task-file` and
`--workspace-file` it runs the same lifecycle from local files, so you can
test it without a cluster.

This folder has a local Task and Workspace:

| File | What it is |
|---|---|
| [workspace-local.yaml](workspace-local.yaml) | Clones `octocat/Hello-World` (depth 1) |
| [task-local.sh.yaml](task-local.sh.yaml) | bash/macOS/Linux: a `sh -c` loop that calls `tokn ax report-usage` |
| [task-local.ps1.yaml](task-local.ps1.yaml) | Windows: the same loop in PowerShell |

The task command stands in for an agent. Each loop reports one model call of
20,000 prompt and 2,000 completion tokens, and stops when `report-usage`
fails. The Task mounts the workspace at `./workspace`, not `/workspace`, so the
test writes under the current folder.

From a clone of this repository, copy the files to an empty folder and start
the runner in the background:

bash:

```bash
mkdir -p ~/tokn-ax && cp examples/ax-runner/*.yaml ~/tokn-ax/ && cd ~/tokn-ax
tokn ax runner --task-file task-local.sh.yaml --workspace-file workspace-local.yaml \
  --port 8080 --marker-dir .ax-markers \
  --provider anthropic --model claude-opus-5 --budget-usd 0.5 \
  > runner.out 2> runner.err &
RUNNER_PID=$!
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\tokn-ax" | Out-Null
Copy-Item examples\ax-runner\*.yaml "$HOME\tokn-ax"
Set-Location "$HOME\tokn-ax"
$runner = Start-Process tokn -ArgumentList 'ax','runner','--task-file','task-local.ps1.yaml','--workspace-file','workspace-local.yaml','--port','8080','--marker-dir','.ax-markers','--provider','anthropic','--model','claude-opus-5','--budget-usd','0.5' -RedirectStandardOutput runner.out -RedirectStandardError runner.err -PassThru -NoNewWindow
```

| Flag | Why here |
|---|---|
| `--port 8080` | The default is 80, which AX probes. Locally, use a free high port. |
| `--marker-dir .ax-markers` | The default is `/ax`. Markers record that a workspace is already prepared. |
| `--provider`, `--model` | Used to price reported tokens. Without them, cost is unknown. |
| `--budget-usd 0.5` | The local spend ceiling. 0 disables it. |

Wait a few seconds, then probe it (`curl.exe` in Windows PowerShell):

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s http://127.0.0.1:8080/readyz
curl -s http://127.0.0.1:8080/metadata/v1alpha1/ax/workspaces
```

Expected:

```text
ok
ready
apiVersion: ax.io/v1alpha1
kind: Workspace
metadata:
    name: spend-demo-workspace
spec:
    git:
        - name: hello
          repo: https://github.com/octocat/Hello-World.git
          depth: 1
```

`/metadata/v1alpha1/ax/task` returns the Task the same way. The runner log
(`runner.err`) shows the lifecycle:

```text
warning: AX paths are Linux paths; on windows, absolute paths such as the workspace path and marker dir resolve to the drive root (marker dir: …\tokn-ax\.ax-markers). For local tests, point the Workspace path and --marker-dir at a scratch folder.
level=INFO msg="AX workspace prepared" path=./workspace alreadySetup=false reposCloned=1 warnings=0
level=INFO msg="AX task command started" pid=6028 dir=./workspace
Error: ax: spend ceiling exceeded
level=INFO msg="AX task command exited" pid=6028 exitCode=0 error=<nil>
```

The first line appears only outside Linux. It is a reminder, not an
error: the fixtures already use a relative workspace path and a local
`--marker-dir`.

`./workspace` now holds `Hello-World/` and `.agents/` (the default skills
folder). The runner keeps serving after the command exits, so the sandbox
stays inspectable.

## 6. Report usage and hit the ceiling

The task command's output is in `runner.out`. Each `report-usage` call prints
the running total (shortened):

```text
  "calls": 1,
  "estimatedCostUSD": 0.15,
  "ceilingExceeded": false,
  "calls": 2,
  "estimatedCostUSD": 0.3,
  "ceilingExceeded": false,
  "calls": 3,
  "estimatedCostUSD": 0.45,
  "ceilingExceeded": false,
  "calls": 4,
  "estimatedCostUSD": 0.6,
  "ceilingExceeded": true,
ceiling reached on call 4
```

Read the total from outside, as `ax ssh` or an in-cluster client would:

bash:

```bash
curl -s http://127.0.0.1:8080/metadata/v1alpha1/tokn/usage
```

PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/metadata/v1alpha1/tokn/usage
```

Expected (bash):

```json
{"provider":"anthropic","model":"claude-opus-5","promptTokens":80000,"completionTokens":8000,"cacheReadTokens":0,"calls":4,"estimatedCostUSD":0.6,"costKnown":true,"ceilingUSD":0.5,"ceilingExceeded":true,"axUsage":{"promptTokens":80000,"completionTokens":8000},"reportedToControlPlane":false,"note":"computed locally; AX has no channel to receive it"}
```

How to read it:

- `axUsage` has the shape of AX's `TaskStatus.usage`. It is ready, but
  `reportedToControlPlane` is `false`: AX has no way to receive it.
- The ceiling is checked **after** each call is recorded. Call 4 pushed spend
  from $0.45 to $0.60, then `report-usage` exited non-zero. Spend can pass the
  ceiling by up to one call.
- The runner does not kill the task. The task command must stop when
  `report-usage` fails, as the loop here does.

Only the task's own process can report. The runner hands it a random bearer
token in `TOKN_AX_USAGE_TOKEN` and its URL in `AX_METADATA_URL`. From
outside:

```bash
tokn ax report-usage --url http://127.0.0.1:8080 --prompt 100 --completion 10
tokn ax report-usage --url http://127.0.0.1:8080 --token guess --prompt 100 --completion 10
```

Expected, each exiting 1:

```text
Error: report AX usage: usage token is required
...
Error: report AX usage: metadata server returned 401:
```

### An unpriced model never trips the ceiling

Restart the runner with a model TOKN has no price for (for example
`--model my-private-model`). The same loop runs all 10 calls:

```json
{"provider":"anthropic","model":"my-private-model","promptTokens":200000,"completionTokens":20000,"cacheReadTokens":0,"calls":10,"estimatedCostUSD":0,"costKnown":false,"ceilingExceeded":false,...,"note":"unpriced model; estimated cost is unknown; computed locally; AX has no channel to receive it"}
```

The runner warns once on stderr and tells you to add a price to
`.nospace/pricing.json` (or `~/.nospace/pricing.json`). Leaving out
`--provider` and `--model` has the same effect; then the runner warns at start
that the ceiling is set but cannot trip.

## 7. Resume: workspace setup runs once

AX snapshots `/workspace` on suspend and restores it into a fresh container.
Stop the runner and start it again with the same command and marker folder:

bash:

```bash
kill $RUNNER_PID
# then run the same `tokn ax runner ... &` command from step 5 again
```

PowerShell:

```powershell
Stop-Process -Id $runner.Id
# then run the same Start-Process command from step 5 again
```

Expected in `runner.err`:

```text
level=INFO msg="AX workspace prepared" path=./workspace alreadySetup=true reposCloned=0 warnings=0
```

The workspace is not cloned again, so an agent's work in it survives. The
task command does run again. The spend total starts again from zero: it is
held in the runner process, so it covers one runner process, not the whole
life of the Task. `tokn ax runner --help` documents this limit.

## 8. Clean up

bash:

```bash
kill $RUNNER_PID
cd ~ && rm -rf ~/tokn-ax
```

PowerShell:

```powershell
Stop-Process -Id $runner.Id
Set-Location $HOME; Remove-Item -Recurse -Force "$HOME\tokn-ax"
```

## 9. Optional: deploy to an AX cluster (not verified)

**Not run for this example.** The outline, following
[AX's README](https://github.com/google/ax):

1. Run `tokn ax preflight` and install what it lists (`ax`, `kubectl`, and
   `ko` if you deploy the AX control plane yourself).
2. Build and push the runner image from step 4.
3. Create the Kubernetes secret named in `--secret-name` with your model key.
4. Generate manifests with `tokn ax gen` (step 3), using your image, and apply
   them with `ax apply -f fix-flake.yaml`.

Two things to know before you rely on the ceiling in a cluster:

- AX starts `ax-task-runner` with no flags. The runner then reads the ceiling,
  provider and model from its environment, and falls back to the Task's
  `spec.env` (`TOKN_AX_BUDGET_USD`, `TOKN_AX_PROVIDER`, `TOKN_AX_MODEL`),
  which `gen` writes when you pass `--budget-usd`, `--provider` and `--model`.
  In a local `--task-file` run with no flags, those `spec.env` values set the
  ceiling and it tripped on call 4. In a cluster this was not verified.
- Without a provider and model the cost is unknown and the ceiling never trips;
  the runner warns about this at start.

## What to look for

- `tokn ax explain` draws the line clearly: TOKN computes and serves usage,
  and enforces a ceiling in the sandbox; it cannot write `TaskStatus.usage`.
- `/metadata/v1alpha1/tokn/usage` returns `reportedToControlPlane: false`
  every time. That is the gap, stated in the data.
- `costKnown: false` means "no price", not "free". A ceiling is never
  enforced against an unknown cost.
- `alreadySetup=true` on restart: a restored workspace is not cloned over.
- Only the task process, holding the runner's token, can add to the spend.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Nothing answers on port 8080 | The default port is 80. Pass `--port 8080`, and wait for `ready` on `/readyz`; cloning can take a few seconds. |
| A `C:\workspace` or `/workspace` folder appears | The Task mounts `/workspace`. For local tests, use a relative `path:` such as `./workspace`, as the fixtures do. |
| `report-usage` says `usage token is required` | It only works from inside the task command, which gets `TOKN_AX_USAGE_TOKEN` from the runner. |
| `report-usage` says `metadata server returned 401` | The token is wrong. Do not pass `--token` inside a task; the default comes from the environment. |
| `ceilingExceeded` stays `false` and `costKnown` is `false` | The model has no price. Pass `--provider` and `--model`, or add a price to `.nospace/pricing.json`. |
| No `ceilingUSD` in the usage JSON | No ceiling is set. Pass `--budget-usd`, or set `TOKN_AX_BUDGET_USD` in the runner's environment or the Task's `spec.env`. |
| `gen` says `invalid name: "Bad_Name" must be lowercase letters, digits and '-' …` | Use a DNS-1123 name, such as `fix-flake`. |
| The task command cannot find `tokn` | Put `tokn` on your `PATH`; the local task command calls it by name. |
| `gen` says `missing required flag(s): --image` | Build a runner image first (step 4). There is no published TOKN runner image. |
| Manifests say `atespace:` | Expected. That is AX's own spelling of its namespace field. |
| `preflight` says `docker found, daemon NOT running` | Start Docker Desktop (Windows, macOS) or `sudo systemctl start docker` (Linux). |
