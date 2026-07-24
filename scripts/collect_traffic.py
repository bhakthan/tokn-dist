#!/usr/bin/env python3
"""Collect GitHub traffic + release-download stats and append to a persisted
time-series so the data survives GitHub's 14-day traffic-retention window.

GitHub never exposes *who* clones or downloads (by design) — only daily counts
and unique-visitor counts. This script captures:

  * traffic/clones  — daily clone count + uniques (last 14 days, then erased)
  * traffic/views   — daily view count + uniques  (last 14 days, then erased)
  * releases assets — download_count per asset. NOTE: this counter resets to 0
    whenever an asset is re-uploaded (e.g. `gh release upload --clobber`), so we
    keep a per-asset carry offset (downloads_state) to make the effective total
    monotonic across clobbered releases.
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
        "downloads_state": {},
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
    """Return {asset_name: raw_download_count} summed across all releases.

    The raw count is what GitHub currently reports; it resets to 0 when an asset
    is replaced via --clobber. reconcile_downloads() turns these raw values into
    a monotonic effective total.
    """
    raw = {}
    page = 1
    while True:
        rels = api_get(f"/repos/{REPO}/releases?per_page=100&page={page}")
        if not rels:
            break
        for rel in rels:
            for a in rel.get("assets", []):
                c = a.get("download_count", 0)
                raw[a["name"]] = raw.get(a["name"], 0) + c
        if len(rels) < 100:
            break
        page += 1
    return raw


def reconcile_downloads(hist: dict, raw: dict):
    """Fold raw per-asset counts into a clobber-proof effective total.

    For each asset we persist {last, carry} in hist["downloads_state"]:
      * `last`  — the previous raw download_count we saw.
      * `carry` — downloads accumulated from prior asset resets (clobbers).
    A drop (raw < last) means the asset was re-uploaded, so we bank `last` into
    `carry`. The effective per-asset count is always carry + raw, which never
    decreases. On first run under this scheme we seed `carry` from the historical
    high-water mark so pre-existing snapshots aren't lost.
    """
    state = hist.setdefault("downloads_state", {})

    # historical high-water per asset (max ever recorded in a snapshot)
    hi = {}
    for snap in hist.get("downloads_snapshots", {}).values():
        for name, cnt in (snap.get("assets") or {}).items():
            hi[name] = max(hi.get(name, 0), cnt)

    total = 0
    effective_assets = {}
    for name, c in raw.items():
        st = state.get(name)
        if st is None:
            # first observation under the carry scheme: recover any pre-reset
            # downloads only if the current raw already fell below the old high.
            seed_carry = hi.get(name, 0) if c < hi.get(name, 0) else 0
            st = {"last": c, "carry": seed_carry}
        else:
            if c < st["last"]:  # asset was clobbered/re-uploaded -> bank the old total
                st["carry"] += st["last"]
            st["last"] = c
        state[name] = st
        eff = st["carry"] + c
        effective_assets[name] = eff
        total += eff
    return total, effective_assets


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

    raw = collect_downloads()
    total, assets = reconcile_downloads(hist, raw)
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
