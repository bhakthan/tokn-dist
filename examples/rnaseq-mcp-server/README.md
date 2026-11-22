# Example: TOKN writes an MCP server for bulk RNA-seq quality control

This example asks TOKN to build a Model Context Protocol (MCP) server for a
deep-domain job: checking the quality of a bulk RNA-seq count matrix before
anyone runs differential expression on it. The result is one Python file,
`server.py`, that uses only the standard library and speaks MCP over stdio.
An MCP client such as Claude Desktop, VS Code, or GitHub Copilot CLI can start
it and call three `rnaseq_` tools to check a count matrix and report which
samples to look at.

TOKN writes the server from `task.md`, which is the request. A separate
checker, `check.py`, then tests the server without trusting the agent's own
tests.

## What the example contains

| File | Purpose |
|---|---|
| `task.md` | The request given to TOKN: the three tools, their rules, and the MCP behaviour required. |
| `make_data.py` | Writes the synthetic, seeded count matrix and sample sheet into `data/`. |
| `run-agent.ps1` | PowerShell (pwsh 7+) runner: preflight, fresh `work/` copy, run TOKN, run the checker. |
| `run-agent.sh` | Bash runner with the same steps. |
| `check.py` | Starts `server.py` as an MCP client and checks it against an answer key it computes itself. |
| `.env.example` | Reference template. The runners read only `ANTHROPIC_API_KEY` from a local `.env`; gateway settings come from your shell. |
| `.gitignore` | Keeps `.env`, `work/` and `data/` out of git. |

`data/` and `work/` are generated. The runner rebuilds both, and both are
git-ignored.

## The data

`make_data.py` writes 400 genes by 8 samples of integer read counts. The
values come from a fixed seed, so every run produces the same files. Thirteen
of the genes carry the mitochondrial prefix `MT-`. The sample sheet
(`data/samples.tsv`) gives each sample a condition and a batch.

The data has two planted problems:

| Sample | Problem | Why it matters |
|---|---|---|
| **S07** | Shallow library: about a fifth of the reads of the other samples. | Few reads means noisy counts. A sample this small adds noise to every gene and can hide real differences. |
| **S08** | High mitochondrial fraction (about 9 times the mito counts of the others). | Mitochondrial reads rise when cells are stressed or dying. Such samples can distort the comparison between conditions. |

The other six samples are normal. A good QC step should flag S07 and S08 and
leave the rest alone.

## Prerequisites

- **TOKN** on your `PATH`. Check with `tokn version`.
- **Python 3.10 or newer.** No pip packages are needed. The example is
  standard library only.
- **An Anthropic API key**, or the key from an Anthropic-compatible gateway.
  Use a model capable of the required tool calls; provider charges and number
  of turns depend on the run. A missing/failed tool result is unassessed, not
  a pass.
- **PowerShell 7+** if you use `run-agent.ps1`. Bash is enough for `run-agent.sh`.

## Setup

PowerShell:

Set the key in your session, not in a file. In PowerShell, read it from your
secret store (for example `Get-Secret` from the SecretManagement module):

```powershell
cd examples\rnaseq-mcp-server
$env:ANTHROPIC_API_KEY = Get-Secret -Name AnthropicKey -AsPlainText
```

bash (the key is typed without echo and kept out of shell history):

```bash
cd examples/rnaseq-mcp-server
read -rs ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY
```

If you use an Anthropic-compatible gateway, also set `ANTHROPIC_BASE_URL`
(and `ANTHROPIC_AUTH_HEADER` if your gateway needs it) in the same trusted
shell. The runners never read endpoint or routing settings from a file in
this folder. A local `.env` with only `ANTHROPIC_API_KEY=` is still accepted
as a fallback; it is git-ignored, but check with `git status` before you push.

## Step 1: Read the request

Open `task.md`. It asks for one file, `server.py`, with these rules.

**The three tools.** Every tool name starts with `rnaseq_`, and every tool
takes a `counts_path` argument.

1. `rnaseq_qc_summary` returns one record per sample: `library_size` (sum of
   counts), `detected_genes` (genes with count above 0), and `mito_fraction`
   (MT- counts divided by library size, rounded to 4 decimals). An optional
   `samples_path` checks that every sample in the sheet matches a count column.
2. `rnaseq_flag_outliers` flags a sample with `low_library_size` when its
   library is below half the median library size, and with `high_mito` when
   its mito fraction is above `max_mito_fraction` (optional, default 0.2). It
   returns the flagged samples and the thresholds it used.
3. `rnaseq_list_genes` pages through gene ids in file order. Inputs are
   `offset` (default 0) and `limit` (default 50, maximum 200). Outputs are
   `genes`, `total`, `has_more` and `next_offset` (null at the end).

**The MCP behaviour every tool must have.** These mirror current MCP server
best practice.

- **Annotations.** Each tool sets `readOnlyHint: true`, `destructiveHint:
  false`, `idempotentHint: true` and `openWorldHint: false`. The tools only
  read files. Clients use these hints to decide whether to ask you before
  running a tool. A read-only, idempotent tool can usually run without a
  prompt. A destructive or open-world tool should be confirmed first.
