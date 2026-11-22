# Example: triage a synthetic host audit with the cybersecurity domain (defensive only)

This walkthrough runs one defensive triage task, from start to finish:

> *Triage this synthetic host configuration and auth log. List misconfigurations
> and suspicious sign-ins, map each to an ATT&CK technique, verify any CVE
> before relying on it, and write an incident note for a defender.*

It shows how the cybersecurity domain (`--mode cybersec`) enforces its gates
while the agent works. The scope is two local synthetic files. No host,
network, or service is touched, and no attack or exploit tooling is used.

| Feature | What it does here |
|---|---|
| **Cybersecurity domain** (`--mode cybersec`) | Adds threat-intel, CVE, ATT&CK, TLP and incident-response tools, with 8 hooks and a 12-phase kill-chain lifecycle. |
| **Blocking hooks** | `verify_cve_format` rejects malformed CVE IDs. `enforce_attack_mapping` needs an ATT&CK ID in analysis output. `enforce_tlp_classification` and `check_tlp_red_leak` guard TLP labels and TLP:RED content. |
| **Attack-simulation containment hook** | A scope guard. It only activates when a red-team simulation signature appears. This task has none, so it should stay silent. |

All data in `synthetic/` is invented. Addresses use documentation ranges.

---

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN **v0.3.57 or newer** | First release with this example's flags | `tokn version` |
| **Trial** licence (domain mode) | Community grants only `domains:basic`. `cybersec` needs the trial. | `tokn license features` |
| An LLM provider and key | Runs the agent | see [SETUP.md](../../SETUP.md) |
| Python 3 (optional) | Runs the stdlib checker in step 6 | `python --version` |

**Tier:** domain modes need the 14-day trial. Start it once with
`tokn license trial`, then inspect entitlement with `tokn license features`.

> **What leaves your machine.** The model provider receives the prompt and the
> two synthetic files the agent reads. Starting the trial also sends a one-time
> anonymous install registration (a machine hash, no personal data). Nothing
> else is sent.

## 1. Set up a scratch folder

Keep runs outside the repo so no result files are committed.

macOS / Linux:

```bash
mkdir -p ~/tokn-cyber && cp -r examples/cybersec/synthetic examples/cybersec/prompt.md examples/cybersec/check_results.py ~/tokn-cyber/
cd ~/tokn-cyber
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\tokn-cyber | Out-Null
Copy-Item examples\cybersec\synthetic, examples\cybersec\prompt.md, examples\cybersec\check_results.py $HOME\tokn-cyber -Recurse
Set-Location $HOME\tokn-cyber
```

## 2. Start the trial

```bash
tokn license trial
tokn license status
tokn license features
```

```powershell
tokn license trial
tokn license status
tokn license features
```

Expected: `status` reports an active trial and `features` lists
`domains:cybersec` or `domains:*`. If `trial` says one was already used on
this machine, the domain modes cannot be enabled here.

## 3. Configure the LLM

Follow [SETUP.md](../../SETUP.md) for your provider. For Anthropic, for example:

```bash
export NOSPACE_MODEL_PROVIDER=anthropic
export NOSPACE_MODEL_NAME='YOUR_MODEL_ID'
read -rs -p 'Anthropic API key: ' ANTHROPIC_API_KEY; echo; export ANTHROPIC_API_KEY
```

```powershell
$env:NOSPACE_MODEL_PROVIDER = "anthropic"
$env:NOSPACE_MODEL_NAME     = "YOUR_MODEL_ID"
# Set ANTHROPIC_API_KEY through your trusted secret manager or existing shell session.
```

Keep credentials in a trusted secret store or existing shell session. Never put a populated `.env` file in the example or commit a key.
For a static provider configuration check, run
`tokn doctor --provider anthropic`; it does not verify a live credential.

## 4. Run the triage

