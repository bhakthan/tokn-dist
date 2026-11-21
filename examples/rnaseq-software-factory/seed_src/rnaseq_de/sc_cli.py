"""PROTOTYPE CLI for single-cell annotation. See rnaseq_de/sc.py."""
import argparse
import sys
from pathlib import Path

from . import sc


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rnaseq_de.sc_cli")
    ap.add_argument("--sc-counts", required=True)
    ap.add_argument("--cells", required=True)
    ap.add_argument("--c2s-url", default="http://127.0.0.1:8091")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1, help="accepted for compatibility; requests are sequential")
    a = ap.parse_args(argv)
    counts, cells = sc.load(a.sc_counts, a.cells)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ann = sc.annotate(counts, cells, a.c2s_url)
    ann.to_csv(out / "celltypes.tsv", sep="\t", index=False)
    sc.pooled_de(counts, cells).to_csv(out / "sc_de.tsv", sep="\t", index=False)
    (out / "sc_report.md").write_text("# Single-cell report\n\n" + ann["cell_type"].value_counts().to_string() + "\n",
                                      encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