- **`outputSchema` and `structuredContent`.** Each tool declares a JSON Schema
  for its output. Each result carries the data as `structuredContent` for the
  program, plus a short `text` block for the person reading it.
- **Actionable errors.** A failure, such as a missing file or a sample sheet
  that does not match the counts, returns a normal result with `isError: true`.
  The text says what went wrong and what to do next. The server never crashes
  and never answers a tool failure with a JSON-RPC error.
- **Pagination.** Long lists come back in pages, with `has_more` and
  `next_offset`, so a client can read a large matrix in steps.
- **Name prefix.** The `rnaseq_` prefix avoids collisions when a client also
  runs other MCP servers that have tools called `qc_summary` or `list_genes`.

**Done means.** `server.py` works as above. `test_server.py` uses `unittest`,
starts `server.py` as a subprocess, and exercises every tool and at least two
error cases. Its tests pass.

## Step 2: Run the agent

PowerShell:

```powershell
pwsh ./run-agent.ps1
```

bash:

```bash
./run-agent.sh
```

The script does five things, in order.

1. **Preflight.** It checks that `tokn` and Python are installed. If either is
   missing, it lists every missing dependency and stops.
2. **Key.** If `ANTHROPIC_API_KEY` is not already set, it reads that one line
   from a local `.env`. Every other line, including any base URL, is ignored.
   It stops if the key is empty or still a placeholder.
3. **Fresh `work/` copy.** A previous `work/` is renamed to `work.prev-<timestamp>/`,
   not deleted, so a failed run's evidence survives. The script regenerates `data/`
   and copies only `data/` and `task.md` into the new `work/`. The agent never sees
   `check.py` or the rest of this folder.
4. **Run TOKN.** It runs the agent inside `work/`. The command is:

   ```bash
   tokn agent-run --model-provider anthropic --model-name claude-haiku-5.5 \
     --repo-root . --prompt-file task.md \
     --max-steps 40 --permission-mode default --mcp-disabled
   ```

   `--permission-mode default` asks you before each file write or command.
   To run unattended, opt in with `-Unattended` (PowerShell) or `UNATTENDED=1`
   (bash), which swaps in `--no-confirm` and auto-approves every tool call. Do
   that only on a throwaway machine or folder.
   `--mcp-disabled` keeps the agent from connecting to other MCP servers.
5. **Check.** It runs `check.py` on `work/`. The overall result passes only if
   the agent exited 0 **and** `check.py` passed. A failed agent run exits non-zero
   even when `check.py` passes.

To try another model, pass `-Model` in PowerShell or set `MODEL` in bash:

```powershell
pwsh ./run-agent.ps1 -Model claude-sonnet-5.5
```

```bash
MODEL=claude-sonnet-5.5 ./run-agent.sh
```

To keep the agent's working copy outside this folder, give a new path. The
runner refuses a path that already exists:

```powershell
pwsh ./run-agent.ps1 -WorkDir $HOME\rnaseq-mcp-work
```

```bash
WORK_DIR=~/rnaseq-mcp-work ./run-agent.sh
```

Then pass the same path to `check.py` in Step 4.


If you prefer to run TOKN by hand, create `work/` yourself, copy `data/` and
`task.md` into it, then run the `tokn agent-run` command above from inside
`work/`.

## Step 3: What a real run looked like

This is one historical live run on Claude Haiku 5.5, recorded with an earlier
unattended version of the runner. It is not a guarantee of cost or outcome:

- 20 agent steps, about 5 minutes. Provider charges for your run will differ.
- 30 tool calls. The agent exited with code 0.
- The agent wrote `server.py` (579 lines) and `test_server.py` (273 lines,
  19 `unittest` tests, all passing).
- Its closing summary flagged **S07** as `low_library_size` (38,776 reads,
  against a cutoff of 94,758.75, which is half the median) and **S08** as
  `high_mito` (fraction 0.2674, above 0.2). The other six samples had mito
  fractions of 0.038 to 0.039.

Results vary from run to run, because models are not deterministic. The code
the agent writes may differ, and so may the wording of its summary. Do not
judge a run by its summary. Judge it with `check.py`.

## Step 4: Check it independently

```bash
python check.py
```

Run it from this folder. It defaults to `./work`. You can also pass a
different folder, such as `python check.py path/to/work`.

`check.py` starts `server.py` as a real MCP client would, over stdio. It
computes its own answer key from `data/counts.tsv`, so it does not rely on
the agent's tests. It then checks the protocol, the annotations and schemas,
the numbers, the planted flags, the threshold override, paging, and two
error cases.

A passing run looks like this (abridged, with some lines elided by `...`):

```
[PASS] initialize returns tools capability
[PASS] ping
[PASS] unknown method -> -32601
[PASS] tools/list has the three rnaseq_ tools
...
[PASS] flag_outliers finds S07 low library and S08 high mito
[PASS] flag_outliers honours max_mito_fraction
[PASS] list_genes pages through every gene in order
[PASS] missing file -> isError with a next step
[PASS] mismatched sample sheet -> isError naming S99

21/21 checks passed
```

