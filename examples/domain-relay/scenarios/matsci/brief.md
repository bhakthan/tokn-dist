# Brief — screening cathode-coating candidates from a DFT batch

You are a computational materials scientist. A colleague ran a VASP batch for five candidate **coating materials for a Li-ion cathode**. Before the lab commits to synthesizing any of them, they want a defensible screen of the batch.

The data is synthetic but realistic. Everything you need is in `inputs/`:

| File | Contents |
|---|---|
| `inputs/candidates.json` | The five candidates: formula, energy above the convex hull (`e_above_hull`, eV/atom), and structure source |
| `inputs/incar_snapshots.json` | The INCAR settings actually used, as a reference snapshot `REF` followed by one snapshot per candidate |
| `inputs/encut_convergence.json` | Per-candidate total energy (eV/atom) at increasing ENCUT |
| `inputs/pseudopotentials.json` | The POTCAR family used for each species |

## Items to assess

`CAND-A`, `CAND-B`, `CAND-C`, `CAND-D`, `CAND-E`

## Status vocabulary (use exactly one per item)

- `recommend`: comparable, converged, and thermodynamically stable.
- `recommend_with_caveats`: comparable and converged, but only metastable. Say so in calibrated language.
- `reject`: comparable and converged, but unstable.
- `blocked`: its energy cannot be trusted for comparison. The cause is INCAR drift from `REF`, a pseudopotential family mismatch, or an ENCUT series that has not converged. Fix the calculation before ranking it.

## Rules

1. **Comparability and convergence come first.** A `blocked` cause overrides any stability result, however good the `e_above_hull` looks.
2. Use the materials-science convention for stability: at most 0 is stable, at most 25 meV/atom is metastable, and anything above 25 meV/atom is unstable.
3. Convergence means the change between the last two ENCUT points is at most 1 meV/atom.
4. Report the structure provenance hierarchy and whether it forces a calibrated-language downgrade.
5. Every number you report must come from a tool call, not mental arithmetic.

## Deliverable

`result.json` and `RESULT.md`, as described in your stage instructions.
