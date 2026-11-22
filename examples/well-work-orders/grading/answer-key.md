# Grader-only answer key

| Item | Status | Why |
|---|---|---|
| `OG-1` | `approve` | No trap; supplied tool results agree with the plan. |
| `OG-2` | `blocked` | `secondary_barrier_verified` is false, so the two-barrier gate refuses the perforation job. |
| `OG-3` | `approve` | Treating pressure is exactly 5000 psi, equal to MAASP; the gate blocks only a value strictly above it. |
| `OG-4` | `revise` | Compression ratio is 1700/400 = 4.25, so the calculated two stages disagree with the one planned stage. |
| `OG-5` | `blocked` | Emissions confidence 0.72 is above the 0.70 cap for engineering estimates. |
| `OG-6` | `revise` | The drilling tool returns `operating`, but 15.55 ppg exceeds the 15.5 ppg maximum from `og_mud_weight`. |

All six correct counts as PASS. This is a simulated review disposition, not a job release. A qualified human approver must review the real work package before mobilization.
