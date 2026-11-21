"""Single-cell (C2S) service invariants. Offline: the model is tests/fake_c2s.py."""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

from rnaseq_de import sc, sc_cli

ROOT = Path(__file__).resolve().parents[1]
SC = ROOT / "data" / "sc"
SCRATCH = ROOT / ".pytest_out"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fake_c2s  # noqa: E402


@pytest.fixture
def outdir(request):
    d = SCRATCH / request.node.name
    shutil.rmtree(d, ignore_errors=True)
    d.parent.mkdir(parents=True, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def oracle(tmp_path):
    srvs = []

    def start(mode="normal"):
        log = tmp_path / f"{mode.replace(':', '_')}.jsonl"
        srv, url = fake_c2s.serve(0, mode, str(log))
        srvs.append(srv)
        return url, log

    yield start
    for s in srvs:
        s.shutdown()
        s.server_close()


def _cli(url, out, counts=SC / "counts.tsv"):
    return sc_cli.main(["--sc-counts", str(counts), "--cells", str(SC / "cells.tsv"), "--c2s-url", url,
                        "--out", str(out), "--workers", "4"])


def _gold():
    return pd.read_csv(ROOT / "golden" / "sc_celltypes_examples.tsv", sep="\t").set_index("cell_id")["cell_type"]


def test_sentence_is_descending_count_ties_by_symbol():
    col = pd.Series({"B2M": 3, "ACTB": 3, "CD3E": 9, "MT-CO1": 0})
    assert sc.cell_sentence(col) == ["CD3E", "ACTB", "B2M"]


@pytest.mark.parametrize("text,label", [
    ("CD16-positive, CD56-dim natural killer cell, human.<ctrl100>", "nk"),
    ("effector memory CD8-positive, alpha-beta T cell, terminally differentiated.", "cd8_t"),
    ("classical monocyte.", "monocyte"),
    ("naive B cell.", "b"),
])
def test_aliases_map_c2s_phrasing(text, label):
    assert sc.normalize_label(text) == (label, "ok")


@pytest.mark.parametrize("text", ["mature NK T cell.", "plasma cell.", "not a monocyte.",
                                  "monocyte or B cell.", "", "B cell.\nmonocyte."])
def test_unmapped_or_ambiguous_is_unassigned(text):
    assert sc.normalize_label(text)[0] == sc.UNASSIGNED


def test_marker_guardrail_rejects_unsupported_label():
    sentence = ["MS4A1", "CD79A", "CD79B", "CD19", "ACTB"]
    assert sc.verify_label("b", sentence)[0]
    assert not sc.verify_label("monocyte", sentence)[0]


@pytest.mark.parametrize("url", ["http://example.com:8091", "https://127.0.0.1:8091", "http://u:p@127.0.0.1:1"])
def test_only_plain_loopback_endpoints(url):
    with pytest.raises(sc.InputError):
        sc.check_endpoint(url)


def test_service_end_to_end(oracle, outdir):
    url, log = oracle()
    assert _cli(url, outdir) == 0
    lab = pd.read_csv(outdir / "celltypes.tsv", sep="\t", keep_default_na=False).set_index("cell_id")
    gold = _gold()
    assert (lab.loc[gold.index, "cell_type"] == gold).mean() >= 0.9
    qcj = json.loads((outdir / "sc_qc.json").read_text(encoding="utf-8"))
    excluded = set(qcj["excluded_low_quality"]) | set(qcj["doublets"])
    prompts = [json.loads(ln)["prompt"] for ln in log.read_text(encoding="utf-8").splitlines()]
    assert len(prompts) == qcj["n_sent"] == lab.shape[0] - len(excluded), "QC must run before the model"
    ids = set(lab.index) | set(lab["sample_id"])
    assert not any(t.strip(".,") in ids or "SUBJ-" in t for p in prompts for t in p.split())
    for f in outdir.iterdir():
        assert "SUBJ-" not in f.read_text(encoding="utf-8"), f"{f.name} leaks subject_ref"


def test_adversarial_model_cannot_mislabel(oracle, outdir):
    url, _ = oracle("flip")
    assert _cli(url, outdir) == 0
    got = pd.read_csv(outdir / "celltypes.tsv", sep="\t", keep_default_na=False).set_index("cell_id")["cell_type"]
    gold = _gold()
    got = got.loc[gold.index]
    assert not ((got != gold) & got.isin(sc.VOCAB)).any()


@pytest.mark.parametrize("mode", ["die_after:20", "invalid"])
def test_fails_closed_when_model_breaks(oracle, outdir, mode):
    url, _ = oracle(mode)
    assert _cli(url, outdir) == 4
    assert not outdir.exists()


def test_invalid_input_sends_nothing(oracle, outdir, tmp_path):
    url, log = oracle()
    lines = (SC / "counts.tsv").read_text(encoding="utf-8").splitlines()
    bad = tmp_path / "dup.tsv"
    bad.write_text("\n".join(lines + [lines[3]]) + "\n", encoding="utf-8")
    assert _cli(url, outdir, bad) == 2
    assert not outdir.exists() and not (log.exists() and log.read_text(encoding="utf-8"))
