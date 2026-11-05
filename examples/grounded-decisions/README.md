# Example: Grounded decisions — the web and your knowledge base in one call

> "Search the web, read our policy, and give me a typed answer with sources, in one call."

**The scenario.** You run the Travel Desk at *Example Corp* (a fictional company).
Request **TR-1042** comes in: a solutions engineer wants to fly to Lisbon to present at a
customer workshop. Departure is 8 days away. To route the request you need four answers:

| Question | Where the fact lives | How often it changes |
|---|---|---|
| What is the destination's current travel advisory level? | A government website | Any day |
| Must the trip be registered with the travel insurer? | Your duty of care standard | Rarely |
| Was it requested inside the booking window? | Your travel policy plus the request dates | Rarely |
| Is a security briefing mandatory? | Your policy **and** the advisory level | Both |

The last question needs facts from **both** places. A decision model alone cannot answer
any of them reliably: it does not know today's advisory, and it has never read your policy.

The usual fix is a pipeline you have to build and keep running yourself:

```text
search the web ─┐
                ├─► merge, trim, de-duplicate ─► decision model ─► answers (no sources)
search the KB  ─┘
```

`tokn system-one ground` does this in **one call**:

```text
trip.json ─► one shared evidence pack (web + kb/ folder + optional TOKN memory)
          ─► every question answered against the same pack
          ─► typed answers + probability + confidence + evidence-sufficiency + sources
```

Every question in the request shares the same retrieval, so four questions cost one search
and one decision call, not four of each. An answer that the evidence cannot support is
returned as **unknown**, not guessed.

## What this example shows

| Step | Capability | Command | Needs |
|---|---|---|---|
| 3 | Check the routing logic offline | `tokn circuit test` | nothing |
| 4 | Knowledge base only: answers it can support, abstains on the rest | `--sources docs --docs-dir kb` | decision backend |
| 5 | Web and knowledge base as one shared retrieval | `--sources web,docs --docs-dir kb` | + WebIQ key |
| 7 | Let the model search again, and see which source mattered | `--rounds 2 --influence` | same |
| 8 | Freshness and trusted sites only | `max_age`, `allow_domains` | same |
| 9 | Save the evidence and replay it for an audit | `--snapshot-out` / `--replay` | decision backend |
| 10 | Route the whole request through a decision circuit | `tokn circuit run --ground` | same as step 5 |
| 11 | Add what TOKN has learned in your sessions | `--memory` | optional |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.79 or later | Ships `system-one ground` and `circuit run --ground` | `tokn version` |
| A System One decision backend | Answers the typed questions (steps 4–11) | `tokn system-one status` |
| A WebIQ key (optional) | Live web search (steps 5, 7, 8 and 10) | see step 2 |

Steps 1 and 3 need no credentials at all. Without a WebIQ key, steps 4 and 9 still work
on the knowledge base alone. No Python, Docker or database is needed.

### What leaves your machine

- **Knowledge base search is local.** TOKN reads `kb/` on your machine with an offline
  lexical search. Nothing is uploaded to search it.
- **Web search** sends the search queries (the `queries` in `trip.json`, or queries TOKN
  derives from the questions) to WebIQ.
- **The decision call** sends the `state`, the questions and the selected evidence
  passages (including the matching `kb/` passages) to your System One backend. Retrieved
  text is placed inside an evidence envelope as **data**; it is never treated as
  instructions.
- `tokn circuit test`, `tokn circuit analyze` and `--replay` retrieval make no search calls.

## 1. Look at the files

```text
grounded-decisions/
├── kb/                               ← the knowledge base: any folder of md/txt/csv/json/html
│   ├── travel-policy.md              approval by advisory level, 14-day booking window
│   ├── duty-of-care.md               insurance registration, security briefing rule
│   └── expenses.md                   a distractor: relevant-sounding, answers nothing here
├── trip.json                         the grounded request: state + 4 questions + search hints
├── state.json                        the same trip, as the state for the circuit in step 10
├── travel-approval.circuit.json      routes the trip to an approval path
└── travel-approval.vectors.json      offline test cases for the circuit
```

Open `trip.json`. It is an ordinary System One request (`state` plus typed `questions`)
with three optional grounding fields:

| Field | In this example | Effect |
|---|---|---|
| `queries` | three search phrases | What to search for. Omit it and TOKN derives queries from the state and questions |
| `allow_domains` | `["travel.state.gov"]` | Web results from other hosts are dropped. Does not affect `kb/` |
| `max_age` | not set (step 8 adds it) | Drop dated evidence older than this |

