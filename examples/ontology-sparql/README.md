# Example: Ontology and SPARQL on a Synthetic Plant

> "Load a small plant ontology, ask it questions in SPARQL, show what reasoning adds, then let the agent answer a question by querying the graph."

A plain agent can guess at structure it has not read. This walkthrough gives TOKN a small RDF graph of a fictional wind-and-pump plant. You load it into TOKN's embedded triplestore, query it with SPARQL 1.1, run the reasoner, and watch which answers appear only after inference. Then an agent answers a question by calling the graph tools. Everything is synthetic.

| Capability | What you see |
|---|---|
| Embedded triplestore | `/rdf load` parses a Turtle file into a named dataset, saved locally. |
| SPARQL 1.1 engine | `/rdf query` runs SELECT and ASK, with FILTER, GROUP BY, and COUNT. |
| RDFS / OWL-lite reasoner | `/rdf reason` adds subclass, subproperty, domain, transitive, and inverse triples. |
| Before and after | Two queries return different rows before and after `/rdf reason`. |
| Agent tools | The agent calls `rdf_load`, `rdf_query`, and `rdf_reason` during `tokn agent-run`. |
| Warehouse connectors (optional) | `/warehouse` and the `query_warehouse` tool read from Snowflake or Fabric. Read-only by default. Not connected to the triplestore. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The RDF commands and tools shown here ship in this version. | `tokn version` |
| Community tier (no trial) | The RDF store, SPARQL engine, reasoner, and warehouse tools are not gated by a license feature. | `tokn agent-repl` starts and `/rdf` lists |
| An LLM provider (step 6 only) | The agent step calls a model. Steps 1 to 5 and 7 do not. | See [../../SETUP.md](../../SETUP.md) |
| Python 3.9+ (step 7 only) | Runs the offline checker. Standard library only. | `python --version` |
| Warehouse account (optional) | Only for the warehouse section. Not needed for the core walkthrough. | See section 8 |

**What leaves your machine:** Steps 1 to 5 and 7 stay on your machine. The dataset is saved under your local TOKN RDF directory (default `~/.nospace/rdf`). The agent step (step 6) sends your prompt and tool results to the LLM provider you configure. The optional warehouse section sends SQL to the warehouse endpoint you configure. Nothing else leaves the machine. The data in this example is synthetic.

## 1. Go to the example folder

Run everything from this folder so the relative paths in the commands resolve.

```bash
cd examples/ontology-sparql
```

```powershell
Set-Location examples\ontology-sparql
```

The folder contains `data/plant.ttl`, five queries in `queries/`, `prompt.md`, `expected_answers.json`, and `check_walkthrough.py`.

## 2. Read the ontology

Open `data/plant.ttl`. It declares these constructs, and each one is a reasoner rule that TOKN implements:

| Construct in the file | What the reasoner does with it |
|---|---|
| `rdfs:subClassOf` (Turbine, Pump, Component under Asset; Gearbox, Generator, Motor under Component) | Types each instance with every superclass. |
| `rdfs:subPropertyOf` (`:hasComponent` under `:hasPart`) | Copies each `:hasComponent` triple to `:hasPart`. |
| `rdfs:domain` and `rdfs:range` (`:hasPart`, `:locatedIn`) | Types the subject and object of each use. |
| `owl:inverseOf` (`:partOf` and `:hasPart`) | Adds the reverse triple. |
| `owl:TransitiveProperty` (`:locatedIn`) | Chains `locatedIn` links. |

The file uses no OWL restrictions, cardinality, or `owl:hasValue`. The reasoner does not implement those, so the example avoids them.

## 3. Start the REPL and load the data

```bash
tokn agent-repl
```

Inside the REPL, load the file as the dataset `plant`:

```
/rdf load plant data/plant.ttl
/rdf datasets
```

