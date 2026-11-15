"""Check a few CSV rows against SHACL shapes for one ontology class.

The helper materialises the rows of one CSV as RDF, then validates them with
pyshacl. It is a focused subset check. It is not an R2RML engine, not a TOKN
validator, and not a database conformance test.

Choose one way to give the mapping:
  --mapping FILE                         a hand-written JSON mapping (below)
  --ontology FILE --table T --id-column C
                                         derive the mapping from ontology.json
                                         and shapes.ttl using element IDs

Either way, the mapping must match the shapes file before any row is checked:
at least one shape must target the class, and each mapped property must have a
property shape on that target with the same sh:path and sh:datatype.

Only accepted scalar data properties are checked. Object relationships,
including foreign keys, are not materialised, so a CSV check says nothing about
an inferred foreign key. CSV columns carry no NOT NULL or uniqueness metadata,
so no minimum count is assumed for them.

The helper refuses to run for a missing CSV column, a short or over-wide row,
an empty or repeated identifier, more rows than --max-rows, or zero focus nodes.
Literal text is checked as written: a value such as "not-a-boolean" is not
normalised before validation.

Mapping file (JSON). Local names must match the shapes file exactly:
  {
    "base_iri": "<namespace used by the shapes file>",
    "class_name": "<class local name>",
    "id_column": "<CSV column that identifies each row>",
    "properties": {
      "<CSV column>": {"predicate": "<property local name>", "datatype": "xsd:string"}
    }
  }

Requires rdflib and pyshacl.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.parse import quote

XSD_TYPE_NAMES = ["xsd:integer", "xsd:decimal", "xsd:string", "xsd:date", "xsd:boolean"]


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--csv", required=True, help="UTF-8 CSV with a header row")
    p.add_argument("--shapes", required=True, help="SHACL shapes file (Turtle), as written by the build")
    p.add_argument("--expect", choices=["pass", "fail"], required=True, help="expected result for this check")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--mapping", help="hand-written JSON mapping file")
    source.add_argument("--ontology", help="ontology.json produced by tokn ontology build")
    p.add_argument("--table", help="with --ontology: canonical table name")
    p.add_argument("--id-column", help="with --ontology: CSV column that identifies each row")
    p.add_argument("--max-rows", type=int, default=1000, help="refuse CSV files with more data rows than this")
    p.add_argument("--rdf-out", help="optional new Turtle file for the materialised graph")
    args = p.parse_args(argv)
    if args.ontology and not (args.table and args.id_column):
        p.error("--ontology needs --table and --id-column")
    if args.mapping and (args.table or args.id_column):
        p.error("--table and --id-column apply only with --ontology")
    return args


def mapping_from_file(path, rdf):
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"error: cannot read --mapping: {type(exc).__name__}")
    for key in ("base_iri", "class_name", "id_column", "properties"):
        if key not in raw:
            sys.exit(f"error: mapping is missing '{key}'")
    if not raw["properties"]:
        sys.exit("error: mapping lists no properties to check")
    base = raw["base_iri"]
    properties = {}
    for column, spec in raw["properties"].items():
        if not isinstance(spec, dict) or "predicate" not in spec or "datatype" not in spec:
            sys.exit(f"error: property {column} needs 'predicate' and 'datatype'")
        if spec["datatype"] not in XSD_TYPE_NAMES:
            sys.exit(f"error: unsupported datatype for {column}; use one of {XSD_TYPE_NAMES}")
        properties[column] = {"predicate_iri": rdf["URIRef"](base + spec["predicate"]), "datatype": spec["datatype"]}
    return {
        "class_iri": rdf["URIRef"](base + raw["class_name"]),
        "instance_base": f"{base}{raw['class_name']}/",
        "id_column": raw["id_column"],
        "properties": properties,
    }


def nodes_with_literal(shapes, element_id, rdf):
    literal_type = rdf["Literal"]
    return {s for s, _, o in shapes if isinstance(o, literal_type) and str(o) == element_id}


def mapping_from_ontology(ontology_path, table, id_column, shapes, rdf):
    try:
        ontology = json.loads(Path(ontology_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"error: cannot read --ontology: {type(exc).__name__}")
    sh, xsd, uriref = rdf["SH"], rdf["XSD"], rdf["URIRef"]

    classes = [c for c in ontology.get("classes", []) if (c.get("tables") or [""])[0] == table]
    if len(classes) != 1:
        sys.exit("error: --table must be the canonical table of exactly one class in ontology.json")
    cls = classes[0]

    class_nodes = nodes_with_literal(shapes, cls["id"], rdf)
    class_iris = {o for n in class_nodes for o in shapes.objects(n, sh.targetClass)}
    class_iris |= {n for n in class_nodes if set(shapes.subjects(sh.targetClass, n))}
    if len(class_iris) != 1:
        sys.exit("error: could not identify exactly one class target in shapes.ttl")
    class_iri = class_iris.pop()
    target_shapes = set(shapes.subjects(sh.targetClass, class_iri))

    properties = {}
    for prop in ontology.get("data_properties", []):
        if prop.get("domain") != cls["id"] or prop.get("table") != table:
            continue
        if prop.get("status") != "accepted":
            continue
        column = prop.get("column")
        range_name = str(prop.get("range", ""))
        if range_name not in XSD_TYPE_NAMES:
            sys.exit(f"error: column {column} has an unsupported type {range_name}")
        candidates = [n for n in nodes_with_literal(shapes, prop["id"], rdf) if set(shapes.objects(n, sh.path))]
        if len(candidates) != 1:
            sys.exit(f"error: no unique property shape in shapes.ttl for column {column}")
        pshape = candidates[0]
        if not any((t, sh.property, pshape) in shapes for t in target_shapes):
            sys.exit(f"error: the property shape for column {column} is not attached to the class shape")
        path = shapes.value(pshape, sh.path)
        if not isinstance(path, uriref):
            sys.exit(f"error: the sh:path for column {column} is not a single IRI")
        if shapes.value(pshape, sh.datatype) != xsd[range_name.split(":", 1)[1]]:
            sys.exit(f"error: the shape datatype for column {column} differs from the ontology type")
        properties[column] = {"predicate_iri": path, "datatype": range_name}

    if not properties:
        sys.exit("error: no accepted scalar data properties for this table")
    return {
        "class_iri": class_iri,
        "instance_base": f"urn:tokn:csv-row:{quote(table, safe='')}/",
        "id_column": id_column,
        "properties": properties,
    }


def check_mapping_against_shapes(shapes, resolved, rdf):
    sh, xsd = rdf["SH"], rdf["XSD"]
    targeting = set(shapes.subjects(sh.targetClass, resolved["class_iri"]))
    if not targeting:
        sys.exit("error: no shape in --shapes targets the mapped class; check the class and base namespace")
    for column, spec in resolved["properties"].items():
        datatype = xsd[spec["datatype"].split(":", 1)[1]]
        matched = False
        for shape in targeting:
            for pshape in shapes.objects(shape, sh.property):
                if (pshape, sh.path, spec["predicate_iri"]) not in shapes:
                    continue
                if list(shapes.objects(pshape, sh.datatype)) != [datatype]:
                    sys.exit(f"error: the shape for column {column} does not declare the mapped datatype")
                matched = True
        if not matched:
            sys.exit(f"error: no property shape on the target class has sh:path for column {column}")
    return len(targeting)


def read_rows(csv_path, resolved, max_rows):
    required = [resolved["id_column"], *resolved["properties"].keys()]
    try:
        fh = open(csv_path, newline="", encoding="utf-8-sig")
    except OSError as exc:
        sys.exit(f"error: cannot read --csv: {type(exc).__name__}")
    rows, seen = [], set()
    with fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        if len(header) != len(set(header)):
            sys.exit("error: CSV header has duplicate column names")
        missing = [column for column in required if column not in header]
        if missing:
            sys.exit(f"error: CSV is missing mapped column(s): {', '.join(missing)}")
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                sys.exit(f"error: CSV line {line} has a different number of fields from the header")
            if len(rows) >= max_rows:
                sys.exit(f"error: more than {max_rows} data rows; use a smaller file or raise --max-rows")
            identifier = row[resolved["id_column"]].strip()
            if not identifier:
                sys.exit(f"error: empty identifier on CSV line {line}")
            if identifier in seen:
                sys.exit(f"error: duplicate identifier on CSV line {line}; identifiers must be unique")
            seen.add(identifier)
            rows.append((identifier, row))
    return rows


def materialise_row(graph, identifier, row, resolved, rdf):
    subject = rdf["URIRef"](resolved["instance_base"] + quote(identifier, safe=""))
    graph.add((subject, rdf["RDF"].type, resolved["class_iri"]))
    for column, spec in resolved["properties"].items():
        value = row[column].strip()
        if value == "":
            continue
        datatype = rdf["XSD"][spec["datatype"].split(":", 1)[1]]
        literal = rdf["Literal"](value, datatype=datatype, normalize=False)
        graph.add((subject, spec["predicate_iri"], literal))


def main(argv=None):
    args = parse_args(argv)
    try:
        import pyshacl
        from rdflib import RDF, Graph, Literal, URIRef
        from rdflib.exceptions import ParserError
        from rdflib.namespace import SH, XSD
    except ImportError:
        sys.exit("error: rdflib and pyshacl are missing; install them with: pip install rdflib pyshacl")
    if args.max_rows < 1:
        sys.exit("error: --max-rows must be at least 1")
    if args.rdf_out and Path(args.rdf_out).exists():
        sys.exit("error: --rdf-out already exists; choose a new file name")

    rdf = {"URIRef": URIRef, "Literal": Literal, "RDF": RDF, "SH": SH, "XSD": XSD}
    try:
        shapes_path = Path(args.shapes).resolve()
        with shapes_path.open("rb") as source:
            shapes = Graph().parse(source=source, format="turtle", publicID=shapes_path.as_uri())
    except (OSError, ValueError, SyntaxError, ParserError) as exc:
        sys.exit(f"error: cannot parse --shapes: {type(exc).__name__}")

    if args.mapping:
        resolved = mapping_from_file(args.mapping, rdf)
        route = "mapping file"
    else:
        resolved = mapping_from_ontology(args.ontology, args.table, args.id_column, shapes, rdf)
        route = "ontology.json and shapes.ttl"
    target_shapes = check_mapping_against_shapes(shapes, resolved, rdf)

    rows = read_rows(args.csv, resolved, args.max_rows)
    if not rows:
        sys.exit("error: the CSV has no data rows; a check with no rows is not evidence")
    data = Graph()
    for identifier, row in rows:
        materialise_row(data, identifier, row, resolved, rdf)
    focus_nodes = len(set(data.subjects(RDF.type, resolved["class_iri"])))
    if focus_nodes != len(rows):
        sys.exit("error: materialised focus nodes do not match the CSV rows")

    conforms, _, report_text = pyshacl.validate(data, shacl_graph=shapes, inference="none")

    if args.rdf_out:
        with Path(args.rdf_out).open("x", encoding="utf-8") as fh:
            fh.write(data.serialize(format="turtle"))

    print(
        f"route: {route}; shapes targeting the class {target_shapes}; "
        f"mapped properties {len(resolved['properties'])}; rows {len(rows)}; "
        f"focus nodes {focus_nodes}; conforms {bool(conforms)}"
    )
    if not conforms:
        print(report_text)
    met = conforms if args.expect == "pass" else not conforms
    print(f"expectation '{args.expect}': {'met' if met else 'NOT met'}")
    return 0 if met else 1


if __name__ == "__main__":
    sys.exit(main())
