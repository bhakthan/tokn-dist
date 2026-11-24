# Ethnointelligence: stated context versus open context

> A TOKN walkthrough: the same question, "is a 70,000 misstatement material?", asked by two teams with different stated context. One team declares its regime; the other states nothing. TOKN keeps the unstated part visible as **open** instead of quietly filling it with a default.

**Minimum version:** TOKN **v0.3.125** (`tokn version` should print `0.3.125`).

## What you need

| Requirement | Why | Check | Needs a model? |
|---|---|---|---|
| TOKN v0.3.125 or later | `tokn environment`, `tokn connect` and the finrisk materiality gate | `tokn version` | — |
| A scratch folder | The steps create `.nospace/` folders; never run them inside a repo you care about | `New-Item -ItemType Directory $env:TEMP\ethno-lab` | — |
| A hosted model key and a finrisk trial or licence | Step 4 only | `tokn license trial` | Yes (step 4 only) |

Steps 1, 2, 3 and 5 need **no model and no network**. Step 4 needs a hosted model
and the `finrisk` domain, which is part of the trial or a paid licence. On the
community tier, `finrisk` refuses to run. The walkthrough says so where it
matters.

## The idea in one paragraph

Analysts say "it depends on the context". TOKN makes that concrete. The
**Environment Contract** describes a working environment in eight facets:
*domain, measures, practice, regime, culture, evidence, compute* and
*capability*. Each facet shows where its value came from: **declared** (someone
wrote it in `.nospace/environment.json`), **probed** (TOKN checked this machine),
or **open** (nobody stated it). Core rule: a fact nobody stated stays open. TOKN
never fills it with a foreign default.

Culture here means how meaning is communicated (register, units, structure),
not translation.

---

## Step 1: a bare folder, six facets open

Create the scratch lab and run the read-only view in an empty folder.

```powershell
New-Item -ItemType Directory -Force "$env:TEMP\ethno-lab\bare" | Out-Null
Set-Location "$env:TEMP\ethno-lab\bare"
tokn environment
```

```bash
mkdir -p "$TMPDIR/ethno-lab/bare" && cd "$TMPDIR/ethno-lab/bare"
tokn environment
```

Captured output (real binary, v0.3.124):

```text
Folder: .

Domain — the concepts and words used here
  open — not stated; TOKN will not assume a default

Measures — units, tolerances, and thresholds
  open — not stated; TOKN will not assume a default

Practice — how work is done: workflows, checks, and when to escalate
  open — not stated; TOKN will not assume a default

Regime — rules and regulations that apply
  open — not stated; TOKN will not assume a default

Culture — how things are said and explained here
  open — not stated; TOKN will not assume a default

Compute — this machine, and what it is allowed to reach
  os: windows  (source: checked on this machine (runtime.GOOS))
  arch: amd64  (source: checked on this machine (runtime.GOARCH))
  cpu_count: 16  (source: checked on this machine (runtime.NumCPU))
  ollama: not found  (source: checked on this machine (PATH lookup: ollama))
  llama-server: found  (source: checked on this machine (PATH lookup: llama-server))
  egress: open — not stated; TOKN will not assume a default

Evidence — which sources count as authoritative
  open — not stated; TOKN will not assume a default

Capability — what is actually available to use here
  modes: 53  (source: checked on this machine (introspect.Modes))
  domain_plugs: 38  (source: checked on this machine (introspect.Modes))
  provider_keys_set: none  (source: checked on this machine (environment variables))

To state something, add it to .nospace/environment.json. This page only reads; it changes nothing.
```

**What you are seeing:** the compute and capability facets are *probed*
(TOKN checked the machine). The rest are *open*. The probed values will differ on
your machine, and `cpu_count` and `llama-server` show that. Nothing was written.

**Observed vs. inferred:** "open" is the observed output. Reading it as "TOKN
would refuse to answer a regime question here" is an inference from the rule
above, and step 4 tests it.

---

## Step 2: a declared folder, same machine, different answers

