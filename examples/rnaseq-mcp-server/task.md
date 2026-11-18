# Build an RNA-seq QC MCP server

Build a Model Context Protocol (MCP) server that lets an AI assistant check the
quality of a bulk RNA-seq count matrix before anyone runs differential
expression on it.

## Constraints

- One file, `server.py`, Python 3.10+, **standard library only** (no `mcp`
  SDK, no pandas, no numpy). It must run on a machine with no internet.
- Transport: stdio. One JSON-RPC 2.0 message per line on stdin; one response
  per line on stdout. Never print anything else to stdout; logs go to stderr.
- Handle `initialize` (reply with `protocolVersion` "2025-06-18",
  `capabilities: {"tools": {}}` and `serverInfo`), `tools/list`, `tools/call`
  and `ping`. Ignore notifications (messages with no `id`). An unknown method
  gets JSON-RPC error -32601.

## Input files

- `counts.tsv`: tab-separated. Header `gene_id` then one column per sample.
  One row per gene, integer read counts.
- `samples.tsv` (optional): tab-separated sample sheet with a `sample_id`
  column.
- Mitochondrial genes are the ones whose `gene_id` starts with `MT-`.

## Tools

Every tool name starts with `rnaseq_`. Every tool takes `counts_path`
(string, required) and gives each input property a description.

1. **`rnaseq_qc_summary`**: one record per sample with
   - `sample_id`
   - `library_size` (sum of counts)
   - `detected_genes` (genes with count > 0)
   - `mito_fraction` (MT- counts / library size, rounded to 4 decimals)

   It also returns `n_genes` and `n_samples`. Optional `samples_path`: when
   given, every `sample_id` in the sheet must match a count column, otherwise
   return an error.
2. **`rnaseq_flag_outliers`**: flags samples by these exact rules.
   - `low_library_size` when `library_size < 0.5 * median(library_size)`.
   - `high_mito` when `mito_fraction > max_mito_fraction`. `max_mito_fraction`
     is an optional number input, default 0.2.

   Returns `flagged`: a list of `{sample_id, reasons}` sorted by `sample_id`,
   and `thresholds`: `{min_library_size, max_mito_fraction}` as used.
3. **`rnaseq_list_genes`**: pages through gene ids in file order.
   - Inputs: `offset` (default 0) and `limit` (default 50, max 200).
   - Returns `genes`, `total`, `has_more` and `next_offset` (null when there
     is no more).

## Behaviour every tool must have

- `annotations`: `readOnlyHint: true`, `destructiveHint: false`,
  `idempotentHint: true`, `openWorldHint: false`. The tools only read files.
- An `outputSchema` (JSON Schema object). Each result carries the same data
  as `structuredContent` plus a short human-readable `text` block.
- Failures (missing file, sample sheet that does not match the count columns,
  non-integer count, bad argument) come back as a normal result with
  `isError: true`. The text must say what went wrong **and what to do next**,
  for example "File not found: x.tsv. Check the path is relative to the
  server's working directory or pass an absolute path." Never crash, and
  never answer a tool failure with a JSON-RPC error.

## Done means

- `server.py` exists and works as above.
- `test_server.py` exists, uses `unittest`, starts `server.py` as a
  subprocess, and exercises every tool and at least two error cases against
  `data/counts.tsv` and `data/samples.tsv`.
- You ran `python -m unittest test_server -v` and every test passed.
- Finish with a short summary listing the tools and the flagged samples you
  found in `data/`.
