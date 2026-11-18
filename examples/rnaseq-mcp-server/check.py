"""Check the MCP server that TOKN generated, without trusting its own tests.

The script starts server.py as a stdio MCP server, speaks JSON-RPC to it the
way an MCP client would, and compares every answer with values it computes
itself from data/counts.tsv.

Standard library only. Run from this folder:  python check.py [work-dir]
work-dir defaults to ./work, where run-agent writes server.py.
Exit code 0 means every check passed.
"""

import json
import os
import statistics
import subprocess
import sys

HERE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                       os.path.join(os.path.dirname(os.path.abspath(__file__)), "work"))
COUNTS = os.path.join(HERE, "data", "counts.tsv")
SAMPLES = os.path.join(HERE, "data", "samples.tsv")
TOOLS = {"rnaseq_qc_summary", "rnaseq_flag_outliers", "rnaseq_list_genes"}

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail and not ok else ""))


def answer_key():
    with open(COUNTS) as f:
        rows = [line.rstrip("\n").split("\t") for line in f if line.strip()]
    header, body = rows[0][1:], rows[1:]
    per = {}
    for j, s in enumerate(header):
        col = [int(r[j + 1]) for r in body]
        lib = sum(col)
        mt = sum(int(r[j + 1]) for r in body if r[0].startswith("MT-"))
        per[s] = {"library_size": lib,
                  "detected_genes": sum(1 for c in col if c > 0),
                  "mito_fraction": round(mt / lib, 4)}
    cutoff = 0.5 * statistics.median(v["library_size"] for v in per.values())
    flagged = {}
    for s, v in per.items():
        reasons = []
        if v["library_size"] < cutoff:
            reasons.append("low_library_size")
        if v["mito_fraction"] > 0.2:
            reasons.append("high_mito")
        if reasons:
            flagged[s] = sorted(reasons)
    return [r[0] for r in body], per, flagged


class Client:
    def __init__(self):
        self.p = subprocess.Popen([sys.executable, "server.py"], cwd=HERE,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.n = 0

    def send(self, method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            self.n += 1
            msg["id"] = self.n
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()
        if notify:
            return None
        line = self.p.stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout")
        return json.loads(line)

    def call(self, tool, args):
        return self.send("tools/call", {"name": tool, "arguments": args})["result"]

    def close(self):
        self.p.stdin.close()
        try:
            self.p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.p.kill()


def main():
    if not os.path.exists(os.path.join(HERE, "server.py")):
        print(f"server.py not found in {HERE}. Run the agent first (run-agent.ps1 or run-agent.sh).")
        return 2
    genes, per, flagged = answer_key()
    c = Client()
    try:
        init = c.send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "check.py", "version": "1"}})
        check("initialize returns tools capability", "tools" in init.get("result", {}).get("capabilities", {}))
        c.send("notifications/initialized", notify=True)
        check("ping", c.send("ping").get("result") == {})
        check("unknown method -> -32601", c.send("no/such").get("error", {}).get("code") == -32601)

        listed = {t["name"]: t for t in c.send("tools/list")["result"]["tools"]}
        check("tools/list has the three rnaseq_ tools", TOOLS <= set(listed), sorted(listed))
        for name in sorted(TOOLS & set(listed)):
            t = listed[name]
            a = t.get("annotations", {})
            check(f"{name} annotated read-only",
                  a.get("readOnlyHint") is True and a.get("destructiveHint") is False
                  and a.get("idempotentHint") is True and a.get("openWorldHint") is False, a)
            check(f"{name} has outputSchema", isinstance(t.get("outputSchema"), dict))
            props = t.get("inputSchema", {}).get("properties", {})
            check(f"{name} input properties described",
                  "counts_path" in props and all(p.get("description") for p in props.values()))

        r = c.call("rnaseq_qc_summary", {"counts_path": "data/counts.tsv", "samples_path": "data/samples.tsv"})
        sc = r.get("structuredContent", {})
        check("qc_summary returns structuredContent and text",
              not r.get("isError") and sc and any(x.get("type") == "text" for x in r.get("content", [])))
        check("qc_summary n_genes / n_samples",
              sc.get("n_genes") == len(genes) and sc.get("n_samples") == len(per))
        got = {s["sample_id"]: s for s in sc.get("samples", [])}
        bad = [s for s, v in per.items() if s not in got or any(got[s].get(k) != v[k] for k in v)]
        check("qc_summary matches the answer key for every sample", not bad, bad)

        r = c.call("rnaseq_flag_outliers", {"counts_path": "data/counts.tsv"})
        got = {f["sample_id"]: sorted(f["reasons"]) for f in r.get("structuredContent", {}).get("flagged", [])}
        check("flag_outliers finds S07 low library and S08 high mito", got == flagged, f"got {got}, want {flagged}")
        r = c.call("rnaseq_flag_outliers", {"counts_path": "data/counts.tsv", "max_mito_fraction": 0.5})
        got = {f["sample_id"] for f in r.get("structuredContent", {}).get("flagged", [])}
        check("flag_outliers honours max_mito_fraction", got == {"S07"}, got)

        seen, offset, pages = [], 0, 0
        while offset is not None and pages < 50:
            sc = c.call("rnaseq_list_genes", {"counts_path": "data/counts.tsv", "offset": offset, "limit": 150})["structuredContent"]
            seen += sc["genes"]
            offset = sc["next_offset"] if sc["has_more"] else None
            pages += 1
        check("list_genes pages through every gene in order", seen == genes and sc["total"] == len(genes),
              f"{len(seen)} genes in {pages} pages")

        r = c.call("rnaseq_qc_summary", {"counts_path": "data/missing.tsv"})
        text = " ".join(x.get("text", "") for x in r.get("content", []))
        check("missing file -> isError with a next step",
              r.get("isError") is True and "missing.tsv" in text and len(text.split()) > 6, text)
        sheet = os.path.join(HERE, "data", "_bad_sheet.tsv")
        with open(sheet, "w") as f:
            f.write("sample_id\tcondition\nS01\tcontrol\nS99\ttreated\n")
        try:
            r = c.call("rnaseq_qc_summary", {"counts_path": "data/counts.tsv", "samples_path": sheet})
        finally:
            os.remove(sheet)
        text = " ".join(x.get("text", "") for x in r.get("content", []))
        check("mismatched sample sheet -> isError naming S99", r.get("isError") is True and "S99" in text, text)
    finally:
        c.close()

    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
