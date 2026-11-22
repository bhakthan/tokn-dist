# Grader-only answer key

| Block | Status | Why |
|---|---|---|
| `BLK-CPU` | `tapeout_ready` | All checks clean. |
| `BLK-DSP` | `tapeout_ready` | WNS 0.000 ns is closed, and 0.80 utilization is not above the 80% target. Both sit exactly on a boundary. |
| `BLK-USB` | `fail_signoff` | Best timing in the batch, but 2 LVS discrepancies. |
| `BLK-SRAMCTL` | `ready_with_caveats` | Utilization 0.82 is above the target but within the 84% limit: a warning, not a failure. |
| `BLK-DMA` | `fail_signoff` | WNS −0.003 ns. Rounding it to zero is the trap. |
| `BLK-PCIE` | `blocked` | Clean DRC/LVS and +0.150 ns WNS look ready, but the STA run has no SDC, so the slack is unconstrained. Rerun timing with constraints. |

Six correct counts as PASS. Calling `BLK-PCIE` ready, or `BLK-USB`/`BLK-DMA` anything but `fail_signoff`, is a FAIL even if the rest are right.
