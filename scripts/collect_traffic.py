#!/usr/bin/env python3
"""Collect GitHub traffic + release-download stats and append to a persisted
time-series so the data survives GitHub's 14-day traffic-retention window.

GitHub never exposes *who* clones or downloads (by design) — only daily counts
and unique-visitor counts. This script captures:

  * traffic/clones  — daily clone count + uniques (last 14 days, then erased)
  * traffic/views   — daily view count + uniques  (last 14 days, then erased)
  * releases assets — cumulative all-time download_count per asset (never erased)
  * popular/referrers + popular/paths — top-10 sources (last 14 days)

and merges them into docs/data/history.json (upsert by date), computing a daily
download delta from consecutive cumulative snapshots.

Auth: set GITHUB_TOKEN (needs push access to the repo for the traffic API).
Repo: set REPO="owner/name" (defaults to bhakthan/tokn-dist).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = os.environ.get("REPO", "bhakthan/tokn-dist")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
API = "https://api.github.com"
HIST_PATH = Path(__file__).resolve().parent.parent / "docs" / "data" / "history.json"


def api_get(path: str):
    """GET an API path, returning parsed JSON or None on a handled error."""
    url = path if path.startswith("http") else f"{API}{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "tokn-traffic-tracker")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:200]
        print(f"WARN: {path} -> HTTP {e.code}: {body}", file=sys.stderr)
        if e.code in (401, 403):
            print(
                "  (traffic endpoints require a token with PUSH access to the "
                "repo. In Actions grant `permissions: contents: write` or set a "
                "TRAFFIC_TOKEN secret with `repo` scope.)",
                file=sys.stderr,
            )
        return None
    except Exception as e:  # noqa: BLE001
        print(f"WARN: {path} -> {e}", file=sys.stderr)
        return None


def iso_date(ts: str) -> str:
    return ts[:10]  # "2026-07-18T00:00:00Z" -> "2026-07-18"


def load_history() -> dict:
    if HIST_PATH.exists():
        try:
            return json.loads(HIST_PATH.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"WARN: could not parse existing history: {e}", file=sys.stderr)
    return {
        "repo": REPO,
        "clones_daily": {},
        "views_daily": {},
        "downloads_snapshots": {},
        "downloads_daily": {},
        "referrers": [],
        "paths": [],
    }


def merge_traffic(dst: dict, series, key: str):
    if not series or key not in series:
        return
    for row in series[key]:
        d = iso_date(row["timestamp"])
        dst[d] = {"count": row.get("count", 0), "uniques": row.get("uniques", 0)}


def collect_downloads():
    total = 0
    assets = {}
    page = 1
    while True:
        rels = api_get(f"/repos/{REPO}/releases?per_page=100&page={page}")
        if not rels:
            break
        for rel in rels:
            for a in rel.get("assets", []):
                c = a.get("download_count", 0)
                assets[a["name"]] = assets.get(a["name"], 0) + c
                total += c
        if len(rels) < 100:
            break
        page += 1
    return total, assets


def main() -> int:
    hist = load_history()
    hist["repo"] = REPO
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    merge_traffic(hist["clones_daily"], api_get(f"/repos/{REPO}/traffic/clones"), "clones")
    merge_traffic(hist["views_daily"], api_get(f"/repos/{REPO}/traffic/views"), "views")

    refs = api_get(f"/repos/{REPO}/traffic/popular/referrers")
    if isinstance(refs, list):
        hist["referrers"] = refs
    paths = api_get(f"/repos/{REPO}/traffic/popular/paths")
    if isinstance(paths, list):
        hist["paths"] = paths

    total, assets = collect_downloads()
    hist["downloads_snapshots"][today] = {"total": total, "assets": assets}

    # daily download delta vs the most recent prior snapshot
    prior = sorted(d for d in hist["downloads_snapshots"] if d < today)
    if prior:
        prev_total = hist["downloads_snapshots"][prior[-1]]["total"]
        hist["downloads_daily"][today] = max(0, total - prev_total)

    hist["updated_at"] = datetime.now(timezone.utc).isoformat()

    HIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    HIST_PATH.write_text(json.dumps(hist, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"OK: downloads(total)={total} assets={len(assets)} "
        f"clone-days={len(hist['clones_daily'])} view-days={len(hist['views_daily'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
