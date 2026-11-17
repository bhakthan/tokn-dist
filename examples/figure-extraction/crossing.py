"""Read the JSON from `tokn vision extract <chart> --kind chart` and find where the curve crosses a level.

Usage:
    tokn vision extract fsc.png --kind chart > chart.json
    python crossing.py chart.json [level]
"""
import csv
import io
import json
import sys


def load_points(path):
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    rows = csv.reader(io.StringIO(data["csv"]))
    next(rows)  # header: series,x,y
    return sorted((float(x), float(y)) for _, x, y in rows)


def first_crossing(points, level):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if (y0 - level) * (y1 - level) <= 0 and y0 != y1:
            return x0 + (level - y0) * (x1 - x0) / (y1 - y0)
    return None


def main():
    path = sys.argv[1]
    level = float(sys.argv[2]) if len(sys.argv) > 2 else 0.143
    x = first_crossing(load_points(path), level)
    if x is None:
        print(f"No crossing of y={level} found in the chart data.")
        return
    print(f"Crossing at y={level}: x = {x:.4f} 1/A")
    print(f"Resolution: {1 / x:.2f} A")


if __name__ == "__main__":
    main()
