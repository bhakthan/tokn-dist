#!/usr/bin/env python3
"""Generate the bulk RNA-seq case study (deterministic; numpy + stdlib only).

Writes, relative to this file's directory:
    case/counts.tsv          genes x samples raw integer counts
    case/samples.tsv         sample_id, condition, batch
    answer_key/truth.tsv     gene_id, is_de, true_log2fc   (NOT for the solver)

Generative model (all synthetic; no real subjects or data)
    count_gj ~ NegBin(mean = mu_gj, dispersion = phi_g)   [Var = mu + phi*mu^2]
    mu_gj    = base_g * depth_j * 2^( lfc_g * [treated_j] + bfx_g * [batch B_j] )
  * base_g  : two populations - "expressed" (log-normal, median ~90) and
              "low" (log-normal, median ~0.4) that should be filtered out.
  * phi_g   : mean-dispersion trend (higher for low counts) x log-normal scatter.
  * depth_j : log-normal library-size factor (several-fold range of totals).
  * bfx_g   : batch B vs A log2 shift; 60% of genes have a sizeable effect (sd 1.0 log2).
  * lfc_g   : non-zero only for the truly DE genes (drawn among expressed genes).
  Design is balanced: 3 control + 3 treated in each of 2 batches (12 samples),
  so batch is orthogonal to condition but still inflates variance if ignored.
  true_log2fc is the log2 fold change treated/control on the scale of this
  model (no composition effect: depth_j is independent of gene content).

Re-running reproduces byte-identical files for the same numpy major version
(PCG64 Generator streams); a SHA-256 of each output is printed.
"""
import hashlib
import os

import numpy as np

SEED = 20240607
N_GENES = 4000
N_PER_CELL = 3                 # samples per condition x batch cell
N_DE = 280                     # truly DE genes
FRAC_LOW = 0.25                # fraction of genes that are lowly expressed
DE_MIN_BASE = 10.0             # DE genes are drawn among genes with base >= this

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    rng = np.random.default_rng(SEED)
    G = N_GENES

    # ---- samples: balanced 2 conditions x 2 batches, shuffled IDs ----------
    cells = [(c, b) for c in ("control", "treated") for b in ("A", "B")
             for _ in range(N_PER_CELL)]
    order = rng.permutation(len(cells))
    cells = [cells[i] for i in order]
    J = len(cells)
    sample_ids = [f"S{j + 1:02d}" for j in range(J)]
    cond = np.array([1 if c == "treated" else 0 for c, _ in cells])
    batch = np.array([1 if b == "B" else 0 for _, b in cells])

    # ---- gene-level parameters ---------------------------------------------
    low = rng.random(G) < FRAC_LOW
    base = np.where(low,
                    rng.lognormal(np.log(0.4), 0.9, G),
                    np.clip(rng.lognormal(np.log(90.0), 1.4, G), 2.0, 8000.0))
    trend = 0.03 + 1.0 / base
    phi = np.clip(trend * rng.lognormal(0.0, 0.4, G), 0.01, 2.0)

    big_batch = rng.random(G) < 0.60
    bfx = np.where(big_batch, rng.normal(0, 1.0, G), rng.normal(0, 0.1, G))

    eligible = np.flatnonzero((~low) & (base >= DE_MIN_BASE))
    de_idx = rng.choice(eligible, size=N_DE, replace=False)
    lfc = np.zeros(G)
    mag = np.clip(0.75 + rng.exponential(0.6, N_DE), 0.75, 3.5)
    sign = np.where(rng.random(N_DE) < 0.55, 1.0, -1.0)
    lfc[de_idx] = sign * mag
    is_de = np.zeros(G, dtype=int)
    is_de[de_idx] = 1

    # ---- library depth and counts ------------------------------------------
    depth = np.clip(np.exp(rng.normal(0.0, 0.35, J)), 0.5, 2.0)
    log2mu = (np.log2(base)[:, None] + np.log2(depth)[None, :]
              + lfc[:, None] * cond[None, :] + bfx[:, None] * batch[None, :])
    mu = 2.0 ** log2mu
    shape = 1.0 / phi[:, None]
    lam = rng.gamma(shape, mu / shape)          # gamma mean = mu, var = phi*mu^2
    counts = rng.poisson(lam).astype(np.int64)

    # ---- write ---------------------------------------------------------------
    os.makedirs(os.path.join(HERE, "case"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "answer_key"), exist_ok=True)
    gene_ids = [f"GENE{i + 1:05d}" for i in range(G)]

    cpath = os.path.join(HERE, "case", "counts.tsv")
    with open(cpath, "w", newline="\n") as fh:
        fh.write("gene_id\t" + "\t".join(sample_ids) + "\n")
        for g in range(G):
            fh.write(gene_ids[g] + "\t" + "\t".join(str(v) for v in counts[g]) + "\n")

    spath = os.path.join(HERE, "case", "samples.tsv")
    with open(spath, "w", newline="\n") as fh:
        fh.write("sample_id\tcondition\tbatch\n")
        for j in range(J):
            fh.write(f"{sample_ids[j]}\t{cells[j][0]}\t{cells[j][1]}\n")

    tpath = os.path.join(HERE, "answer_key", "truth.tsv")
    with open(tpath, "w", newline="\n") as fh:
        fh.write("gene_id\tis_de\ttrue_log2fc\n")
        for g in range(G):
            fh.write(f"{gene_ids[g]}\t{is_de[g]}\t{lfc[g]:.6f}\n")

    # ---- summary -------------------------------------------------------------
    lib = counts.sum(axis=0)
    print(f"genes={G} samples={J} DE={int(is_de.sum())} low-expressed={int(low.sum())}")
    print("library sizes:", lib.tolist(), f"(max/min = {lib.max() / lib.min():.2f})")
    print(f"genes with mean count < 1: {int((counts.mean(axis=1) < 1).sum())}")
    print(f"zero-total genes: {int((counts.sum(axis=1) == 0).sum())}")
    for p in (cpath, spath, tpath):
        print(f"sha256 {os.path.relpath(p, HERE)}: {sha256(p)}")


if __name__ == "__main__":
    main()
