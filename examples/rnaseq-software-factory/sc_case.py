"""Deterministic SYNTHETIC single-cell (PBMC-like) fixture for the C2S feature loop.

Imported by make_case.py; not a CLI. Real, current HGNC symbols are used because
Cell2Sentence (C2S-Scale) reads gene NAMES. Cells are simulated from textbook
marker programs on a reduced 2,048-gene panel, not derived from any real dataset
or person. This is a deliberately enriched PBMC-like challenge, not a reference
distribution for healthy donors.

Generative model (per cell c of type t in donor d):
  p_c = m_c * MT + r_c * RIBO + (1 - m_c - r_c) * ENDO_t,d,c          (module masses)
  p_obs = (1 - rho_c) * p_c + rho_c * ambient_d,  rho_c ~ U(0.01, 0.04)
  X_g ~ Poisson(Gamma(theta_g, (L_c * p_obs,g) / theta_g))            (NB, Var = mu + mu^2/theta)
ENDO carries housekeeping, shared and lineage programs, an interferon module, a
stress module and a low-abundance tail, plus gene-specific donor effects,
donor-by-module effects and per-cell state effects.

Planted truth (hidden answer key):
  * 8 independent donors (4 control, 4 treated), 25 known clean cells each, with
    a per-donor allocation; B cells are ~14% of post-QC cells in control vs ~29%
    in treated (a COMPOSITION shift: no B-cell gene changes expression)
  * 4 QC-eligible pDC-like cells (out of the product vocabulary => "unassigned")
  * 2 low-quality cells/donor (mitochondrial fraction 28-42%; clean ~2-8%)
  * 1 heterotypic doublet/donor from two independent same-donor parents
  * an interferon response in TREATED MONOCYTES ONLY: 8 core ISGs at +2.2..+2.7
    log2 and 7 secondary ISGs at +0.4..+1.2 log2 (secondary are not nulls)
  * ambient RNA 1-4% in every barcode, so off-lineage marker UMIs occur
Independent RNG streams keep adding a trap from regenerating the whole cohort.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CELL_TYPES = ("cd4_t", "cd8_t", "b", "nk", "monocyte")
OOV_TYPE = "pdc"  # biologically real, outside the product vocabulary
N_GENES = 2048

# Donor slots -> opaque sample ids (condition is NOT encoded in the id).
SAMPLES = [  # sample_id, condition, slot
    ("SC01", "treated", 0), ("SC02", "control", 0), ("SC03", "control", 1), ("SC04", "treated", 1),
    ("SC05", "treated", 2), ("SC06", "control", 2), ("SC07", "treated", 3), ("SC08", "control", 3),
]
ALLOCATION = {  # (condition, slot) -> clean known cells (cd4_t, cd8_t, b, nk, monocyte)
    ("control", 0): (7, 4, 4, 3, 7), ("control", 1): (8, 4, 3, 4, 6),
    ("control", 2): (7, 5, 3, 3, 7), ("control", 3): (7, 4, 4, 4, 6),
    ("treated", 0): (5, 3, 8, 3, 6), ("treated", 1): (5, 4, 7, 3, 6),
    ("treated", 2): (6, 3, 7, 3, 6), ("treated", 3): (5, 4, 8, 3, 5),
}
PDC_SLOTS = {("control", 0), ("control", 2), ("treated", 1), ("treated", 3)}
N_LOW_QUALITY = 2  # per donor
DOUBLET_PAIRS = [("cd4_t", "b"), ("cd8_t", "monocyte"), ("b", "monocyte"), ("cd4_t", "monocyte")]

# ---- curated programs (all current HGNC approved symbols; see validate_symbols) ----
T_CORE = "CD3D CD3E CD3G TRAC CD2 IL32 CD247".split()
CYTO = "NKG7 GZMA CST7".split()                      # shared CD8 T / NK
FCR = "TYROBP FCER1G".split()                        # shared NK / myeloid
APC = "CD74 HLA-DRA HLA-DRB1 HLA-DPA1 HLA-DPB1 HLA-DQA1".split()  # shared B / myeloid / pDC
IDENTITY = {
    "cd4_t": "CD4 IL7R CCR7 LEF1 TCF7 SELL MAL LTB CD28 ICOS".split(),
    "cd8_t": "CD8A CD8B GZMK CCL5 GZMH".split(),
    "b": "MS4A1 CD79A CD79B CD19 BANK1 TCL1A IGHM IGKC CD22 FCRLA VPREB3".split(),
    "nk": "GNLY KLRF1 KLRD1 PRF1 FCGR3A GZMB NCAM1 SPON2 CTSW".split(),
    "monocyte": "CD14 LYZ S100A8 S100A9 FCN1 VCAN CSF1R CST3 LST1 AIF1 MNDA CD68".split(),
    "pdc": "CLEC4C IL3RA LILRA4 TCF4 IRF8 PLD4 SERPINF1 ITM2C JCHAIN PTCRA".split(),
}
SHARED = {  # type -> (genes, natural-log weight)
    "cd4_t": [(T_CORE, 3.7)], "cd8_t": [(T_CORE, 3.7), (CYTO, 2.9)],
    "b": [(APC, 3.6)], "nk": [(CYTO, 4.6), (FCR, 3.4)],
    "monocyte": [(FCR, 3.8), (APC, 3.1)], "pdc": [(APC, 3.5), (["GZMB"], 3.0)],
}
# Real PBMC identity programs are skewed, not flat: a few transcripts dominate each
# type (e.g. LYZ/S100A8/S100A9 in CD14 monocytes, GNLY/NKG7 in NK, LTB/IL7R in naive
# CD4 T); immunoglobulin transcripts stay modest in non-plasma B cells.
IDENTITY_WEIGHT = {
    "cd4_t": {"LTB": 4.8, "IL7R": 4.5, "CCR7": 4.2, "LEF1": 3.9, "TCF7": 3.8, "MAL": 3.7, "CD4": 3.3},
    "cd8_t": {"CD8A": 4.5, "CD8B": 4.6, "CCL5": 4.4, "GZMK": 4.0, "GZMH": 3.5},
    "b": {"CD79A": 4.8, "MS4A1": 4.7, "CD79B": 4.3, "BANK1": 3.8, "TCL1A": 4.2, "IGHM": 3.3, "IGKC": 3.4},
    "nk": {"GNLY": 5.6, "PRF1": 4.3, "KLRD1": 4.2, "FCGR3A": 4.0, "GZMB": 4.3, "KLRF1": 3.9},
    "monocyte": {"LYZ": 5.8, "S100A9": 5.7, "S100A8": 5.4, "FCN1": 4.6, "CST3": 4.6, "VCAN": 4.2, "CD14": 4.1},
    "pdc": {"LILRA4": 4.4, "IRF8": 4.2, "PLD4": 4.2, "ITM2C": 4.3, "SERPINF1": 4.0, "JCHAIN": 3.8},
}
STATE_VAR = {"CCR7": 0.5, "IL7R": 0.5, "SELL": 0.4, "GZMK": 0.5, "CCL5": 0.5, "GZMH": 0.6}
ISGS = "ISG15 IFI6 MX1 IFIT1 IFIT3 IFI44L RSAD2 OAS1".split()             # core positives
ISGS_SECONDARY = "IFITM3 LY6E BST2 STAT1 IRF7 XAF1 TRIM22".split()         # weak co-movers
STRESS = "FOS JUN JUNB DUSP1 HSPA1A HSPA1B IER2 ZFP36".split()
MITO = "MT-CO1 MT-CO2 MT-CO3 MT-ND1 MT-ND2 MT-ND3 MT-ND4 MT-ND4L MT-ND5 MT-ND6 MT-CYB MT-ATP6 MT-ATP8".split()
RIBO = ("RPL3 RPL4 RPL5 RPL6 RPL7 RPL7A RPL8 RPL9 RPL10 RPL10A RPL11 RPL12 RPL13 RPL13A RPL14 RPL15 "
        "RPL17 RPL18 RPL18A RPL19 RPL21 RPL22 RPL23 RPL23A RPL24 RPL26 RPL27 RPL27A RPL28 RPL29 RPL30 "
        "RPL31 RPL32 RPL34 RPL35 RPL35A RPL36 RPL36A RPL37 RPL37A RPL38 RPL39 RPL41 RPLP0 RPLP1 RPLP2 "
        "RPS2 RPS3 RPS3A RPS4X RPS5 RPS6 RPS7 RPS8 RPS9 RPS10 RPS11 RPS12 RPS13 RPS14 RPS15 RPS15A "
        "RPS16 RPS17 RPS18 RPS19 RPS20 RPS21 RPS23 RPS24 RPS25 RPS26 RPS27 RPS27A RPS28 RPS29 RPSA").split()
HOUSE = ("ACTB GAPDH B2M TMSB4X MALAT1 EEF1A1 TPT1 FTL FTH1 PTMA HSP90AB1 UBA52 MYL6 PFN1 CFL1 OAZ1 SRGN "
         "ARHGDIB CORO1A LCP1 PTPRC HCST LAPTM5 CD52 CD37 SH3BGRL3 EIF1 NACA FAU UBB H3-3B HNRNPA1 YBX1 RACK1 "
         "SERF2 COX4I1 ATP5F1E NPM1 TXN PPIA").split()
BACKGROUND = ("KLF6 CXCR4 BTG1 SAT1 ANXA1 VIM S100A4 S100A6 S100A10 LGALS1 CD48 SEPTIN7 RAC2 ARPC3 ARPC2 "
              "ACTG1 TMSB10 CALM2 GSTP1 ITM2B SOD1 COXFA4 COX7C EMP3 CD99 HLA-A HLA-B HLA-C HLA-E PSAP CTSS "
              "GABARAP SUMO2 UQCRB ATP5MG EIF3E EIF4A1 EIF3K EEF1D EEF2 GNAS HINT1 SNRPD2 SRSF3 SRSF7 HNRNPDL "
              "DDX5 PABPC1 NOP53 BTF3 NME2 PPDPF COX6C COX7A2 ATP5MC2 ATP5PO NDUFB9 NDUFS5 POLR2L PSMA7 PSMB1 "
              "RBM3 CIRBP SELENOK TOMM7 TOMM20 UQCRH MYL12A MYL12B ARL6IP5 CD47 CD44 CD53 LSP1 FXYD5 RHOA RAC1 "
              "CDC42 GDI2 YWHAZ YWHAB CALR CANX PDIA3 HSPA8 HSPA5 HSP90AA1 DNAJB1 UBC UBE2D3 SQSTM1 NEAT1 "
              "ZFAS1 SNHG8 SNHG6 GAS5 TXNIP SPCS1 SEC61B SSR4 KDELR1 OST4 TMBIM6 ATP6V0E1 ATP6V1F IFITM2").split()

# Lineage-exclusive panels for doublet calls; verify panels for the label guardrail.
LINEAGE_PANELS = {"T": ["CD3D", "CD3E", "TRAC"], "B": ["MS4A1", "CD79A", "CD79B", "CD19"],
                  "myeloid": ["CD14", "FCN1", "CSF1R", "VCAN"]}
B_COMPOSITION_PANEL = ["MS4A1", "CD79A", "CD79B", "CD19", "BANK1"]

TYPE_DEPTH = {"cd4_t": 0.9, "cd8_t": 0.95, "b": 0.9, "nk": 1.05, "monocyte": 1.25, "pdc": 1.0}
TYPE_RIBO = {"cd4_t": 0.30, "cd8_t": 0.27, "b": 0.26, "nk": 0.22, "monocyte": 0.16, "pdc": 0.18}
MEDIAN_UMI = 3500.0


def curated_genes() -> list[str]:
    out = [*RIBO, *MITO, *HOUSE, *BACKGROUND, *ISGS, *ISGS_SECONDARY, *STRESS, *T_CORE, *CYTO, *FCR, *APC]
    for t in IDENTITY:
        out += IDENTITY[t]
    return list(dict.fromkeys(out))


def tail_genes() -> list[str]:
    lines = (HERE / "sc_genes_tail.txt").read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def gene_universe() -> list[str]:
    cur = curated_genes()
    tail = [g for g in tail_genes() if g not in set(cur)]
    genes = cur + tail[: N_GENES - len(cur)]
    if len(genes) != N_GENES or len(set(genes)) != N_GENES:
        raise RuntimeError(f"gene universe must be {N_GENES} unique symbols, got {len(set(genes))}")
    return sorted(genes)


def _streams(seed):
    ss = np.random.SeedSequence(seed + 1009)
    names = ("programs", "donors", "plan", "cells", "molecules", "examples")
    return {n: np.random.default_rng(s) for n, s in zip(names, ss.spawn(len(names)))}


def _programs(rng, genes, idx):
    """Endogenous natural-log weights per type (MT/ribo handled as separate modules)."""
    n = len(genes)
    base = np.full(n, -np.inf)
    module = np.full(n, "", dtype=object)
    special = set(MITO) | set(RIBO)
    for g in genes:
        if g not in special:
            base[idx[g]] = rng.normal(-1.6, 1.1)
            module[idx[g]] = "tail"
    for g in HOUSE:
        base[idx[g]] = rng.normal(3.6, 0.5)
        module[idx[g]] = "house"
    for g in BACKGROUND:
        base[idx[g]] = rng.normal(1.6, 0.8)
        module[idx[g]] = "background"
    for g in STRESS:
        base[idx[g]] = rng.normal(1.4, 0.4)
        module[idx[g]] = "stress"
    for g in ISGS_SECONDARY:
        base[idx[g]] = rng.normal(1.0, 0.3)
        module[idx[g]] = "isg"
    lineage = {g for t in IDENTITY for g in IDENTITY[t]} | set(T_CORE) | set(CYTO) | set(FCR) | set(APC)
    for g in lineage:
        base[idx[g]] = -np.inf  # structural zeros; ambient RNA supplies realistic leakage
        module[idx[g]] = "lineage"
    prog = {}
    for t in (*CELL_TYPES, OOV_TYPE):
        w = base.copy()
        for genes_, lw in SHARED[t]:
            for g in genes_:
                w[idx[g]] = rng.normal(lw, 0.25)
        for g in IDENTITY[t]:
            w[idx[g]] = rng.normal(IDENTITY_WEIGHT[t].get(g, 3.6), 0.25)
        isg_base = 0.9 if t == "monocyte" else -0.2
        for g in ISGS:
            w[idx[g]] = rng.normal(isg_base, 0.2)
        prog[t] = w
    theta = np.where(np.isin(module, ["house"]), 8.0, np.where(module == "lineage", 5.0, 3.0))
    return prog, module, theta


def _norm(w):
    e = np.where(np.isfinite(w), np.exp(np.where(np.isfinite(w), w, 0.0)), 0.0)
    return e / e.sum()


def generate(seed: int) -> dict:
    rs = _streams(seed)
    genes = gene_universe()
    idx = {g: i for i, g in enumerate(genes)}
    prog, module, theta = _programs(rs["programs"], genes, idx)
    mt_idx = np.array([idx[g] for g in MITO])
    ribo_idx = np.array([idx[g] for g in RIBO])
    theta[mt_idx] = 8.0
    theta[ribo_idx] = 8.0
    mt_w = np.zeros(len(genes))
    mt_w[mt_idx] = _norm(rs["programs"].normal(0.0, 0.35, len(mt_idx)))
    ribo_base = rs["programs"].normal(0.0, 0.45, len(ribo_idx))
    isg_idx = np.array([idx[g] for g in ISGS])
    sec_idx = np.array([idx[g] for g in ISGS_SECONDARY])
    core_lfc = dict(zip(ISGS, rs["programs"].uniform(2.2, 2.7, len(ISGS)).round(3)))
    sec_lfc = dict(zip(ISGS_SECONDARY, rs["programs"].uniform(0.4, 1.2, len(ISGS_SECONDARY)).round(3)))
    mods = {m: np.where(module == m)[0] for m in ("house", "background", "stress", "isg", "tail")}

    donors = {}
    for sid, cond, slot in SAMPLES:
        d = rs["donors"]
        donors[sid] = {
            "gene": d.normal(0.0, 0.13, len(genes)),
            "module": {m: d.normal(0.0, 0.12) for m in (*CELL_TYPES, OOV_TYPE, "isg", "stress", "house", "ribo")},
            "ribo": ribo_base + d.normal(0.0, 0.1, len(ribo_idx)),
        }

    def endo(t, sid, cond, cstate):
        dn = donors[sid]
        w = prog[t] + dn["gene"]
        lin = np.isfinite(w) & (module == "lineage")
        w[lin] += dn["module"][t] + cstate["identity"]
        for g, sd in STATE_VAR.items():
            if np.isfinite(w[idx[g]]):
                w[idx[g]] += cstate["var"][g] * sd
        w[mods["isg"]] += dn["module"]["isg"]
        w[isg_idx] += dn["module"]["isg"]
        w[mods["stress"]] += dn["module"]["stress"] + cstate["stress"]
        w[mods["house"]] += dn["module"]["house"]
        if cond == "treated" and t == "monocyte":
            f = cstate["ifn"]
            w[isg_idx] += np.array([core_lfc[g] for g in ISGS]) * np.log(2.0) * f
            w[sec_idx] += np.array([sec_lfc[g] for g in ISGS_SECONDARY]) * np.log(2.0) * f
        return _norm(w)

    def profile(t, sid, cond, cstate, mt_frac):
        r = TYPE_RIBO[t] * float(np.exp(cstate["ribo"]))
        rw = np.zeros(len(genes))
        rw[ribo_idx] = _norm(donors[sid]["ribo"])
        return mt_frac * mt_w + r * rw + (1.0 - mt_frac - r) * endo(t, sid, cond, cstate)

    def new_state(rng):
        return {"identity": rng.normal(0.0, 0.25), "stress": rng.normal(0.0, 0.5),
                "ribo": rng.normal(0.0, 0.12), "ifn": float(np.exp(rng.normal(0.0, 0.2))),
                "var": {g: rng.normal() for g in STATE_VAR}}

    def clean_mt(rng):
        return float(np.clip(np.exp(rng.normal(np.log(0.04), 0.3)), 0.015, 0.09))

    def depth(rng, t):
        return MEDIAN_UMI * TYPE_DEPTH[t] * float(np.exp(rng.normal(0.0, 0.38)))

    mol = rs["molecules"]

    def draw(p, lib):
        mu = p * lib
        lam = mol.gamma(theta, np.maximum(mu, 1e-300) / theta)
        return mol.poisson(lam)

    # ambient per donor: composition-weighted mean of reference (state-free) profiles
    zero_state = {"identity": 0.0, "stress": 0.0, "ribo": 0.0, "ifn": 1.0, "var": {g: 0.0 for g in STATE_VAR}}
    ambient = {}
    for sid, cond, slot in SAMPLES:
        alloc = dict(zip(CELL_TYPES, ALLOCATION[(cond, slot)]))
        tot = sum(alloc.values())
        ambient[sid] = sum(alloc[t] / tot * profile(t, sid, cond, zero_state, 0.04) for t in CELL_TYPES)

    plan_rng, cell_rng = rs["plan"], rs["cells"]
    cols, cell_rows, truth = [], [], {}
    low_quality, doublets, oov = [], [], []
    for si, (sid, cond, slot) in enumerate(SAMPLES):
        plan = []
        for t, k in zip(CELL_TYPES, ALLOCATION[(cond, slot)]):
            plan += [("clean", t)] * k
        if (cond, slot) in PDC_SLOTS:
            plan.append(("clean", OOV_TYPE))
        lq_types = plan_rng.choice(list(CELL_TYPES), N_LOW_QUALITY, p=[0.3, 0.15, 0.15, 0.15, 0.25])
        plan += [("low_quality", str(t)) for t in lq_types]
        a, b = DOUBLET_PAIRS[si % len(DOUBLET_PAIRS)]
        plan.append(("doublet", f"{a}+{b}"))
        perm = plan_rng.permutation(len(plan))
        for ci, pidx in enumerate(perm, start=1):
            kind, t = plan[pidx]
            cid = f"{sid}_c{ci:03d}"
            rho = float(cell_rng.uniform(0.01, 0.04))
            if kind == "doublet":
                ta, tb = t.split("+")
                xs = []
                for tt in (ta, tb):
                    p = profile(tt, sid, cond, new_state(cell_rng), clean_mt(cell_rng))
                    xs.append(draw((1 - rho) * p + rho * ambient[sid], depth(cell_rng, tt)))
                x = mol.binomial(xs[0] + xs[1], float(cell_rng.uniform(0.8, 1.0)))
                doublets.append(cid)
                truth[cid] = "doublet"
            else:
                st = new_state(cell_rng)
                lib = depth(cell_rng, t)
                if kind == "low_quality":
                    mt = float(cell_rng.uniform(0.28, 0.42))
                    lib *= float(cell_rng.uniform(0.45, 0.70))
                    low_quality.append(cid)
                else:
                    mt = clean_mt(cell_rng)
                p = profile(t, sid, cond, st, mt)
                x = draw((1 - rho) * p + rho * ambient[sid], lib)
                truth[cid] = t
                if t == OOV_TYPE and kind == "clean":
                    oov.append(cid)
            cols.append(x)
            cell_rows.append((cid, sid, cond, f"SUBJ-{2100 + int(sid[2:]):04d}"))
    mat = np.stack(cols, axis=1).astype(np.int64)
    excluded = set(low_quality) | set(doublets)
    cond_of = {c: cond for c, _, cond, _ in cell_rows}
    sample_of = {c: s for c, s, _, _ in cell_rows}
    post_qc = [c for c, *_ in cell_rows if c not in excluded]
    comp, per_sample = {}, {}
    for cond in ("control", "treated"):
        cc = [c for c in post_qc if cond_of[c] == cond]
        comp[cond] = {t: round(sum(truth[c] == t for c in cc) / len(cc), 4) for t in CELL_TYPES}
        comp[cond]["unassigned"] = round(sum(truth[c] == OOV_TYPE for c in cc) / len(cc), 4)
    for sid, _, _ in SAMPLES:
        cc = [c for c in post_qc if sample_of[c] == sid]
        per_sample[sid] = {t: sum(truth[c] == t for c in cc) for t in (*CELL_TYPES, OOV_TYPE)}
    return {"genes": genes, "counts": mat, "cells": cell_rows, "truth": truth,
            "low_quality": sorted(low_quality), "doublets": sorted(doublets), "oov": sorted(oov),
            "composition": comp, "per_sample": per_sample,
            "isgs": list(ISGS), "isgs_secondary": list(ISGS_SECONDARY),
            "isg_core_log2fc": core_lfc, "isg_secondary_log2fc": sec_lfc,
            "examples": _examples(rs["examples"], cell_rows, truth, excluded)}


def _examples(rng, cell_rows, truth, excluded):
    """Public acceptance examples: 2 eligible cells per (condition, type) from distinct donors."""
    out = []
    for cond in ("control", "treated"):
        for t in CELL_TYPES:
            by_donor = {}
            for c, s, cd, _ in cell_rows:
                if cd == cond and truth[c] == t and c not in excluded:
                    by_donor.setdefault(s, []).append(c)
            ds = sorted(by_donor)
            pick = rng.choice(len(ds), 2, replace=False)
            for i in sorted(pick):
                cells = by_donor[ds[i]]
                out.append((cells[int(rng.integers(len(cells)))], t))
    assert len(out) == 20 and not set(c for c, _ in out) & excluded
    return sorted(out)


def counts_tsv(genes, cells, mat) -> str:
    lines = ["gene\t" + "\t".join(c for c, *_ in cells)]
    for g, row in zip(genes, mat):
        lines.append(g + "\t" + "\t".join(str(int(v)) for v in row))
    return "\n".join(lines) + "\n"


def cells_tsv(cells) -> str:
    return "cell_id\tsample_id\tcondition\tsubject_ref\n" + "".join("\t".join(r) + "\n" for r in cells)


def golden_celltypes(sc: dict) -> list[tuple[str, str]]:
    return list(sc["examples"])
