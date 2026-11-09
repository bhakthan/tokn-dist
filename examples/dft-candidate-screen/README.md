# Example: DFT Candidate Screen

> Screen five coating candidates for comparability, convergence and thermodynamic stability before synthesis.

A general-purpose LLM reads the records and gives a confident verdict. The `matsci` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `compute_phase_stability` | Classify a candidate by e_above_hull (eV/atom) using the 25 meV/atom convention: ≤0 stable, ≤0.025 metastable, >0.025 unstable. |
| `compute_convergence_test` | Evaluate ENCUT or k-mesh convergence from a series of per-atom energies. |
| `diff_incar_parameters` | Detect ENCUT / KSPACING / EDIFF / ISMEAR / functional drift across a set of INCAR snapshots. |
| `validate_pseudopotential_consistency` | Check that a set of runs uses a single pseudopotential family (PAW_PBE / PAW_PBE_GW / PAW_PBE_SOC / PAW_PBESOL / PAW_LDA). |
| `classify_structure_provenance` | Classify a set of crystal-structure sources into the ICSD > Materials Project > COD > derived hierarchy and flag calibrated-language downgrades when layers are mixed. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.82 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:matsci` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/dft-candidate-screen ~/dft-candidate-screen-run
cd ~/dft-candidate-screen-run
```

```powershell
Copy-Item -Recurse examples\dft-candidate-screen $HOME\dft-candidate-screen-run
Set-Location $HOME\dft-candidate-screen-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`candidates.json`, `encut_convergence.json`, `incar_snapshots.json`, `pseudopotentials.json`), then assign a status to each item yourself: `CAND-A`, `CAND-B`, `CAND-C`, `CAND-D`, `CAND-E`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode matsci --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

5 items with 5 tools each can take 25 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `compute_phase_stability`, `compute_convergence_test`, `diff_incar_parameters`, `validate_pseudopotential_consistency`, `classify_structure_provenance` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does any candidate with INCAR drift or an unconverged ENCUT series still receive recommend or recommend_with_caveats? |
| 3 | Trap avoided | Answer is no: Does the result describe a metastable candidate with more certainty than the 25 meV/atom convention supports? |
| 4 | Evidence is cited | `RESULT.md` mentions `meV/atom`, `metastable`, `ENCUT`, `provenance` |
| 5 | Calibrated language | Nothing says "guaranteed to be stable", "definitely stable", "proven stable", "will be synthesizable" |
| 6 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `CAND-A` | `recommend` | No trap: the status follows directly from the tool results. |
| `CAND-B` | `recommend_with_caveats` | No trap: the status follows directly from the tool results. |
| `CAND-C` | `blocked` | Looks best (on the hull, ICSD source) but was run at ENCUT 400 eV against a 520 eV reference. |
| `CAND-D` | `reject` | No trap: the status follows directly from the tool results. |
| `CAND-E` | `blocked` | Only 6 meV/atom above hull, but the last ENCUT step still moves 4 meV/atom. |

All 5 correct counts as PASS. Missing any trap item (`CAND-C`, `CAND-E`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:matsci` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode matsci`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
