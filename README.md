# TOKN — download & try

**TOKN** is a trust-first agentic coding and reasoning harness: a single static
binary with 20+ regulated-domain plugs, offline licensing, and in-place
self-update. This repo hosts **the binaries only** so you can try TOKN — the
source lives in a private repository.

---

## Why TOKN? Value for teams running agents in production

Most agents look great in a demo and get fragile in production. TOKN is the
**harness around the model** — the part that makes an agent *reliable, safe, and
honest about its own quality*. A few concrete ways it adds value, in plain terms:

- **Self-improvement that can't fool itself.** Agents that tune themselves often
  push one number up while the real goal quietly gets worse.
  *Example: a support bot's "tickets resolved" climbs because it learned to close
  hard tickets fast — while renewals fall.* TOKN's **Graph of Loops** wraps the
  optimizing loop in governance loops and ties every change to **anchors** (real
  outcomes, a frozen held-out test set, human judgment). A change ships **only if
  every anchor agrees.** → `tokn loopgraph` · `/learn loopgraph`

- **Measure quality, then fix it — on a loop.** You can't improve what you don't
  score. *Example: you suspect your agent "sometimes invents a citation." TOKN
  turns that worry into a countable metric, grades a batch of runs, applies a fix,
  and re-grades — and blocks any change that regresses your baseline.*
  → `tokn flywheel` · `/learn flywheel`

- **Hard guardrails for regulated work.** In medicine, finance, or legal,
  "usually right" isn't good enough. *Example: a precision-medicine gate blocks a
  high-risk drug–gene recommendation from ever being emitted; a finance gate
  enforces the required disclaimer language before an answer leaves the agent.*
  20+ domain plugs ship these gates and validators, and you can encode your own
  thresholds. → see **Domain harnesses** in [CAPABILITIES.md](CAPABILITIES.md)

- **Air-gapped by default — your code and data never leave your metal.** Your
  code, prompts, and context call out to nothing unless you enable and explicitly
  trust it. *Example: external tools and the Microsoft IQ / MCP connectors ship
  **disabled + trust-gated**, so an offline or regulated shop runs with zero
  surprise network calls.* → `tokn mcp list`. The **only** built-in network call is
  a single anonymous install ping (TOKN version + OS/arch + a one-way hashed machine
  id — never your code, prompts, or data). On an air-gapped box it queues locally and
  only flushes if that machine is ever online; disable it entirely with
  `TOKN_NO_TELEMETRY=1` (or `DO_NOT_TRACK=1`).

- **Customize without waiting for a vendor.** Every prompt is a file, not baked-in
  code. *Example: a new model lands that follows instructions differently — you
  tune behavior by editing `.nospace/prompts/…`, no recompile and no release.*
  → `/learn customize`

**See it clearly:** `tokn config doctor` shows exactly which config files and env
vars are in effect (secrets redacted); `tokn introspect` prints a machine-readable
capability contract.

**Learn more:** the full tour is in **[CAPABILITIES.md](CAPABILITIES.md)**. Inside
a session, `/learn` opens an interactive lesson for any concept above
(e.g. `/learn loopgraph`), and `tokn --help` is always the authoritative,
version-accurate catalog.

---

> Start here: download for your OS → put it on your `PATH` → run `tokn license trial`.

> Curious what it does? See **[CAPABILITIES.md](CAPABILITIES.md)** for a quick tour —
> or just run `tokn --help` after installing.

> ✨ **New in v0.2.9 — Graph of Loops.** A single self-improvement loop can optimize
> the wrong thing (raise a metric while the real goal quietly degrades). v0.2.9 lets
> one TOKN act as an **outer-loop custodian** over another: an optimizing loop wrapped
> by governance loops and grounded by **anchors** (real outcomes, frozen held-out
> rules, human judgment). A win is accepted **only if every anchor agrees** —
> improvement that can't fool itself. Try `tokn loopgraph` or `/learn loopgraph`.

> 🧾 **Also new — the Design-Loop Card.** Every `autodesign` / `autoresearch` run now
> emits a portable card that records *how* a result emerged (bounds, evaluator
> feedback, held-out check, rejected-candidate graveyard) — and a **fail-closed
> verdict**. A win selected only by the in-loop evaluator is an honest
> *unconfirmed-win*, never a contribution; **only a held-out-confirmed win is
> reportable**. It catches the "simulator escape" (beating a benchmark by exploiting a
> weakened evaluator) instead of shipping it.

> 🔑 **Bring your own model.** TOKN needs an LLM provider (OpenAI, Azure OpenAI,
> Anthropic/Claude, Gemini, or a local runtime). See **[SETUP.md](SETUP.md)** to
> configure your provider and API key in under a minute.

