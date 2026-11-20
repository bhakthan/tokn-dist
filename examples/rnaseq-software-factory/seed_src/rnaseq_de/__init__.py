"""RNA-seq differential expression (SYNTHETIC teaching fixture).

Pipeline: counts -> strandedness -> RIN filter -> design check -> CPM ->
log2(CPM+1) -> Welch t -> BH-FDR -> report.
"""

__all__ = ["counts_io", "normalize", "qc", "de", "report", "cli"]
