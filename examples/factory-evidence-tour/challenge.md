# Challenge

1. Locate the final verification receipt in `demo/repo`.
2. Compare the receipt with the `factory verify --json` result.
3. Explain why a deployment intent alone is weaker evidence than a reconciled
   delivery receipt.
4. Try the migration template only in a separate scratch directory. Record
   which files the dry run prints, and confirm the demo repository is unchanged.

This exercise has no hidden key or model answer. The receipt checker validates
the evidence-chain fields; it does not certify the underlying software.
