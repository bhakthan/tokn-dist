# Example: Author a small domain plugin and check it

> "I want a tiny `lab-inventory` plugin that bundles a domain-author skill with
> stock-level gates, so my team can validate and share it."

This walkthrough builds a toy plugin from scratch on your machine, validates it
with the offline `tokn plugin` commands, and installs it where TOKN discovers
plugins. It also shows where the boundary is: what a plugin can do today, and
what only the compiled-in domain modes can do.

| Capability | How this example uses it |
|---|---|
| Plugin scaffold | `tokn plugin init` creates a starter bundle you then replace |
| Manifest validation | `tokn plugin validate` checks the bundle offline |
| Discovery | `tokn plugin list` and `tokn plugin inspect` show what TOKN finds |
| Domain-author skill | A `SKILL.md` that states gates and validators in plain language |
| Optional checker | A stdlib-only Python script that reads local files only |

Nothing in this walkthrough calls a model. The only LLM step is an optional
"expected, not a recorded run" check in step 8.

## 0. What you need

| Requirement | Why | Check |
|---|---|---|
| TOKN v0.3.57 or later | The `plugin` command tree shipped in this version line | `tokn version` |
| Licence tier: **community** | `plugin` commands have no licence gate in the source | `tokn license --help` |
| Python 3.8+ (optional) | Runs the offline checker in step 7 | `python --version` |
| A terminal in an empty folder | Keeps the toy plugin separate from your repos | `pwd` |

**Tier note.** The plugin commands are free in community. Built-in domain modes
are a separate matter. Their gates depend on the `domains:<name>` feature, and
community is granted only `domains:basic`. Trial or paid tiers unlock the other
domain modes. See [../../SETUP.md](../../SETUP.md) for activation.

**What leaves your machine.** Nothing. Every step here reads and writes local
files. `validate`, `list`, and `inspect` do not upload your plugin.

**Install preflight.** If `tokn` is not found, install the TOKN CLI first using
the steps in [../../SETUP.md](../../SETUP.md), then re-run `tokn version`.

## 1. Make a workspace

```bash
mkdir -p ~/tokn-demo/lab-inventory-workspace && cd ~/tokn-demo/lab-inventory-workspace
```

```powershell
New-Item -ItemType Directory -Force "$HOME\tokn-demo\lab-inventory-workspace" | Out-Null
Set-Location "$HOME\tokn-demo\lab-inventory-workspace"
```

## 2. Read the plugin commands

```bash
tokn plugin --help
tokn plugin init --help
tokn plugin validate --help
```

```powershell
tokn plugin --help
tokn plugin init --help
tokn plugin validate --help
```

Expected, not a recorded run: the top-level help lists `list`, `inspect`,
`validate`, `init`, and `export`. There is no `install` or `catalog`
subcommand in the released source, so installing is a manual copy (step 6).

## 3. Scaffold a starting point

```bash
tokn plugin init lab-inventory --domain --domain-name lab-inventory --description "Stock-level gates for a toy lab inventory"
ls -R lab-inventory
```

```powershell
tokn plugin init lab-inventory --domain --domain-name lab-inventory --description "Stock-level gates for a toy lab inventory"
Get-ChildItem -Recurse lab-inventory | Select-Object FullName
```

Expected, not a recorded run: a `lab-inventory/` folder containing a root
`plugin.json` (the Agent Plugins layout) and a domain-author `SKILL.md`. The
scaffold is a starting point. You replace the manifest in the next step so you
know every field.

## 4. Write your own manifest

Replace the scaffolded `lab-inventory/plugin.json` with this file.

```bash
cat > lab-inventory/plugin.json <<'EOF'
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "lab-inventory",
  "version": "0.1.0",
  "description": "Stock-level gates for a toy lab inventory",
  "license": "MIT",
  "keywords": ["lab-inventory", "domain", "example"]
}
EOF
```

```powershell
@'
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "lab-inventory",
  "version": "0.1.0",
  "description": "Stock-level gates for a toy lab inventory",
  "license": "MIT",
  "keywords": ["lab-inventory", "domain", "example"]
}
'@ | Set-Content -Encoding utf8 lab-inventory\plugin.json
```

Rules the validator enforces, read from source:

- `name` must be lowercase letters, digits, dots, or hyphens. It must start and
  end with a letter or digit, and be at most 64 characters.
- `version` is a string. Use semantic versioning.
- `description` is a single sentence.

## 5. Write the domain-author skill

Replace the scaffolded `SKILL.md` with a small one. Gates are plain conditions.
TOKN gives the agent this text as guidance. It does not execute the gates.

```bash
cat > lab-inventory/SKILL.md <<'EOF'
---
name: lab-inventory
description: Checks stock levels against reorder thresholds before an order is drafted.
license: MIT
---

# lab-inventory (toy domain)

## Instructions

1. Read the stock table the user supplies (item, quantity, reorder_at).
2. Confirm every row has a non-negative integer quantity.
3. Draft a reorder list only for rows where quantity is at or below reorder_at.

## Domain gates

- `stock-table-complete`: every row has item, quantity, and reorder_at. Stop and
  list the incomplete rows if this fails.
- `no-negative-stock`: a negative quantity is a data error, not a reorder. Stop
  and ask for a recount.
EOF
```

```powershell
@'
---
name: lab-inventory
description: Checks stock levels against reorder thresholds before an order is drafted.
license: MIT
---

# lab-inventory (toy domain)

## Instructions

1. Read the stock table the user supplies (item, quantity, reorder_at).
2. Confirm every row has a non-negative integer quantity.
3. Draft a reorder list only for rows where quantity is at or below reorder_at.

## Domain gates

- `stock-table-complete`: every row has item, quantity, and reorder_at. Stop and
  list the incomplete rows if this fails.
- `no-negative-stock`: a negative quantity is a data error, not a reorder. Stop
  and ask for a recount.
'@ | Set-Content -Encoding utf8 lab-inventory\SKILL.md
```

