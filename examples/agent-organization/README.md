# Example: A self-organizing agent organization fixes a small repo

> "Give several workers one goal and one verifier. No orchestrator assigns the work: they claim bugs, share findings on a board, and only verified patches are integrated."

This walkthrough runs `tokn agora org`, TOKN's self-organizing multi-agent harness. The design is adapted from [microsoft/agensh](https://github.com/microsoft/agensh) (MIT). There is no central planner. Each worker:

1. reads the shared goal and the organization board,
2. claims a piece of work with a lease, so two workers do not fix the same bug,
3. works in its own private git clone,
4. posts what it found or changed to the board,
5. hands in a patch that **your verifier** must pass before it is integrated.

The repository is a toy: a tiny Python text-statistics module with **three independent bugs** and a unit-test suite. Independent bugs give the workers something to divide among themselves. The source repository is never modified. Accepted work lands in a separate checkout for you to review.

## What this example shows

| Capability | What you will do | Command |
|---|---|---|
| Plan without cost | Validate the configuration with no writes and no model calls | `tokn agora org plan` |
| Initialize | Create an isolated run root from a clean, committed repo | `tokn agora org init` |
| Run | Let the workers self-organize, verify and integrate | `tokn agora org run --execute` |
| Inspect | Activity, budgets, verification and the accepted patch | `tokn agora org status` / `results` / `search` |
| Keep going until done | Repeat rounds until a done-check passes; a failed check goes back to the workers | `tokn agora org supervise` |
| Airgap / local models | Workers on your own llama.cpp or Ollama server; public endpoints refused | `--worker gguf:…@http://…` `--airgap` |
| Scale out | 8 to 64 workers, workers on other machines, MCP clients as workers | `--profile large`, `serve` / `tokens` / `work`, `mcp-config` |
| Upstream Agensh | Preflight, plan or stage the upstream Docker stack; import its board | `tokn agora org agensh …` |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.60 or later | Ships `agora org`, local-model workers and `agensh` interop | `tokn version` |
| Git | The run root is built from a committed repo; each worker turn uses a private clone | `git --version` |
| Python 3.8+ | Creates the fixture repo and runs its tests as the verifier | `python --version` |
| A model for each worker | A cloud model, **or** a local server for the airgap path (section 6) | see [SETUP.md](../../SETUP.md) |

`plan` and `init` never call a model. Only `run --execute` and `supervise` do.

### What leaves your machine

- `plan`, `init`, `status`, `results` and `search` make **no model calls** and no network calls.
- During `run --execute`, each worker sends the goal, the board and the files it reads to **its own** configured model. With `--airgap` and local workers (section 6), nothing leaves your network.
- The verifier (`python -m unittest`) runs candidate code **on your machine**. Treat it like running an untrusted pull request. Use `--sandbox auto` (section 8) to run it in an MXC sandbox when one is ready.

## 1. Create the fixture repository

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

The run root must be a **new absolute directory outside the source repo**, and its parent must exist. Two workers are the default `local` profile's limit for concurrency. Replace the worker models with ones you have configured (see [SETUP.md](../../SETUP.md)).

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

Expected: a JSON plan listing `worker-1` and `worker-2`, `"concurrency": 2`, `"max_turns": 2`, `"max_steps": 12`, and `"verify": ["python", "-m", "unittest"]`.

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

- Each worker reads the board, then claims a bug with a lease, for example `word_count`.
- It fixes the bug in its private clone, runs the tests, and posts a `PATCH_SUMMARY` to the board.
- The host runs the verifier on each submitted patch. A patch is integrated into the accepted checkout **only if the verifier exits 0**.
- If a worker posts a `FAIL` for a label, earlier patches with the same label are dropped.

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
git apply --check <patch path printed by results>
git apply <patch path printed by results>
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
3. **If the check fails, its output is posted to the board** as a host `FAIL` entry labelled `done-check`, with the exit code and the last line of output. The workers see the summary in the next round and can open the full output with `agora_context_unfold`, so the next round targets what actually failed.

`supervise` stops when:

- the check passes,
- `--max-rounds` is reached, or
- the turn budget is spent (it tells you so instead of looping uselessly).

It also fails if the check modifies the accepted checkout. The check only decides **when to stop**. Your verifier remains the only gate for integration. Add `--json` for a machine-readable report, including the board sequence number of each posted failure.

## 6. Airgap: local models only

TOKN can run the whole organization on your own hardware. Each worker names its provider, its model and, optionally, its own server.

| Worker form | Meaning |
|---|---|
| `ollama:qwen3:8b` | Ollama on its default local port |
| `gguf:qwen3-8b@http://127.0.0.1:8080/v1` | a llama.cpp `llama-server` |
| `openai:Qwen/Qwen3-32B@http://vllm.lan:8000/v1` | any OpenAI-compatible server on your network, such as vLLM |

