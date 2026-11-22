#!/usr/bin/env python3
"""Emit a candidate JSON Schema for the synthetic parity exercise."""

import json
import sys

with open(sys.argv[1], encoding="utf-8-sig") as source:
    data = json.load(source)
print(json.dumps(data["schema"], separators=(",", ":")))
