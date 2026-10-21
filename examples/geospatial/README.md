# Example: CRS, cloud-mask and resolution gates on a synthetic change study

This walkthrough runs TOKN's **geospatial** domain on a small synthetic study.
The inputs are built so that several gates should fire. You can see each gate
block or flag a step, and read the message it gives back.

> *Summarise change in a fictional reserve from 2014 to 2024, measuring area
> and distance, and compare a 10 m scene with a 250 m context layer.*

| Gate (PreToolUse unless noted) | Triggered by in this example |
|---|---|
| `validate_area_crs` | Area of the boundary in EPSG:4326; distance on the road in EPSG:3857 |
| `enforce_cloud_mask` | Optical analysis on the cloudy Landsat scene with no mask applied |
| `validate_resolution_compat` | 10 m scene compared with the 250 m context layer (25× ratio) |
| `validate_crs_input` | Every load and measurement call must name a valid EPSG code |
| Temporal window (PostToolUse, `validate_temporal_window`) | 2014 baseline against 2024 current (10-year gap) |

Other geospatial gates (`enforce_datum_provenance`, `enforce_band_harmonization`)
are not exercised here. The inputs contain no datum mixing and no multi-sensor band stack.

All data in `inputs/` is synthetic. "Maple Hollow Reserve" is fictional.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with these inputs' domain behaviour | `tokn version` |
| 14-day trial **or** a domain tier | Domain modes (`--mode geospatial`) need the trial. Community grants only `domains:basic`. | `tokn license trial`, then `tokn license features` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |

> **Tier.** Run `tokn license trial` once per machine to start the 14-day
> full-feature trial. After it ends, `--mode geospatial` falls back to
> Community and the domain gates are not loaded.

> **What leaves your machine.** The model provider receives the prompt and any
> file the agent reads from `inputs/`. These files are synthetic. Nothing else is
> sent. The stdlib checker in step 6 reads only your local output file.

## 1. Go to the example folder

macOS / Linux:

```bash
cd examples/geospatial
```

Windows PowerShell:

```powershell
Set-Location examples\geospatial
```

You now have:

```text
geospatial/
  prompt.md                 # the task
  inputs/aoi.geojson        # study boundary, stated CRS EPSG:4326
  inputs/roads_3857.geojson # access road, stated CRS EPSG:3857
  inputs/scenes.csv         # scene metadata: sensor, CRS, resolution, cloud mask flags
  check_output.py           # optional read-only checker (Python stdlib)
```

## 2. Start the trial

macOS / Linux / PowerShell:

```bash
tokn license trial
tokn license features
```

`features` should list the geospatial domain. If it does not, stop and check
the Troubleshooting table.

## 3. Configure the LLM

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

## 4. Run the study

Run from `examples/geospatial`. The run saves its text output so the checker can read it.

macOS / Linux:

```bash
tokn agent-run --mode geospatial --prompt-file prompt.md --repo-root . \
  --max-steps 25 --output-format text 2>&1 | tee run-output.txt
```

Windows PowerShell:

```powershell
tokn agent-run --mode geospatial --prompt-file prompt.md --repo-root . `
  --max-steps 25 --output-format text 2>&1 | Tee-Object -FilePath run-output.txt
```

Flags used:

| Flag | Meaning |
|---|---|
| `--mode geospatial` | Loads the geospatial domain's tools, hooks and gates |
| `--prompt-file prompt.md` | The task, read from this file |
| `--repo-root .` | Limits file access to this folder |
| `--max-steps 25` | Stops the run after 25 agent steps |
| `--output-format text` | Plain text output, which the checker can read |

If you want to skip interactive confirmations, add `--no-confirm`. This example
does not need it. The agent only reads `inputs/`.

## 5. Check the result

Expected gate outcomes are taken from the domain's hooks and error messages in
`environment-manager/internal/agent/domains/geospatial/`. They are not a recorded
run.

| Step in `prompt.md` | Expected gate behaviour | Message to look for |
|---|---|---|
| 2. Area of the boundary | Blocked: area computed in a geographic CRS | `GEOGRAPHIC CRS FOR MEASUREMENT` |
| 2. Length of the road | Blocked: distance in Web Mercator. The same hook covers distance and area. | `WEB MERCATOR FOR AREA` |
| 3. Cloudy Landsat scene | Blocked: optical analysis with no cloud mask | `CLOUD MASK REQUIRED` |
| 3. Cloudy Landsat scene | Not a hook in v0.3.57. The 34% cover is above the 20% default, so the agent should report it. | `CLOUD COVER EXCEEDED` (only if the validator is called) |
| 4. 10 m scene against 250 m layer | Blocked: resolution ratio above 10× | `RESOLUTION MISMATCH` |
| 5. 2014 baseline vs 2024 current | Gap of 10 years, above the 5-year default. No hook blocks this in v0.3.57; the agent must report it. | `TEMPORAL GAP EXCEEDED` (if the validator is called) |

The Web Mercator line is the trap in this example. The boundary is measured
in a geographic CRS, and the road is in Web Mercator. Both should be blocked
for measurement.

Run the optional checker, which reads only the local `run-output.txt`:

macOS / Linux / PowerShell:

```bash
python check_output.py run-output.txt
```

It prints `SEEN` or `not seen` for each marker. `not seen` means the step did
not run, not that the gate passed. Read the summary too.

## 6. What to look for

- **Blocked steps are not invented.** The agent should say a step was blocked
  and name the data it needs. It should not produce an area or distance figure
  for a blocked step.
- **CRS is named every time.** Each figure should state units and CRS.
- **Cloudy scene is excluded.** The agent should use the masked Sentinel-2 scene
  for change detection, not the Landsat scene with no mask.
- **Temporal gap is reported.** Even without a hard block, a 10-year gap should
  be stated in the summary.
- **Output is labelled synthetic.** The summary should not read as a real
  land-use finding.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `tokn: your 14-day trial has ended` | Trial expired | Trials are one per machine, so `tokn license trial` will not restart it. Domain modes need a domain tier. |
| `--mode geospatial` is not accepted | Older binary | Check `tokn version` is v0.3.57 or newer. |
| `tokn license features` does not list geospatial | No trial or domain tier | Run `tokn license trial` once per machine. |
| Agent never calls area or distance tools | Prompt not read | Confirm `--prompt-file prompt.md` path and that you run from `examples/geospatial`. |
| No gate message in `run-output.txt` | Wrong output format or redirection | Use `--output-format text` and the `tee` / `Tee-Object` command from step 4. |
| Checker says `No such file` | Run file not created in this folder | Run step 4 from `examples/geospatial`. |
| Model call fails with an auth error | Key not set in this shell | Re-run the step 3 exports in the same terminal. |