The questions use the two common decision types:

- **`choice`** — pick one option from `criteria` (`advisory_level`: `level_1` … `level_4`).
- **`noul`** — a yes/no probability between 0 and 1 (`insurance_registration`,
  `booking_window_ok`, `security_briefing`).

## 2. Configure the backends

**Decision backend.** Any System One backend works: Jev, Nimble, Microsoft Decision-1, or
the OpenAI / Azure OpenAI Decisions API. The [decisions-api](../decisions-api/README.md)
example shows each configuration. For example, OpenAI:

```bash
export SYSTEMONE_BACKEND=openai
export OPENAI_API_KEY=<your OpenAI key>
```

**Web search (optional).** Set your WebIQ key:

```bash
export WEBIQ_API_KEY=<your WebIQ key>
```

TOKN also reads the name `WEB-IQ-KEY`, which suits `credentials.env` (most shells cannot
export a name containing hyphens). Put these in your shell or in
`~/.tokn/config/credentials.env`. TOKN does not load a
backend switch or endpoint from a repository `.env`, because they decide where data is sent.
PowerShell uses `$env:NAME = "value"`.

Check the decision backend without calling it:

```bash
tokn system-one status
```

## 3. Check the routing logic offline first

Before spending any model calls, check what the circuit does with each possible answer.
This step needs no credentials and no network:

```bash
cd examples/grounded-decisions
tokn circuit test travel-approval.circuit.json --vectors travel-approval.vectors.json
```

Recorded output:

```text
PASS  level_1_booked_early_auto_approves -> auto_approve (normal_and_on_time)
PASS  level_1_short_notice_needs_manager -> manager_approval (manager)
PASS  level_3_needs_vp_and_briefing -> vp_approval_and_briefing (reconsider)
PASS  level_4_is_prohibited -> prohibited (do_not_travel)
PASS  advisory_not_found_goes_to_travel_desk -> travel_desk_review
PASS  low_confidence_advisory_goes_to_travel_desk -> travel_desk_review
6 passed, 0 failed
```

The fifth vector matters most for this example. When the advisory level **cannot be
found**, the circuit sends the trip to a human. That is exactly what the policy says
(*"Do not assume Level 1"*), and it is what grounding produces when the evidence is thin.

```bash
tokn circuit analyze travel-approval.circuit.json
```

This lists every reachable output and shows that the circuit abstains to
`travel_desk_review` in 4 of its 15 abstract states.

## 4. Knowledge base only

Ask all four questions with the knowledge base as the only source:

```bash
tokn system-one ground --file trip.json --sources docs --docs-dir kb
```

**Predict first.** Before you read the result, decide which of the four questions
`kb/` can answer on its own. Then compare.

Expected (illustrative and trimmed; exact values vary by model):

```json
{
  "answers": {
    "insurance_registration": {"type": "noul", "noul": 0.97},
    "booking_window_ok":      {"type": "noul", "noul": 0.04}
  },
  "unknown": {
    "advisory_level":    "insufficient_evidence",
    "security_briefing": "insufficient_evidence"
  },
  "sufficiency": {
    "advisory_level": 0.08, "insurance_registration": 0.93,
    "booking_window_ok": 0.9, "security_briefing": 0.21
  },
  "sources": [
    {"id": "S1", "source": "docs", "trust": "internal", "path": "travel-policy.md#1", "text": "..."},
    {"id": "S2", "source": "docs", "trust": "internal", "path": "duty-of-care.md#1", "text": "..."},
    {"id": "S3", "source": "docs", "trust": "internal", "path": "expenses.md#1", "text": "..."}
  ],
  "decision_calls": 1
}
```

What happened:

- **`insurance_registration`** is answered: `duty-of-care.md` says every international
  trip must be registered.
- **`booking_window_ok`** is answered *false*: the policy needs 14 days; the trip was
  requested on 1 October for a 9 October departure.
- **`advisory_level`** is **withheld**. Nothing in `kb/` says what Portugal's advisory
  level is. Each question gets a hidden *evidence-sufficiency* check in the same call,
  and this one scored below the 0.5 threshold. The model's raw guess is kept in
  `withheld` for inspection but is never reported as an answer.
- **`security_briefing`** is withheld too: the rule is in `duty-of-care.md`, but it
  depends on the advisory level, which the knowledge base does not have.

