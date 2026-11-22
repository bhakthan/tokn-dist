# Example: A self-organizing agent organization fixes a small repo

> "Give several workers one goal and one verifier. They share findings and submit patches; accepted patches must pass your configured verifier."

This walkthrough runs `tokn agora org`, TOKN's self-organizing multi-agent harness. The design is adapted from [microsoft/agensh](https://github.com/microsoft/agensh) (MIT). There is no central planner. Each worker:

1. reads the shared goal and the organization board,
2. claims a piece of work on the shared board,
3. works in its own private git clone,
4. posts what it found or changed to the board,
5. hands in a patch that **your verifier** must pass before it is integrated.

The repository is a toy: a tiny Python text-statistics module with **three independent bugs** and a unit-test suite. Independent bugs give the workers something to divide among themselves. The source repository is never modified. Accepted work lands in a separate checkout for you to review.

## What this example shows

| Capability | What you will do | Command |
|---|---|---|
| Preview | Validate the organization configuration without model calls or creating a run root | `tokn agora org plan` |
| Initialize | Create an isolated run root from a clean, committed repo | `tokn agora org init` |
| Run | Let the workers self-organize, verify and integrate | `tokn agora org run --execute` |
| Inspect | Activity, budgets, verification and the accepted patch | `tokn agora org status` / `results` / `search` |
| Keep going until done | Repeat rounds until a done-check passes; a failed check goes back to the workers | `tokn agora org supervise` |
| Airgap / local models | Workers on your own llama.cpp or Ollama server; public endpoints refused | `--worker gguf:…@http://…` `--airgap` |
| Scale out | Preview a larger budget, remote workers or an MCP client as a worker | `--profile large`, `serve` / `tokens` / `work`, `mcp-config` |
| Upstream Agensh | Preflight, plan or stage the upstream Docker stack; import its board | `tokn agora org agensh …` |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.60 or later | Ships `agora org`, local-model workers and `agensh` interop | `tokn version` |
| Git | The run root is built from a committed repo; each worker turn uses a private clone | `git --version` |
| Python 3.8+ | Creates the fixture repo and runs its tests as the verifier | `python --version` |
| A model for each worker | A cloud model, **or** a local server for the airgap path (section 6) | see [SETUP.md](../../SETUP.md) |

`plan` and `init` do not call a model. In this walkthrough, `run --execute`
and `supervise` do. Optional remote workers call models when started with
`work --execute`.

### What leaves your machine

- `plan`, `init`, `status`, `results` and `search` make **no model calls**.
  `--probe-local` explicitly contacts your model servers without requesting
  a completion.
- During `run --execute`, each worker sends task context and files it reads
  to its configured model. `--airgap` restricts worker model endpoints
  (section 6); it is not a machine-wide network sandbox.
- For an offline session, stage dependencies and weights first, set
  `TOKN_NO_REGISTER=1` and `TOKN_NO_UPDATE_CHECK=1`, and review other
  integrations. `init` and execution create local repositories and run state.
- The verifier (`python -m unittest`) runs candidate code **on your machine**. Treat it like running an untrusted pull request. Use `--sandbox auto` (section 8) to run it in an MXC sandbox when one is ready.

## 1. Create the fixture repository

Start in `examples/agent-organization`, where `make_repo.py` lives. Check
Git and Python with the commands above before running the fixture script.

`make_repo.py` writes the module, the tests, and one commit. Pass an **absolute** path that does not exist yet.

bash:

```bash
python make_repo.py "$HOME/tokn-org-demo/textstats"
cd "$HOME/tokn-org-demo/textstats" && python -m unittest; cd -
```

PowerShell:

```powershell
python make_repo.py "$HOME\tokn-org-demo\textstats"
Push-Location "$HOME\tokn-org-demo\textstats"; python -m unittest; Pop-Location
```

Expected: `FAILED (failures=5)`. The three bugs are:

| Function | Bug |
|---|---|
| `word_count` | splits on a single space, so tabs, newlines, repeated spaces and empty text are miscounted |
| `average_word_length` | divides by the length of the text instead of the number of words |
| `top_words` | drops the last item and does not break ties alphabetically |

## 2. Plan the organization (no model, no writes)

The run root must be a **new absolute directory outside the source repo**,
and its parent must exist. Replace the worker models with ones you have
configured (see [SETUP.md](../../SETUP.md)). Review the budget printed by
`plan` before consenting to execution.

bash:

```bash
ORG=(
  --root "$HOME/tokn-org-demo/runs/textstats-org"
  --repo "$HOME/tokn-org-demo/textstats"
  --goal "Make every test in test_textstats.py pass without changing the tests"
  --worker "openai:<your model>"
  --worker "anthropic:<your model>"
  --verify python --verify-arg=-m --verify-arg=unittest
)
mkdir -p "$HOME/tokn-org-demo/runs"
tokn agora org plan "${ORG[@]}"
```