The team's declarations live in `team-ifrs/environment.json` in this example.
TOKN reads `.nospace/` only, so copy the file in. This keeps your own repo
clean, because `.nospace/` is git-ignored in this folder.

```powershell
Set-Location C:\path\to\tokn-dist\examples\ethnointelligence
New-Item -ItemType Directory -Force "$env:TEMP\ethno-lab\team-ifrs\.nospace" | Out-Null
Copy-Item team-ifrs\environment.json "$env:TEMP\ethno-lab\team-ifrs\.nospace\"
Set-Location "$env:TEMP\ethno-lab\team-ifrs"
tokn environment
```

```bash
cd path/to/tokn-dist/examples/ethnointelligence
mkdir -p "$TMPDIR/ethno-lab/team-ifrs/.nospace" && cp team-ifrs/environment.json "$TMPDIR/ethno-lab/team-ifrs/.nospace/"
cd "$TMPDIR/ethno-lab/team-ifrs" && tokn environment
```

Captured output (trimmed to the declared facets; the compute and capability
sections match step 1):

```text
Domain — the concepts and words used here
  material: large enough to change a reader's decision; always name the regime and basis  (source: declared in .nospace/environment.json)
  misstatement: a known or likely error in reported figures  (source: declared in .nospace/environment.json)

Measures — units, tolerances, and thresholds
  currency: EUR  (source: declared in .nospace/environment.json)
  materiality_basis: total assets  (source: declared in .nospace/environment.json)
  rounding: whole euros; ratios shown to two decimal places of a percent  (source: declared in .nospace/environment.json)
  tolerance: compare the unrounded ratio against the threshold  (source: declared in .nospace/environment.json)

Practice — how work is done: workflows, checks, and when to escalate
  escalation: any item in the borderline band or above goes to the controller for written sign-off  (source: declared in .nospace/environment.json)

Regime — rules and regulations that apply
  jurisdiction: IFRS  (source: declared in .nospace/environment.json)
  standard: principles-based materiality (IAS 1 and IAS 8)  (source: declared in .nospace/environment.json)

Culture — how things are said and explained here
  numbers: always with explicit units (EUR, %)  (source: declared in .nospace/environment.json)
  register: formal written English  (source: declared in .nospace/environment.json)
  structure: state the basis before the conclusion  (source: declared in .nospace/environment.json)

Evidence — which sources count as authoritative
  primary: audited financial statements  (source: declared in .nospace/environment.json)
  secondary: ledger extract signed by the controller  (source: declared in .nospace/environment.json)
```

`compute.egress` is also declared in this file (`"none"`), and TOKN accepted it.
Only `capability` is refused outright (step 3). Keep your declarations to facts
you can name; leave anything you cannot name open.

The JSON view shows the same entries with machine-readable sources:

```powershell
tokn environment --json
```

```text
      "facet": "regime",
        "entries": [
          {
            "key": "jurisdiction",
            "value": "IFRS",
            "source": "declared",
            "from": ".nospace/environment.json"
```

**Observed vs. inferred:** the displayed facts are observed. That the team's
numbers are *consistent* with its regime is an inference you would have to
check yourself.

---

## Step 3: TOKN refuses an invalid declaration

`invalid/environment.json` declares `capability`, which TOKN probes on the
machine rather than accepting from a file.

```powershell
New-Item -ItemType Directory -Force "$env:TEMP\ethno-lab\invalid\.nospace" | Out-Null
Copy-Item invalid\environment.json "$env:TEMP\ethno-lab\invalid\.nospace\"
Set-Location "$env:TEMP\ethno-lab\invalid"
tokn environment
```

Captured output (the last line of the error, verbatim):

```text
Error: environment contract: .nospace/environment.json: facet "capability" cannot be declared; it is probed on this machine
```

An empty value is also refused rather than treated as "not stated". Create one
to see it:

```powershell
New-Item -ItemType Directory -Force "$env:TEMP\ethno-lab\empty\.nospace" | Out-Null
'{"measures":{"currency":""}}' | Set-Content -Encoding utf8 "$env:TEMP\ethno-lab\empty\.nospace\environment.json"
Set-Location "$env:TEMP\ethno-lab\empty"
tokn environment
```

