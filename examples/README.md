# TOKN examples

Synthetic, non-sensitive input files referenced by
[GETTING_STARTED.md](../GETTING_STARTED.md). They contain no real data of any
kind.

## `judgments/`

Two request files for the offline governed-judgment walkthrough. Both use the
local `rules` provider, so evaluating them makes no external judgment call and
needs
**no API key**.

| File | Describes | Expected decision |
|------|-----------|-------------------|
| `request-clean.json` | a run that finished with no recorded tool errors or blocks | `continue` / `RUNTIME_EVIDENCE_ONLY` |
| `request-errors.json` | the same run with 2 tool errors and 1 tool block | `revise` / `RECORDED_EXECUTION_FAILURE` |

Run them (from a directory you own — the commands write `bundle.json` there):

```bash
tokn judgments example > bundle.json
tokn judgments evaluate --bundle bundle.json --file request-clean.json  --mode advisory --air-gap
tokn judgments evaluate --bundle bundle.json --file request-errors.json --mode advisory --air-gap
```

Both exit `0`. The difference is in `decision.action` — a `revise` judgment means
the command worked and is telling you something about the run it was given.

`decision.applied` is always `false`: a judgment is advisory and authorises
nothing.

## Running all of it unattended

`../scripts/community-smoke.sh` (bash) and `../scripts/community-smoke.ps1`
(PowerShell) run the three domain previews **and** the same two judgment cases,
asserting the expected decision for each. They do not read the files in this
directory — each script writes its own inline copies (identical `state` fields,
a different `trace_id`) into a temp directory it deletes on exit — so nothing
here is modified and the scripts work from a bare binary download too.

```bash
bash scripts/community-smoke.sh        # from the repository root
```

```powershell
.\scripts\community-smoke.ps1          # from the repository root
```

Exit code `0` means every check passed.
