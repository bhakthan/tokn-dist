# PROOF.md — proof-of-work ledger (hand-written sample)

## Change: shorten log retention from 30 to 7 days

- Edited `app.txt`: `retention_days = 30` -> `retention_days = 7`.
- Dry-run: replayed the cleanup job against a copy of the log volume; 0 errors.
- Rollback: set `retention_days = 30` and redeploy. Logs already deleted are not recoverable.
