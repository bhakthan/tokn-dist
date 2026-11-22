#!/usr/bin/env python3
"""Synthetic legacy event formatter."""

import json
import sys

with open(sys.argv[1], encoding="utf-8-sig") as source:
    record = json.load(source)
for event in record["events"]:
    print(json.dumps(event, separators=(",", ":")))
