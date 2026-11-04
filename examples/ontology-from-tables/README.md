# Example: an ontology from your tables

TOKN can read a set of tables and propose an **ontology**: the things your data
is about, their attributes, and how they relate. Every claim carries evidence
and a confidence score. Nothing the data does not support becomes a link. You
review the proposals, accept or reject them, and export the result as OWL,
R2RML, JSON-LD, a Mermaid ER diagram, or a Fabric / Power BI semantic model
(TMDL).

> *A small vehicle-service workshop keeps its records in nine tables. What
> are the business concepts, and how do you join a part to the customer who
> paid for it?*

| Feature | What it does here |
|---|---|
| **`tokn ontology build`** | Profiles every table, finds keys and links, and classifies each table as an entity, a lookup, a junction or a variant. |
| **`tokn ontology review`** | Lists what still needs a human decision, weakest first. |
| **`tokn ontology certify`** | Records your accept / reject decisions. They survive rebuilds. |
| **`tokn ontology join-path`** | The shortest join between two concepts, with its SQL. |
| **`tokn ontology export`** | Prints one artifact (Turtle, R2RML, JSON-LD, Mermaid or JSON). |

The same nine tables are provided four ways: CSV files, a SQLite database,
Parquet files, and SQL scripts for PostgreSQL or MySQL. You can follow any
path. The CSV path needs nothing but TOKN.

All data is synthetic. The people, companies and plates are invented.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.77 or newer** | `tokn ontology` and the classification fixes used here | `tokn version` |
| Licence tier | `tokn ontology` is **Community**; no trial needed | `tokn license features` |

**Optional, only for some paths:**

| Requirement | Used by | Check |
|---|---|---|
| Python 3.9+ | Step 7 (builds `workshop.db`) and step 9 (Parquet) | `python --version` |
| `pyarrow` | Step 9 only | `python -c "import pyarrow"` |
| Docker | Step 8 (PostgreSQL / MySQL in a container) | `docker version` |
| A local model (Ollama, GGUF) | Step 11, `--enrich` only | `ollama list` |

Install commands, if a check fails:

| Piece | Windows | macOS | Linux (Debian/Ubuntu) |
|---|---|---|---|
| Python 3 | `winget install Python.Python.3.12` | `brew install python@3.12` | `sudo apt-get install -y python3 python3-pip` |
| pyarrow | `python -m pip install pyarrow` | `python3 -m pip install pyarrow` | `python3 -m pip install pyarrow` |
| Docker | `winget install Docker.DockerDesktop` | `brew install --cask docker` | `sudo apt-get install -y docker.io` |

> **What leaves your machine.** Nothing, for steps 1 to 10. Sources are opened
> read-only, profiling happens in memory, and every file is written inside the
> `--out` folder you name. Step 11 (`--enrich`) sends table and column names,
> and with `full` some statistics, to the model provider you choose. Values of
> columns that look like personal data (emails, phone numbers) are never sent.
> With a local model, nothing leaves the machine at all.

All commands below run from this folder:

```bash
cd examples/ontology-from-tables
```

## 1. Look at the data

| Table | Rows | What it holds |
|---|---:|---|
| `customers` | 14 | Name, email, city |
| `vehicles` | 20 | Make, model, year, plate; owned by a customer |
| `technicians` | 7 | Name and grade |
| `suppliers` | 4 | Company name, contact email, country |
| `parts` | 12 | Part name and price; bought from a supplier |
| `work_order_status` | 4 | A code list: `OPEN`, `IN_PROGRESS`, `DONE`, `CANCELLED` |
| `work_orders` | 40 | One visit of a vehicle. Two links to `technicians`: who did the work, and who inspected it |
| `work_order_parts` | 73 | Which parts each work order used. Only two key columns |
| `stg_work_orders` | 8 | A staging extract: 4 of the 7 `work_orders` columns |

The CSV files declare no keys. TOKN has to discover them. The table set is
small, but it contains the four shapes the classifier must tell apart: plain
**entities**, a **lookup** code list, a **junction** table, and a staging
**variant** of a real table. It also has a role-played link: two columns in
`work_orders` point at the same `technicians` table.

## 2. Build from a set of CSV files

```bash
tokn ontology build --source csv:data --out out/csv
```

```text
ontology written to out/csv
  classes 6, data properties 22, object properties 7, enumerations 1; 14 proposed for review
  next: tokn ontology review
```

