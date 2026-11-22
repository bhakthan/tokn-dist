# Task: assess one additional synthetic projection claim

Assess the single claim in `demo-input/ensemble_claims.json`. The synthetic
inputs are authoritative. Call `query_cmip6_catalog` and
`compute_ensemble_stats` using `demo-input/catalog_requests.json`; if a call
returns a dependency or network error, quote it and continue from the supplied
data. An error is not evidence that a gate passed.

For `tas`, the plausible range is 180–340 K and the 10% tolerance band is
164–356 K. Count each mapped model family once, then calculate the agreement
probability from independent families—not raw model count. Use the likelihood
bands in the main prompt: `virtually certain` 0.99–1.00, `very likely`
0.90–0.99, `likely` 0.66–0.90, `about as likely as not` 0.33–0.66, and
`unlikely` 0.10–0.33. Scan from the top and use the first matching band.
Statuses are `supported`, `miscalibrated`, `insufficient_ensemble`, and
`implausible`; precedence is implausible, insufficient ensemble, miscalibrated,
then supported.

Write `RESULT.md` with the item ID, exactly one status from the main prompt's
vocabulary, and separate evidence for the independent-family count,
agreement/likelihood, and physical-range check. Distinguish tool output from
the synthetic input values and from your own interpretation.
