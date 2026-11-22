# Example: Warehouse AMR fleet from the physai mode

> "Build a multi-agent software system for a warehouse fleet of autonomous mobile
> robots, organised as 14 cooperating agents across five layers."

Give TOKN a written spec and the `physai` mode generates a project: a
14-agent system for a warehouse fleet of autonomous mobile robots (AMRs), with
safety, perception, path-planning, fleet-coordination, and hardware layers, plus
a simulation test. This example shows you how to run it and what to check. It
does **not** include a generated project; you create that yourself. You start
with a single role (the emergency-stop path) and a static check, and only then,
if you choose, generate the full 14-agent system. Everything is software and
simulation; no real robot or hardware is involved.

| Capability | What TOKN produces |
|---|---|
| Physical-systems mode | `--mode physai` shapes the agents and their safety gates |
| Five layers | Reactive, perception, tactical, strategic, and hardware modules |
| Named model components | Perception uses a detector and a pose estimator as named slots |
| Simulation test | A test file that runs a small fleet and prints throughput and E-stop latency |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | Includes the physai mode | `tokn version` |
| Tier: **trial or paid license** | `physai` is a domain plug; Community does not include `domains:physai` | `tokn license features` should list `domains:physai` or `domains:*` |
| An LLM API key | `agent-run` calls a model. Use a model capable of the required tool calls; provider charges and number of turns depend on the run. A missing/failed tool result is unassessed, not a pass. | `tokn doctor --provider anthropic` (static; see [SETUP.md](../../SETUP.md)) |
| Python 3.10+ | To run the generated simulation test yourself | `python --version` |

To start a trial, run `tokn license trial` once per machine. If you do not have a
trial or paid license, this example will not run in physai mode.

## What leaves your machine

- The prompt file you run (`one-role-prompt.md` or `task-prompt.md`) and whatever
  TOKN reads from the output folder are sent to the model provider you configure.
- The generated code is written locally and is not sent anywhere by this example.

## Steps

### 1. Create an output folder

bash:
```bash
mkdir ~/physai-fleet-out
cp one-role-prompt.md task-prompt.md ~/physai-fleet-out/
cd ~/physai-fleet-out
```

PowerShell:
```powershell
New-Item -ItemType Directory $HOME\physai-fleet-out | Out-Null
Copy-Item one-role-prompt.md, task-prompt.md $HOME\physai-fleet-out\
Set-Location $HOME\physai-fleet-out
```

`mkdir` fails if the folder already exists, so the run always starts empty.

### 2. Configure your model

The key is read without echo, so it stays out of your shell history.

bash:
```bash
export NOSPACE_MODEL_PROVIDER='anthropic'
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
```

PowerShell:
```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "YOUR_MODEL_ID"
$env:ANTHROPIC_API_KEY = Read-Host 'Anthropic key' -MaskInput   # pwsh 7.1+; or read it from your secret store
```

### 3. Generate the system

Flags were checked against `tokn agent-run --help-all`. Every command here uses
`--permission-mode default`, so TOKN asks before each file write or command and
you see every tool call. Leaving the flag out does **not** give you prompts: the
scripted default runs without asking. Run the commands only in the empty output
folder you created.

**Start with one role.** Generate only the emergency-stop path:

bash:
```bash
tokn agent-run --mode physai --prompt-file one-role-prompt.md --repo-root . \
  --permission-mode default --max-steps 20
```

PowerShell:
```powershell
tokn agent-run --mode physai --prompt-file one-role-prompt.md --repo-root . `
  --permission-mode default --max-steps 20
```

Then check the contract yourself, without trusting the agent's summary. Compile
every generated file and run the stop test:

```bash
python -m compileall -q safety
python -m unittest discover -s safety -p "test_*.py" -v
```

Read `safety/estop.py` and confirm `request_stop`, `tick`, `stopped` and
`reset` exist and that nothing imports a hardware, network or serial module.
If a file is missing or a test fails, that role is unassessed or failed; do not
move on as if it passed.

**Advanced: the full 14-agent simulation.** Only after the one-role check, and
only if you accept a much longer and costlier run, generate the full system in
the same folder:

bash:
```bash
tokn agent-run --mode physai --prompt-file task-prompt.md --repo-root . \
  --permission-mode default --max-steps 60 --token-budget 400000
```

PowerShell:
```powershell
tokn agent-run --mode physai --prompt-file task-prompt.md --repo-root . `
  --permission-mode default --max-steps 60 --token-budget 400000
```

`--max-steps` limits turns and `--token-budget` is a soft budget, not a hard
spend cap. Press Ctrl+C to stop the run at any point; files already written stay
in the folder for you to inspect. Do not add `--no-confirm` here: it
auto-approves every tool call.

### 4. Look at the shape of what was generated

You should see a tree roughly like this (trimmed; yours will differ):

```text
physai-fleet-out/
  STATUS.md
  agents/            # reactive and strategic agents
  perception/        # detector and pose-estimator components
  planning/          # per-robot path planning
  orchestration/     # fleet auction and deadlock handling
  safety/            # E-stop path
  hardware/          # replaceable motor and sensor adapter
  test_fleet_simulation.py
```

Read `STATUS.md` first. It lists what was simulated and what was not run on hardware.

### 5. Run the generated simulation test yourself

Open `test_fleet_simulation.py` and read its header to see how it expects to be run,
then run it as the header says. This example does not provide a runner for it.

## What to look for

| Check | How | Expected |
|---|---|---|
| Layers present | `ls` the output folder | The five layer folders listed above |
| Status honest | Open `STATUS.md` | It separates simulated results from anything run on hardware |
| E-stop path exists | Search `safety/` for `estop` or `stop` | A stop path that the reactive layer can trigger |
| Simulation test runs | Step 5 | It prints deliveries, throughput, and E-stop latency |
| Deadlock case | Read the simulation output | Check whether deadlock was resolved; do not assume it was |

## What one of our runs looked like (your numbers will differ)

These are from one generation run on our side, shown only to illustrate what
checks produce. Your system will be different.

| Area | Result |
|---|---|
| Syntax of generated Python files | 19 of 19 pass |
| Safety tests | 3 of 4 pass |
| E-stop tests | 3 of 4 pass |
| Perception tests | 5 of 5 pass |
| Path planner tests | 3 of 3 pass |
| Fleet coordination tests | 2 of 3 pass |
| Simulation | 50 of 50 deliveries, about 1440 packages/hour, E-stop latency 0.0 ms for 6 robots |
| Deadlock resolution | **Not resolved** in the run we saw |

We did not fix the failing cases for this example. Treat the failures as what
you should expect to investigate, not as a finished result.

## Troubleshooting

| Symptom | Fix |
|---|---|
| License or domain error on `agent-run` | Run `tokn license trial`, then `tokn license features` and confirm `domains:physai` or `domains:*` |
| Run stops early | Raise `--max-steps` and re-run in the same folder |
| Generated files appear in the wrong place | Use an empty output folder and pass it as `--repo-root` |
| No model response | Check the three `NOSPACE_*` and key variables from step 2 |
| Simulation test fails | Read its failure lines and STATUS.md; the generated code is a starting point, not a verified controller |

## Important

The generated system is a software design and a simulation. It is not a
certified safety system. Do not connect generated hardware code to real robots
without independent review and on-site testing.
