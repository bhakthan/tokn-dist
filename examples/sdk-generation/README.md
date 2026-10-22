# Example: Generate a Client SDK from an OpenAPI Spec

> "Generate a TypeScript and a Python client for this Petstore spec, then check that both compile."

Writing API clients by hand drifts from the spec. TOKN's `sdkgen` command reads an OpenAPI 3 file and writes client code from it. It does not use a model, so the same spec gives the same output. This walkthrough covers the three steps you can run yourself: ingest, generate, and validate.

| Capability | What the command does |
|---|---|
| `tokn sdkgen ingest` | Parses the spec into a normalised intermediate form and prints a summary with a content hash. |
| `tokn sdkgen generate` | Writes one client folder per language from that intermediate form. |
| `tokn sdkgen validate` | Checks that each generated folder compiles with its language toolchain. Skips a language when its toolchain is missing. |

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or newer | The `sdkgen` command ships in this version. | `tokn version` |
| Community tier (no trial) | The `sdkgen` commands are not behind a licence gate. | `tokn sdkgen --help` |
| Python 3.9+ | Runs the offline output checker. Also needed for the Python client. | `python --version` |
| Node.js 18+, npm, TypeScript (`tsc`) | Needed to compile the TypeScript client. | `node --version`, `npm --version`, `tsc --version` |

Install the toolchains for your OS. Only the ones you need for the languages you pick are required. `validate` skips a language if its toolchain is missing and reports that it did so.

| Toolchain | Needed for | Windows (PowerShell) | macOS (Homebrew) | Linux (Debian/Ubuntu) |
|---|---|---|---|---|
| Node.js and npm | `ts` | `winget install OpenJS.NodeJS.LTS` | `brew install node` | `sudo apt install nodejs npm` |
| TypeScript (`tsc`) | `ts` | `npm install -g typescript` | `npm install -g typescript` | `sudo npm install -g typescript` |
| Python 3 and pip | `py` | `winget install Python.Python.3.12` | `brew install python` | `sudo apt install python3 python3-pip` |
| Go (optional) | `go` | `winget install GoLang.Go` | `brew install go` | `sudo apt install golang-go` |
| Rust toolchain (optional) | `rs` | `winget install Rustlang.Rustup` | `brew install rustup` then `rustup default stable` | `curl https://sh.rustup.rs -sSf \| sh` |

After installing, open a new terminal so the new `PATH` entries are picked up.

**What leaves your machine:** `ingest` and `generate` run locally and send nothing. `validate` can run `npm install` for the TypeScript client, which downloads packages from the npm registry. TOKN runs it with `--ignore-scripts`. No LLM is called in this walkthrough. The spec is synthetic.

## 1. Copy the example to a scratch folder

`generate` writes its output to `generated-sdk/` under the folder you run it from.

```bash
cp -r examples/sdk-generation ~/sdk-run
cd ~/sdk-run
```

```powershell
Copy-Item -Recurse examples\sdk-generation $HOME\sdk-run
Set-Location $HOME\sdk-run
```

## 2. Ingest the spec

Print only the summary. Leave out the full intermediate form.

```bash
tokn sdkgen ingest petstore.yaml --meta-only --pretty
```

```powershell
tokn sdkgen ingest petstore.yaml --meta-only --pretty
```

Expected, not a recorded run: a JSON object with a `meta` block. It should show the title `Petstore Demo`, four operations, three schemas, and an `ir_hash` value. Run it again and the hash should not change, because the spec did not change.

To save the full intermediate form for inspection, drop `--meta-only` and add `--out petstore.ir.json`.

## 3. Generate the clients

```bash
tokn sdkgen generate --spec petstore.yaml --out generated-sdk --package-name petstore --languages ts,py
```

```powershell
tokn sdkgen generate --spec petstore.yaml --out generated-sdk --package-name petstore --languages ts,py
```

Expected, not a recorded run: a `generated-sdk/ts/` folder and a `generated-sdk/py/` folder. Each holds the client code for the four operations (`listPets`, `createPet`, `getPet`, `deletePet`) and the three schemas.

Add `go` or `rs` to `--languages` if you installed those toolchains.

Check the output locally:

```bash
python check_sdk_output.py generated-sdk ts py
```

```powershell
python check_sdk_output.py generated-sdk ts py
```

This only counts files. It does not compile anything.

## 4. Validate the clients

```bash
tokn sdkgen validate generated-sdk --languages ts,py
```

```powershell
tokn sdkgen validate generated-sdk --languages ts,py
```

`validate` first checks that each toolchain is present. It then compiles each language. Add `--lint` for an advisory lint pass, or `--json` to get the full report on stdout. `--timeout` sets the limit for each command, in seconds. The default is 120.

Expected, not a recorded run: one result per language. A language with its toolchain installed shows a compile result. A language with a missing toolchain is reported as skipped, with the binary it needed.

## 5. Optional: check the generated code against the spec

Open `generated-sdk/ts/` and find the code for `listPets`. Check that it takes the `limit` query parameter from `petstore.yaml`. Then edit the spec, rerun steps 2 to 4, and compare the two output folders.

## What to look for

Expected, not a recorded run:

- `ingest` reports the same `ir_hash` for an unchanged spec. The hash changes when the spec changes.
- `generate` writes the same files each time. It has no model in the loop, so the output is repeatable.
- `validate` reports a compile result for every language whose toolchain is installed, and a skip for the rest.
- The checker lists non-zero file counts for `ts` and `py`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tokn: command not found` or `unknown command "sdkgen"` | Your TOKN is older than v0.3.57, or the install is not on `PATH`. Run `tokn version`. |
| `--spec is required` | Pass the spec file with `--spec petstore.yaml`. |
| `validate` reports `node` or `tsc` missing | Install the toolchain from the table in step 0, then open a new terminal. |
| `validate` reports `pip` or `python` missing | Install Python 3 and pip from the table, then open a new terminal. |
| The checker says the output folder does not exist | Run step 3 first, from the same folder. |
| `validate` is slow on the first run | It is downloading npm packages. Raise `--timeout` if a command hits the limit. |
