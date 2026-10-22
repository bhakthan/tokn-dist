# Example: Open Knowledge Format (OKF) Bundles

> "Export what the team knows about the pump station as a portable bundle, check it, and answer questions from it in a fresh session."

The Open Knowledge Format is a plain-markdown way to package knowledge: each concept is a `.md` file with a small YAML header that says what it is, who made it, who checked it, and where it came from. TOKN can validate a bundle, import it into a local RDF dataset, export it back out, migrate v0.1 bundles to v0.2, and query the imported knowledge with SPARQL.

| Capability | What it does here |
|---|---|
| `okf_validate` | Checks a bundle folder against the OKF structure rules. Reports errors and warnings. |
| `okf_import` | Loads a bundle into a named RDF dataset. |
| `okf_export` | Writes an RDF dataset back out as an OKF bundle. |
| `okf_migrate` | Lifts v0.1 `timestamp` and `# Citations` into v0.2 fields. Dry run unless you pass an output folder. |
| `rdf_query` | Runs SPARQL against a named dataset, so the agent can answer from imported knowledge. |
| `check_bundle.py` | Offline, standard-library Python. Checks the bundle folders for required structure. Reads local files only. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The OKF and RDF agent tools ship in this line. | `tokn version` |
| Community tier (no license needed) | The OKF tools are not behind a license feature check. | `tokn license features` |
| Python 3.8+ (optional) | Runs the offline checker. No packages to install. | `python --version` |
| An LLM provider | The agent calls the OKF tools through a model. | See [../../SETUP.md](../../SETUP.md) |
| RDF enabled | The import, export and query tools are registered unless RDF is disabled. | `NOSPACE_RDF_DISABLE` is unset or not `1` |

Configure the LLM with placeholders. Replace each one with your own value.

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<a model you have access to>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<a model you have access to>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

**What leaves your machine:** the prompts you send, the bundle markdown the agent reads through the OKF tools, and tool results. These go to the LLM provider you configure. The bundles here are synthetic. Datasets are stored locally under your TOKN home folder (`~/.nospace/rdf`, or `NOSPACE_RDF_DIR` if set).

## 1. Copy the example to a scratch folder

Run the walkthrough outside this repo. The import and export steps write files and a local dataset.

```bash
cp -r examples/knowledge-bundles ~/okf-run   # any scratch folder you own
cd ~/okf-run
```

```powershell
Copy-Item -Recurse examples\knowledge-bundles $HOME\okf-run
Set-Location $HOME\okf-run
```

## 2. Know the bundle format

A bundle is a folder of markdown files. Each concept file starts with a YAML block between `---` lines.

| Part | Rule |
|---|---|
| Root `index.md` | Its frontmatter may hold only `okf_version: 0.2`. |
| Concept `.md` file | Needs a frontmatter block with a non-empty `type`. |
| `generated` | Who produced the concept and when. Actor form: `human:<id>`, `process:<id>`, or `<producer>/<version>`. |
| `verified` | A list of `by` and `at` stamps from people or processes that checked the concept. |
| `sources` | Where the knowledge came from: `id`, `resource`, and optional `title`. |
| `stale_after` | An optional date after which the concept should be re-checked. |
| `log.md` | Optional. Each date heading must be ISO `YYYY-MM-DD`. |

Trust is a derived label, not a stored field. The tool reads `verified`: a `human:` verifier gives a human-reviewed label, another verifier gives machine-confirmed, and no verifier gives unverified. The source does not show a fail-closed gate on this label, so this walkthrough does not treat it as access control.

The folder `bundle-valid/` is a hand-written v0.2 bundle with two concepts. The folder `bundle-broken/` is a copy with two deliberate problems. The folder `bundle-v01/` is a small v0.1 bundle for the migration step.

## 3. Validate the valid and broken bundles

Ask the agent to run the validator on both folders. Use a single-quoted prompt in bash and PowerShell.

```bash
tokn agent-run --repo-root . --max-steps 6 \
  --prompt 'Call okf_validate on path bundle-valid, then on path bundle-broken. Report every error and warning verbatim, one line each.'
```

```powershell
tokn agent-run --repo-root . --max-steps 6 `
  --prompt 'Call okf_validate on path bundle-valid, then on path bundle-broken. Report every error and warning verbatim, one line each.'
```

The same check runs offline without any model call:

```bash
python check_bundle.py bundle-valid bundle-broken
```

```powershell
python check_bundle.py bundle-valid bundle-broken
```

**Expected, not a recorded run:**

- `bundle-valid`: no errors. The agent reports no blocking findings.
- `bundle-broken`: one error on `pump-shutdown-checklist.md`, which has no `type`. The validator says the frontmatter is missing a required non-empty `type`.
- `bundle-broken`: one warning on `rain-gauge-calibration.md`, whose `verified` stamp has no `at` time. Warnings do not fail validation.

Missing provenance or a missing `verified` time is not a hard failure in OKF. It is a warning that tells you the record is weaker than it looks. Hard failures are structural: unparseable frontmatter, a missing `type`, and reserved files in the wrong shape.

The offline checker reports the same `type` error as `FAIL` for `bundle-broken`, and `PASS` for `bundle-valid`. It does not check the `verified` warning.

## 4. Import the valid bundle and answer from it

Import into a dataset name you choose, then ask a question in a new session. The dataset persists on disk, so the new session still has the knowledge.

```bash
tokn agent-run --repo-root . --max-steps 8 \
  --prompt 'Call okf_import with dataset pump-demo and path bundle-valid. Then call rdf_query on dataset pump-demo to list the steps of the pump station shutdown checklist. Answer from that query result only.'
