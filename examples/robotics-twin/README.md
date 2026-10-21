# Example: stop an unsafe robot deployment before it reaches real hardware

This walkthrough runs TOKN's autonomous robotics and digital-twin domain on a
small, synthetic mission spec:

> *Deploy the pick-and-place controller to the real cell, which is the requested
> phase. Check timing, physics limits, sim-to-real transfer and SIL evidence,
> then deploy.*

The mission is written to look ready for deployment. It is not. The controller
was validated only in synthetic simulation, its timing and payload are out of
bounds, and it declares a SIL without evidence. The domain's gates should block
each step. Every gate in this example is expected to fire on the synthetic data.

For the physical-AI fleet view (safety envelopes across a set of robots), see
[`../physai-fleet/README.md`](../physai-fleet/README.md). This example covers the
single-mission lifecycle and gates. The two are complementary.

| Gate or tool | What it checks here |
|---|---|
| **Sim-to-real transfer gate** (`sim_to_real_validate`) | Transfer from synthetic data (Layer 4) to real hardware (Layer 1) is an **absolute block**. Layer 4 may not be used as evidence for Layer 1 at all. |
| **Lifecycle order** (`deploy_controller`) | A 12-phase lifecycle. DEPLOYMENT requires SAFETY_CERTIFICATION first, which requires SIM_VALIDATION and HARDWARE_IN_LOOP first. |
| **Timing budget** (`check_timing_budget`) | Mean latency above the control period is a TIMING VIOLATION. |
| **Physics limits** (`check_physics_constraints`) | Torque, velocity and payload limits. Defaults are 100 N·m, 3.14 rad/s and 10 kg, unless the approved robot model sets its own. |
| **SIL evidence** (`verify_sil_compliance`, `deploy_controller`) | A controller must declare a SIL with its evidence before deployment. SIL2 and above require WCET (worst-case execution time) evidence. The maximum authorized level is SIL3. |

All data in `mission_spec.json` is synthetic.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | Current release with the robotics mode | `tokn version` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |
| **14-day trial** (`tokn license trial`) | `--mode robotics` is a domain mode. Community grants only `domains:basic`. | `tokn license features` |

The trial is one per machine. The agent run in step 5 needs the trial or a
licence that grants `domains:robotics`.

> **What leaves your machine.** The model provider receives the task and the
> mission spec that the agent reads. Nothing else is sent. Steps 1–3 make no model
> call.

## 1. Copy the example into a scratch folder

macOS / Linux:

```bash
mkdir -p ~/tokn-twin && cp examples/robotics-twin/mission_spec.json examples/robotics-twin/task-prompt.txt ~/tokn-twin/
cd ~/tokn-twin
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-twin | Out-Null
Copy-Item examples\robotics-twin\mission_spec.json, examples\robotics-twin\task-prompt.txt $HOME\tokn-twin\
Set-Location $HOME\tokn-twin
```

You now have:

```text
tokn-twin/
  mission_spec.json   # the mission, controller and sim-to-real data (synthetic)
  task-prompt.txt     # the task given to the agent
```

## 2. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a Claude model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "<a Claude model you have access to>"
$env:ANTHROPIC_API_KEY      = "<your key>"
```

Use your shell or `~/.tokn/config/credentials.env` for keys. Never commit a
key to the repo.

## 3. Check your tier and preview the mission

```bash
tokn license features
```

```powershell
tokn license features
```

If `domains:robotics` is not listed, start the trial once per machine with
`tokn license trial`.

Read the mission spec:

```bash
cat mission_spec.json
```

```powershell
Get-Content mission_spec.json
```

Note the values that matter: `current_phase` is `SIM_VALIDATION`, `requested_phase`
is `DEPLOYMENT`, the controller is `SIL2` with `wcet_evidence: false`, the
mean latency (11.2 ms) is above the 10 ms period, the sim-to-real source is
Layer 4 and the target is Layer 1, and the payload is 12 kg.

## 4. Run the agent in the robotics mode

```bash
tokn agent-run --mode robotics --repo-root . --prompt-file task-prompt.txt --max-steps 12
```

```powershell
tokn agent-run --mode robotics --repo-root . --prompt-file task-prompt.txt --max-steps 12
```

Leave tool confirmation on (the default), so you see each tool call before it runs.
Do not approve a deployment step by hand. The point of this example is that the
gates should refuse it.

## 5. Read the result

Compare the agent's answer with the table below. Each row states what the gate
rules say should happen. It is **not** a record of a run.

| Check | Expected (from the gate rules) |
|---|---|
| Deploy to real hardware from Layer 4 synthetic evidence | `SIM-TO-REAL ABSOLUTE BLOCK`. Deployment is refused. |
| Requested DEPLOYMENT from SIM_VALIDATION | Blocked by lifecycle order: SAFETY_CERTIFICATION and HARDWARE_IN_LOOP come first. |
| Mean latency 11.2 ms against a 10 ms period | Timing violation. |
| Torque 120 N·m, payload 12 kg | Above the 100 N·m and 10 kg defaults. Reported as a physics limit violation. |
| SIL2 with no WCET evidence | Not compliant: missing evidence. Deployment is refused. |

### What to look for

- **The refusal.** The agent should say that deployment is blocked and name the
  rule that fired, not just stop.
- **The numbers.** Each block should carry the figure that failed (latency,
  torque, layer, SIL evidence).
- **No hardware.** The agent should not call `emergency_stop` or any action that
  touches real hardware. This example has no hardware attached.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `unknown mode "robotics"` or no robotics tools | Upgrade to TOKN v0.3.57 or newer: `tokn version` |
| Domain tools missing, or the mode refuses to start | Start the trial (`tokn license trial`) and check `tokn license features` |
| Every step falls back, or no tool calls happen | The LLM is not configured. Re-check step 2 |
| The agent deploys anyway | Check that you ran with `--mode robotics` and not `--mode default`. Report the run if the gates did not fire. |
| `mission_spec.json` not found | Run step 1 again, and run `tokn agent-run` from inside `tokn-twin` |
