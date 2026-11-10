# Example: GHG Inventory Assurance Check

> Assign a review status to four entity inventories, one Scope 3 calculation and one draft disclosure claim from Scope 1/2 calculations, contractual-instrument quality, emission-factor provenance, Scope 3 double-count checks and anti-greenwashing claim checks before the sustainability statement goes to internal review.

A general-purpose LLM reads the records and gives a confident verdict. The `esg` domain mode runs each item through deterministic domain tools and gates, so the status comes from a tool result, not from the model's impression of the numbers.

| Tool | What it does |
|---|---|
| `esg_scope1_calculate` | Scope 1 direct emissions: activity × emission factor per gas, CO2e via GWP100 of the explicit gwp_set. |
| `esg_scope2_dual_report` | Scope 2 dual reporting. |
| `esg_factor_provenance_check` | Audit an emission-factor register. |
| `esg_scope3_screen` | Scope 3 screening across all 15 categories. |
| `esg_scope3_calculate` | Scope 3 calculation. |
| `esg_claim_language_check` | Anti-greenwashing claim check. |

This is the single-agent version of a TOKN domain-relay scenario. It uses the same synthetic data, one model and a few cents of tokens, not a five-model relay.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.83 or newer | Includes the domain tools this example calls. | `tokn version` |
| 14-day trial (`tokn license trial`) | Domain modes need the trial. | `tokn license features` shows `domains:esg` or `domains:*` |
| An LLM provider | TOKN calls a model. Any supported provider works. | See [../../SETUP.md](../../SETUP.md) |

**What leaves your machine:** the prompt, the files TOKN reads from the scratch folder, and tool results. These go to the LLM provider you configure. The demo data is synthetic.

## 1. Copy the example to a scratch folder

TOKN writes `.nospace/` state and output files into the working folder, so run it outside this repo.

```bash
cp -r examples/ghg-inventory-check ~/ghg-inventory-check-run
cd ~/ghg-inventory-check-run
```

```powershell
Copy-Item -Recurse examples\ghg-inventory-check $HOME\ghg-inventory-check-run
Set-Location $HOME\ghg-inventory-check-run
```

## 2. Configure the LLM

Set `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your provider key as described in [../../SETUP.md](../../SETUP.md). The [semicon-signoff](../semicon-signoff/README.md#2-configure-the-llm) example shows the exact commands for bash and PowerShell.

## 3. Before you run: make your own call

Read `prompt.md` and the files in `demo-input/` (`claims.json`, `factor_register.json`, `scope1_scope2.json`, `scope3.json`), then assign a status to each item yourself: `ENT-A`, `ENT-B`, `ENT-C`, `ENT-D`, `SC3-CAT3`, `CLAIM-1`. Write it down. Comparing your call with TOKN's is the point of the exercise.

## 4. Run the task

```bash
tokn agent-run --mode esg --repo-root . --prompt-file prompt.md --max-steps 40 --no-confirm
```

6 items with 6 tools each can take 36 or more tool calls. If the run stops early, raise `--max-steps`.

## 5. Check the result

| # | Expectation | Pass signal |
|---|---|---|
| 1 | The domain tools run | The run log shows `esg_scope1_calculate`, `esg_scope2_dual_report`, `esg_factor_provenance_check`, `esg_scope3_screen`, `esg_scope3_calculate`, `esg_claim_language_check` applied to the items they cover |
| 2 | Trap avoided | Answer is no: Does the result report ENT-B's market-based Scope 2 as a valid Scope 2 figure even though no location-based (grid-average) figure can be computed? |
| 3 | Trap avoided | Answer is no: Does the result let REC-C-2022-077 (vintage 2022, market GRID-WEST) reduce ENT-C's market-based Scope 2 for a GRID-NORTH site in reporting year 2025? |
| 4 | Trap avoided | Answer is no: Does the result accept CLAIM-1's 'carbon neutral' wording although gross emissions are unchanged and the claim rests entirely on retired carbon credits? |
| 5 | Evidence is cited | `RESULT.md` mentions `location-based`, `market-based`, `vintage`, `double count`, `offsets`, `unit` |
| 6 | Calibrated language | Nothing says "net zero achieved", "100% green", "guaranteed compliant", "fully compliant with CSRD", "zero risk of greenwashing" |
| 7 | One status per item | Every item gets exactly one status from the vocabulary in `prompt.md` |

<details>
<summary>Answer key (open after your run)</summary>

| Item | Status | Why |
|---|---|---|
| `ENT-A` | `pass` | Clean reference: valid same-market 2025 GO applied to its own site, both Scope 2 figures present (location-based 840 t, market-based 432 t), all factors within age and units reconciled. Marking it down for 'possible' issues is too harsh. |
| `ENT-B` | `blocked` | Has a valid, retired, same-market 2025 GO and a residual-mix factor, so a market-based figure looks complete, but the site has no grid-average location_factor. Scope 2 dual reporting is mandatory, so the scope2_dual_inputs PreToolUse hook blocks esg_scope2_dual_report: a market-based-only Scope 2 is not assessable. |
| `ENT-C` | `fail` | The REC is retired and covers 100% of consumption, which would make market-based Scope 2 zero, but its vintage (2022) does not match reporting year 2025 and its market (GRID-WEST) differs from the site's market (GRID-NORTH). instrument_issues = 2, so the instrument_integrity gate fails the item; market-based falls back to the residual mix (576 t), not 0. |
| `ENT-D` | `fail` | Factors carry full provenance and the diesel line reconciles, but the electricity line reports 1.84 tCO2e for 4,600 MWh at 0.4 kg CO2e/kWh. Activity x factor after MWh-to-kWh conversion is 1,840 t: a kWh/MWh (factor 1,000) slip. unit_mismatches = 1 fails the factor_register_clean gate. |
| `SC3-CAT3` | `fail` | Screening is complete (all 15 categories addressed, exclusions justified), so the item looks clean, but ENT-A's location-based grid factor already includes T&D losses (location_factors_include_td_losses = true). The cat 3 td_losses line (72 t) counts them twice; double_counts = 1 fails the no_double_counting gate. |
| `CLAIM-1` | `fail` | The second sentence (6% below base year) is fine, and offsets are quantified and retired, but 'carbon neutral' rests entirely on 12,400 t of credits against 12,400 t gross emissions. The anti_greenwashing gate blocks the claim; the fix is to report gross emissions and disclose credits separately. |

All 6 correct counts as PASS. Missing any trap item (`ENT-A`, `ENT-B`, `ENT-C`, `ENT-D`, `SC3-CAT3`, `CLAIM-1`) is a FAIL even if the rest are right.

</details>

## Reflect

- Which item did you get wrong in step 3, and which number or field misled you?
- Pick one trap item, edit its record in `demo-input/` so the deciding check passes, and predict the new status before you rerun. Did the tool agree?
- Where did the run's evidence come from a tool result, and where from the model's own reading? Which of those would you show an auditor?

## Troubleshooting

| Symptom | Fix |
|---|---|
| `domains:esg` is missing | Run `tokn license trial`, then `tokn license features`. |
| The domain tools are not called | Confirm `--mode esg`. Other modes do not load these tools. |
| The run stops at the step limit | Increase `--max-steps`. |
| No model response | Check `NOSPACE_MODEL_PROVIDER`, `NOSPACE_MODEL_NAME` and your key. See [../../SETUP.md](../../SETUP.md). |
