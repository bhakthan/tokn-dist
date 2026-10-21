---
name: verify-regression
description: Check a detection result against the known regression cases before it is reported.
triggers: regression, verify, check result, expected output, test cases
category: product-verification
---

# Verify against regression cases

## When to use
A detection or report is ready and must be checked before it is shared.

## Steps
1. Read `data/regression_cases.csv`. Each row gives a station, a timestamp and the expected outcome (`breach` or `ok`).
2. For each case, find the matching reading and check your result agrees.
3. Report the number of cases that pass and list any that fail, with the reason.

## Verification
- Every case in the file is accounted for.
- A failing case is reported, never silently fixed.
