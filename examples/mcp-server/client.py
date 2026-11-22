"""Minimal MCP client for `tokn serve`. Python standard library only.

Default (stdio): starts `tokn serve --mcp-disabled` as a child process in the
repository given on the command line, performs the MCP handshake, inspects the
advertised capabilities (tools with their annotations and output schemas,
resources, prompts) and calls the read-only `git_status` tool.

Optional (loopback HTTP): `--http URL` talks to a `tokn serve --transport=http`
server you started yourself, for example http://127.0.0.1:8090/mcp. Stop that
server when you are done.

Listing capabilities never invokes a tool. The only tool call is `git_status`,
and it is skipped unless the server advertises it as read-only. Pass
`--no-call` to list capabilities only.
"""

import argparse
import json
import subprocess
import urllib.request

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


class McpHttpClient:
    """Streamable HTTP: one JSON-RPC message per POST; replies may be JSON or SSE."""

    def __init__(self, url):
        self.url = url
        self.session = None
        self._next_id = 1

    def _post(self, message):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.url, data=json.dumps(message).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            self.session = resp.headers.get("Mcp-Session-Id") or self.session
            body = resp.read().decode("utf-8")
            ctype = resp.headers.get("Content-Type", "")
        if not body.strip():
            return []
        if "text/event-stream" in ctype:
            return [json.loads(line[5:].strip()) for line in body.splitlines() if line.startswith("data:")]
        parsed = json.loads(body)
        return parsed if isinstance(parsed, list) else [parsed]

    def request(self, method, params=None):
        req_id = self._next_id
        self._next_id += 1
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params
        for reply in self._post(msg):
            if reply.get("id") == req_id:
                if "error" in reply:
                    raise RuntimeError(f"{method} failed: {reply['error']}")
                return reply.get("result", {})
        raise RuntimeError(f"{method}: no reply")

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._post(msg)

    def close(self):
        pass


def list_all(client, method, key):
    items, cursor = [], None
    while True:
        result = client.request(method, {"cursor": cursor} if cursor else {})
        items.extend(result.get(key, []))
        cursor = result.get("nextCursor")
        if not cursor:
            return items


def inspect(client, capabilities):
    print(f"[client] server capabilities -> {', '.join(sorted(capabilities)) or 'none'}")

    tools = list_all(client, "tools/list", "tools")
    read_only = [t["name"] for t in tools if (t.get("annotations") or {}).get("readOnlyHint") is True]
    destructive = [t["name"] for t in tools if (t.get("annotations") or {}).get("destructiveHint") is True]
    structured = [t["name"] for t in tools if t.get("outputSchema")]
    first = ", ".join(t["name"] for t in tools[:3])
    print(f"[client] tools/list -> {len(tools)} tools (first: {first})")
    print(f"  annotated read-only: {len(read_only)}  destructive: {len(destructive)}  with outputSchema: {len(structured)}")

    if "resources" in capabilities:
        resources = list_all(client, "resources/list", "resources")
        sample = ", ".join(r.get("uri", "?") for r in resources[:3])
        print(f"[client] resources/list -> {len(resources)} resources (first: {sample})")
    if "prompts" in capabilities:
        prompts = list_all(client, "prompts/list", "prompts")
        print(f"[client] prompts/list -> {len(prompts)} prompts")
    return {t["name"]: t for t in tools}


def call_git_status(client, tools):
    tool = tools.get("git_status")
    if tool is None:
        print("[client] git_status not advertised; skipping the call")
        return
    if (tool.get("annotations") or {}).get("readOnlyHint") is not True:
        print("[client] git_status is not annotated read-only; skipping the call")
        return
    result = client.request("tools/call", {"name": "git_status", "arguments": {}})
    status = "error" if result.get("isError") else "ok"
    print(f"[client] tools/call git_status -> {status}")
    if "structuredContent" in result:
        print(f"  structuredContent keys: {', '.join(sorted(result['structuredContent']))}")
    text = "\n".join(
        part.get("text", "") for part in result.get("content", []) if part.get("type") == "text"
    )
    try:
        output = json.loads(text).get("output", text)
    except (json.JSONDecodeError, AttributeError):
        output = text
    for line in output.splitlines():
        print(f"  {line}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", nargs="?", help="git repository to start the stdio server in")
    parser.add_argument("--http", metavar="URL", help="connect to a running loopback `tokn serve --transport=http` instead")
    parser.add_argument("--no-call", action="store_true", help="list capabilities only; call no tool")
    args = parser.parse_args()
    if not args.http and not args.repo:
        parser.error("give a repository path, or --http URL")

    if args.http:
        client = McpHttpClient(args.http)
        print(f"[client] connecting: {args.http}")
    else:
        client = McpStdioClient(["tokn", "serve", "--mcp-disabled"], cwd=args.repo)
        print(f"[client] started: tokn serve --mcp-disabled (in {args.repo})")
    try:
        init = client.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "tokn-dist-example", "version": "1.1"},
            },
        )
        client.notify("notifications/initialized")
        server = init.get("serverInfo", {}).get("name", "?")
        print(f'[client] initialize -> protocol {init.get("protocolVersion")}, server "{server}"')
        tools = inspect(client, init.get("capabilities", {}))
        if not args.no_call:
            call_git_status(client, tools)
    finally:
        client.close()


if __name__ == "__main__":
    main()
