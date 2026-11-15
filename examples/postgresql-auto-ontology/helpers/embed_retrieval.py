"""Embedding-assisted retrieval over schema-only terms in one ontology.json.

Only schema names are embedded: labels, names, table and column names. Evidence,
profile, sample and statistics subtrees are skipped, and so are branches that
hold enumeration members or data values. Run once per ontology, and keep the
PostgreSQL and CSV results in separate output files.

Pass the Azure OpenAI account endpoint (https://<resource>.openai.azure.com,
optionally ending in /openai/v1). Project routes are rejected before any token
is requested. Vectors come from the account-level /openai/v1/embeddings route.
Authenticate with an API key from an environment variable, or with Microsoft
Entra ID through the Azure CLI. Secrets and endpoints are never printed.
Uses only the standard library.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TERM_KEYS = {"label", "name", "table", "column"}
SKIP_KEYS = {
    "evidence", "profile", "profiles", "samples", "sample", "statistics", "top_values",
    # Enumeration members and data values are not schema terms.
    "members", "enum_members", "enumeration_values", "values", "data_values", "value_labels",
}
MAX_TERMS = 5000
BATCH_SIZE = 16
COGNITIVE_SCOPE = "https://cognitiveservices.azure.com"


def collect_terms(node, found):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in SKIP_KEYS:
                continue
            if key in TERM_KEYS and isinstance(value, str) and value.strip():
                found.add(value.strip())
            else:
                collect_terms(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_terms(item, found)
    return found


def normalize_endpoint(raw):
    parsed = urllib.parse.urlsplit(raw.strip())
    if parsed.scheme != "https" or not parsed.netloc or "@" in parsed.netloc:
        sys.exit("error: the endpoint must be an https account URL without credentials")
    if parsed.query or parsed.fragment:
        sys.exit("error: the endpoint must not contain a query or fragment")
    if parsed.path.rstrip("/") not in ("", "/openai/v1"):
        sys.exit("error: use the account endpoint (https://<resource>.openai.azure.com), not a project or other route")
    return f"https://{parsed.netloc}/openai/v1/embeddings"


def entra_token():
    az = shutil.which("az")
    if not az:
        sys.exit("error: Azure CLI (az) not found; install it, or use --auth key")
    result = subprocess.run(
        [az, "account", "get-access-token", "--resource", COGNITIVE_SCOPE,
         "--query", "accessToken", "--output", "tsv"],
        capture_output=True, text=True, check=False,
    )
    token = result.stdout.strip()
    if result.returncode != 0 or not token:
        sys.exit("error: could not get a token; run az login and check the account")
    return token


def validate_vectors(payload, expected_count):
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or len(data) != expected_count:
        sys.exit("error: embeddings response has an unexpected number of items")
    vectors = [None] * expected_count
    for item in data:
        index = item.get("index") if isinstance(item, dict) else None
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < expected_count:
            sys.exit("error: embeddings response has an invalid index")
        if vectors[index] is not None:
            sys.exit("error: embeddings response repeats an index")
        vector = item.get("embedding")
        if not isinstance(vector, list) or not vector:
            sys.exit("error: embedding vector is empty")
        for value in vector:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                sys.exit("error: embedding vector contains a non-finite or non-numeric value")
        vectors[index] = [float(value) for value in vector]
    return vectors


def embed(url, deployment, headers, texts):
    vectors = []
    for start in range(0, len(texts), BATCH_SIZE):
        chunk = texts[start:start + BATCH_SIZE]
        body = json.dumps({"model": deployment, "input": chunk}).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json", **headers},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            sys.exit(f"error: embeddings request failed with HTTP {exc.code}")
        except urllib.error.URLError:
            sys.exit("error: embeddings endpoint is unreachable")
        except json.JSONDecodeError:
            sys.exit("error: embeddings response is not JSON")
        vectors.extend(validate_vectors(payload, len(chunk)))
    dims = {len(vector) for vector in vectors}
    if len(dims) != 1:
        sys.exit("error: embedding vectors have different dimensions")
    return vectors


def cosine(a, b):
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        sys.exit("error: a zero-length embedding vector cannot be ranked")
    return sum(x * y for x, y in zip(a, b)) / (norm_a * norm_b)


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ontology", required=True, help="ontology.json produced by tokn ontology build")
    p.add_argument("--query", required=True, help="search text, embedded once")
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--endpoint-env", default="AZURE_OPENAI_EMBEDDING_ENDPOINT", help="env var holding the embeddings account endpoint (kept separate from the Responses/project configuration)")
    p.add_argument("--deployment-env", default="AZURE_OPENAI_EMBEDDING_DEPLOYMENT", help="env var holding the embedding deployment name")
    p.add_argument("--auth", choices=["key", "entra"], default="entra")
    p.add_argument("--api-key-env", default="AZURE_OPENAI_API_KEY", help="env var holding the API key (with --auth key)")
    p.add_argument("--out", required=True, help="new JSON file to create")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not args.query.strip():
        sys.exit("error: --query must not be empty")
    if args.top_k < 1:
        sys.exit("error: --top-k must be at least 1")
    out = Path(args.out)
    if out.exists():
        sys.exit("error: --out already exists; choose a new file name")
    if not out.parent.is_dir():
        sys.exit("error: the folder for --out does not exist")
    try:
        ontology = json.loads(Path(args.ontology).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"error: cannot read --ontology: {type(exc).__name__}")

    terms = sorted(collect_terms(ontology, set()))
    if len(terms) > MAX_TERMS:
        sys.exit(f"error: {len(terms)} schema terms exceed the limit of {MAX_TERMS}; a partial ranking is refused")
    if not terms:
        sys.exit("error: no schema-only terms found in the ontology")
    if args.top_k > len(terms):
        sys.exit(f"error: --top-k cannot exceed the number of schema terms ({len(terms)})")

    endpoint = os.environ.get(args.endpoint_env)
    deployment = os.environ.get(args.deployment_env)
    if not endpoint or not deployment:
        sys.exit(f"error: set {args.endpoint_env} and {args.deployment_env} in the environment")
    url = normalize_endpoint(endpoint)

    if args.auth == "key":
        key = os.environ.get(args.api_key_env)
        if not key:
            sys.exit(f"error: environment variable {args.api_key_env} is not set")
        headers = {"api-key": key}
    else:
        headers = {"Authorization": f"Bearer {entra_token()}"}

    vectors = embed(url, deployment, headers, [args.query] + terms)
    query_vector, term_vectors = vectors[0], vectors[1:]
    ranked = sorted(
        ((cosine(query_vector, vector), term) for term, vector in zip(terms, term_vectors)),
        reverse=True,
    )[:args.top_k]

    result = {
        "ontology_file": Path(args.ontology).name,
        "query": args.query,
        "term_count": len(terms),
        "results": [{"term": term, "score": round(score, 4)} for score, term in ranked],
    }
    with out.open("x", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")
    print(f"wrote {len(ranked)} ranked terms from {len(terms)} schema terms to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
