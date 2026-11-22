#!/usr/bin/env python3
"""Synthetic candidate with an intentional per-order ordering regression."""

import json
import sys

with open(sys.argv[1], encoding="utf-8-sig") as source:
    record = json.load(source)
for event in reversed(record["events"]):
    print(json.dumps(event, separators=(",", ":")))
