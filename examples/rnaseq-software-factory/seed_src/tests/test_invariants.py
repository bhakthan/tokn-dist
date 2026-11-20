"""Invariant tests for the RNA-seq DE pipeline. Several FAIL on the seed on purpose."""
import io
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rnaseq_de import cli, counts_io, de, qc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCRATCH = ROOT / ".pytest_out"


@pytest.fixture
def outdir(request):
    d = SCRATCH / request.node.name
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _run(outdir, samples="samples.tsv"):
    return cli.run(DATA / "counts.tsv", DATA / "counts_opposite.tsv", DATA / samples, outdir)


def test_counts_reject_non_integer():
    with pytest.raises(ValueError, match="integer"):
        counts_io.load_counts(io.StringIO("gene\tS1\tS2\nG1\t1.5\t2\nG2\t3\t4\n"))


def test_counts_reject_negative():
    with pytest.raises(ValueError, match="negative"):
        counts_io.load_counts(io.StringIO("gene\tS1\tS2\nG1\t-1\t2\nG2\t3\t4\n"))


def test_counts_load_as_integers():
    c = counts_io.load_counts(DATA / "counts.tsv")
    assert all(np.issubdtype(t, np.integer) for t in c.dtypes)


def test_low_rin_samples_excluded():
    s = counts_io.load_samples(DATA / "samples.tsv")
    kept, excluded = qc.filter_low_rin(s)
    assert excluded, "a sample with RIN < 6 exists and must be excluded"
    assert all(s.loc[x, "rin"] < qc.MIN_RIN for x in excluded)
    assert (kept["rin"] >= qc.MIN_RIN).all()


def test_bh_fdr_reference_values():
    p = np.array([0.01, 0.04, 0.03, 0.005])
    np.testing.assert_allclose(de.bh_fdr(p), [0.02, 0.04, 0.04, 0.02])


def test_strandedness_inferred_from_data():
    c = counts_io.load_counts(DATA / "counts.tsv")
    o = counts_io.load_counts(DATA / "counts_opposite.tsv")
    calls = qc.infer_strandedness(c, o)
    assert set(calls) == set(c.columns)
    assert set(calls.values()) <= {"forward", "reverse"}
    fixed = qc.apply_strandedness(c, o, calls)
    for sid in c.columns:
        sense = fixed[sid].sum()
        assert sense > (c[sid].sum() + o[sid].sum()) - sense, f"{sid}: corrected counts are not the sense strand"


def test_confounded_design_refused():
    s = counts_io.load_samples(DATA / "samples_confounded.tsv")
    with pytest.raises(qc.ConfoundedDesignError):
        qc.check_confounding(s)


def test_balanced_design_accepted():
    qc.check_confounding(counts_io.load_samples(DATA / "samples.tsv"))


def test_outputs_carry_no_subject_identifiers(outdir):
    assert _run(outdir) == 0
    for f in outdir.iterdir():
        assert "SUBJ-" not in f.read_text(encoding="utf-8"), f"{f.name} leaks subject_ref"


def test_golden_de_recovered(outdir):
    assert _run(outdir) == 0
    res = pd.read_csv(outdir / "de_results.tsv", sep="\t")
    called = de.call_de(res).set_index("gene")["log2fc"]
    golden = pd.read_csv(ROOT / "golden" / "de_golden.tsv", sep="\t")
    hits = sum(1 for g, d in zip(golden["gene"], golden["direction"])
               if g in called.index and (called[g] > 0) == (d == "up"))
    assert hits >= 0.9 * len(golden), f"golden recall {hits}/{len(golden)}"
    qcj = json.loads((outdir / "qc.json").read_text(encoding="utf-8"))
    assert qcj["excluded_samples"], "qc.json must list the RIN-excluded samples"