PowerShell:

```powershell
$org = @(
  '--root', "$HOME\tokn-org-demo\runs\textstats-org",
  '--repo', "$HOME\tokn-org-demo\textstats",
  '--goal', 'Make every test in test_textstats.py pass without changing the tests',
  '--worker', 'openai:<your model>',
  '--worker', 'anthropic:<your model>',
  '--verify', 'python', '--verify-arg=-m', '--verify-arg=unittest'
)
New-Item -ItemType Directory -Force "$HOME\tokn-org-demo\runs" | Out-Null
tokn agora org plan @org
```

Expected: a plan listing both workers, the execution budget and the
`python -m unittest` verifier. A valid plan is not evidence that the models
can fix the bugs.

The verifier is an **executable plus arguments**, never a shell command. Write each argument as `--verify-arg=<value>` (with `=`) so values that start with `-` are not read as flags.

## 3. Initialize and run

`init` creates the isolated state and runs no model. `run --execute` is your explicit consent to the model calls and to running candidate code through the verifier.

bash:

```bash
tokn agora org init "${ORG[@]}"
tokn agora org run --root "$HOME/tokn-org-demo/runs/textstats-org" --execute
```

PowerShell:

```powershell
tokn agora org init @org
tokn agora org run --root "$HOME\tokn-org-demo\runs\textstats-org" --execute
```

What happens during the run (expected, not a recorded run):

- Workers use the board to divide the work, for example fixing `word_count`.
- They work in separate checkouts and submit their findings and patches.
- The host runs the verifier on each submitted patch. A patch is integrated into the accepted checkout **only if the verifier exits 0**.
- Failed or unverified work is not evidence that the goal has been achieved.

`run` is resumable. Running it again continues within the durable budgets (turns, steps and wall-clock time), and never starts over.

## 4. Inspect the result

```bash
tokn agora org status  --root "$HOME/tokn-org-demo/runs/textstats-org"
tokn agora org results --root "$HOME/tokn-org-demo/runs/textstats-org"
tokn agora org search  --help
```

- `status` reports activity, budgets, verification and integration **separately**. A worker that claims success but has no verified patch shows up as such.
- `results` prints where the accepted patch is. It never applies it to your source repo.
- `search` is a read-only boolean search over the board, for example to find every `FAIL` entry.

To keep the work, review the accepted patch, then apply it to your own repo yourself:

```bash
cd "$HOME/tokn-org-demo/textstats"
git apply --check "<patch path printed by results>"
git apply "<patch path printed by results>"
python -m unittest
```

## 5. Keep going until a done-check passes

With small models, one run may leave a bug unfixed. `supervise` repeats rounds until a **done-check** exits 0, up to `--max-rounds`. The check runs directly in the accepted checkout and is never passed through a shell.

bash:

```bash
tokn agora org supervise --root "$HOME/tokn-org-demo/runs/textstats-org" \
  --check-cmd "python -m unittest" --max-rounds 3
```

PowerShell:

```powershell
tokn agora org supervise --root "$HOME\tokn-org-demo\runs\textstats-org" `
  --check-cmd "python -m unittest" --max-rounds 3
```

Each round between checks:

1. The organization resumes, the same as `run --execute`.
2. The done-check runs.
3. If it fails, workers receive failure feedback so the next round can
   address the remaining problem.

`supervise` stops when:

- the check passes,
- `--max-rounds` is reached, or
- the turn budget is spent (it tells you so instead of looping uselessly).

It also fails if the check modifies the accepted checkout. The check only
decides **when to stop**. Your verifier remains the integration check.
A passing verifier establishes only what its tests actually cover. Review
the accepted diff and rerun tests before applying it elsewhere.

## 6. Airgap: local models only

TOKN can run the whole organization on your own hardware. Each worker names its provider, its model and, optionally, its own server.

| Worker form | Meaning |
|---|---|
| `ollama:qwen3:8b` | Ollama on its default local port |
| `gguf:qwen3-8b@http://127.0.0.1:8080/v1` | a llama.cpp `llama-server` |
| `openai:Qwen/Qwen3-32B@http://YOUR_TRUSTED_HOST:8000/v1` | an OpenAI-compatible server on your network; this is a template, not a real host |

`--airgap` refuses every worker endpoint with a public address. The check happens when TOKN connects, and proxy settings are ignored. It covers the workers' model traffic only.