This is the core safety property: **thin evidence produces "unknown", not a confident
guess.** Change the threshold with `--sufficiency 0.7` (stricter) or turn gating off with
`--sufficiency -1`.

## 5. Add the web: one shared retrieval

Run the same request with both sources:

```bash
tokn system-one ground --file trip.json --sources web,docs --docs-dir kb
```

TOKN searches the web and `kb/` with the same queries, merges and de-duplicates the
results into **one** evidence pack, and asks all four questions against it in one
decision call.

Expected (illustrative and trimmed; the advisory level is whatever the site says today):

```json
{
  "answers": {
    "advisory_level":         {"type": "choice", "choice": "level_1", "confidence": 0.91,
                               "probabilities": {"level_1": 0.91, "level_2": 0.07, "level_3": 0.01, "level_4": 0.01}},
    "insurance_registration": {"type": "noul", "noul": 0.97},
    "booking_window_ok":      {"type": "noul", "noul": 0.04},
    "security_briefing":      {"type": "noul", "noul": 0.06}
  },
  "sources": [
    {"id": "S1", "source": "web",  "trust": "external", "url": "https://travel.state.gov/...", "text": "..."},
    {"id": "S2", "source": "docs", "trust": "internal", "path": "travel-policy.md#1",  "text": "..."},
    {"id": "S3", "source": "docs", "trust": "internal", "path": "duty-of-care.md#1",   "text": "..."}
  ],
  "decision_calls": 1
}
```

Put the two runs side by side:

| Question | Step 4: `kb/` only | Step 5: web + `kb/` | Why it changed |
|---|---|---|---|
| `advisory_level` | unknown | `level_1` | The web supplied the missing fact |
| `insurance_registration` | yes | yes | Policy only; the web adds nothing |
| `booking_window_ok` | no | no | Policy plus dates; the web adds nothing |
| `security_briefing` | unknown | no | Needs the policy rule **and** the web fact together |

`security_briefing` is the point of a *shared* retrieval. Neither source answers it alone;
one evidence pack holding both does. Two separate pipelines would each have returned
"don't know".

## 6. Read the result

| Field | What it tells you |
|---|---|
| `answers` | Only grounded answers: enough evidence, not refused |
| `unknown` | Withheld question → reason: `insufficient_evidence`, `no_evidence` or `refused` |
| `withheld` | The model's raw answer for a withheld question, for inspection only |
| `sufficiency` | Evidence-sufficiency (0–1) per question |
| `sources` | Exactly the passages the model saw, numbered `S1`, `S2`, … in rank order |
| `rounds` | One entry per retrieval round: queries, strategy, passages retrieved and new |
| `snapshot.hash` | Fingerprint of the evidence pack (see step 9) |
| `decision_calls` | Every decision API call made, including influence checks |
| `warnings` | Anything dropped or trimmed, and why |

## 7. Let the model look again, and see which source mattered

```bash
tokn system-one ground --file trip.json --sources web,docs --docs-dir kb --rounds 2 --influence
```

- **`--rounds 2`** — after the first round, the decision model may steer one more
  retrieval for unresolved questions (narrow, broaden, prefer recent, or stop). Rounds
  are a hard cap (1–3), and the round with the most grounded answers wins. If everything
  was answered in round 1, it stops early.
- **`--influence`** — re-asks with each top source left out and reports how far the
  answer moved. Expected: removing the `travel.state.gov` passage moves `advisory_level`
  a lot (and may flip it); removing `expenses.md` moves nothing. That tells you which
  source the decision actually rested on.

## 8. Freshness and trusted sites only

Advisories change; a cached page from last year is a liability. Add to `trip.json`:

```json
"max_age": "720h"
```

or pass `--max-age 720h` (30 days). Dated passages older than that are dropped before the
model sees them. This includes `kb/` files, which are dated by their last modification
time, so a policy nobody has touched in a year is dropped too. That is often what you
want; if not, leave `max_age` out. Every drop is listed in `warnings`.

`allow_domains` already limits the web to `travel.state.gov`; add `deny_domains` to block
specific hosts. These two apply to web results only, never to `kb/`.

## 9. Save the evidence, replay it for an audit

```bash
tokn system-one ground --file trip.json --sources web,docs --docs-dir kb --snapshot-out pack.json
tokn system-one ground --file trip.json --replay pack.json
```

