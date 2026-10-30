# Adaptive research journeys: learn the next evidence decision, not just a new prompt

Requires **TOKN v0.3.73 or newer**. These are runnable, end-to-end **synthetic
protein-prediction workflow exercises**. They use no sequences, structures,
biological scores or real measured GPU results. The goal is to make defensible
next-action decisions, not to establish that a protein has folded correctly.

The beginner, intermediate and research journeys differ in their starting
support, response patterns, remediation and evaluation work. They are not
three versions of the same explanation. **All three retain exactly the same
scientific and execution restrictions.**

## 1. Dependencies and the first complete run

For all offline exercises, the only dependency is an installed TOKN executable.
PowerShell uses its built-in JSON parser; a POSIX shell can display JSON directly.
No GPU, Docker, Python, Node, credentials, model service or paid call is needed.

Check installation before running:

```powershell
Get-Command tokn -ErrorAction Stop
tokn version
tokn biomol journey --help
tokn biomol journey demo --track beginner
```

POSIX shell:

```sh
command -v tokn
tokn version
tokn biomol journey --help
tokn biomol journey demo --track beginner
```

If TOKN is missing, use the repository's [installation guide](../../../GETTING_STARTED.md).
Do not install scientific models to make an offline example work.

The final command runs a real deterministic supervisor over recorded responses.
The learner responses are supplied fixtures, not observed human behaviour.
`replay_complete` means the supplied rounds were processed; it does **not**
mean a scientific question was solved.

## 2. One objective, three bounded loops

Our scenario is deliberately operational: *A protein-prediction computation
finished, but its metrics are absent. What should happen next?*

| Loop | Input and check | What it can change |
|---|---|---|
| Evidence | Closed predictor observations; unchanged rules recommend review, collection, comparison, abstention or an eligible untried predictor | A shadow next-action recommendation only |
| Understanding | A committed action, declared confidence and whether the answer was already revealed; compare against the reference | Per-skill support and counters in this run |
| Policy evaluation | Optional declared development/holdout dataset; compare recorded choices with baselines on the same subset | An aggregate report, never a policy update |

One outer `max_steps` budget pays **one step per evidence check**, **one per
observed learner response**, and **one per aggregate policy benchmark**.
The benchmark's internal cases are bounded by its dataset contract; they are
not individually charged supervisor steps. `no_progress` stops consecutive
learning steps without correct unaided transfer to a new declared family and
novel operational evidence. The final processed round completes replay; the
optional benchmark can still run if the step budget permits.

Every report retains `authority: none`, `acceptance: held_unvalidated`,
`parity: not_verified`, `scientific_status: evidence_held`,
`learning_claim: not_established` and `policy_update: none`.
Neither being a researcher nor receiving several matching AI opinions changes
those facts.

## 3. Beginner: full support, partial support, independent transfer

Start from this directory and run the explicit input file:

```powershell
$path = (Resolve-Path .\beginner.json).Path
$report = tokn biomol journey replay --input $path | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Beginner journey failed" }
$report.events | Select-Object round, skill, scaffold, feedback, transfer, stage_after, support_change
$report.skills
$report.stop_reason
```

```sh
tokn biomol journey replay --input "$PWD/beginner.json"
```

**Think aloud.** A completed process is not evidence sufficiency. Since
`metrics_present` is false, `collect_evidence` is the expected workflow action.
Changing `off` to `exact` does not create missing evidence or prove parity.

The file records six responses:

| Round | What the fixture records | Expected learning result |
|---|---|---|
| 1 | Correct answer, but already revealed | `ASSISTED_NOT_COUNTED`; worked support remains |
| 2 | Correct unaided answer from a new family | First transfer credit |
| 3 | Another correct unaided new family | `PROMOTED`; worked becomes partial |
| 4 | Copy of round 3's family and evidence | `REPEATED_FAMILY_NOT_COUNTED`; no transfer |
| 5 | Correct unaided new-family cofolding case | First credit at the partial stage |
| 6 | Another new-family correct answer | `PROMOTED`; partial becomes independent |

The stage measures this **operational skill**, not expertise in all molecular
biology. It is not a credential, access grant or scientific reliability score.
Families are operator-supplied opaque integers; TOKN cannot establish actual
biological independence from those integers. Renumbering identical evidence,
reordering predictors or changing cost/provenance does not earn transfer credit.
`initial_support` records the chosen track; `promotions_earned` counts actual
upward transitions, and `unaided_correct` excludes revealed answers.

### Fade the example instead of memorising it

For a **partial exercise**, make a copy of `beginner.json` outside the repository.
Before looking at a prior report, predict the outcome if round 4's answer is
revealed. It should still gain no transfer credit.

For a **problem-only exercise**, construct two new synthetic evidence cases
whose missing metrics require collection. Commit your own responses before
revealing the answer. Keep the family and `revealed` declarations truthful.
Rerun the full file: there is no hidden cross-run learner memory.

Passing a replay of answers written after reading its report is not evidence
of learning. A real teaching evaluation needs a blind unseen-family post-test.

