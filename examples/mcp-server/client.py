"""Minimal MCP stdio client for `tokn serve`. Python standard library only.

Starts `tokn serve` as a child process in the repository given on the command
line, performs the MCP handshake, lists the tools, and calls `git_status`.
No sockets are opened; all traffic goes over the child's stdin/stdout.
"""

import json
import subprocess
import sys

PROTOCOL = "2025-03-26"


class McpStdioClient:
    def __init__(self, command, cwd):
        self.proc = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        self._next_id = 1

    def _send(self, message):
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params=None):
        req_id = self._next_id
        self._next_id += 1
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("tokn serve closed its output")
            reply = json.loads(line)
            if reply.get("id") == req_id:
                if "error" in reply:
                    raise RuntimeError(f"{method} failed: {reply['error']}")
                return reply.get("result", {})

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def close(self):
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        self.proc.wait(timeout=10)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: client.py <path-to-git-repo>")
    repo = sys.argv[1]

    client = McpStdioClient(["tokn", "serve"], cwd=repo)
    print(f"[client] started: tokn serve (in {repo})")
    try:
        init = client.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "tokn-dist-example", "version": "1.0"},
            },
        )
        client.notify("notifications/initialized")
        server = init.get("serverInfo", {}).get("name", "?")
        print(f'[client] initialize -> protocol {init.get("protocolVersion")}, server "{server}"')

        tools = client.request("tools/list").get("tools", [])
        first = ", ".join(t["name"] for t in tools[:3])
        print(f"[client] tools/list -> {len(tools)} tools (first: {first})")

        result = client.request("tools/call", {"name": "git_status", "arguments": {}})
        text = "\n".join(
            part.get("text", "") for part in result.get("content", []) if part.get("type") == "text"
        )
        status = "error" if result.get("isError") else "ok"
        print(f"[client] tools/call git_status -> {status}")
        try:
            output = json.loads(text).get("output", text)
        except (json.JSONDecodeError, AttributeError):
            output = text
        for line in output.splitlines():
            print(f"  {line}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
