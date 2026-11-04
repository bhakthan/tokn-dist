"""Convert data/*.csv into parquet/*.parquet with typed columns.

Needs pyarrow:  python -m pip install pyarrow
Run from examples/ontology-from-tables:
    python scripts/make_parquet.py
"""
import glob
import os
import sys

try:
    import pyarrow.csv as pacsv
    import pyarrow.parquet as pq
except ImportError:
    sys.exit("pyarrow is not installed. Install it with:\n"
             "    python -m pip install pyarrow\n"
             "then re-run: python scripts/make_parquet.py")

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
out = os.path.join(root, "parquet")
os.makedirs(out, exist_ok=True)

files = sorted(glob.glob(os.path.join(root, "data", "*.csv")))
for path in files:
    table = pacsv.read_csv(path)
    name = os.path.splitext(os.path.basename(path))[0]
    pq.write_table(table, os.path.join(out, name + ".parquet"))
    print(f"{name}: {table.num_rows} rows, {table.num_columns} columns")

print(f"wrote {len(files)} parquet files to {out}")
