# Brief — checking CMIP6 projection claims before an adaptation brief goes out

You are a climate scientist reviewing five regional projection claims that a colleague drafted for a planning audience. Each claim states an IPCC likelihood term. Before anything is published, you must confirm that each term follows from the ensemble once dependent models are removed, and that the underlying field passes a physical plausibility check. A wrong likelihood word in a planning document is costly: it gets quoted for years.

The data is synthetic. Everything you need is in `inputs/`:

| File | Contents |
|---|---|
| `inputs/catalog_requests.json` | Per item, the arguments for `query_cmip6_catalog` and `compute_ensemble_stats` (`variable_id`, `experiment_id`, `table_id`, `deduplicate`, ...) |
| `inputs/ensemble_claims.json` | Per item: the claim, `stated_likelihood`, and each model's `agrees_with_claimed_sign`. Also includes TOKN's `model_families` map |
| `inputs/field_ranges.json` | Per item: min and max of the regridded ensemble-mean field, in the units the file declares |

## Items to assess

`CL-01`, `CL-02`, `CL-03`, `CL-04`, `CL-05`

## Status vocabulary (use exactly one per item)

- `supported`: the field is plausible, the ensemble has enough independent families, and `stated_likelihood` equals the term derived in rule 4.
- `miscalibrated`: the field is plausible and the ensemble is large enough, but `stated_likelihood` differs from the derived term.
- `insufficient_ensemble`: fewer than 5 independent model families remain after deduplication.
- `implausible`: the field's min or max lies outside the physical tolerance band in rule 2.

If more than one applies, precedence is `implausible` > `insufficient_ensemble` > `miscalibrated` > `supported`.

## Rules

1. Call `query_cmip6_catalog` and `compute_ensemble_stats` for every item, passing the arguments from `catalog_requests.json`. Both tools read the live Pangeo catalog through Python (`intake` and `xarray`). If a call returns a Python, dependency or network error, quote the error in that item's evidence and carry on. The input files are authoritative, and no status depends on the live catalog.
2. **Physical range** (TOKN `PhysicalRanges` with 10 % tolerance: band = [min − 0.1·span, max + 0.1·span]):

   | Variable | Plausible range | Tolerance band |
   |---|---|---|
   | `tas` | 180–340 K | 164–356 K |
   | `pr` | −1e-6–0.02 kg m-2 s-1 | −0.0020011–0.0220001 |
   | `tos` | 270–315 K | 265.5–319.5 K |

   Compare each field against the **tolerance band**, not the plausible range. Do not convert units. Use the values exactly as declared.
3. **Independence.** Map every `source_id` to its family using `model_families`. A model missing from the map is its own family. Count each family once, as TOKN's `GetIndependentModels` does. Fewer than 5 families means `insufficient_ensemble`.
4. **Likelihood term.** p = families that agree with the claimed sign ÷ independent families. Members of one family always agree with each other here. Scan this table from the top and take the **first** row where low ≤ p ≤ high (TOKN `IPCCLikelihoodScale`):

   | Term | low | high |
   |---|---|---|
   | virtually certain | 0.99 | 1.00 |
   | very likely | 0.90 | 0.99 |
   | likely | 0.66 | 0.90 |
   | about as likely as not | 0.33 | 0.66 |
   | unlikely | 0.10 | 0.33 |

   Never compute p from the raw model count.
5. Use only calibrated AR6 language. Write a likelihood term together with its probability range (for example "likely (66–100 %)"). Avoid everyday certainty words.

## Deliverable

`result.json` and `RESULT.md`, as described in your stage instructions. In each item's evidence, give the family count, p, the derived term, and the band check.
