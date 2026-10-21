"""Offline structural check for a procedural graph JSON file.

Reads one local file, uses only the standard library, and makes no network
calls. It mirrors a few obvious rules so you can inspect a hand-written graph
before running `tokn procgraph validate`. It is not a replacement for that command.

Usage: python check_graph.py graph.json
"""

import json
import sys

NODE_TYPES = {"ACTION", "REASONING", "STATE", "STATUS"}
RELATIONS = {"LEADS_TO", "REQUIRES", "ENABLES", "EXTRACTS", "PROVIDES", "VERIFIES", "FALLBACK"}


def check(path):
    with open(path, encoding="utf-8") as fh:
        graph = json.load(fh)

    problems = []
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    ids = [n.get("id", "") for n in nodes]
    seen = set()
    for node_id in ids:
        if not node_id.strip():
            problems.append("a node has an empty id")
        elif node_id in seen:
            problems.append(f"duplicate node id: {node_id}")
        seen.add(node_id)

    for node in nodes:
        if node.get("type") not in NODE_TYPES:
            problems.append(f"node {node.get('id')!r} has unknown type {node.get('type')!r}")

    for edge in edges:
        for end in ("source", "target"):
            if edge.get(end) not in seen:
                problems.append(f"edge {end} {edge.get(end)!r} is not a node")
        if edge.get("relation") not in RELATIONS:
            problems.append(f"edge has unknown relation {edge.get('relation')!r}")

    for conventional in ("Start", "End"):
        if conventional not in seen:
            problems.append(f"missing conventional node {conventional!r}")

    print(f"{len(nodes)} nodes, {len(edges)} edges")
    if problems:
        for problem in problems:
            print(f"PROBLEM: {problem}")
        return 1
    print("ok (structural checks only)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(check(sys.argv[1]))
