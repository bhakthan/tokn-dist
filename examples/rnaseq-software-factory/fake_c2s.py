"""Offline stand-in for a llama.cpp `llama-server` hosting a C2S-Scale GGUF model.

It speaks the same wire protocol the product uses (POST /completion, GET /props,
GET /health) and answers with Cell Ontology-style phrasing observed from the real
C2S-Scale-Gemma-2-2B model ("CD16-positive, CD56-dim natural killer cell, human.",
"effector memory CD8-positive, alpha-beta T cell, terminally differentiated.", ...),
chosen by a transparent marker rule over the cell sentence. It is a test double, not
a classifier: it exists so the factory loop, the unit tests and the grader run with
no GPU, no download and no network.

Modes (FAKE_C2S_MODE or --mode):
  normal          marker oracle
  flip            adversarial: B cells come back as "classical monocyte." and CD8 T
                  cells as "mature NK T cell." -- the guardrail must refuse both
  die_after:K     serve K completions, then refuse connections-equivalent (HTTP 503)
  invalid         HTTP 200 with an empty completion
Every request prompt is appended to --log (JSONL) so a grader can compare the exact
multiset of prompts with the expected one.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PANELS = {
    "monocyte": ["LYZ", "S100A8", "S100A9", "CD14", "FCN1", "VCAN", "CST3"],
    "b": ["MS4A1", "CD79A", "CD79B", "CD19", "BANK1", "TCL1A"],
    "nk": ["GNLY", "NKG7", "KLRD1", "KLRF1", "PRF1", "FCGR3A"],
    "cd8_t": ["CD8A", "CD8B", "GZMK", "CCL5"],
    "cd4_t": ["CD4", "IL7R", "CCR7", "LEF1", "TCF7", "MAL", "LTB"],
    "pdc": ["LILRA4", "PLD4", "IRF8", "SERPINF1", "ITM2C"],
}
PHRASES = {
    "monocyte": ["classical monocyte.", "CD14-positive monocyte.", "monocyte."],
    "b": ["naive B cell.", "B cell.", "memory B cell."],
    "nk": ["CD16-positive, CD56-dim natural killer cell, human.", "natural killer cell."],
    "cd8_t": ["CD8-positive, alpha-beta T cell.",
              "effector memory CD8-positive, alpha-beta T cell, terminally differentiated."],
    "cd4_t": ["CD4-positive, alpha-beta T cell.", "naive thymus-derived CD4-positive, alpha-beta T cell."],
    "pdc": ["plasmacytoid dendritic cell."],
    None: ["lymphocyte."],
}
TOP_N = 50
_SENTENCE = re.compile(r"Cell sentence: (.*?)\.\n", re.S)


def label_for(prompt: str, mode: str = "normal") -> str:
    m = _SENTENCE.search(prompt)
    genes = m.group(1).split()[:TOP_N] if m else []
    top = set(genes)
    score = {k: sum(g in top for g in p) for k, p in PANELS.items()}
    best = max(score, key=lambda k: (score[k], -list(PANELS).index(k)))
    kind = best if score[best] >= 2 else None
    if mode == "flip" and kind == "b":
        return "classical monocyte.<ctrl100>"
    if mode == "flip" and kind == "cd8_t":
        return "mature NK T cell.<ctrl100>"
    opts = PHRASES[kind]
    pick = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest(), 16) % len(opts)
    return opts[pick] + "<ctrl100>"


class _State:
    def __init__(self, mode: str, log_path: str | None):
        self.mode, self.log_path = mode, log_path
        self.served = 0
        self.lock = threading.Lock()


def _handler(state: _State):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, code, doc):
            body = json.dumps(doc).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"status": "ok"})
            if self.path == "/props":
                return self._send(200, {"model_path": "fake-c2s-oracle.gguf", "build_info": "fake_c2s",
                                        "total_slots": 4, "default_generation_settings": {"n_ctx": 8192}})
            self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/completion":
                return self._send(404, {"error": "not found"})
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            prompt = str(req.get("prompt", ""))
            with state.lock:
                if state.log_path:
                    with open(state.log_path, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"prompt": prompt, "n_predict": req.get("n_predict"),
                                             "temperature": req.get("temperature")}) + "\n")
                mode = state.mode
                if mode.startswith("die_after:"):
                    if state.served >= int(mode.split(":", 1)[1]):
                        return self._send(503, {"error": "model unloaded"})
                    mode = "normal"
                state.served += 1
            if mode == "invalid":
                return self._send(200, {"content": ""})
            self._send(200, {"content": label_for(prompt, mode), "stop": True})

    return H


def serve(port: int = 0, mode: str = "normal", log_path: str | None = None):
    """Start on 127.0.0.1 in a daemon thread; returns (server, url). Call server.shutdown() to stop."""
    srv = ThreadingHTTPServer(("127.0.0.1", port), _handler(_State(mode, log_path)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def main(argv=None):
    import os
    ap = argparse.ArgumentParser(prog="fake_c2s")
    ap.add_argument("--port", type=int, default=8091)
    ap.add_argument("--mode", default=os.environ.get("FAKE_C2S_MODE", "normal"))
    ap.add_argument("--log", default=None)
    a = ap.parse_args(argv)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), _handler(_State(a.mode, a.log)))
    print(f"fake_c2s ({a.mode}) on http://127.0.0.1:{srv.server_address[1]}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
