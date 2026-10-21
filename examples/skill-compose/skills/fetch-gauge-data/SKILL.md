---
name: fetch-gauge-data
description: Load river gauge readings from the local CSV export and summarise them per station.
triggers: gauge, readings, river level, csv, station data
category: data-fetching
---

# Fetch gauge data

## When to use
The task needs river gauge readings (level in metres, one row per station per hour).

## Steps
1. Open `data/gauge_readings.csv`. Columns: `station,timestamp,level_m`.
2. Group rows by `station`. Record the first and last timestamp and the maximum `level_m` for each station.
3. Report the per-station summary as a small table before doing any threshold work.

## Verification
- Every station in the file appears in the summary.
- Row count per station matches the file.

## Gotchas
- Timestamps are UTC. Do not convert them.