What TOKN decided:

| Table | Became | Why |
|---|---|---|
| customers, vehicles, technicians, suppliers, parts, work_orders | **6 classes** | Things with their own identity |
| work_order_status | **1 enumeration** (SKOS concept scheme) | Small, a code-like key, few descriptive columns, referenced by other tables |
| work_order_parts | **a many-to-many link** `has parts` | Its key is made only of two foreign keys |
| stg_work_orders | **no new class**; mapped onto Work Order | Its name is `work_orders` plus `stg_`, and all its columns exist there |

Small tables are not automatically lookups. `technicians` (7 rows) and
`suppliers` (4 rows) stay classes, because a person's name or a contact email
marks real-world things, not codes.

A link becomes an object property only when the data agrees. TOKN checks that
every value of `work_orders.vehicle_id` exists in `vehicles.vehicle_id`
(containment). The two technician columns become two separate links,
`assigned technician` and `inspected by technician`.

## 3. Read what was written

```text
out/csv/
  ontology.json      canonical result, with evidence and confidence for every element
  ontology.ttl       OWL 2 + SKOS, in Turtle
  r2rml.ttl          W3C R2RML mapping: how each table and column maps to the ontology
  ontology.jsonld    JSON-LD
  er.mmd             Mermaid ER diagram
  tmdl/              Fabric / Power BI semantic model (TMDL folder)
  report.md          coverage, validation, and the review queue
```

Start with `report.md`. Paste `er.mmd` into any Mermaid viewer (GitHub renders
it in a fenced `mermaid` block) to see the diagram. Part of it:

```mermaid
erDiagram
    Vehicle {
        int vehicle_id PK
        int customer_id FK
        string make
        string model
        int model_year
        string plate
    }
    Supplier {
        int supplier_id PK
        string supplier_name
        string contact_email
        string country_code
    }
```

## 4. Review, then certify

```bash
tokn ontology review --out out/csv
```

```text
0.80  enumeration      enum_a3e31c9d0d59  Work Order Status  [work_order_status]
0.89  object_property  op_5477fdaa5e1e  inspected by technician  [work_orders(inspected_by_technician_id) -> technicians(technician_id)]
0.89  object_property  op_784a2a343a4b  assigned technician  [work_orders(assigned_technician_id) -> technicians(technician_id)]
0.90  data_property    dp_0a92c8d5402a  technician id  [technicians.technician_id]
...
0.95  object_property  op_f3dcd52ed2b4  vehicle  [work_orders(vehicle_id) -> vehicles(vehicle_id)]

14 proposed. Decide with: tokn ontology certify --accept <id> --reject <id>
```

Everything here was inferred, not declared, so it waits for you. The lowest
confidence comes first. IDs are derived from table and column names, so yours
match the ones above.

Accept the two technician roles, and reject a property you do not want to
publish:

```bash
tokn ontology certify --out out/csv --accept op_784a2a343a4b --accept op_5477fdaa5e1e --reject dp_0a92c8d5402a
tokn ontology build --source csv:data --out out/csv
```

```text
recorded 2 accepted, 1 rejected in out/csv/ontology.overrides.yaml
re-run `tokn ontology build` to apply
ontology written to out/csv
  classes 6, data properties 22, object properties 7, enumerations 1; 11 proposed for review
```

Decisions live in `out/csv/ontology.overrides.yaml`, keyed by ID. It is plain
YAML you can commit and review. Run the build again with nothing changed and
TOKN does no work:

```text
ontology up to date in out/csv (use --force to rebuild)
```

**Check yourself.** Why is `stg_work_orders` not in the review list as a
class? (Answer: it is a variant. Its rows map onto the Work Order class in
`r2rml.ttl`, so it needs no class of its own.)

## 5. Ask for a join path

```bash
tokn ontology join-path --out out/csv Part Customer
```

```text
1. parts(part_id) -> work_order_parts(part_id)  [op_328e60787d64]
2. work_order_parts(work_order_id) -> work_orders(work_order_id)  [op_328e60787d64]
3. work_orders(vehicle_id) -> vehicles(vehicle_id)  [op_f3dcd52ed2b4]
4. vehicles(customer_id) -> customers(customer_id)  [op_016bfdc053cc]

FROM "parts"
JOIN "work_order_parts" ON "parts"."part_id" = "work_order_parts"."part_id"
JOIN "work_orders" ON "work_order_parts"."work_order_id" = "work_orders"."work_order_id"
JOIN "vehicles" ON "work_orders"."vehicle_id" = "vehicles"."vehicle_id"
JOIN "customers" ON "vehicles"."customer_id" = "customers"."customer_id"
```