```text
Error: environment contract: .nospace/environment.json: measures.currency is empty; remove it to leave it open
```

**Why this matters:** a typo that silently drops a regime is more dangerous than
a loud error. TOKN fails, names the file and the key, and tells you the fix.

---

## Step 4: finrisk materiality, named regime versus unnamed (needs a model and the finrisk licence)

The materiality gate does not read `environment.json`. Version 0.3.125 only
displays the contract; it does not wire it into the gate. Either you or the
agent that read the contract must pass the jurisdiction to the tool, which is
why prompt B in [prompt.md](prompt.md) names IFRS explicitly. What the
contract adds is visibility: in the bare folder, step 1 already showed that the
regime was **open**.

Put the two prompts from [prompt.md](prompt.md) into `a.txt` and `b.txt`, then
run them. This needs a trial or licence (`tokn license trial`) and a provider
key; see [.env.example](.env.example).

```powershell
Set-Location "$env:TEMP\ethno-lab\bare"
tokn agent-run --mode finrisk --model-provider anthropic --model-name claude-haiku-5-5 --prompt-file a.txt --mcp-disabled --no-stdin --run-timeout 300s

Set-Location "$env:TEMP\ethno-lab\team-ifrs"
tokn agent-run --mode finrisk --model-provider anthropic --model-name claude-haiku-5-5 --prompt-file b.txt --mcp-disabled --no-stdin --run-timeout 300s
```

`--mode` belongs to `agent-run` and `agent-repl`; `tokn --mode` fails.

### A. Nothing named: the gate refuses to guess

Captured from a live run (Claude Haiku 5.5, v0.3.125). The tool call carried
no jurisdiction:

```text
tool.call   assess_materiality {"amount":70000,"total_assets":1000000}
tool.result {"jurisdiction":"","level":"unclassified",
             "open":"regime unknown: no jurisdiction was given, so no thresholds apply; materiality not classified",
             "status":"unclassified"}
```

The model's answer (excerpt):

```text
**Status: unclassified.** The tool did not classify the misstatement as material or immaterial.
- Ratio produced: No. The output contains no ratio or threshold field.
Materiality thresholds depend on the reporting regime (for example SEC, IFRS, EU, or UK), and none
was supplied, so I did not assume one. The 70,000 figure is 7% of total assets. That is simple
arithmetic I did myself, not a tool output, and it is not a materiality conclusion because no
benchmark has been applied.
To get a classification: Tell me the reporting framework or jurisdiction and I will rerun the assessment.
```

There is no ratio and no level, and no default regime was used. The open fact
is named, and the answer tells you how to close it.

### B. IFRS named: the gate classifies, and says how far to trust it

```text
tool.call   assess_materiality {"amount":70000,"jurisdiction":"IFRS","total_assets":1000000}
tool.result {"jurisdiction":"IFRS","level":"material","ratio":0.07,"status":"success",
             "statement":"The amount of 70000.00 represents 7.00% of total assets (1000000.00), classified as
              material under IFRS thresholds. Note: this jurisdiction uses principles-based materiality;
              quantitative thresholds are indicative only."}
```

The model's answer (excerpt):

```text
**Result: Yes, a 70,000 misstatement is classified as material under IFRS.**
- IFRS is principles-based. Under IFRS, materiality also depends on qualitative factors such as
  whether the misstatement changes a trend, flips a profit to a loss, affects covenant compliance,
  or involves related parties. A 7% ratio does not settle the question alone.
- I did not verify the "environment contract" you mentioned. I used the jurisdiction value you specified.
```

**What changed between A and B:** only one stated fact, the regime. Once it is
named, the same tool, the same numbers and the same model produce a
classification, and the result carries a caveat specific to that regime.
Without it, you get an honest "unclassified" instead of a confident answer
under a regime nobody chose.