## 6. Validate, then make TOKN discover it

```bash
tokn plugin validate lab-inventory
```

```powershell
tokn plugin validate lab-inventory
```

Expected, not a recorded run: a pass line for `lab-inventory`. If validation
fails, the message names the file and field.

Now copy the bundle into a discovery root. TOKN's default roots include
`~/.copilot/installed-plugins/` and `~/.claude/plugins/`. The example uses the
Copilot root.

```bash
mkdir -p ~/.copilot/installed-plugins
cp -R lab-inventory ~/.copilot/installed-plugins/
tokn plugin list
tokn plugin inspect lab-inventory
```

```powershell
New-Item -ItemType Directory -Force "$HOME\.copilot\installed-plugins" | Out-Null
Copy-Item -Recurse lab-inventory "$HOME\.copilot\installed-plugins\"
tokn plugin list
tokn plugin inspect lab-inventory
```

Expected, not a recorded run: `list` shows `lab-inventory` at 0.1.0. `inspect`
shows the manifest fields and the skill it found. When you are finished, delete
`~/.copilot/installed-plugins/lab-inventory`.

## 7. Optional: run the offline checker

This stdlib-only script reads your local bundle and checks its shape. It does
not call TOKN, the network, or a model. Save it as `check_lab_inventory.py` in
your workspace, next to the `lab-inventory/` folder.

```python
#!/usr/bin/env python3
"""Offline shape check for a lab-inventory plugin bundle. Reads local files only."""
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.\-]{0,62}[a-z0-9])?$")
REQUIRED_GATES = ("stock-table-complete", "no-negative-stock")


def main(bundle: str) -> int:
    root = Path(bundle)
    problems = []

    manifest_path = root / "plugin.json"
    manifest = {}
    if not manifest_path.is_file():
        problems.append("missing plugin.json at bundle root")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"plugin.json is not valid JSON: {exc}")

    name = str(manifest.get("name", ""))
    if not NAME_RE.match(name):
        problems.append(f"name {name!r} does not match the lowercase slug rule")
    if str(manifest.get("version", "")).count(".") < 2:
        problems.append("version should look like MAJOR.MINOR.PATCH")

    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        problems.append("missing SKILL.md")
    else:
        text = skill_path.read_text(encoding="utf-8")
        if "## Domain gates" not in text:
            problems.append("SKILL.md has no '## Domain gates' section")
        for gate in REQUIRED_GATES:
            if f"`{gate}`" not in text:
                problems.append(f"SKILL.md does not define gate `{gate}`")

    if problems:
        print("FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK: {name} {manifest.get('version')} has a manifest, skill, and both gates")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "lab-inventory"
    sys.exit(main(target))
```

```bash
python check_lab_inventory.py lab-inventory
```

```powershell
python check_lab_inventory.py lab-inventory
```

Expected, not a recorded run: `OK: lab-inventory 0.1.0 has a manifest, skill,
and both gates`.

## 8. The mode boundary (read this before you expect more)

You may want the toy domain to run only when its own mode is active. That part
is **not reachable from a user manifest** in the released binary:

- Agent modes are a fixed list compiled into TOKN. A plugin cannot add
  `lab-inventory` to that list, so `tokn agent-run --mode` will not accept it.
- The compiled-in domain plugs are managed by an internal lifecycle package. It
  is not a user-facing loader.
- So a plugin's skill is guidance an agent reads when it is relevant. It is not
  a hook that fires only in a mode.

Expected, not a recorded run: an unknown mode is rejected with an "unsupported
agent mode" message that lists the valid modes. Read the message; do not treat
this as a test.

```bash
tokn agent-run --mode lab-inventory --prompt "Check this stock table"
```

```powershell
tokn agent-run --mode lab-inventory --prompt "Check this stock table"
```

For a real mode-scoped domain, use a built-in one. See
[../custom-hooks/README.md](../custom-hooks/README.md) and
[../compbio-gates/README.md](../compbio-gates/README.md). Those depend on the
domain feature for your licence tier.

## What to look for

- `plugin validate` passes, and when it fails the message names the file and field.
- `plugin list` shows `lab-inventory` only after you copy it into a discovery root.
- The checker reports both gates. If you rename a gate in `SKILL.md`, the
  checker fails, which tells you the gate names moved.
- No command in this walkthrough needs a key or a network call.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `tokn: command not found` | CLI not on PATH | Follow [../../SETUP.md](../../SETUP.md), then open a new terminal |
| `validate` rejects `name` | Uppercase letters, spaces, or a leading hyphen | Use lowercase, digits, dots, or hyphens |
| `list` does not show the plugin | Copied into the wrong folder | Confirm `~/.copilot/installed-plugins/lab-inventory/plugin.json` exists |
| `plugin install` is "unknown command" | No install subcommand in the released source | Copy the folder as in step 6 |
| Checker says `missing plugin.json` | Ran it from the wrong folder | Pass the bundle path, e.g. `python check_lab_inventory.py lab-inventory` |
| Mode is "unsupported" | Expected: plugins cannot add modes | See step 8 |

## Related

- [../../SETUP.md](../../SETUP.md): install and licence activation
- [../custom-hooks/README.md](../custom-hooks/README.md): hooks in a built-in workflow
- [../compbio-gates/README.md](../compbio-gates/README.md): a domain with real gates