Concepts can be named by label (`"Work Order"`) or by ID. Every hop names the
object property it used, so you can trace the SQL back to evidence.

## 6. One table, or a few

Point `csv:` at a single file:

```bash
tokn ontology build --source csv:data/work_orders.csv --out out/one
```

```text
  classes 1, data properties 7, object properties 0, enumerations 0; 1 proposed for review
```

With one table there is nothing to link to, so the foreign-key columns stay
plain data properties. To work on part of a folder or database, name the
tables instead:

```bash
tokn ontology build --source csv:data --tables work_orders,technicians,vehicles --out out/three
```

```text
  classes 3, data properties 13, object properties 3, enumerations 0; 6 proposed for review
```

`--tables` works the same for every source type.

### Declaring keys you already know

Inference is the fallback, not the only option. A CSV folder can carry an
optional `_schema.json` that declares keys. `keys/_schema.json` declares the
primary key and the four foreign keys of `work_orders`. Try it on a copy, so
`data/` stays as it was:

bash:

```bash
cp -r data data-keys && cp keys/_schema.json data-keys/
tokn ontology build --source csv:data-keys --out out/keys
```

PowerShell:

```powershell
Copy-Item data data-keys -Recurse; Copy-Item keys\_schema.json data-keys\
tokn ontology build --source csv:data-keys --out out/keys
```

```text
  classes 6, data properties 22, object properties 7, enumerations 1; 9 proposed for review
```

The four declared links are now accepted outright, so the queue drops from 14
to 9. Tables the file does not mention are still inferred.

## 7. A database: SQLite

`sql/schema.sql` declares every primary and foreign key. Build a SQLite file
from it (standard-library Python only):

```bash
python scripts/make_sqlite.py
tokn ontology build --source sqlite:workshop.db --out out/sqlite
```

```text
wrote .../workshop.db with 9 tables: customers, parts, stg_work_orders, ...
ontology written to out/sqlite
  classes 6, data properties 22, object properties 7, enumerations 1; 1 proposed for review
```

The ontology has the same shape as the CSV build, but only **one** item is
proposed: the Work Order Status enumeration, which is still a judgement call.
Declared keys are evidence, and declared evidence is accepted. The database is
opened read-only.

**Compare.** Put `out/csv/report.md` and `out/sqlite/report.md` side by side.
Where does each link's evidence say `declared`, and where `containment`?

## 8. A database: PostgreSQL or MySQL

The same SQL scripts load into either server. The commands below start a
throwaway container. Use your own server if you have one.

Keep credentials out of the command line and your shell history: put the
connection string in an environment variable and pass `env:NAME`.

**PostgreSQL**, bash:

```bash
docker run -d --name workshop-pg -e POSTGRES_PASSWORD=workshop -e POSTGRES_DB=workshop -p 5432:5432 postgres:16
sleep 10
cat sql/schema.sql sql/data.sql | docker exec -i workshop-pg psql -q -U postgres -d workshop -v ON_ERROR_STOP=1
export WORKSHOP_PG="postgres://postgres:workshop@localhost:5432/workshop?sslmode=disable"
tokn ontology build --source postgres:env:WORKSHOP_PG --out out/pg
```

PowerShell:

```powershell
docker run -d --name workshop-pg -e POSTGRES_PASSWORD=workshop -e POSTGRES_DB=workshop -p 5432:5432 postgres:16
Start-Sleep 10
Get-Content sql\schema.sql, sql\data.sql | docker exec -i workshop-pg psql -q -U postgres -d workshop -v ON_ERROR_STOP=1
$env:WORKSHOP_PG = "postgres://postgres:workshop@localhost:5432/workshop?sslmode=disable"
tokn ontology build --source postgres:env:WORKSHOP_PG --out out/pg
```

**MySQL**, bash (MySQL takes longer to start; repeat the load if it says it
cannot connect):

```bash
docker run -d --name workshop-my -e MYSQL_ROOT_PASSWORD=workshop -e MYSQL_DATABASE=workshop -p 3306:3306 mysql:8
sleep 30
cat sql/schema.sql sql/data.sql | docker exec -i workshop-my mysql -uroot -pworkshop workshop
export WORKSHOP_MY="root:workshop@tcp(localhost:3306)/workshop"
tokn ontology build --source mysql:env:WORKSHOP_MY --out out/mysql
```

