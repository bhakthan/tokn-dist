# Example: Codebase graph — what breaks if I change X?

> "If I change `LookupPrice`, what else do I have to re-test?"

This walkthrough builds a small call graph over a six-file Go project and asks TOKN for the **blast radius** of a change: every symbol that can reach the one you touch, within a set number of hops. It runs entirely on your machine with the built-in `/codebase` command. No model call is needed to answer the graph questions.

| Capability | Where it lives | What you get |
|---|---|---|
| Build the graph | `/codebase build` in `tokn agent-repl` | A local call graph of the repo |
| Blast radius | `/codebase blast <symbol> [hops] [in\|out\|any]` | Symbols within N hops, by distance |
| Stats | `/codebase stats` | Symbol and edge counts |
| Path and distance | `/codebase path` / `/codebase distance` | Shortest call path between two symbols |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | `/codebase` ships in this release line | `tokn version` |
| Community tier | `/codebase` is free. No trial is needed | `tokn license status` shows Community |
| Go toolchain (optional) | Only to compile the fixture. Not required to run the graph | `go version` |
| A configured provider (optional) | `agent-repl` starts with your configured model. The `/codebase` commands themselves make no model call | See [SETUP.md](../../SETUP.md) |

Tier: **Community**. Domain modes need `tokn license trial`. This example does not.

## What leaves your machine

Nothing from the graph. `/codebase build` parses the fixture locally with Go's AST and writes its index to `.nospace\codebase-graph.json` inside the repo you point it at. It does not upload source. Starting `agent-repl` may contact your configured model provider, as any REPL session does.

The fixture is run from a scratch copy, so the `.nospace` folder never lands in the distribution repo.

## Steps

### 1. Copy the fixture to a scratch folder

**bash**
```bash
cp -r examples/codebase-graph/fixture/shop ~/shop-scratch
cd ~/shop-scratch
```

**PowerShell**
```powershell
Copy-Item -Recurse examples\codebase-graph\fixture\shop $HOME\shop-scratch
Set-Location $HOME\shop-scratch
```

The fixture has six Go files: `api.go`, `pricing.go`, `items.go`, `catalog.go`, `discount.go`, `receipt.go`. The call chain is:

```
HandleCheckout -> ComputeTotal -> SumItems -> ParseItems -> splitOn
                                  SumItems -> LookupPrice
                  ComputeTotal -> ApplyDiscount -> IsBulk
HandleCheckout -> FormatReceipt -> renderLine
ExportReport   -> FormatReceipt
```

Every function name is unique. The graph resolves calls by name, so duplicate names would make an edge ambiguous and drop it.

### 2. Start the REPL on the scratch folder

**bash**
```bash
tokn agent-repl --repo-root ~/shop-scratch
```

**PowerShell**
```powershell
tokn agent-repl --repo-root $HOME\shop-scratch
```

### 3. Build the graph

Inside the REPL:

```
/codebase build
/codebase stats
```

`build` indexes the Go files. `stats` should report the symbol and edge counts for the six files. Exact counts are not listed here because they depend on the Go extractor version.

### 4. Ask the blast-radius question

"What breaks if I change `LookupPrice`?" Use `in` to walk callers, which is the direction that matters for change impact:

```
/codebase blast LookupPrice 3 in
```

### 5. Ask the reverse question

"What does `HandleCheckout` depend on, and how deep does it go?" Use `out` to walk callees:

```
/codebase blast HandleCheckout 3 out
```

### 6. Ask about a helper with two callers

```
/codebase blast FormatReceipt 3 in
```

### 7. (Optional) Find a call path

```
/codebase path HandleCheckout LookupPrice
```

The output format for `path` was not captured in a run, so check what it prints on your build.

## What to look for

Expected results, computed by hand from the fixture. **These are expected, not a recorded run.** Your output should match the symbol sets. Ordering and line numbers may differ slightly.

**Step 4: `blast LookupPrice 3 in`** should return 4 symbols:

| Distance | Symbol | File |
|---|---|---|
| 0 | `shop.LookupPrice` | catalog.go |
| 1 | `shop.SumItems` | items.go |
| 2 | `shop.ComputeTotal` | pricing.go |
| 3 | `shop.HandleCheckout` | api.go |

Impacted files: `api.go`, `catalog.go`, `items.go`, `pricing.go`. Changing the price lookup puts the whole checkout chain in scope, but not `receipt.go`.

**Step 5: `blast HandleCheckout 3 out`** should return 9 symbols:

| Distance | Symbols |
|---|---|
| 0 | `HandleCheckout` |
| 1 | `ComputeTotal`, `FormatReceipt` |
| 2 | `ApplyDiscount`, `SumItems`, `renderLine` |
| 3 | `IsBulk`, `LookupPrice`, `ParseItems` |

`splitOn` sits at distance 4 (through `ParseItems`), so the 3-hop limit leaves it out. Raising the limit to 4 adds it.

**Step 6: `blast FormatReceipt 3 in`** should return 3 symbols:

| Distance | Symbol |
|---|---|
| 0 | `FormatReceipt` |
| 1 | `ExportReport`, `HandleCheckout` |

`ComputeTotal` is not in this set. It does not call `FormatReceipt`.

The pattern to take away: a change to a shared leaf like `LookupPrice` reaches the top-level entry point through several hops. A change to `FormatReceipt` reaches only two symbols.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `unknown command: /codebase` | Older TOKN build | Upgrade to v0.3.57+ and re-run `tokn version` |
| Blast returns only the origin | Graph not built, or the symbol name is wrong | Run `/codebase build`, then use the exact name (`LookupPrice`, not `lookupPrice`) |
| Fewer callers than expected | Duplicate function names make the call ambiguous, so the edge is dropped | Keep names unique, or check the qualified name with `/codebase find` |
| Python or other non-Go files show no edges | Only the Go extractor records call sites | Use Go files for this example |
| Banner says the trial has ended | Expected on Community | Harmless for this example. See [GETTING_STARTED.md](../../GETTING_STARTED.md) |
| REPL fails to start with a provider error | No model configured | Follow [SETUP.md](../../SETUP.md) for your provider. The graph commands do not need it once the REPL is up |

## See also

- [First ten minutes](../first-ten-minutes/README.md): install check, Community license, and a first agent run.
- [Examples index](../README.md): other walkthroughs by tier.
- [GETTING_STARTED.md](../../GETTING_STARTED.md) and [SETUP.md](../../SETUP.md).
