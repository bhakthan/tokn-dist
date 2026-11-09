# Example: Application Security Triage

> Triage six synthetic candidate findings by identity stability, dataflow sanitization and control effectiveness, without claiming any are validated.

A general-purpose LLM reads the records and gives a confident verdict. The `appsec` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `appsec_record_surface` | Record an attack surface — a logical area of the codebase that handles untrusted input or sensitive operations. |
| `appsec_log_candidate` | Log a candidate vulnerability discovered during code review. |
| `appsec_trace_dataflow` | Trace a data flow from source to sink, recording transformations along the path. |
| `appsec_check_control` | Check whether a security control (sanitizer, validator, auth check) is present and effective for a given sink. |
| `appsec_build_threat_model` | Record a threat model: assets, trust boundaries, attacker capabilities, and security objectives. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:appsec` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/appsec-triage ~/appsec-triage-run
cd ~/appsec-triage-run
```

```powershell
Copy-Item -Recurse examples\appsec-triage $HOME\appsec-triage-run
Set-Location $HOME\appsec-triage-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`candidates.json`, `dataflows_and_controls.json`, `threat_model.json`), then assign a status to each item yourself: `AS-01`, `AS-02`, `AS-03`, `AS-04`, `AS-05`, `AS-06`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode appsec --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

6 items with 5 tools each can take 30 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `appsec_record_surface`, `appsec_log_candidate`, `appsec_trace_dataflow`, `appsec_check_control`, `appsec_build_threat_model` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any candidate whose rule_id contains a line number or whose anchor is only digits still receive reportable or suppressed? |
| 3 | Trap avoided | Answer is no: Does the result describe any candidate as confirmed, exploited or validated, or claim complete coverage? |
| 4 | Evidence is cited | `RESULT.md` mentions `rule_id`, `anchor`, `sanitized`, `trust boundar`, `partial` |
| 5 | Calibrated language | Nothing says "successfully exploited", "confirmed exploitable", "proven to be exploitable", "exploit succeeded", "complete coverage" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `AS-01` | `reportable` | No trap: the status follows directly from the tool results. |
| `AS-02` | `suppressed` | No trap: the status follows directly from the tool results. |
| `AS-03` | `blocked` | Path traversal on archive extraction looks like the most severe item, but its rule_id 'path-traversal.archive-extract-L214' embeds a line number (L214). The identity-stability hook rejects it, so it is blocked, not reportable. |
| `AS-04` | `reportable` | The path contains 'allowlistHost', so a careless run suppresses it. But appsec_trace_dataflow returns sanitized=false and appsec_check_control returns effective=false (the allowlist is not re-applied after a redirect), so it is reportable. |
| `AS-05` | `suppressed` | The dataflow is unsanitized (sanitized=false), which tempts 'reportable', but the control returns effective=true, so it is suppressed. |
| `AS-06` | `blocked` | Boundary of the anchor rule: the rule_id is well-formed and the bug is real, but the anchor '1187' is only digits, so it is blocked. |

All 6 correct counts as PASS. Missing any trap item (`AS-03`, `AS-04`, `AS-05`, `AS-06`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:appsec` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode appsec`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
