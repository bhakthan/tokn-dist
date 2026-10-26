# Example: Let TOKN use Google's Gemini API CLI

> "I want my agent to make a diagram, read a PDF or run a deep-research job, without giving it a raw shell."

Google's [Gemini API CLI](https://github.com/google-gemini/gemini-api-cli) (`gemini-api`, beta) is a command-line tool for Gemini models: text generation, file analysis, transcription, images, speech, music, video and managed agents such as deep research. It is **not** Gemini CLI (`gemini`), the coding agent covered in [coding-clis](../coding-clis/README.md).

When `gemini-api` is on your `PATH`, TOKN gives its agent a tool called `gemini_api`. The agent asks for a command by name, and TOKN builds a safe command line for it:

| TOKN does this | So that |
|---|---|
| Only allows `generate`, `analyze`, `transcribe`, `image`, `tts`, `music`, `video`, `agent_run`, `agent_status`, `agent_cancel`, `files_upload`, `files_list` and `models` | The agent cannot change your account, keys, webhooks or triggers |
| Puts your prompt after `--` | Text in a prompt is never read as a flag |
| Keeps local inputs and outputs inside the project folder, symlinks included | The agent cannot read or write elsewhere on disk |
| Saves media to `.nospace/gemini-api/` by default | Generated files are easy to find and to ignore in git |
| Passes only `GEMINI_API_KEY`, proxy and profile variables to the CLI | Your other secrets stay out of the subprocess |
| Marks the output as external and scans it for prompt injection | A malicious document cannot steer the agent |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.66 or later | The `gemini_api` tool | `tokn version` |
| `gemini-api` | The CLI that TOKN calls | `gemini-api --version` |
| A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) | Every call except `models` and dry runs uses it | `echo $GEMINI_API_KEY` |
| Network access to the Gemini API | It is a cloud service, so it does not work in air-gap mode | — |
| A model key for TOKN itself | TOKN's own agent decides when to call the tool | `tokn doctor` |

Gemini API calls are billed to your Google account. Video and music generation cost the most.

### Install `gemini-api`

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.sh | bash
```

```powershell
# Windows (PowerShell)
iwr -useb https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.ps1 | iex
```

```bash
# Any OS with Go 1.22+
go install github.com/google-gemini/gemini-api-cli/cmd/gemini-api@latest
```

Then set your key. Either export it, or let the CLI store it in your OS keychain:

```bash
export GEMINI_API_KEY="your-key"           # macOS / Linux
```

```powershell
$env:GEMINI_API_KEY = "your-key"           # Windows
```

```bash
gemini-api configure --interactive         # alternative: keychain
```

TOKN never runs `configure` or `auth` itself. Setting up credentials is your step.

## 1. Check the CLI on its own

```bash
gemini-api models --output-format json
gemini-api generate --dry-run --no-interactive -- "Say hello"
```

Neither command calls the API. The first prints the model catalog; the second prints the request it would send.

## 2. Copy the sample into a project folder

```bash
mkdir gemini-demo && cd gemini-demo
cp /path/to/tokn-dist/examples/gemini-api/notes.md .
```

`notes.md` holds fictional meeting notes for a library app.

## 3. Ask TOKN to use it

TOKN registers the tool at start-up when it finds `gemini-api`. You do not need any flag. Run these from inside `gemini-demo`.

**Summarise a local file** (`analyze`):

```bash
tokn agent-run "Use the gemini_api tool with command analyze on notes.md. List the decisions, the open questions and the owner, as a short markdown table."
```

**Make an image** (`image`):

```bash
tokn agent-run "Use gemini_api command image to draw a simple wireframe for the overdue-items dashboard described in notes.md, aspect ratio 16:9. Tell me where it was saved."
```

The image is saved under `.nospace/gemini-api/`.

**Turn the notes into speech** (`tts`):

```bash
tokn agent-run "Use gemini_api command tts with voice Kore to read a 3-sentence summary of notes.md. Save it to out/summary.wav."
```

**Run a managed research agent in the background** (`agent_run`, then `agent_status`):

```bash
tokn agent-run "Use gemini_api command agent_run with agent deep-research-preview-04-2026 and background true to research how public libraries send overdue reminders (SMS vs email). Give me the interaction id."
tokn agent-run "Use gemini_api command agent_status with interaction_id <id from above> and summarise the result."
```

### What a tool call looks like

The agent sends structured input, for example:

```json
{
  "command": "analyze",
  "prompt": "List the decisions, open questions and owner.",
  "inputs": ["notes.md"]
}
```

TOKN turns it into:

```text
gemini-api analyze --no-interactive --output-format json --input <project>/notes.md -- "List the decisions, open questions and owner."
```

Add `"dry_run": true` to see the request without calling the API.

## 4. What happens when something is missing

| Situation | What the agent is told |
|---|---|
| `gemini-api` is not installed | The install command for your OS, plus the key and network requirements |
| No key, or a bad key (exit code 3) | Set `GEMINI_API_KEY` or run `gemini-api configure --interactive` |
| A path outside the project | The call is refused before the CLI runs |
| A command that is not allowed, for example `configure` | The call is refused and the allowed list is returned |

To force-register the tool so it can explain how to install the CLI, set `GEMINI_API_ENABLE_TOOL=1`. To turn it off, set `GEMINI_API_DISABLE_TOOL=1`.

## What leaves your machine

Prompts and every file you pass as an input go to Google's Gemini API, under your Google account's terms. TOKN's own model calls go to the provider you configured for TOKN. Generated media stays in your project folder.