`pack.json` holds every passage the model saw, a timestamp and a sha256 hash, written with
owner-only permissions. Replay re-decides against **exactly** that evidence with no search
at all, so an auditor can ask in six months *"what did the model see when it routed
TR-1042?"* and get the same evidence back. The decision call still goes to your backend.

Replay refuses `--sources`, `--docs-dir`, `--memory` and `--query`: the snapshot *is* the
evidence. If the current policy (for example a tighter `--max-age`) drops a replayed
passage, the result carries a new, *derived* hash and a warning, so the hash always
matches the evidence actually used.

Add `pack.json` to `.gitignore` if it may quote internal documents.

## 10. Route the whole request through the circuit

Step 3 tested the routing logic with fixed answers. Now let grounded answers drive it:

```bash
tokn circuit run travel-approval.circuit.json --state state.json \
  --ground --sources web,docs --docs-dir kb --explain
```

The circuit's gates are planned and retrieved **once** and shared by every stage. Each
gate also gets the evidence-sufficiency check; a gate the evidence cannot support reads
**unknown**, and the circuit's `on_unknown` takes over.

Expected:

| Sources | `advisory_level` | `booking_window_ok` | Output |
|---|---|---|---|
| `web,docs` | `level_1` | no (8 days' notice) | **`manager_approval`** (arm `manager`) |
| `docs` only | unknown | no | **`travel_desk_review`** (`on_unknown`) |

The second row is the circuit doing what the policy demands: no confirmed advisory level,
no automatic route. The evidence hash is printed on stderr; add `--snapshot-out pack.json`
to keep it.

## 11. Add what TOKN has learned (optional)

```bash
tokn system-one ground --file trip.json --sources web,docs --docs-dir kb --memory
```

`--memory` adds TOKN's memory stores (facts and preferences captured in your earlier TOKN
sessions) as a third source in the same pack. It is read-only and local. With an explicit
`--sources` list, `--memory` adds `memory` to it.

## Try it yourself

Each change below has a predictable effect. Predict it, run it, then check.

1. **Book earlier.** In `state.json`, set `"departure": "2026-10-30"` and rerun step 10.
   Expected: `auto_approve` (arm `normal_and_on_time`), if the advisory is still Level 1.
2. **Remove a policy.** Move `kb/duty-of-care.md` out of the folder and rerun step 5.
   Expected: `insurance_registration` becomes unknown. Which other answer changes, and why?
3. **Write your own question.** Add a `noul` question to `trip.json` asking whether the
   flight may be booked in premium economy (Lisbon is about 7 hours from New York).
   Which file answers it? Check `sources` to confirm.

## What to look for

| Check | Expected |
|---|---|
| `tokn circuit test ...` | `6 passed, 0 failed` |
| Step 4, `kb/` only | `advisory_level` and `security_briefing` in `unknown` |
| Step 5, web + `kb/` | All four answered; `sources` mixes `web` and `docs`; `decision_calls` is 1 |
| Step 7 with `--influence` | The government page moves `advisory_level` most; `expenses.md` moves nothing |
| Step 9, `--replay` | Same `snapshot.hash` as the saved pack |
| Step 10, `web,docs` | `manager_approval` |
| Step 10, `docs` only | `travel_desk_review` |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `grounded: web source unavailable: set WEB-IQ-KEY ...` | No WebIQ key | Set the key, or use `--sources docs` |
| `--sources docs needs --docs-dir <folder>` | No folder given | Add `--docs-dir kb` |
| `systemone: backend not configured` | No decision backend | See step 2 and `tokn system-one status` |
| Everything is `insufficient_evidence` | The search found nothing relevant | Check `sources`; improve `queries`; relax `allow_domains` |
| No web sources despite a key | `allow_domains` dropped them, or `max_age` was too strict | Read `warnings`; relax the filter |
| `kb/` passages missing after adding `max_age` | The files are older than `max_age` by modification time | Remove `max_age`, or refresh the files |
| `--replay uses the snapshot's evidence; drop --sources ...` | Source flags with `--replay` | Remove them |
| `--sources web is disabled by --air-gap` | Air-gap mode blocks the web | Use `--sources docs`, or `--replay` a saved pack |

## Related

- [decisions-api](../decisions-api/README.md): typed decisions without retrieval, and every backend's configuration.
- [decision-circuits](../decision-circuits/README.md): circuits, ledgers and evals in depth.
- [decision-council](../decision-council/README.md): several decision models voting.
- [SETUP.md](../../SETUP.md)