**Step A — get a model onto the machine.** Start with loopback on the local
machine. Remote endpoints are an advanced option: use a trusted HTTPS endpoint
and issue a separate token to each worker. Never use a copied placeholder host.
Install or stage Ollama or
`llama-server` first, along with a tool-capable model and enough memory for
it. See [local-llamacpp](../local-llamacpp/README.md) for server setup and
dependency checks. On a connected machine, download the model; copy all
required files to the offline host before importing:

```bash
tokn models recommend
tokn models download unsloth/Qwen3-8B-GGUF --quant UD-Q4_K_XL --name qwen3-8b
# on the airgapped host, after copying the files across:
tokn models import /staged/Qwen3-8B-UD-Q4_K_XL.gguf --name qwen3-8b
```

Inside a closed network, set `HF_ENDPOINT` to a trusted mirror in your shell;
`LLAMA_SERVER_PATH` points at a pre-staged `llama-server`.

**Step B — serve it sized for an organization.** Concurrent workers share
server capacity. Choose `--parallel` and `--ctx-size` to fit your hardware;
more workers can increase memory pressure instead of improving throughput.
On start, `serve` prints the `--worker` line to use.

```bash
tokn models serve qwen3-8b --parallel 2 --ctx-size 32768
```

**Step C — plan with a probe, then run.** `--probe-local` checks that each server is reachable, has the model, and supports tool calls. It never sends a completion. `run --execute` repeats the check and stops with fix-up commands if a server is not ready.

PowerShell:

```powershell
$local = @(
  '--root', "$HOME\tokn-org-demo\runs\textstats-local",
  '--repo', "$HOME\tokn-org-demo\textstats",
  '--goal', 'Make every test in test_textstats.py pass without changing the tests',
  '--worker', 'gguf:qwen3-8b@http://127.0.0.1:8080/v1',
  '--worker', 'gguf:qwen3-8b@http://127.0.0.1:8080/v1',
  '--airgap',
  '--verify', 'python', '--verify-arg=-m', '--verify-arg=unittest'
)
tokn agora org plan @local --probe-local
tokn agora org init @local
tokn agora org run --root "$HOME\tokn-org-demo\runs\textstats-local" --execute
```

Keep the automatic endpoint-concurrency setting initially; consult
`tokn agora org plan --help` before tuning shared-server concurrency.

**Workers need tool calling.** A server that answers chat requests may
still be unsuitable for this workflow. Use `--probe-local` and inspect the
result before execution. If your llama-server needs a key, set `GGUF_API_KEY`.

### Flint, a local coding model