> ⚖️ **Legal:** TOKN is proprietary, evaluation-only software provided **"as is",
> with no warranty and no liability**. It may **not** be copied, redistributed, or
> reverse-engineered — **including any attempt to extract, reconstruct, or retrain
> on its internals with AI/LLM tools**. Cloning or downloading this repo grants you
> **no** such rights. This is a **feedback-first program**: providing feedback is a
> **condition** of the trial. AI output is not professional advice and must be
> verified; you are responsible for compliance and assume all risk. By downloading,
> cloning, or using TOKN you agree to the **[License & Disclaimer](LICENSE.md)** —
> please read it.

---

## 1. Download

Grab the latest build for your platform from the
**[releases page](https://github.com/bhakthan/tokn-dist/releases/latest)**:

| OS | Architecture | File |
|----|--------------|------|
| Windows | x64 | `tokn_windows_amd64.exe` |
| macOS | Apple Silicon | `tokn_darwin_arm64` |
| macOS | Intel | `tokn_darwin_amd64` |
| Linux | x86_64 | `tokn_linux_amd64` |
| Linux | arm64 | `tokn_linux_arm64` |

## 2. Put it on your PATH

**Windows (PowerShell)**
```powershell
Move-Item .\tokn_windows_amd64.exe C:\Tools\tokn.exe
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Tools", "User")
```

**macOS**
```bash
chmod +x tokn_darwin_arm64
sudo mv tokn_darwin_arm64 /usr/local/bin/tokn
```

**Linux**
```bash
chmod +x tokn_linux_amd64
sudo mv tokn_linux_amd64 /usr/local/bin/tokn
```

Verify:
```bash
tokn --version
tokn --help
```

## 3. Point TOKN at a model

TOKN is **bring-your-own-model** — it runs against a provider you already have
(OpenAI, Azure OpenAI, Anthropic/Claude, Gemini, OpenRouter, Fireworks) or a local
runtime (Ollama, llama.cpp/GGUF, ONNX). It even drives **computer-use** models —
Microsoft's **Fara1.5** (via `tokn fara-run`, with a real coordinate browser) and
**MagenticBrain**. Set two variables plus your key, e.g.:

```bash
export NOSPACE_MODEL_PROVIDER=openai
export NOSPACE_MODEL_NAME=gpt-4o
export OPENAI_API_KEY=sk-...
tokn auth status        # confirms the provider is configured & ready
tokn config doctor      # see every config file & env var TOKN picks up (secrets redacted)
```

Prefer a file? Drop the same keys in a `.env` in your working directory (TOKN
auto-loads it, non-overriding — just keep it out of git). **Full provider matrix,
Azure `az login` auth, and local-model setup: [SETUP.md](SETUP.md).**

## 4. Start your 14-day trial

TOKN runs in a free **community** tier by default. Unlock the full feature
surface with a **14-day trial** — no account, no phone-home, fully offline:

```bash
tokn license trial        # or: tokn trial
tokn license status       # tier, expiry, days remaining
```

The trial writes a signed, machine-bound token to `~/.tokn/license.json` and is
limited to **one trial per machine**. When it expires, TOKN automatically
reverts to the community tier — the binary keeps working.

## 5. Stay up to date (works during the trial)

TOKN updates itself in place — no reinstall, no package manager:

```bash
tokn update             # install the latest release
tokn update --check     # check only
tokn update --rollback  # revert to the previous version
```

Updating **does not** reset or invalidate an active trial.

---

## Tiers at a glance

| Tier | Cost | Features | Expiry |
|------|------|----------|--------|
| Community | Free | Capped baseline surface | Perpetual |
| Trial | Free | Full feature surface | 14 days, one per machine |
| Pro / Enterprise | Paid | Full surface, production & regulated use | Annual / perpetual |

## Support & licensing

- Questions, trial extensions, or Pro/Enterprise licensing: **open an issue in this repo**
- Found a bug during your trial? Open an issue in this repo.

## Legal & disclaimer

TOKN is **proprietary, evaluation-only** software. **All Rights Reserved.**

- Provided **"AS IS", with no warranty of any kind.**
- The owner/contributors are **not liable for any damages** arising from its use.
- You **may not copy, redistribute, modify, or reverse-engineer** it.
- AI output **is not professional advice**, may be wrong, and **must be
  independently verified**. Domain features (medical, legal, financial, etc.) are
  decision-support only — **not** certified for clinical, production, or regulated
  use.
- **You are solely responsible for compliance** with all applicable laws
  (data protection, export control, sector regulations) and **assume all risk**.

**By downloading or using TOKN you accept the full
[License & Disclaimer](LICENSE.md).**

_This distribution repo contains released binaries only; the source code is
maintained privately and is not licensed hereunder._