## 4. Intermediate: confidence is a diagnostic, not authority

```powershell
$report = tokn biomol journey replay --input (Resolve-Path .\intermediate.json).Path |
    ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Intermediate journey failed" }
$report.events | Select-Object round, scaffold, feedback, stage_after, support_change
$report.skills
```

```sh
tokn biomol journey replay --input "$PWD/intermediate.json"
```

The learner starts with partial support. The first two cases have two distinct
completed predictors and available metrics. The rules recommend
`compare_existing`, not automatically launching a third predictor.

The fixture instead selects that third predictor at 9000/8500 confidence
basis points. Both errors emit `CONTRAST_REMEDIATION`. Two consecutive errors
reduce support from partial to worked; `support_change: down` remains visible
alongside contrast feedback. Rounds 3 and 4 correctly choose comparison on new
families and distinct operational evidence and recover to partial support.

**The counterintuitive move:** more confidence and more compute are not always
progress. Existing evidence may need comparison before any new computation.
`compare_existing` is a recommendation; this command does not compute structural
similarity or establish scientific agreement.

For a partial exercise, identify the single field that would invalidate
comparison: one predictor's `metrics_present: false`. Before replaying your
edited copy, predict `collect_evidence`. The confidence number never changes
the evidence rule.

## 5. Research: challenge TOKN rather than copy its answer

```powershell
$report = tokn biomol journey replay --input (Resolve-Path .\research.json).Path |
    ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "Research journey failed" }
$report.counterexamples
$report.events | Select-Object round, reference_agreement, correct, feedback
$report.policy_evaluation.paired
$report.policy_update
$report.steps
```

```sh
tokn biomol journey replay --input "$PWD/research.json"
```

This file uses `reference_basis: synthetic_independent_fixture`: supplied
references are compared with TOKN's unchanged rule recommendation. **These are
invented synthetic fixtures**, not independently reviewed biology.
`independent_declared` is reserved for caller-declared external references;
TOKN still cannot verify their actual independence. Rules-based exercises omit
`reference_agreement` because comparing the rules against themselves is circular.

Round 1 supplies `human_review` for an empty evidence case, while the rules
consider the first eligible predictor. The learner's answer is graded against
the supplied reference, not automatically against TOKN's rule. Round 1 is
reported as a counterexample candidate. It is a policy disagreement requiring
human interpretation, not proof that either side is scientifically correct.

Round 2 records a failed computation and correctly requests human review.
Round 3 has a longest-chain band too large for every allowed profile and
correctly abstains. **A justified “not enough support to proceed” is a useful
outcome, not a failure that must be retried away.**

The third loop then evaluates the embedded synthetic policy dataset:

- Development and holdout families/time buckets are structurally separated.
- Development GPU seconds are invented descriptive costs.
- Candidate decisions and baselines are compared on the same recorded holdout
  cases, including correct abstention.
- The omitted cost differs from the explicit zero; neither is filled in.
- A better action-label score does not establish better folding accuracy.
- `policy_update` remains `none`; a disagreement never rewrites the circuit.

The report spends seven steps: three evidence checks, three learner responses
and one aggregate benchmark.

For a problem-only exercise, write compatible synthetic reference labels before
seeing TOKN's recommendations, explain why a disagreement deserves review,
and identify what independently sourced evidence a **real** evaluation would
need. Do not derive a “reference” from the same model being evaluated.

## 6. Minimal-pair reasoning and honest stop conditions

The additional files isolate mechanisms instead of requiring a scientific run:

```powershell
tokn biomol journey replay --input (Resolve-Path .\minimal-pair.json).Path
tokn biomol journey replay --input (Resolve-Path .\budget-stop.json).Path
tokn biomol journey replay --input (Resolve-Path .\awaiting-response.json).Path
```

```sh
tokn biomol journey replay --input "$PWD/minimal-pair.json"
tokn biomol journey replay --input "$PWD/budget-stop.json"
tokn biomol journey replay --input "$PWD/awaiting-response.json"
```

`minimal-pair.json` changes only one observation's `metrics_present` between
rounds. The first needs collection; the second can consider an untried predictor.
This tests a causal decision boundary in the software, not a biological causal
effect. The output's `CONTRAST_REMEDIATION` is a feedback code, not an
automatically generated lesson or experiment.

`budget-stop.json` has only one step. TOKN can inspect evidence but cannot
grade the response: expect `step_budget_exhausted`, `steps: 1` and
`response_observed: false`.

`awaiting-response.json` omits the response: expect `awaiting_response`.
Missing is not wrong, zero-confidence or an implicit abstention.

To test stagnation, repeat one already-answered family in your own copy and
set `no_progress` to 2. Two consecutive non-transfer learning steps stop the
journey rather than inventing progress. Malformed or private fields produce
a nonzero error, not a successful-looking empty report.

## 7. Federated Claude Code, Codex and Copilot second opinions

Federated means **TOKN coordinating available coding-agent harnesses**, not
distributed training or sharing biological datasets. Discovery is automatic
and costs no model call:

```text
tokn biomol journey peers
```