`--airgap` refuses every worker endpoint with a public address. The check happens when TOKN connects, and proxy settings are ignored. It covers the workers' model traffic only.

**Step A — get a model onto the machine.** On a connected machine, download one quant (every shard, sha256-checked). Then copy the files across and register them offline:

```bash
tokn models recommend
tokn models download unsloth/Qwen3-8B-GGUF --quant UD-Q4_K_XL --name qwen3-8b
# on the airgapped host, after copying the files across:
tokn models import /staged/Qwen3-8B-UD-Q4_K_XL.gguf --name qwen3-8b
```

Inside a closed network, `HF_ENDPOINT=https://<your hub mirror>` points `search` and `download` at an internal mirror. `LLAMA_SERVER_PATH` points at a pre-staged `llama-server`.

**Step B — serve it sized for an organization.** `--parallel` sets the number of slots, meaning concurrent requests. Each slot gets `--ctx-size / --parallel` tokens of context, and TOKN warns below 8192. On start, `serve` prints the exact `--worker` line to use.

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

By default, `--endpoint-concurrency 0` caps the workers sharing one llama-server at its `--parallel` slot count, so extra workers queue instead of overloading it.

**Models without tool calling are refused.** A worker needs tool calls to claim work and hand in patches. `tokn models serve` starts llama-server with `--jinja` so the model's chat template keeps tool calling. GGUF `qwen3…` and `flint…` models are recognised as tool-capable. If your llama-server needs a key, set `GGUF_API_KEY`.

### Flint, a local coding model

[`RecursiveSI/flint`](https://huggingface.co/RecursiveSI/flint) is in the catalogue as `flint-int4-gguf` (`--quant Q4_1`) or `flint-nvfp4-gguf` (`--quant NVFP4`). Before you use it:

- It needs **about 48 GB of memory**, and a **llama.cpp build that supports the Flint architecture**. An older `llama-server` fails to load it.
- Flint thinks before calling a tool. TOKN sends that reasoning back to the model during the same tool chain, as Flint expects, and does this only for Flint. Other models never receive it, because some APIs reject it.
- TOKN has not verified Flint live on llama.cpp. Try it on the toy repo first.

## 7. Scale out

**Many workers on one machine.** The `large` profile allows up to 64 workers (16 at a time), 8 turns each and 4 hours. `*N` declares N identical workers. `--allow-large` is your consent to the worst-case number of model calls, workers × turns × steps, which `plan` prints first.

```bash
tokn agora org plan --profile large --allow-large \
  --root "$HOME/tokn-org-demo/runs/textstats-large" \
  --repo "$HOME/tokn-org-demo/textstats" \
  --goal "Make every test in test_textstats.py pass without changing the tests" \
  --worker "gguf:qwen3-8b*8@http://127.0.0.1:8080/v1" \
  --concurrency 8 --turns 4 --timeout 1h --airgap \
  --verify python --verify-arg=-m --verify-arg=unittest
```

Workers are admitted on a staggered schedule (`--stagger`, `--stagger-fast`, `--stagger-ramp`). The reserved `_host` sends a direct message to a worker that has been idle for `--idle-after`, and reminders to everyone as the deadline approaches (`--deadline-early`, `--deadline-final`).

**Workers on other machines.** The host serves the organization over an authenticated HTTP API. Each worker has its own token and runs its own local model. A submitted patch is a claim: only the host verifier integrates it. Remote submissions are **held unverified** unless an MXC sandbox is ready, or you started the organization with `--trust-remote-submissions`.

On the host:

```bash
tokn agora org tokens --root "$HOME/tokn-org-demo/runs/textstats-large" --out "$HOME/tokn-org-demo/tokens.txt"
tokn agora org serve  --root "$HOME/tokn-org-demo/runs/textstats-large" --tokens-file "$HOME/tokn-org-demo/tokens.txt" \
  --listen 0.0.0.0:8787 --tls-cert host.pem --tls-key host-key.pem
```

`tokens` prints each plaintext token **once** and stores only hashes. Hand each token to one worker over a secure channel.

On each worker machine, with a clone of the same repository and its own model server:

```bash
tokn agora org work --url https://<host>:8787 --ca-cert ca.pem --token-file worker-3.token \
  --model "gguf:qwen3-8b@http://127.0.0.1:8080/v1" \
  --repo /src/textstats --workdir /var/tmp/orgwork --airgap
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
| `org plan` | Two workers, verifier `python -m unittest`, no files written |
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
| `supervise` stops early | Turn budget spent | Start a new organization with more `--turns` (large profile up to 8) |

## Related

- [agent-team](../agent-team/README.md): a declarative team with fixed roles, the opposite of self-organization.
- [federation](../federation/README.md): a leader fans one task out to workers.
- [SETUP.md](../../SETUP.md): provider and model configuration.
