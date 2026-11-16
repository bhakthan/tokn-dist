#!/usr/bin/env python3
"""Rebuild docs/data/history.json download totals from git history.

Before 2026-11-17 the collector summed download_count per asset NAME across all
releases and, when that sum dropped, banked the previous sum into a carry. A sum
drops whenever an old release is pruned, so each prune banked the downloads of
every release still present a second time, inflating the total.

Every daily commit of history.json stored the raw per-name sum in
downloads_state[name].last, so the true series can be replayed exactly with the
correct rule: bank only the drop (last - raw). Snapshots written before
downloads_state existed held raw counts directly.

Usage: python3 scripts/rebuild_download_history.py [--write]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REL = "docs/data/history.json"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def raw_series() -> dict[str, dict[str, int]]:
    """date -> {asset_name: raw per-name sum}, last commit of each date wins."""
    series: dict[str, dict[str, int]] = {}
    for sha in reversed(git("log", "--format=%H", "--", REL).split()):
        try:
            h = json.loads(git("show", f"{sha}:{REL}"))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        snaps = h.get("downloads_snapshots") or {}
        if not snaps:
            continue
        day = max(snaps)
        state = h.get("downloads_state") or {}
        if state:
            series[day] = {name: int(st.get("last", 0)) for name, st in state.items()}
        else:
            series[day] = {name: int(c) for name, c in (snaps[day].get("assets") or {}).items()}
    return series


def replay(series: dict[str, dict[str, int]]) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    last: dict[str, int] = {}
    carry: dict[str, int] = {}
    totals: dict[str, int] = {}
    assets_by_day: dict[str, dict[str, int]] = {}
    for day in sorted(series):
        raw = series[day]
        for name, c in raw.items():
            if name in last and c < last[name]:
                carry[name] = carry.get(name, 0) + (last[name] - c)
            last[name] = c
        for name in list(last):
            if name not in raw:  # asset name gone entirely: its last value is banked
                carry[name] = carry.get(name, 0) + last.pop(name)
        eff = {n: carry.get(n, 0) + last.get(n, 0) for n in set(carry) | set(last)}
        assets_by_day[day] = eff
        totals[day] = sum(eff.values())
    return totals, assets_by_day


def main() -> int:
    series = raw_series()
    totals, assets = replay(series)
    hist_path = ROOT / REL
    hist = json.loads(hist_path.read_text(encoding="utf-8"))
    old = hist.get("downloads_snapshots", {})
    for day in sorted(totals)[-8:]:
        print(f"{day}  old={old.get(day, {}).get('total', '-'):>6}  rebuilt={totals[day]:>6}")
    if "--write" not in sys.argv:
        print("(dry run; pass --write to update history.json)")
        return 0
    snaps = {d: {"total": totals[d], "assets": assets[d]} for d in sorted(totals)}
    daily = {}
    days = sorted(snaps)
    for prev, cur in zip(days, days[1:]):
        daily[cur] = max(0, snaps[cur]["total"] - snaps[prev]["total"])
    hist["downloads_snapshots"] = snaps
    hist["downloads_daily"] = daily
    # Downloads of already-pruned releases (and pre-reset counts) as of the
    # last snapshot; the collector adds live per-release counts on top.
    hist["downloads_banked"] = totals[days[-1]] - sum(series[days[-1]].values())
    hist.pop("downloads_state", None)  # replaced by downloads_state_v2 on the next collect
    hist_path.write_text(json.dumps(hist, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {hist_path} (banked total {hist['downloads_banked']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
