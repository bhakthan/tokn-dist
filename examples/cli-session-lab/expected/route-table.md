# Route table

| Goal | Route | What it does not mean |
|---|---|---|
| Discover options offline | `tokn agent-run --help-all` / `tokn agent-repl --help-all` | Does not test credentials or connectivity |
| Ask once | `tokn agent-run -p ...` or `tokn -p ...` | Does not open a persistent REPL |
| Continue unfinished work | `tokn agent-run -c` | Does not reopen a completed transcript |
| Browse history | `tokn list-sessions`, then `tokn load-session SESSION_ID` | Does not restart the session |
| Stop or queue in a REPL | Ctrl+C stops the run; Ctrl+Q queues a follow-up; `/exit` exits | These controls are not demonstrated by the offline route |

Checkpoint availability depends on the local session state and compatibility
checks. Keep session IDs and transcripts private.
