"""Check the known synthetic pipeline structure in a TOKN vision JSON result."""
import json
import re
import sys


EXPECTED_LABELS = ["Raw reads", "Trim + QC", "Align", "Count matrix"]
EXPECTED_EDGES = list(zip(EXPECTED_LABELS, EXPECTED_LABELS[1:]))


def check(mermaid):
    lines = [line.strip() for line in mermaid.splitlines() if line.strip()]
    if not lines or lines[0].lower() != "flowchart lr":
        return False

    nodes = {}
    edges = []
    for line in lines[1:]:
        node = re.fullmatch(r'(\w+)\s*\[\s*"([^"]+)"\s*\]', line)
        edge = re.fullmatch(r"(\w+)\s*-->\s*(\w+)", line)
        if node:
            nodes[node.group(1)] = node.group(2)
        elif edge:
            edges.append((edge.group(1), edge.group(2)))

    if list(nodes.values()) != EXPECTED_LABELS:
        return False
    return [(nodes.get(source), nodes.get(target)) for source, target in edges] == EXPECTED_EDGES


def main(path):
    with open(path, encoding="utf-8-sig") as file:
        result = json.load(file)
    mermaid = result.get("mermaid")
    if not isinstance(mermaid, str) or not check(mermaid):
        print("FAIL: extracted Mermaid does not match the expected pipeline structure")
        return 1
    print("PASS: expected pipeline nodes and edges found")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_pipeline.py <vision-output.json>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
