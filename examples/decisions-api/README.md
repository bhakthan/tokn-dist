# Example: Typed decisions with the Decisions API

> "Ask a model yes/no questions about a message and get calibrated probabilities back, not prose."

The Decisions API (`POST /v1/decisions`) answers **typed questions** about an input. A `predicate` question returns a probability between 0 and 1, and a model may refuse a question instead of guessing. It is served by OpenAI with `gpt-6-luna` and, generally available since October 2026, by **Azure OpenAI in Microsoft Foundry** at `https://<resource>.openai.azure.com/openai/v1/decisions`.

This example shows two ways to call it:

1. **Directly** with the OpenAI Python SDK (`decide.py`).
2. **Through TOKN** with `tokn system-one evaluate` (`request.json`). TOKN applies the same strict validation it uses for every decision backend, so code written against Jev, Clef, Nimble or Microsoft-Decision-1 works unchanged.

## What this example shows

| Capability | What you will do | Command |
|---|---|---|
| Direct SDK call | Three predicate questions about one customer message | `python decide.py "<message>"` |
| Refusals | A refused question is reported, never guessed | (in `decide.py`) |
| TOKN backend | The same API behind TOKN's typed decision contract | `tokn system-one evaluate --file request.json` |
| Catalogue | See every supported decision model and how to configure it | `tokn system-one models gpt-6-luna` |
| Check config | Inspect the configuration without calling the API | `tokn system-one status` |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.59 or later | Ships the GA Azure Decisions endpoint | `tokn version` |
| Python 3.8+ and the `openai` package | Runs `decide.py`. Use a version whose client has `decisions` | `python -c "import openai; print(openai.__version__)"` |
| `azure-identity` (Entra ID only) | Token auth instead of an API key | `pip show azure-identity` |
| An OpenAI key, **or** an Azure OpenAI resource with a `gpt-6-luna` deployment | The model that answers | see below |

Install the Python packages outside this example if you do not have them:

```bash
python -m pip install --upgrade openai azure-identity
```

**Region.** Microsoft excludes East US 2 from the Decisions rollout. A resource there returns an error for `/openai/v1/decisions`; TOKN shows a regional-availability hint instead of a confusing auth error. Use a resource in a supported region.

### What leaves your machine

- `decide.py` sends the message text and the three questions to the endpoint you configure.
- `tokn system-one evaluate` sends only the `state` and `questions` in `request.json`. TOKN never reads or sends repository content for this command.
- `tokn system-one models` and `tokn system-one status` make no API calls.

## 1. Configure a backend

Keys and endpoints come from your environment, never from the code.

**OpenAI:**

```bash
export OPENAI_API_KEY=<your OpenAI key>
```

**Azure OpenAI (API key):**

```bash
export AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/openai/v1/
export AZURE_OPENAI_API_KEY=<your key>
export DECISIONS_MODEL=<your gpt-6-luna deployment name>
```

**Azure OpenAI (Microsoft Entra ID):** run `az login`, leave `AZURE_OPENAI_API_KEY` unset, and set `AZURE_OPENAI_USE_ENTRA=1`. Your identity needs a role that can call the deployment, for example *Cognitive Services OpenAI User*.

PowerShell uses `$env:NAME = "value"` for each line.

## 2. Call the API directly

```bash
python decide.py "I was charged twice for my order. Please return the extra charge."
```

Expected, not a recorded run: high probabilities for `refund_requested` and `duplicate_charge`, and a low one for `threatens_chargeback`. Exact values vary by model version.

Try a message that answers some questions and not others:

```bash
python decide.py "Where is my parcel? It was due on Monday."
```

All three probabilities should be low. Read `decide.py`: the whole request is one `client.decisions.create(model=..., input=..., questions=[...])` call, and each answer is either `predicate` (with a `probability`) or `refusal`.

## 3. The same decision through TOKN

TOKN's typed contract names a yes/no question `noul`. TOKN translates `noul` → `predicate`, `choice` → `choice` and `score` → `score` on the way out, and maps a refusal back to a refused answer.

Look at the catalogue entry first. This needs no credentials:

```bash
tokn system-one models gpt-6-luna
```

Then point TOKN at the same backend. Set these in your real environment or in `~/.tokn/config/credentials.env`. TOKN does not load an endpoint or backend switch from a repository `.env`, because they decide where data is sent.

```bash
# OpenAI
export SYSTEMONE_BACKEND=openai
export OPENAI_API_KEY=<your OpenAI key>

# or Azure OpenAI / Foundry
export SYSTEMONE_BACKEND=azure
export AZURE_OPENAI_ENDPOINT=https://<resource>.cognitiveservices.azure.com/openai/v1
export AZURE_OPENAI_API_KEY=<key>            # omit to use Microsoft Entra ID (az login)
export SYSTEMONE_MODEL=<your gpt-6-luna deployment name>
```

Check it, then evaluate:

```bash
tokn system-one status
tokn system-one evaluate --file request.json
```

`request.json` holds one shared `state` (the message plus two structured fields) and two `noul` questions. Expected, not a recorded run: both questions answered with high probability, and the model name and token usage reported.

TOKN validates the request **before** sending anything. For example, an unknown question type fails locally with `type must be "choice", "score", or "noul"`.

## 4. Where to go next

- **Many states at once.** `tokn system-one batch` runs independent states with bounded parallel calls.
- **Several models voting.** [decision-council](../decision-council/README.md) asks several decision models the same questions and escalates only disagreements.
- **Inside an agent run.** [finrisk-system-one](../finrisk-system-one/README.md) combines a deterministic tool with one typed decision request.

## What to look for

| Check | Expected |
|---|---|
| `decide.py` on the duplicate-charge message | `refund_requested` and `duplicate_charge` high |
| `decide.py` on the parcel message | All three low |
| `tokn system-one models gpt-6-luna` | Both OpenAI and Azure configuration blocks |
| `tokn system-one status` | Backend and model shown; no secret values printed |
| `tokn system-one evaluate --file request.json` | Two answers with probabilities |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `'OpenAI' object has no attribute 'decisions'` | `openai` package too old | `python -m pip install --upgrade openai` |
| 404 on `/decisions` (Azure) | Endpoint missing `/openai/v1`, or wrong deployment name | Use `https://<resource>.openai.azure.com/openai/v1/` and your deployment name |
| Error on an East US 2 resource | Region excluded from the rollout | Use a resource in a supported region |
| 401 with Entra ID | No role on the resource, or not logged in | `az login`; assign *Cognitive Services OpenAI User* |
| TOKN ignores the endpoint in `.env` | By design: destinations are not loaded from a repo `.env` | Set it in your shell or `~/.tokn/config/credentials.env` |
| An answer shows as refused | The model declined that question | That is a valid answer. Rephrase the question or handle it as unknown |

## Related

- [decision-council](../decision-council/README.md)
- [judgments](../judgments/README.md): offline governed judgments, no model.
- [SETUP.md](../../SETUP.md)