**Observed vs. inferred:** the tool calls, results and answers are observed. In
B the model itself says it used the jurisdiction from the prompt, not from the
contract, so this run does not test automatic wiring (which does not exist).
Each run cost under one US cent; your figures will vary with your provider.

---
## Step 5: a connect preview in a scratch folder

`tokn connect` shows what it would write before changing anything. This
example uses the `project` host in a scratch folder. Your real `~/.copilot` and
`~/.claude.json` are never touched.

```powershell
New-Item -ItemType Directory -Force "$env:TEMP\ethno-lab\project" | Out-Null
Set-Location "$env:TEMP\ethno-lab\project"
tokn connect project
```

```text
Preview — TOKN would add this entry in <scratch>\project\.mcp.json (this project):
  in "mcpServers":
  + "tokn": {
  +   "command": "<path to>\tokn.exe",
  +   "args": [
  +     "serve",
  +     "--profile",
  +     "simple"
  +   ]
  + }
Nothing was changed. Re-run with --yes to apply.
```

Only add `--yes` in a folder you own. It writes only the `tokn` entry, through
an atomic write with a `.tokn-bak` backup. `--remove` disconnects. `serve`
takes `--profile simple` or `--profile full`.

---

## What other CLIs would do

Many tools make a silent choice on your behalf: a default currency, a default
jurisdiction, a default register. That choice is convenient, and it is correct
only sometimes. The output looks the same either way, so the choice is easy to
miss.

TOKN's contract makes the choice visible. A fact nobody stated appears as
**open**, and the gate that needs it refuses to classify until someone names
it. You do not have to trust a hidden default.

---

## Worked-example fading

### A. Fully solved: the IFRS team

Declared facts: IFRS regime, EUR, total-assets basis, formal written register.
Open facts: none in the regime or measures facets.

Metacognition: which facts in the team's question were open *before* the file
was added? (Answer: the regime, the currency and the basis.)

### B. Partial: fill in measures

Start from `team-ifrs/environment.json`. Remove the `measures` section and add
your own. Use this checklist:

- currency (with its unit)
- the basis the threshold is a fraction of
- one rounding rule
- one tolerance rule

Run `tokn environment` and confirm that the measures facet now shows
`declared` and the others are unchanged. Then ask yourself: which measure did
you have to guess, and should it have stayed open?

### C. Problem only: declare your own environment

Pick a small, real-feeling question from your own work, such as a reconciliation
tolerance or a sample size. Write `.nospace/environment.json` for your context.
Use only facts you can name.

Predict, before you run it, which facets will be open. Then run
`tokn environment` and compare.

**Metacognition prompt, for any of the three:** *which of my facts were open
when I started, and which of them did I just assume?*

---

## Output and cleanup

- Everything above runs in a scratch folder under `$env:TEMP\ethno-lab`. Delete
  it when you finish: `Remove-Item -Recurse -Force "$env:TEMP\ethno-lab"`.
- `.nospace/` and `.tokn/` are git-ignored in this folder. Live runs write
  session checkpoints under `.tokn/`, and those can contain internal prompts.
  Never commit them.
- `tokn environment` writes nothing. `tokn connect` writes only with `--yes`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Every facet is `open` | The file is not in `.nospace/` | Copy it there; TOKN reads `.nospace/environment.json` only |
| `facet "…" cannot be declared` | You declared `capability` | Remove it; it is probed on the machine |
| `… is empty; remove it to leave it open` | An empty string | Delete the key, or give it a real value |
| `domains:finrisk is not included in the community tier` | No trial or licence | `tokn license trial`, or skip step 4 |
| `tokn --mode finrisk` fails | `--mode` belongs to `agent-run` / `agent-repl` | Use `tokn agent-run --mode finrisk` |

## Links

- [prompt.md](prompt.md): the exact prompts for step 4.
- [team-unstated/README.md](team-unstated/README.md): the intentionally empty team folder.
- [first-ten-minutes](../first-ten-minutes/README.md): onboarding, version and licence checks.
- [finrisk-system-one](../finrisk-system-one/README.md): a finrisk walkthrough with a typed decision request.
