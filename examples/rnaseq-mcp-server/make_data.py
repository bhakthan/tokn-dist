"""Write the synthetic RNA-seq inputs for this example.

The data is synthetic and seeded, so every run produces the same files:

  data/counts.tsv   400 genes x 8 samples of integer read counts. 13 genes
                    carry the mitochondrial prefix "MT-".
  data/samples.tsv  sample sheet: sample_id, condition, batch.

Two samples carry a planted quality problem:

  S07  sequenced shallowly: about a fifth of the reads of the others.
  S08  high mitochondrial fraction: a sign of stressed or dying cells.

Standard library only. Run:  python make_data.py
"""

import math
import os
import random

SEED = 20260611
N_GENES = 400
SAMPLES = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"]
MITO = ["MT-ND1", "MT-ND2", "MT-CO1", "MT-CO2", "MT-ATP8", "MT-ATP6", "MT-CO3",
        "MT-ND3", "MT-ND4L", "MT-ND4", "MT-ND5", "MT-ND6", "MT-CYB"]


def poisson(rng, lam):
    # Normal approximation is fine for the large means used here.
    if lam > 50:
        return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))
    l, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= l:
            return k
        k += 1


def main():
    rng = random.Random(SEED)
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "data")
    os.makedirs(out, exist_ok=True)

    nuclear = [f"GENE{i:04d}" for i in range(1, N_GENES - len(MITO) + 1)]
    genes = nuclear + MITO
    # Log-normal gene means; about one gene in ten is effectively silent.
    base = {}
    for g in nuclear:
        base[g] = 0.0 if rng.random() < 0.10 else math.exp(rng.gauss(5.5, 1.3))
    for g in MITO:
        base[g] = math.exp(rng.gauss(6.2, 0.4))

    depth = {s: rng.uniform(0.9, 1.1) for s in SAMPLES}
    depth["S07"] = 0.2  # shallow library
    mito_boost = {s: 1.0 for s in SAMPLES}
    mito_boost["S08"] = 9.0  # stressed cells

    with open(os.path.join(out, "counts.tsv"), "w", newline="\n") as f:
        f.write("gene_id\t" + "\t".join(SAMPLES) + "\n")
        for g in genes:
            row = []
            for s in SAMPLES:
                lam = base[g] * depth[s] * (mito_boost[s] if g.startswith("MT-") else 1.0)
                row.append(str(poisson(rng, lam) if lam > 0 else 0))
            f.write(g + "\t" + "\t".join(row) + "\n")

    with open(os.path.join(out, "samples.tsv"), "w", newline="\n") as f:
        f.write("sample_id\tcondition\tbatch\n")
        for i, s in enumerate(SAMPLES):
            f.write(f"{s}\t{'treated' if i % 2 else 'control'}\tB{1 + i // 4}\n")

    print(f"wrote {len(genes)} genes x {len(SAMPLES)} samples to {out}")


if __name__ == "__main__":
    main()
