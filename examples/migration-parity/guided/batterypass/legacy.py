#!/usr/bin/env python3
"""Emit a synthetic legacy JSON Schema."""

import json
import sys

with open(sys.argv[1], encoding="utf-8-sig") as source:
    data = json.load(source)
print(json.dumps(data["schema"], separators=(",", ":")))
