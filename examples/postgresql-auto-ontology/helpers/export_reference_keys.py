"""Export one identifier column from a PostgreSQL table to a new UTF-8 CSV file.

The connection string is read from the environment variable named by --dsn-env
and is never printed. The session is read-only. Only the requested column is
written, one value per row, under a header row. NULL values are skipped.
Nothing is written unless --out is a new file in an existing folder.
"""

import argparse
import csv
import os
import sys
from pathlib import Path


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dsn-env", default="PG_DSN", help="environment variable holding the connection string")
    p.add_argument("--schema", required=True, help="schema name (quoted safely)")
    p.add_argument("--table", required=True, help="table name (quoted safely)")
    p.add_argument("--column", required=True, help="identifier column (quoted safely)")
    p.add_argument("--header", default="CustomerID", help="CSV header for the exported column")
    p.add_argument("--limit", type=int, default=1000, help="maximum number of values to export")
    p.add_argument("--out", required=True, help="new CSV file to create")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.limit < 1:
        sys.exit("error: --limit must be at least 1")
    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        sys.exit(f"error: environment variable {args.dsn_env} is not set")
    try:
        import psycopg
        from psycopg import sql
    except ImportError:
        sys.exit('error: psycopg is missing; install it with: pip install "psycopg[binary]"')
    out = Path(args.out)
    if out.exists():
        sys.exit("error: --out already exists; choose a new file name")
    if not out.parent.is_dir():
        sys.exit("error: the folder for --out does not exist")

    query = sql.SQL(
        "SELECT {col} FROM {tbl} WHERE {col} IS NOT NULL ORDER BY {col} LIMIT %s"
    ).format(
        col=sql.Identifier(args.column),
        tbl=sql.Identifier(args.schema, args.table),
    )
    try:
        with psycopg.connect(dsn, connect_timeout=10) as conn:
            conn.read_only = True
            with conn.cursor() as cur:
                cur.execute(query, (args.limit,))
                rows = cur.fetchall()
    except psycopg.Error as exc:
        sys.exit(f"error: query failed ({type(exc).__name__}); check the connection and the names")

    with out.open("x", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([args.header])
        writer.writerows([str(row[0])] for row in rows)
    print(f"wrote {len(rows)} values to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
