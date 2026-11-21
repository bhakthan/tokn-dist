"""Single-cell annotation with a Cell2Sentence (C2S-Scale) model + cell-type-aware pseudobulk DE.

Pipeline (each step is a glossary invariant):
  1. validate: integer UMI counts (genes x cells, unique HGNC-style symbols, no
     empty barcodes) + a cell sheet with one condition per sample; else InputError
  2. QC BEFORE the model: drop cells with mitochondrial fraction > MAX_PCT_MITO and
     heterotypic doublets (>= 2 lineage panels detected); the model never sees them
  3. cell sentence: genes with count > 0 ordered by DESCENDING count (ties: gene
     symbol), top SENTENCE_GENES, in the model-card completion prompt; gene symbols
     only -- no sample, cell or subject identifier ever goes on the wire
  4. the model proposes, the guardrail disposes: the completion is matched against
     an anchored alias table for the controlled vocabulary; unmapped, ambiguous or
     marker-unsupported labels become "unassigned" with a reason code; a label is
     never inferred from markers
  5. fail closed: an unreachable endpoint or an invalid completion raises
     ModelUnavailableError; no label is fabricated and no partial output is written
  6. composition (abundance) is reported separately from expression; DE is per cell
     type on donor-level pseudobulks (>= MIN_CELLS cells per donor-type, >= MIN_DONORS
     donors per arm), library offsets on the full pseudobulk, a declared
     direction-blind expression filter, limma-style moderated t, BH within each type
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
from scipy import special, stats

from . import counts_io, de

VOCAB = ("cd4_t", "cd8_t", "b", "nk", "monocyte")
UNASSIGNED = "unassigned"
CONDITIONS = ("control", "treated")
MAX_PCT_MITO = 20.0
DOUBLET_MIN_UMI = 4
DOUBLET_MIN_MARKERS = 2
SENTENCE_GENES = 200
VERIFY_TOP_N = 100
VERIFY_MIN_HITS = 2
MIN_CELLS = 3          # cells per (donor, type) pseudobulk
MIN_DONORS = 3         # independent donors per arm
FILTER_MIN_COUNT = 5   # pseudobulk UMIs ...
FDR, MIN_ABS_LOG2FC = 0.05, 1.0
N_PREDICT, TEMPERATURE = 24, 0.0

LINEAGE_PANELS = {"T": ["CD3D", "CD3E", "TRAC"], "B": ["MS4A1", "CD79A", "CD79B", "CD19"],
                  "myeloid": ["CD14", "FCN1", "CSF1R", "VCAN"]}
VERIFY_PANELS = {
    "cd4_t": ["CD4", "IL7R", "CCR7", "LEF1", "TCF7", "SELL", "MAL"],
    "cd8_t": ["CD8A", "CD8B", "GZMK"],
    "b": ["MS4A1", "CD79A", "CD79B", "CD19", "BANK1", "TCL1A"],
    "nk": ["GNLY", "KLRF1", "KLRD1", "PRF1", "FCGR3A", "GZMB"],
    "monocyte": ["CD14", "LYZ", "S100A8", "S100A9", "FCN1", "VCAN", "CSF1R"],
}
# Anchored aliases (full match on the normalised completion). Versioned with the product.
# C2S emits Cell Ontology-style names: state prefixes ("effector memory ..."), trailing
# qualifiers (", terminally differentiated", ", CD45RO-positive") and a ", human" suffix.
ALIAS_VERSION = "c2s-pbmc-aliases/2"
_STATE = r"(?:(?:naive|memory|effector|effector memory|central memory|cytotoxic|activated|mature|resting|thymus derived) )*"
_CD8_CD4 = r"{cd} positive,? alpha beta {st}t cells?"
_QUALIFIERS = re.compile(r"(?:, (?:human|terminally differentiated|cd45ro positive|cd45ra positive|"
                         r"cd28 negative|cd27 positive|circulating|peripheral blood))+$")
ALIASES = {
    "monocyte": [rf"{_STATE}(?:classical |inflammatory |cd14 positive )?monocytes?",
                 r"cd14 positive,? cd16 negative classical monocytes?"],
    "b": [rf"{_STATE}(?:transitional |immature )?b cells?", r"b lymphocytes?"],
    "nk": [rf"{_STATE}(?:cd16 positive,? cd56 dim |cd16 negative,? cd56 bright |cd56 dim |cd56 bright )?natural killer cells?",
           r"nk cells?"],
    "cd8_t": [_STATE + _CD8_CD4.format(cd="cd8", st=_STATE), r"cd8 positive t cells?", r"cytotoxic t cells?"],
    "cd4_t": [_STATE + _CD8_CD4.format(cd="cd4", st=_STATE), r"cd4 positive t cells?", r"(?:t )?helper t cells?",
              r"(?:cd4 positive,? cd25 positive,? alpha beta )?regulatory t cells?"],
}
_ALIAS_RE = {t: [re.compile(p) for p in ps] for t, ps in ALIASES.items()}
PROMPT = ("The following is a list of {n} gene names ordered by descending expression level in a Homo sapiens "
          "cell. Your task is to give the cell type which this cell belongs to based on its gene expression.\n"
          "Cell sentence: {genes}.\nThe cell type corresponding to these genes is:")
PROMPT_SHA256 = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()
_SYMBOL = re.compile(r"^[A-Z0-9][A-Za-z0-9.\-]*$")
_ENSEMBL = re.compile(r"^ENS[A-Z]*G\d{6,}(?:\.\d+)?$")


class InputError(ValueError):
    """Invalid input: nothing is sent to the model and nothing is written."""


class ModelUnavailableError(RuntimeError):
    """The C2S endpoint is unreachable or returned an invalid completion; no label may be invented."""


# ---------------------------------------------------------------- loading
def load_cells(path):
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    need = {"cell_id", "sample_id", "condition"}
    if need - set(df.columns):
        raise InputError(f"cell sheet missing columns {sorted(need - set(df.columns))}")
    for col in need:
        if (df[col].str.strip() == "").any():
            raise InputError(f"cell sheet has blank {col} values")
    if df["cell_id"].duplicated().any():
        raise InputError("cell sheet has duplicate cell_id values")
    bad = sorted(set(df["condition"]) - set(CONDITIONS))
    if bad:
        raise InputError(f"condition must be one of {list(CONDITIONS)}; found {bad}")
    per = df.groupby("sample_id")["condition"].nunique()
    if (per > 1).any():
        raise InputError(f"samples with more than one condition: {sorted(per.index[per > 1])}")
    return df.set_index("cell_id", drop=False)


def _check_header(path):
    with open(path, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\r\n").split("\t")
    if len(set(header[1:])) != len(header) - 1:
        raise InputError("counts header has duplicate cell barcodes")


def load(counts_path, cells_path):
    _check_header(counts_path)
    try:
        counts = counts_io.load_counts(counts_path)
    except ValueError as e:
        raise InputError(str(e)) from e
    genes = counts.index.astype(str)
    if genes.duplicated().any():
        raise InputError(f"duplicate gene rows: {sorted(set(genes[genes.duplicated()]))[:5]} (sum or resolve upstream)")
    ens = [g for g in genes if _ENSEMBL.match(g)]
    if ens:
        raise InputError(f"{len(ens)} Ensembl gene IDs found (e.g. {ens[0]}); C2S reads HGNC symbols -- "
                         "map IDs to symbols with a pinned annotation release first")
    badsym = [g for g in genes if not _SYMBOL.match(g)]
    if badsym:
        raise InputError(f"invalid gene symbols, e.g. {badsym[:3]}")
    empty = list(counts.columns[counts.sum(axis=0) == 0])
    if empty:
        raise InputError(f"{len(empty)} barcodes have zero UMIs (e.g. {empty[0]}); remove empty droplets upstream")
    cells = load_cells(cells_path)
    if set(counts.columns) != set(cells.index):
        raise InputError("counts columns and cell sheet cell_id values differ")
    return counts, cells.loc[list(counts.columns)]


# ---------------------------------------------------------------- QC
def pct_mito(counts):
    mito = counts.index.str.upper().str.startswith("MT-")
    return counts[mito].sum(axis=0) / counts.sum(axis=0) * 100.0


def find_doublets(counts):
    out = []
    for c in counts.columns:
        col = counts[c]
        hit = sum(1 for panel in LINEAGE_PANELS.values()
                  if sum(int(col.get(g, 0)) >= DOUBLET_MIN_UMI for g in panel) >= DOUBLET_MIN_MARKERS)
        if hit >= 2:
            out.append(c)
    return out


def qc(counts):
    """Returns (low_quality, doublets, pct_mito). A barcode failing both is low_quality."""
    pm = pct_mito(counts)
    low = sorted(pm.index[pm > MAX_PCT_MITO])
    dbl = sorted(set(find_doublets(counts)) - set(low))
    return low, dbl, pm


# ---------------------------------------------------------------- model I/O
def cell_sentence(col, n=SENTENCE_GENES):
    nz = col[col > 0]
    return sorted(nz.index, key=lambda g: (-int(nz[g]), g))[:n]


def build_prompt(genes):
    return PROMPT.format(n=len(genes), genes=" ".join(genes))


def normalize_label(text):
    """Map a completion to (vocab label | UNASSIGNED, reason)."""
    lines = [ln for ln in str(text).replace("<ctrl100>", "\n").splitlines() if ln.strip()]
    if len(lines) != 1:
        return UNASSIGNED, "unmapped"
    t = lines[0].lower().replace("-", " ").replace("_", " ")
    t = " ".join(t.split()).strip().rstrip(".").strip()
    t = _QUALIFIERS.sub("", t).strip()
    hits = [k for k, rx in _ALIAS_RE.items() if any(r.fullmatch(t) for r in rx)]
    if len(hits) != 1:
        return UNASSIGNED, "ambiguous" if hits else "unmapped"
    return hits[0], "ok"


def verify_label(label, sentence):
    """(ok, reason, hits): >= VERIFY_MIN_HITS own markers in the top VERIFY_TOP_N, no stronger rival."""
    top = set(sentence[:VERIFY_TOP_N])
    hits = {k: sum(g in top for g in p) for k, p in VERIFY_PANELS.items()}
    own = hits.get(label, 0)
    if own < VERIFY_MIN_HITS:
        return False, "unsupported", own
    if any(k != label and h >= VERIFY_MIN_HITS and h > own for k, h in hits.items()):
        return False, "marker_conflict", own
    return True, "ok", own


def check_endpoint(url):
    """Only plain-HTTP loopback endpoints without credentials: cell data never leaves the host."""
    u = urllib.parse.urlsplit(url)
    if u.scheme != "http" or u.username or u.password or u.query or u.fragment:
        raise InputError("--c2s-url must be http://<loopback>:<port> with no credentials, query or fragment")
    host = u.hostname or ""
    try:
        ok = host == "localhost" or ipaddress.ip_address(host).is_loopback
    except ValueError:
        ok = False
    if not ok:
        raise InputError(f"--c2s-url host {host!r} is not loopback; the C2S model must run locally")
    return f"http://{u.netloc}{u.path.rstrip('/')}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


class C2SClient:
    """llama.cpp llama-server (/completion) client for a C2S-Scale GGUF model (loopback only)."""

    def __init__(self, url, timeout=120.0, retries=2):
        self.url = check_endpoint(url)
        self.timeout, self.retries = timeout, retries
        self.attempts = self.completions = 0
        self._open = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect()).open

    def _post(self, path, body):
        req = urllib.request.Request(self.url + path, json.dumps(body).encode("utf-8"),
                                     {"Content-Type": "application/json"})
        with self._open(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    def complete(self, prompt):
        last = None
        for _ in range(self.retries + 1):
            self.attempts += 1
            try:
                doc = self._post("/completion", {"prompt": prompt, "n_predict": N_PREDICT,
                                                 "temperature": TEMPERATURE, "cache_prompt": True})
            except (urllib.error.URLError, OSError, ValueError) as e:
                last = e
                continue
            content = doc.get("content") if isinstance(doc, dict) else None
            if not isinstance(content, str) or not content.strip():
                raise ModelUnavailableError(f"C2S endpoint returned an invalid completion: {str(doc)[:80]!r}")
            self.completions += 1
            return content
        raise ModelUnavailableError(f"C2S endpoint failed after {self.retries + 1} attempts: {last}")

    def describe(self):
        """Best-effort server provenance (basename of the loaded model only; never a full path)."""
        info = {}
        try:
            with self._open(self.url + "/props", timeout=10) as r:
                p = json.loads(r.read().decode("utf-8"))
            info["model_file"] = str(p.get("model_path", "")).replace("\\", "/").rsplit("/", 1)[-1]
            info["server_build"] = str(p.get("build_info", ""))
            info["n_ctx"] = (p.get("default_generation_settings") or {}).get("n_ctx")
            info["slots"] = p.get("total_slots")
        except Exception:  # noqa: BLE001 -- provenance is optional; inference is not
            pass
        return info


def annotate(counts, client, workers=4):
    """One completion per QC-passed cell. Aborts everything on the first model failure."""
    sentences = {c: cell_sentence(counts[c]) for c in counts.columns}
    raw = {}
    ex = ThreadPoolExecutor(max_workers=max(1, workers))
    try:
        futs = {ex.submit(client.complete, build_prompt(sentences[c])): c for c in counts.columns}
        for f in as_completed(futs):
            raw[futs[f]] = f.result()
    except BaseException:
        ex.shutdown(wait=True, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    rows = []
    for c in counts.columns:
        cand, reason = normalize_label(raw[c])
        ok, hits = False, 0
        if cand != UNASSIGNED:
            ok, reason, hits = verify_label(cand, sentences[c])
        rows.append({"cell_id": c, "candidate": cand, "cell_type": cand if ok else UNASSIGNED,
                     "verified": bool(ok), "reason": reason, "marker_hits": int(hits)})
    return pd.DataFrame(rows).set_index("cell_id", drop=False)


# ---------------------------------------------------------------- composition
def composition(annot, cells):
    """Per-sample integer counts/fractions (incl. unassigned and zero rows) + condition summaries."""
    df = annot[["cell_type"]].join(cells[["sample_id", "condition"]], how="left")
    rows = []
    for (sid, cond), g in df.groupby(["sample_id", "condition"], sort=True):
        n = len(g)
        for t in (*VOCAB, UNASSIGNED):
            k = int((g["cell_type"] == t).sum())
            rows.append({"level": "sample", "sample_id": sid, "condition": cond, "cell_type": t,
                         "n_cells": k, "n_total": n, "fraction": round(k / n, 4)})
    per = pd.DataFrame(rows)
    for cond in CONDITIONS:
        sub = per[per["condition"] == cond]
        for t in (*VOCAB, UNASSIGNED):
            s = sub[sub["cell_type"] == t]
            k, n = int(s["n_cells"].sum()), int(s["n_total"].sum())
            rows.append({"level": "condition_pooled", "sample_id": "", "condition": cond, "cell_type": t,
                         "n_cells": k, "n_total": n, "fraction": round(k / n, 4) if n else 0.0})
            rows.append({"level": "condition_donor_mean", "sample_id": "", "condition": cond, "cell_type": t,
                         "n_cells": k, "n_total": n, "fraction": round(float(s["fraction"].mean()), 4) if len(s) else 0.0})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- DE
def _ebayes_prior(s2, d):
    """Smyth (2004) moment estimate of the prior (d0, s0^2) for gene variances."""
    s2 = np.maximum(s2, 1e-12)
    e = np.log(s2) - special.digamma(d / 2) + np.log(d / 2)
    emean = float(e.mean())
    v = float(np.var(e, ddof=1) - special.polygamma(1, d / 2))
    if v <= 0:
        return np.inf, float(np.exp(emean))
    lo, hi = 1e-6, 1e6  # solve trigamma(d0/2) = v
    for _ in range(200):
        mid = np.sqrt(lo * hi)
        lo, hi = (mid, hi) if special.polygamma(1, mid) > v else (lo, mid)
    d0 = 2 * np.sqrt(lo * hi)
    return d0, float(np.exp(emean + special.digamma(d0 / 2) - np.log(d0 / 2)))


def moderated_t(log_expr, conditions):
    """Two-group limma-style moderated t (pooled variance, empirical-Bayes shrinkage)."""
    a = log_expr.loc[:, conditions == "treated"].to_numpy()
    b = log_expr.loc[:, conditions == "control"].to_numpy()
    n1, n2 = a.shape[1], b.shape[1]
    d = n1 + n2 - 2
    s2 = (a.var(axis=1, ddof=1) * (n1 - 1) + b.var(axis=1, ddof=1) * (n2 - 1)) / d
    d0, s02 = _ebayes_prior(s2, d)
    post = np.full_like(s2, s02) if not np.isfinite(d0) else (d0 * s02 + d * s2) / (d0 + d)
    df = d + (d0 if np.isfinite(d0) else 1e6)
    lfc = a.mean(axis=1) - b.mean(axis=1)
    t = lfc / np.sqrt(post * (1 / n1 + 1 / n2))
    p = 2 * stats.t.sf(np.abs(t), df)
    return pd.DataFrame({"gene": log_expr.index, "log2fc": lfc, "pvalue": p}), {"d0": float(d0), "s0_sq": s02}


def pseudobulk_de(counts, annot, cells):
    """Per-cell-type donor pseudobulk DE. Returns (results, support) -- support explains every skip."""
    meta = annot[["cell_type"]].join(cells[["sample_id", "condition"]], how="left")
    out, support = [], {}
    for t in VOCAB:
        sel = meta[meta["cell_type"] == t]
        sums, conds, ncell, dropped = {}, {}, {}, []
        for sid, g in sel.groupby("sample_id", sort=True):
            if len(g) >= MIN_CELLS:
                sums[sid] = counts[list(g.index)].sum(axis=1)
                conds[sid], ncell[sid] = g["condition"].iloc[0], len(g)
            else:
                dropped.append(f"{sid}:{len(g)}")
        cond = pd.Series(conds, dtype=str)
        n_t, n_c = int((cond == "treated").sum()), int((cond == "control").sum())
        info = {"donors_control": n_c, "donors_treated": n_t, "cells": int(sum(ncell.values())),
                "donors_below_min_cells": dropped}
        if min(n_t, n_c) < MIN_DONORS:
            info["status"] = f"not tested: needs >= {MIN_DONORS} donors per arm with >= {MIN_CELLS} cells"
            support[t] = info
            continue
        pb = pd.DataFrame(sums)
        libs = pb.sum(axis=0)  # offsets from the FULL pseudobulk, before filtering
        keep = (pb >= FILTER_MIN_COUNT).sum(axis=1) >= min(n_t, n_c)
        pbk = pb[keep]
        logcpm = np.log2(pbk.div(libs, axis=1) * 1e6 + 1.0)
        res, prior = moderated_t(logcpm, cond.reindex(pbk.columns))
        res["padj"] = de.bh_fdr(res["pvalue"].to_numpy())
        res.insert(0, "cell_type", t)
        res["n_control"], res["n_treated"], res["n_cells"] = n_c, n_t, info["cells"]
        res["called"] = (res["padj"] < FDR) & (res["log2fc"].abs() >= MIN_ABS_LOG2FC)
        info.update(status="tested", genes_tested=int(len(res)), calls=int(res["called"].sum()),
                    prior_df=round(prior["d0"], 3) if np.isfinite(prior["d0"]) else "inf")
        support[t] = info
        out.append(res.sort_values(["pvalue", "gene"], kind="mergesort"))
    cols = ["cell_type", "gene", "log2fc", "pvalue", "padj", "called", "n_control", "n_treated", "n_cells"]
    df = pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=cols)
    return df[cols], support


def pooled_effects(counts, cells, genes):
    """Negative control: all-cells-pooled donor log2FC (composition and expression conflated)."""
    sums = {sid: counts[list(g.index)].sum(axis=1) for sid, g in cells.groupby("sample_id", sort=True)}
    pb = pd.DataFrame(sums)
    lc = np.log2(pb.div(pb.sum(axis=0), axis=1) * 1e6 + 1.0)
    cond = cells.groupby("sample_id")["condition"].first().reindex(pb.columns)
    diff = lc.loc[:, cond == "treated"].mean(axis=1) - lc.loc[:, cond == "control"].mean(axis=1)
    return {g: round(float(diff[g]), 3) for g in genes if g in diff.index}
