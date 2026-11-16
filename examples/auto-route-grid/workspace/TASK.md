Transmission planning check for the 6-bus study network in this folder (buses.csv, lines.csv; 100 MVA base).

Sub-tasks, in order (keep a short plan and update it):
1. Inspect both files and validate the data: connectivity, a single slack bus, positive reactances, and the generation/load balance (the slack covers the residual). Report anything odd.
2. Write dcflow.py (Python standard library only) that solves a DC power flow and prints each line's MW flow and loading as a % of rating.
3. Extend it to an N-1 contingency study: drop each line in turn, re-solve, and flag post-contingency overloads (>100%) and any outage that islands the network.
4. Run it and sanity-check the base case: the flows into each bus must balance its injection within 0.1 MW.
5. Write GRID_REPORT.md: method and assumptions, base-case table, N-1 results table, the worst contingency, the mitigation options you would study next, and the limitations of a DC approximation.
