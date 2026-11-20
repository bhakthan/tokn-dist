"""Write DE outputs: de_results.tsv, qc.json, report.md."""
import json
from pathlib import Path

from . import de


def write_report(out_dir, results, qc_summary, samples):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results.to_csv(out / "de_results.tsv", sep="\t", index=False, float_format="%.6g")
    (out / "qc.json").write_text(json.dumps(qc_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    called = de.call_de(results)
    lines = ["# DE report", "", f"Genes tested: {len(results)}", f"Genes called: {len(called)}", "", "## Samples", ""]
    # TODO(data boundary): this dumps every sample-sheet column, including subject_ref.
    cols = list(samples.columns)
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "---|" * len(cols))
    for _, row in samples.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