Advanced flags come from `tokn agent-run --help-all`: `--mode`, `--prompt-file`,
`--repo-root`, `--max-steps`, `--output-format`.
`--output-format json` prints one final JSON object on stdout. Logs go to stderr.

bash:

```bash
tokn agent-run --mode cybersec --prompt-file prompt.md --repo-root . \
  --max-steps 20 --output-format json > result.json
```

PowerShell:

```powershell
tokn agent-run --mode cybersec --prompt-file prompt.md --repo-root . `
  --max-steps 20 --output-format json > result.json
```

The scope is limited to the two supplied synthetic files; it is not a
permission restriction on the agent. Keep default approvals enabled and review
the report before acting. A missing or failed tool result is unassessed, not a
pass; do not add active reproduction or use a real target.

## 5. Expected gate outcomes

Expected, not a recorded run: these outcomes describe the supplied gate
configuration. Check an actual run against them.

| Gate | Type | Expected in this run |
|---|---|---|
| `verify_cve_format` | blocking, PreToolUse | `CVE-24-0017` fails the `CVE-YYYY-NNNN+` format, so it is reported as unverified and not scored. |
| `enforce_attack_mapping` | blocking, PreToolUse | Analysis output cites at least one ATT&CK ID, for example T1110 (Brute Force) or T1078 (Valid Accounts). |
| `enforce_tlp_classification` | blocking, PreToolUse | Any export or report carries a TLP label. The brief asks for `TLP:AMBER`. |
| `check_tlp_red_leak` | blocking, PostToolUse | No `TLP:RED` material appears in output. |
| `validate_severity_language` | warning | No "critical" or "high" wording without a CVSS score. |
| `verify_cves_in_output` | warning | Only verified CVEs are presented as verified. |
| `annotate_intelligence_layer` | warning | Intelligence annotations are added where threat-feed tools are used. This run calls none, so it should not fire. |
| `validate_stix_output` | warning | Not expected to fire: no STIX bundle is requested. |
| Attack-simulation containment | blocking, PreToolUse | Silent. No simulation signature appears, so the hook does not activate. |
| Kill-chain gates | state machine | Triage stays at `TRIAGE`/`ENRICHMENT`. `contain_threat` is not called. `CONTAINMENT` would need `ENRICHMENT` first, and `ERADICATION` would need `CONTAINMENT` first. |

## 6. Check the result (optional)

```bash
python check_results.py result.json
```

```powershell
python check_results.py result.json
```

The checker reads only `result.json` and makes no network call. It confirms
the JSON shape, that no `TLP:RED` appears, that a TLP label and an ATT&CK ID
are cited, that the root-login finding is mentioned, and that the malformed
CVE is not presented as verified. It is a text check. It does not prove that a
gate fired.

## What to look for

- **Findings match the input.** `PermitRootLogin yes`, password logins, the
  root brute-force pattern from `192.0.2.44`, the successful login from
  `198.51.100.23` after failures, and the `sudo cat /etc/shadow` event.
- **The malformed CVE is flagged, not scored.** A good run says `CVE-24-0017`
  failed the format check.
- **No containment action.** The agent reads and reports. It does not block an
  IP, disable an account, or change the host.
- **Severity wording is backed.** Any "high" or "critical" has a score next to it.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Run refused with a licence or tier message | Community tier (`domains:cybersec` is not in Community) | Run `tokn license trial`, then `tokn license status`. |
| `--mode cybersec` not accepted | TOKN older than v0.3.57 | Upgrade, then check `tokn version`. |
| `result.json` has extra text, or fails to parse | Stdout mixed with other output | Use `--output-format json` and redirect stdout only. Logs go to stderr. |
| Run stops before the final JSON | `--max-steps` reached | Raise `--max-steps` and rerun. |
| `checker: cannot read JSON result` | Run failed before writing JSON | Open the stderr log, fix the cause, and rerun. |
| Model or auth error | Provider env vars not set | Re-check step 3 and [SETUP.md](../../SETUP.md). |