The exit code is 0 when every check passes and 1 when any check fails.

You can also run the agent's own tests:

```bash
cd work
python -m unittest test_server -v
```

## Step 5: Try the tools by hand

You can talk to the server directly. From inside `work/`, send an
`initialize` request and a `tools/call` request, one JSON object per line,
then close stdin:

bash:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"manual","version":"1"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"rnaseq_flag_outliers","arguments":{"counts_path":"data/counts.tsv"}}}' \
  | python server.py
```

PowerShell (run from inside `work/`):

```powershell
@'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"manual","version":"1"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"rnaseq_flag_outliers","arguments":{"counts_path":"data/counts.tsv"}}}
'@ | python server.py
```

The `rnaseq_flag_outliers` call returns this (trimmed):

```json
{"structuredContent": {"n_samples": 8,
  "flagged": [{"sample_id": "S07", "reasons": ["low_library_size"]},
              {"sample_id": "S08", "reasons": ["high_mito"]}],
  "thresholds": {"min_library_size": 94758.75, "max_mito_fraction": 0.2}},
 "content": [{"type": "text",
  "text": "Flagged 2 of 8 samples:\nS07: low_library_size\nS08: high_mito\nThresholds: min_library_size=94758.75 max_mito_fraction=0.2."}]}
```

A missing file returns an error result, not a crash. Calling a tool with
`data/missing.tsv` gives:

```json
{"content":[{"type":"text","text":"File not found: data/missing.tsv. Check the path is relative to the server's working directory or pass an absolute path."}],"isError":true}
```

Paging reaches the end cleanly. Calling `rnaseq_list_genes` with `offset` 395
and `limit` 10 returns the last five genes (trimmed to the tail of the list):

```json
{"genes": ["MT-ND4L", "MT-ND4", "MT-ND5", "MT-ND6", "MT-CYB"],
 "total": 400, "has_more": false, "next_offset": null}
```

## Step 6: Connect it to an MCP client

Use the absolute path to `work/server.py`. Clients do not always start the
server in the folder you expect, so an absolute path avoids surprises. On
Windows, escape each backslash in JSON (`C:\\path\\to\\...`). Use `python`
on Windows and `python3` on macOS and Linux.

Add this under `mcpServers` in your client's config file:

```json
{
  "mcpServers": {
    "rnaseq-qc": {
      "command": "python",
      "args": ["/absolute/path/to/rnaseq-mcp-server/work/server.py"]
    }
  }
}
```

| Client | Config file |
|---|---|
| Claude Desktop | `claude_desktop_config.json` (Settings, Developer, Edit Config) |
| Cursor | `.cursor/mcp.json` in your project |
| GitHub Copilot CLI | `~/.copilot/mcp-config.json` |

VS Code uses `.vscode/mcp.json` in your workspace. It takes a `servers` key
instead of `mcpServers`, and each entry needs `"type": "stdio"`:

```json
{
  "servers": {
    "rnaseq-qc": {
      "type": "stdio",
      "command": "python",
      "args": ["/absolute/path/to/rnaseq-mcp-server/work/server.py"]
    }
  }
}
```

Restart the client after you save. It should list `rnaseq-qc` and its three
tools. The tools take `counts_path` as an argument, so give an absolute path
to your matrix, for example `/abs/path/data/counts.tsv`. If your client lets
you set a working directory for a server, point it at the folder that holds
`data/`, and relative paths will also work.

Then ask the assistant something like:

- "Run QC on `/abs/path/data/counts.tsv` and tell me which samples to drop
  before differential expression."
- "Relax the mito cutoff to 0.3 and check again."

All three tools are annotated read-only, so clients can usually run them
without asking first. The assistant can still choose to ask, depending on
the client's settings.

## Optional: Compare with TOKN's own MCP server

TOKN can also act as an MCP server. `tokn serve` exposes TOKN's built-in
tools over MCP. See [the mcp-server example](../mcp-server/README.md). This
example does something different: it uses TOKN to write a new, standalone
domain server that does not depend on TOKN at run time.

## Next steps and ways to adapt it

- **Add a tool.** Ask for `rnaseq_sample_correlation`, which reports the
  correlation between samples. Add the request to `task.md` and run again.
- **Use your own counts.** Point `counts_path` at a real matrix with a
  `gene_id` column and one integer column per sample. Mitochondrial genes
  must start with `MT-` for the mito check to work.
- **Keep it stdlib only.** The server runs on a machine with no internet and
  no package installs, which suits air-gapped labs.
- **Extend the checker.** Add a case to `check.py` for each new rule in
  `task.md`, so a re-run is judged on the new behaviour too.
- **Change the rules.** Edit `task.md`, such as the 0.5 median rule or the 0.2
  mito default, then run again. Update `check.py` to match, or it will fail.

## Clean up

Remove the generated folders. Both are git-ignored, so they will not be
committed.

PowerShell:

```powershell
Remove-Item -Recurse -Force work, data, work.prev-* -ErrorAction SilentlyContinue
```

bash:

```bash
rm -rf work work.prev-* data
```

The `.env` file holds your key. Delete it too if you do not need it.