The report names `claude-code`, `codex` and `copilot-cli`, installation status
and install guidance. `authentication: not_probed` is deliberate: an executable
on PATH does not prove a working login, compatible version or model access.

External calls are optional and **not part of offline demo/replay**. They need
all of: a compatible trusted CLI; its runtime (Node/npm if installed through
npm); an authenticated account/API credential; permitted network and trusted
TLS/proxy configuration; an existing private scratch root outside repositories.
Use each vendor's current setup/login instructions. TOKN never installs or
logs in for you. CLI version/flag incompatibility and auth failure remain errors.

After deciding to disclose this target-free round and potentially spend from
your peer accounts, explicitly consent:

```powershell
$scratch = Join-Path ([IO.Path]::GetTempPath()) ("tokn-peer-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $scratch | Out-Null
try {
    tokn biomol journey federate --input (Resolve-Path .\research.json).Path `
        --round 1 --scratch-root $scratch --consent --allow-external `
        --max-calls 2 --wall-timeout 60s
    if ($LASTEXITCODE -ne 0) { throw "Peer review failed; inspect the sanitized status, not a supposed scientific result" }
} finally {
    # Only remove the known empty root. Unresolved cleanup must be inspected.
    Remove-Item -LiteralPath $scratch -ErrorAction Stop
}
```

```sh
scratch="$(mktemp -d)"
scratch="$(cd "$scratch" && pwd -P)"
tokn biomol journey federate --input "$PWD/research.json" --round 1 \
  --scratch-root "$scratch" --consent --allow-external --max-calls 2 --wall-timeout 60s
code=$?
rmdir "$scratch"
test "$code" -eq 0
```

TOKN checks installed peers in Claude Code, Codex, Copilot order and selects
eligible peers until the call cap. To choose a subset, add
`--peers claude-code,copilot-cli`. No guessed model
identifier is needed; each harness uses its own configured/default model.

Only the selected round's allowed adapters and operational evidence are sent,
after a response is committed locally. The response, track, family, references, other rounds and
policy evaluation labels are withheld. Responses must be closed, eligible
action/adapter JSON. Raw stdout/stderr and invalid advice are not exported.

Each peer has separate fresh working and home/config directories beneath the
explicit scratch root. Only its relevant credential environment is forwarded.
No cached authentication files, settings, hooks or instructions are copied,
and TOKN does not refresh your real cached OAuth credentials.
Claude's bare mode requires `ANTHROPIC_API_KEY`.
Copilot's OS credential store may be used; file-based login configurations
are not imported into its empty home. Authentication compatibility varies.
Metadata-only help/version checks admit Claude 2.1.248+ and Copilot 1.0.105+
within those major/minor series when the required restriction flags exist.
Windows `.cmd`/script shims and non-regular executable aliases are refused.
This includes the Windows winget/MSIX Copilot app-execution alias and VS Code
shim directories: use a trusted regular executable, not those wrappers.
Unix symlinked installations are resolved before regular-file admission.
New major/minor versions remain held until their restriction profile is
reviewed; installing an update does not silently relax tool restrictions.
**Codex is discovered but execution is held:** a universal tool-free profile
has not been verified. Installation alone never authorizes a call.

The peer prompt uses the embedded default. A differing user-global override
requires `--allow-prompt-override` after reviewing it for private data.
The report records prompt source and SHA256, not the prompt itself.

TOKN requests restricted tool modes, bounds stdout/stderr, terminates the
wrapper process tree and enforces a shared wall timeout and call count.
Unresolved scoped cleanup is an explicit failure. **This is not OS-level containment of third-party
CLIs**, and it does not enforce a hard currency/token budget. Use only trusted
installations; account billing remains with their providers. No external peer
is allowed to become an alternative scientific executor. Tool/flag support
varies across versions; a failed request does not trigger permission bypass.

Matching peer opinions are labelled
`matching_opinions_not_independent_evidence`; disagreement is preserved.
Neither changes learner grades, reference labels, circuit policy or scientific
acceptance. Automatic selection with no eligible peers produces
`offline_only_no_eligible_peers` with per-peer reasons; explicitly requesting an
absent or ineligible peer fails. `credential_required` means Claude needs its
API key; `restriction_unverified` means the executable/profile was not admitted.
`--air-gap` refuses external calls before any peer launch.

This example's live vendor calls are optional, not a prerequisite for learning.
The shipped mechanism has fake-runner regression coverage; GPU or biological
effectiveness is not established by federated text reviews.

## 8. What this implementation does not learn

There is no weight training, automatic scientific discovery, hidden learner
profile, medical inference or cross-run memory. Editing input files and replaying
them is explicit, caller-owned state. The system adapts support within the run
and evaluates supplied policies; it does not claim to improve its own biology.

Actual scientific improvement would require frozen checks, independently
reviewed real labels, appropriate family/time separation, matched hardware,
preregistered comparisons, drift/rollback controls and human interpretation.
Real model execution still follows the separate
[guarded staging and review procedure](../README.md#3-stage-an-actual-future-linux-gpu-environment).