PowerShell:

```powershell
docker run -d --name workshop-my -e MYSQL_ROOT_PASSWORD=workshop -e MYSQL_DATABASE=workshop -p 3306:3306 mysql:8
Start-Sleep 30
Get-Content sql\schema.sql, sql\data.sql | docker exec -i workshop-my mysql -uroot -pworkshop workshop
$env:WORKSHOP_MY = "root:workshop@tcp(localhost:3306)/workshop"
tokn ontology build --source mysql:env:WORKSHOP_MY --out out/mysql
```

Both give the same result as SQLite: 6 classes, 7 object properties, 1
enumeration, 1 proposed. If port 5432 or 3306 is already in use, change the
left side of `-p` (for example `-p 55432:5432`) and the port in the
connection string.

Clean up when done:

```bash
docker rm -f workshop-pg workshop-my
```

## 9. Parquet

```bash
python scripts/make_parquet.py
tokn ontology build --source parquet:parquet --out out/parquet
```

```text
wrote 9 parquet files to .../parquet
  classes 6, data properties 22, object properties 7, enumerations 1; 14 proposed for review
```

Parquet files, like CSV, carry column types but no keys, so the result matches
step 2. If `pyarrow` is missing, the script says so and prints the install
command.

## 10. Use the result elsewhere

| You want to… | Do this |
|---|---|
| Query the data as a knowledge graph in an external virtual-KG engine (Ontop, Morph-KGC, …) | Give it `r2rml.ttl` plus a connection to the same database |
| Open the model in Fabric or Power BI | Use the `tmdl/` folder (a TMDL semantic-model definition) |
| Load the ontology into TOKN's own RDF store and query it with SPARQL | Add `--rdf-dataset workshop` to `build`, then follow [ontology-sparql](../ontology-sparql/README.md) |
| Print one artifact to stdout | `tokn ontology export --out out/csv --format r2rml` (or `turtle`, `jsonld`, `mermaid`, `json`) |

```bash
tokn ontology build --source csv:data --out out/csv --rdf-dataset workshop --force
```

```text
  rdf dataset "workshop": 437 triples
```

**A TMDL folder is also a source.** `tmdl:` reads an existing Fabric or Power
BI semantic model:

```bash
tokn ontology build --source tmdl:out/csv/tmdl --out out/from-tmdl
```

TMDL holds metadata only: tables, columns and relationships, but no rows. So
relationships become declared links, and nothing can be profiled. Without row
counts TOKN cannot tell a code list from an entity, so every table except the
staging variant becomes a class (8 here), and the keyless junction table
produces warnings. That is expected.
Read a model this way to bootstrap an ontology, not to replace a build from
the data.

## 11. Optional: better names with a model

Labels like `work order id` come from column names. A model can propose
clearer labels and descriptions, break ties between candidate links the data
already verified, and suggest superclasses. It never creates a link.

```bash
tokn ontology build --source csv:data --out out/enriched --enrich=names-only --model-provider ollama --model-name qwen2.5:7b
```

`names-only` sends table and column names only. `--enrich` (full) also sends
column statistics and non-personal sample values. Model suggestions are marked
with `llm` evidence and stay **proposed** until you certify them.

## Troubleshooting

| You see | Do this |
|---|---|
| `unknown command "ontology"` | Upgrade TOKN to v0.3.77 or newer |
| A small people or company table became an enumeration | Check the table has a name, email or phone column. A key and one label column, with nothing else, is indistinguishable from a code list. Reject the enumeration with `certify --reject <id>`, or declare keys (step 6) |
| A link you expected is missing | The data may not support it. Check `report.md` for the containment figure. If the link is real, declare it in `_schema.json` or as a foreign key in your database |
| `ontology up to date` but you changed something outside the source | Add `--force` |
| Connection refused on step 8 | The container is still starting. Wait a few seconds and re-run the load |

## Tidy up

```bash
rm -rf out data-keys workshop.db parquet
```

PowerShell:

```powershell
Remove-Item -Recurse -Force out, data-keys, workshop.db, parquet -ErrorAction SilentlyContinue
```

A `.gitignore` in this folder already keeps these out of version control.
