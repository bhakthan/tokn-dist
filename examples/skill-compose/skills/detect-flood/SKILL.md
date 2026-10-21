---
name: detect-flood
description: Detect flood events by comparing each gauge reading with its station's flood stage, and list every breach with its time.
triggers: detect flood, flood event, exceeds, breach, flood detection
category: business-process
---

# Detect floods

## When to use
A task asks which readings are floods, or when a station crossed its flood stage.

## Steps
1. Use the station summary from the gauge data.
2. For each reading, compare `level_m` with that station's flood stage.
3. A reading at or above the flood stage is a **breach**. Record station, timestamp and level.
4. Output the breaches as a table, sorted by timestamp. Output "no breaches" if there are none.

## Verification
- Every breach has a level at or above its station's flood stage.
- No reading below its flood stage appears in the list.

## Gotchas
- Equal to the flood stage counts as a breach.
