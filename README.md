# TOKN — download & try

**TOKN** is a trust-first agentic coding and reasoning harness: a single static
binary with 20+ regulated-domain plugs, offline licensing, and in-place
self-update. This repo hosts **the binaries only** so you can try TOKN — the
source lives in a private repository.

> Start here: download for your OS → put it on your `PATH` → run `tokn license trial`.

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

=== Windows (PowerShell)
```powershell
Move-Item .\tokn_windows_amd64.exe C:\Tools\tokn.exe
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Tools", "User")
```

=== macOS
```bash
chmod +x tokn_darwin_arm64
sudo mv tokn_darwin_arm64 /usr/local/bin/tokn
```

=== Linux
```bash
chmod +x tokn_linux_amd64
sudo mv tokn_linux_amd64 /usr/local/bin/tokn
```

Verify:
```bash
tokn --version
tokn --help
```

## 3. Start your 14-day trial

TOKN runs in a free **community** tier by default. Unlock the full feature
surface with a **14-day trial** — no account, no phone-home, fully offline:

```bash
tokn license trial        # or: tokn trial
tokn license status       # tier, expiry, days remaining
```

The trial writes a signed, machine-bound token to `~/.tokn/license.json` and is
limited to **one trial per machine**. When it expires, TOKN automatically
reverts to the community tier — the binary keeps working.

## 4. Stay up to date (works during the trial)

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

- Questions, trial extensions, or Pro/Enterprise licensing: **licensing@tokn.dev**
- Found a bug during your trial? Open an issue in this repo.

_TOKN is a commercial product. This distribution repo contains released binaries
only; the source code is maintained privately._
