I'm the physical-design signoff lead on a mixed-signal SoC (open 130 nm PDK).
Six hard macros just came back from place-and-route, and the programme manager
needs a signoff status for each one before the integration freeze tomorrow.

The working directory contains:

- `demo-input/floorplans.json`: utilization and aspect ratio per block
- `demo-input/sta_runs.json`: the post-route static-timing run record per block
- `demo-input/physical_verification.json`: DRC and LVS records per block

Blocks: `BLK-CPU`, `BLK-DSP`, `BLK-USB`, `BLK-SRAMCTL`, `BLK-DMA`, `BLK-PCIE`.

Give each block exactly one status:

- `tapeout_ready`: timing closed, DRC clean, LVS clean, utilization at or below
  our 80% target.
- `ready_with_caveats`: otherwise ready, but utilization is above the 80%
  target while still inside the 5% margin. Name the risk.
- `fail_signoff`: any signoff check fails.
- `blocked`: the block can't be judged yet. Say what must be fixed first.

Check each block with the semicon tools (`floorplan`, `static_timing`,
`drc_check`, `lvs_check`). Pass each record to the tools exactly as given. Don't
fill in missing files yourself.

Write `RESULT.md` with a table of block, status and the evidence for it, plus a
short note for the programme manager. Every number must come from a tool result
or the input files.