```

```powershell
tokn agent-run --repo-root . --max-steps 8 `
  --prompt 'Call okf_import with dataset pump-demo and path bundle-valid. Then call rdf_query on dataset pump-demo to list the steps of the pump station shutdown checklist. Answer from that query result only.'
```

**Expected, not a recorded run:** the agent lists the four shutdown steps in order: the low-float check, the breaker lock-out, closing the discharge valve before the isolation valve, and logging the time. The answer should cite the query result, not general knowledge.

## 5. Migrate the v0.1 bundle to v0.2

The v0.1 sample has a `timestamp` field and a `# Citations` list in the body. Migration moves the timestamp into `generated.at`, attributes it to the actor you name, and turns the citation list into `sources`.

Run a dry run first. The tool reports the changes and writes nothing when no output folder is given.

```bash
tokn agent-run --repo-root . --max-steps 6 \
  --prompt 'Call okf_migrate on path bundle-v01 with generated_by human:example-reviewer and no out (dry run). Report what would change.'
```

```powershell
tokn agent-run --repo-root . --max-steps 6 `
  --prompt 'Call okf_migrate on path bundle-v01 with generated_by human:example-reviewer and no out (dry run). Report what would change.'
```

Then write the result to a new folder and check it:

```bash
tokn agent-run --repo-root . --max-steps 6 \
  --prompt 'Call okf_migrate on path bundle-v01 with generated_by human:example-reviewer and out bundle-v02-migrated. Report what was written.'
python check_bundle.py bundle-v02-migrated
```

```powershell
tokn agent-run --repo-root . --max-steps 6 `
  --prompt 'Call okf_migrate on path bundle-v01 with generated_by human:example-reviewer and out bundle-v02-migrated. Report what was written.'
python check_bundle.py bundle-v02-migrated
```

**Expected, not a recorded run:** the dry run reports one timestamp lifted and two citations converted. The written bundle has `generated.at: 2025-11-04T08:12:00Z`, `generated.by: human:example-reviewer`, a `sources` list with the two URLs, and no `# Citations` section. If you omit `generated_by`, the tool leaves the old `timestamp` in place rather than invent who produced it.

## 6. Export the dataset and bridge to RDF

The bridge runs both ways. Imported bundles become RDF triples in a named dataset, and `okf_export` reads concepts from that dataset back out as a bundle. You can also query the triples directly with SPARQL. For SPARQL and reasoning over the same data, see [../ontology-sparql/](../ontology-sparql/) (being written; not in this repo yet).

```bash
tokn agent-run --repo-root . --max-steps 8 \
  --prompt 'Call okf_export with dataset pump-demo and out exported-bundle. Then call okf_validate on path exported-bundle and report the result.'
```

```powershell
tokn agent-run --repo-root . --max-steps 8 `
  --prompt 'Call okf_export with dataset pump-demo and out exported-bundle. Then call okf_validate on path exported-bundle and report the result.'
```

**Expected, not a recorded run:** the export writes concept files under `exported-bundle/`, and the validator reports no errors. If the dataset has no concepts, export returns a `no_concepts` result instead of an empty bundle. Export does not read agent-run sessions. Its input is always an RDF dataset.

## 7. Peer exchange (brief)

Bundles are meant to move between TOKN installs and other OKF tools. For how peers exchange them, see [../federation/](../federation/) and [../peer-collab/](../peer-collab/). This walkthrough does not run a peer exchange.

## What to look for

- A bundle is a folder of markdown with simple frontmatter. You can read and diff it without TOKN.
- Validation separates hard errors (the bundle is malformed) from warnings (the record is weaker than it should be).
- Trust comes from `verified` stamps. An unverified concept is labelled as such. The label does not hide the concept.
- Migration never invents provenance. If you do not name a `generated_by`, it does not guess one.
- The same dataset answers questions in a new session, because it persists on disk.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `okf_validate` or `okf_import` is not offered to the agent | RDF is disabled in your environment. | Unset `NOSPACE_RDF_DISABLE`, or set it to something other than `1`. Then retry. |
| `okf_migrate` reports `invalid_actor` | The `generated_by` value is not in an accepted form. | Use `human:<id>`, `process:<id>`, or `<producer>/<version>`. |
| `okf_export` returns `no_concepts` | The dataset has no concepts with the OKF subject type. | Run `okf_import` on the bundle first, with the same dataset name. |
| `python check_bundle.py` reports `no leading --- frontmatter block` | The file starts with a blank line or lacks the opening `---`. | The frontmatter must be the first thing in the file. |
| Checker says `not a directory` | You ran it from the wrong folder. | Run it from the scratch copy, where the bundle folders sit. |
| `tokn version` is older than v0.3.57 | The OKF tools may not be in your build. | Update TOKN, then retry. |
