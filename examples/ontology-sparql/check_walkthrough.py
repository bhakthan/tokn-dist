"""Offline structural checker for the ontology-sparql walkthrough.

Stdlib only. No network, no TOKN binary, no model calls. It checks that the
synthetic data, the query files, and the expected-answers file are consistent.
It does NOT run SPARQL; the expected answers are hand-computed.

Usage (from this folder):
    python check_walkthrough.py
        Syntax and fixture sanity only.
    python check_walkthrough.py --answer result.json
        Also grades an agent run: reads the JSON object saved from
        `tokn agent-run --output-format json` and compares the turbine and part
        ids in its final `result` with the bindings in expected_answers.json.
Exit code 0 = all checks passed, 1 = at least one failed.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "plant.ttl"
QUERIES = HERE / "queries"
EXPECTED = HERE / "expected_answers.json"

failures = []


def check(cond, msg):
    if cond:
        print(f"  ok   {msg}")
    else:
        print(f"  FAIL {msg}")
        failures.append(msg)


def strip_noise(text):
    """Remove comments, @prefix lines and <IRI> tokens so dots/semicolons count correctly."""
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("@prefix"):
            continue
        line = re.sub(r"#.*$", "", line)
        out.append(line)
    text = "\n".join(out)
    return re.sub(r"<[^>]*>", "<iri>", text)


def count_triples(text):
    """Each ';'-separated segment contributes 1 + number of ',' objects.
    Statements end at a '.' token."""
    total = 0
    for stmt in re.split(r"\.\s*(?=\n|$|\s)", strip_noise(text)):
        if not stmt.strip():
            continue
        for seg in stmt.split(";"):
            if seg.strip():
                total += 1 + seg.count(",")
    return total


def local(iri):
    return iri.rsplit("#", 1)[-1]


def grade_answer(path, exp, ttl_names):
    """Compare the ids named in the agent's final answer with expected bindings."""
    print(f"Agent answer ({path})")
    try:
        res = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        check(False, f"result file is readable JSON ({e})")
        return
    status = res.get("status")
    check(status == "success", f"run status is 'success' (got {status!r}); otherwise the answer is unassessed")
    if status != "success":
        return
    answer = str(res.get("result") or "")
    q = exp.get("queries", {})
    over_2000 = {local(r["turbine"]) for r in q.get("01_turbines_over_2000kw.rq", {}).get("before_reasoning", [])}
    in_north = {local(r["asset"]) for r in q.get("04_assets_in_site_north.rq", {}).get("after_reasoning", [])}
    parts = {local(r["part"]) for r in q.get("05_parts_of_wt01.rq", {}).get("after_reasoning", [])}
    want = (over_2000 & in_north) | parts
    universe = {n for n in ttl_names if re.fullmatch(r"(WT|GB|GEN|MO)-\d+", n)}
    named = set(re.findall(r"\b(?:WT|GB|GEN|MO)-\d+\b", answer))
    for n in sorted(want):
        check(n in named, f"answer names {n} (expected binding)")
    extra = sorted((named & universe) - want)
    check(not extra, "answer names no other turbine or part"
          + (f" (also named: {', '.join(extra)}; read the answer: a mention as excluded is fine)" if extra else ""))


def main():
    answer_path = None
    if len(sys.argv) == 3 and sys.argv[1] == "--answer":
        answer_path = sys.argv[2]
    elif len(sys.argv) != 1:
        print(__doc__)
        return 2
    print("Data")
    check(DATA.is_file(), "data/plant.ttl exists")
    ttl = DATA.read_text(encoding="utf-8")
    check(bool(re.search(r"@prefix\s+:\s+<http://example\.org/plant#>", ttl)),
          "default prefix ':' declared as http://example.org/plant#")
    n = count_triples(ttl)
    print(f"  info triples counted by this checker: {n}")
    check(30 <= n <= 80, "triple count within 30-80")

    print("Expected answers")
    check(EXPECTED.is_file(), "expected_answers.json exists")
    try:
        exp = json.loads(EXPECTED.read_text(encoding="utf-8"))
        check(True, "expected_answers.json parses as JSON")
    except (OSError, json.JSONDecodeError) as e:
        exp = {}
        check(False, f"expected_answers.json parses as JSON ({e})")
    check(exp.get("data_statement_count_hand_count") == n,
          "hand-count in expected_answers.json matches checker count")
    check("expected, not a recorded run" in exp.get("_status", ""),
          "expected file is labelled 'expected, not a recorded run'")

    local_names = set(re.findall(r"^:?([A-Za-z][\w-]*)\b", ttl, flags=re.M))
    local_names |= set(re.findall(r"[\s,]:([A-Za-z][\w-]*)", ttl))

    print("Queries")
    rq_files = sorted(QUERIES.glob("*.rq"))
    check(len(rq_files) >= 3 and len(rq_files) <= 5, "3-5 .rq files present")
    query_keys = set(exp.get("queries", {}).keys())
    for rq in rq_files:
        body = rq.read_text(encoding="utf-8").strip()
        check("\n" not in body, f"{rq.name} is one line (required by /rdf query)")
        check(body.count("{") == body.count("}"), f"{rq.name} has balanced braces")
        check(bool(re.match(r"(PREFIX\s+\S+\s+<[^>]+>\s+)*(SELECT|ASK)\b", body)),
              f"{rq.name} starts with PREFIX* then SELECT or ASK")
        check(rq.name in query_keys, f"{rq.name} has an entry in expected_answers.json")
    check(query_keys == {p.name for p in rq_files},
          "expected_answers.json keys match queries/*.rq exactly")

    print("Expected IRIs exist in data")
    for qname, block in exp.get("queries", {}).items():
        blob = json.dumps(block)
        for frag in set(re.findall(r"plant#([A-Za-z][\w-]*)", blob)):
            check(frag in local_names, f"{qname}: {frag} is defined in plant.ttl")

    if answer_path:
        grade_answer(answer_path, exp, local_names)

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s)")
        return 1
    if answer_path:
        print("All checks passed. (Answer ids match the expected bindings; SPARQL is not executed here.)")
    else:
        print("All checks passed. (Syntax and fixture sanity only; SPARQL results are not executed.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
