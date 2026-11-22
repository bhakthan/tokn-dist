#!/usr/bin/env python3
"""Emit the candidate synthetic series in the atmchem oracle format."""

import json
import sys

with open(sys.argv[1], encoding="utf-8-sig") as source:
    data = json.load(source)
print(json.dumps({"NO2": data["candidate"]}, separators=(",", ":")))
