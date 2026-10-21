---
name: flood-thresholds
description: Flood stage reference levels (metres) for each gauge station, used to judge whether a reading is a flood.
triggers: flood stage, threshold, warning level, flood level, reference level
category: library-reference
---

# Flood thresholds

## When to use
A task compares gauge levels against flood stage, or asks which stations are at risk.

## Reference table
| Station | Warning level (m) | Flood stage (m) |
|---|---|---|
| RIV-01 | 3.0 | 3.5 |
| RIV-02 | 2.2 | 2.8 |
| RIV-03 | 4.1 | 4.6 |

Use the **flood stage** column for "flood" decisions. Use the warning level only
for "watch" language.

## Gotchas
- Stage values are fixed for this exercise. Do not estimate new ones.
