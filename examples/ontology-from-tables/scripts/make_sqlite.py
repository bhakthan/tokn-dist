"""Build workshop.db (SQLite) from sql/schema.sql and sql/data.sql.

Uses only the Python standard library. Run from examples/ontology-from-tables:
    python scripts/make_sqlite.py
"""
import os
import sqlite3

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
db_path = os.path.join(root, "workshop.db")

if os.path.exists(db_path):
    os.remove(db_path)

con = sqlite3.connect(db_path)
try:
    con.execute("PRAGMA foreign_keys = ON")
    for name in ("schema.sql", "data.sql"):
        with open(os.path.join(root, "sql", name), encoding="utf-8") as f:
            con.executescript(f.read())
    con.commit()
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
finally:
    con.close()

print(f"wrote {db_path} with {len(tables)} tables: {', '.join(tables)}")