The file extension `.ttl` selects the Turtle parser. Dataset names may not contain `/`, `\`, or `..`.

## 4. Query before reasoning

Each query is one line. Paste the line after `/rdf query plant`. The text matches `queries/*.rq`.

```
/rdf query plant PREFIX : <http://example.org/plant#> SELECT ?turbine ?kw WHERE { ?turbine a :Turbine ; :ratedPowerKW ?kw . FILTER(?kw > 2000) } ORDER BY ?turbine
/rdf query plant PREFIX : <http://example.org/plant#> SELECT ?site (COUNT(?turbine) AS ?turbines) WHERE { ?turbine a :Turbine ; :locatedIn ?site } GROUP BY ?site ORDER BY ?site
/rdf query plant PREFIX : <http://example.org/plant#> ASK { :PU-02 :hasComponent ?m . ?m a :Motor }
```

Expected results are in `expected_answers.json`. Run the 04 and 05 queries now as well. They return nothing yet:

```
/rdf query plant PREFIX : <http://example.org/plant#> SELECT ?asset WHERE { ?asset a :Asset ; :locatedIn :SiteNorth } ORDER BY ?asset
/rdf query plant PREFIX : <http://example.org/plant#> SELECT ?part WHERE { :WT-01 :hasPart ?part } ORDER BY ?part
```

## 5. Reason, then compare

Run the reasoner. It saves the inferred triples into the dataset and records them in a provenance graph.

```
/rdf reason plant
```

Run the same 04 and 05 queries again. They now return rows:

```
/rdf query plant PREFIX : <http://example.org/plant#> SELECT ?asset WHERE { ?asset a :Asset ; :locatedIn :SiteNorth } ORDER BY ?asset
/rdf query plant PREFIX : <http://example.org/plant#> SELECT ?part WHERE { :WT-01 :hasPart ?part } ORDER BY ?part
```

## 6. Let the agent answer from the graph

Configure the LLM with placeholders. Replace each one with your own value. See [../../SETUP.md](../../SETUP.md) for other providers.

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME=<your model name>
export ANTHROPIC_API_KEY=<your key>
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME = "<your model name>"
$env:ANTHROPIC_API_KEY = "<your key>"
```

Run the agent with the prompt in `prompt.md`:

```bash
tokn agent-run --repo-root . --prompt-file prompt.md --no-confirm --max-steps 8
```

```powershell
tokn agent-run --repo-root . --prompt-file prompt.md --no-confirm --max-steps 8
```

The prompt asks the agent to load `data/plant.ttl` as `plant`, then query it. The agent should call `rdf_load`, then `rdf_query` (and `rdf_reason` if it needs inferred triples). `--no-confirm` auto-approves tool calls, so use it only on this copy. Watch the tool calls in the output to confirm the agent queried the graph rather than answering from memory.

## 7. Check the walkthrough offline

This step only reads local files. It checks the data, the query files, and the expected answers.

```bash
python check_walkthrough.py
```

```powershell
python check_walkthrough.py
```

The checker counts the triples in `data/plant.ttl` and confirms that each query file is one line with a valid SELECT or ASK form. It does not run SPARQL. `expected_answers.json` is a hand-computed expectation, not a recorded run.

## 8. Optional: warehouse connectors

The warehouse connectors are a separate feature from the triplestore. Warehouse data is not loaded into the RDF graph. Use this section only if you have a Snowflake or Fabric account. Replace every placeholder. Never paste real credentials into a file you commit.

| Backend | Environment variables | Auth |
|---|---|---|
| Snowflake | `SNOWFLAKE_ACCOUNT=<your-account>`, `SNOWFLAKE_USER=<your-user>`, `SNOWFLAKE_WAREHOUSE=<your-warehouse>`, `SNOWFLAKE_DATABASE=<your-database>`, `SNOWFLAKE_SCHEMA=<your-schema>`, `SNOWFLAKE_ROLE=<your-role>` | Preferred: key-pair. Set `SNOWFLAKE_PRIVATE_KEY=@<path to your .p8 key file>`. Set `SNOWFLAKE_PRIVATE_KEY_PWD` only if the key is encrypted. |
| Fabric | `FABRIC_SERVER=<your-server>`, `FABRIC_DATABASE=<your-database>` | Preferred: Entra ID. Run `az login` so the default Azure credential applies. Or set `FABRIC_ACCESS_TOKEN=<your token>` for a short-lived token. |

Shared settings: `WAREHOUSE_BACKEND` selects the backend. Run `/warehouse setup` inside `tokn agent-repl` to see the accepted values and the missing settings. `WAREHOUSE_MAX_ROWS` (default 1000) caps rows returned. `WAREHOUSE_TIMEOUT_SECONDS` sets the query timeout. `WAREHOUSE_ENABLE=1` forces the tools on when no backend is configured.

Inside `tokn agent-repl`:

```
/warehouse status
/warehouse describe <your-table>
/warehouse query SELECT COUNT(*) FROM <your-table>
```

**Guardrails:** queries are read-only by default. Statements such as INSERT, UPDATE, DELETE, MERGE, and CREATE are blocked unless you set `WAREHOUSE_ALLOW_WRITE=1`. Do not set it for this walkthrough.

**What leaves your machine:** each `/warehouse` query sends its SQL to your Snowflake or Fabric endpoint, and the result rows come back to your machine. Choose a read-only role.

## What to look for

- **Step 4 vs step 5:** queries 04 and 05 return no rows before `/rdf reason` and rows after it. Every extra row is an inferred fact.
- **Hall-N1 in query 04:** Hall-N1 is not an Asset in the data, but `:locatedIn` has `rdfs:domain :Asset`. So the reasoner types Hall-N1 as an Asset. This is a good check on whether your domain axioms say what you meant.
- **PU-01 in query 04:** PU-01 is in SiteNorth only through `:locatedIn` transitivity (PU-01 to Hall-N1 to SiteNorth).
- **Query 05:** `:WT-01 :hasPart ?part` returns the components because `:hasComponent` is a sub-property of `:hasPart`.
- **Agent step:** the agent's answer should match the rows from steps 4 and 5. If it does not, check which tools it called.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/rdf` is unknown or the RDF tools are missing | Check `NOSPACE_RDF_DISABLE` is not set to `1`. Unset it and restart TOKN. |
| `/rdf load` cannot find the file | Start `tokn agent-repl` from this folder, or use an absolute path to `data/plant.ttl`. |
| `/rdf query` returns nothing for 04 or 05 | Did you run `/rdf reason plant` first? Check with `/rdf datasets`. |
| Query text fails to parse | Keep each query on one line and include the `PREFIX :` line. Copy it exactly from step 4. |
| Dataset name rejected | Use a plain name with no `/`, `\`, or `..`. |
| `/warehouse` says it is not configured | Set the backend variables in section 8. Run `/warehouse setup` to see what is missing. |
| Warehouse write refused | Expected. Writes are blocked by default. Use a read-only role. |
| `agent-run` fails before calling a model | Check the three `NOSPACE_MODEL_*` and `ANTHROPIC_API_KEY` values from step 6. See [../../SETUP.md](../../SETUP.md). |
| Checker reports a count mismatch | Someone edited `data/plant.ttl`. Recompute the expected answers by hand and update `expected_answers.json`. |