[`RecursiveSI/flint`](https://huggingface.co/RecursiveSI/flint) is in the catalogue as `flint-int4-gguf` (`--quant Q4_1`) or `flint-nvfp4-gguf` (`--quant NVFP4`). Before you use it:

- It needs **about 48 GB of memory**, and a **llama.cpp build that supports the Flint architecture**. An older `llama-server` fails to load it.
- TOKN has not verified Flint live on llama.cpp. Try it on the toy repo first.

## 7. Scale out

**Many workers on one machine.** `*N` declares N identical workers.
The `large` profile permits larger runs; `--allow-large` consents to the
budget shown by `plan`. Start small and review that budget before running.

```bash
tokn agora org plan --profile large --allow-large \
  --root "$HOME/tokn-org-demo/runs/textstats-large" \
  --repo "$HOME/tokn-org-demo/textstats" \
  --goal "Make every test in test_textstats.py pass without changing the tests" \
  --worker "gguf:qwen3-8b*8@http://127.0.0.1:8080/v1" \
  --concurrency 8 --turns 4 --timeout 1h --airgap \
  --verify python --verify-arg=-m --verify-arg=unittest
```

Use `plan --help` for concurrency, scheduling and timeout options rather
than assuming that more workers will make a run faster.

**Workers on other machines.** The host serves the organization over an authenticated HTTP API. Each worker has its own token and runs its own local model. A submitted patch is a claim: only the host verifier integrates it. Remote submissions are **held unverified** unless an MXC sandbox is ready, or you started the organization with `--trust-remote-submissions`.

On the host:

```bash
tokn agora org tokens --root "$HOME/tokn-org-demo/runs/textstats-large" --out "$HOME/tokn-org-demo/tokens.txt"
tokn agora org serve  --root "$HOME/tokn-org-demo/runs/textstats-large" --tokens-file "$HOME/tokn-org-demo/tokens.txt" \
  --listen 0.0.0.0:8787 --tls-cert host.pem --tls-key host-key.pem
```

`tokens` exports worker credentials. Protect `tokens.txt`, hand each worker
only its own token over a secure channel, and never commit token files.
Remote hosting also needs a reachable HTTPS address and certificates
appropriate to your deployment; this is not configured by the example.

On each worker machine, with a clone of the same repository and its own model server:

```bash
tokn agora org work --url "https://YOUR_TRUSTED_HOST:8787" --ca-cert ca.pem --token-file worker-3.token \
  --model "gguf:qwen3-8b@http://127.0.0.1:8080/v1" \
  --repo /src/textstats --workdir "$HOME/tokn-org-demo/worker-3" --airgap
```

Without `--execute`, `work` prints its plan (identity, baseline and model check) and calls no model. Add `--execute` to run. One process is one worker; start several processes, each with its own token, to add more.

**An MCP client as a worker.** Copilot CLI or Claude Code can act as one worker. This prints the JSON to merge into the client's MCP configuration and writes nothing:

```bash
tokn agora org mcp-config --root "$HOME/tokn-org-demo/runs/textstats-org" --worker worker-2 --client copilot
```

## 8. Optional: sandbox the verifier

By default the verifier runs on your host. With a [microsoft/mxc](https://github.com/microsoft/mxc) executor installed, `--sandbox auto` runs it with network egress denied, and `--sandbox mxc` fails closed if the sandbox is not ready. TOKN never downloads MXC.

```bash
tokn agora org sandbox preflight
```

The preflight lists every missing dependency with install guidance. `--worker-exec` gives workers a sandboxed shell tool, and is never registered without a ready sandbox.

## 9. Optional: the upstream Agensh stack

`tokn agora org agensh` works with the upstream [microsoft/agensh](https://github.com/microsoft/agensh) reference stack. It requires Docker, Compose v2 and systemd, on Linux or WSL 2. **Nothing runs without `--yes`.** Without it, each command prints the ordered plan of commands and stops.

```bash
tokn agora org agensh preflight
tokn agora org agensh plan --checkout /opt/agensh --tasks <task-id>
tokn agora org agensh up --dir /opt/agensh --tasks <task-id> --workers 4 \
  --worker-runtime tokn --model-provider gguf --model-endpoint http://localhost:8080/v1
```

- `preflight` lists **every** missing prerequisite at once, with install commands. It only searches PATH and checks files.
- `up` checks out pinned upstream commits. `--worker-runtime tokn` runs TOKN inside the upstream worker images, speaking the Agent Client Protocol (`tokn acp`). `--model-endpoint` points those workers at your local server.
- **Airgap.** On a connected host, `agensh stage --out <bundle> --tasks <task-id>` prints the plan for a transfer bundle: git bundles, images, task data and a checksum manifest. On the airgapped host, `agensh up --offline --bundle <bundle>` uses only the bundle and never clones, pulls or builds.
- **Bring the board home.** `agensh import --from <snapshot.json or board URL> --org <run root>` copies upstream board notes into a TOKN organization as host context.

The Docker launch, online or offline, and ACP inside Agensh are **not live-verified by TOKN yet**. Start with `preflight` and `plan`.

## What to look for

| Check | Expected |
|---|---|
| `python -m unittest` before | `FAILED (failures=5)` |
| `org plan` | Two workers, verifier `python -m unittest`, no run root created |
| `org status` after `run --execute` | Verification and integration reported separately; verified patches integrated |
| Accepted checkout | `python -m unittest` prints `OK` (7 tests) |
| `supervise` with a failing check | A `FAIL` entry labelled `done-check` on the board, then another round |
| `plan --airgap` with a public endpoint | Refused before anything runs |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `requires --profile large` | `*N` worker form under the default profile | Add `--profile large --allow-large`, or list each worker |
| `--repo` refused as not clean | Uncommitted or untracked files | Commit them, or run `make_repo.py` again into a new path |
| `--root` refused | Root exists, is relative, sits inside the repo, or has no parent | Use a new absolute path whose parent exists, outside the repo |
| Verifier argument read as a flag | `--verify-arg -m` without `=` | Write `--verify-arg=-m` |
| Local preflight fails | Server down, model missing, or no tool calling | Run the fix-up commands it prints; serve with `tokn models serve` |
| Flint fails to load | llama.cpp too old, or not enough memory | Build llama.cpp with Flint support; about 48 GB of memory is needed |
| Remote patch shows as held | No ready sandbox and no opt-in | `tokn agora org sandbox preflight`, or init with `--trust-remote-submissions` |
| `supervise` stops early | Turn budget spent | Inspect status and plan a new organization with an appropriate budget |

Stop any model or organization server you started when finished. Keep the
run root for inspection, or remove it deliberately after reviewing accepted
work. Do not copy run state, token files or generated credentials into the
source repository.

## Related

- [agent-team](../agent-team/README.md): a declarative team with fixed roles, the opposite of self-organization.
- [federation](../federation/README.md): a leader fans one task out to workers.
- [SETUP.md](../../SETUP.md): provider and model configuration.
