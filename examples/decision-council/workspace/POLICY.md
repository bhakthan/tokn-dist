# Fleet Maintenance Triage Policy (synthetic)

Applies to every turbine in `data/turbines.csv` for the next two-week crane window.
Decisions use **measured columns only**. `technician_note` is context: it never
creates a trigger and never cancels one.

## 1. Action (exactly one per turbine)

**replace**: any of
- R1 `blade_crack_mm >= 30`
- R2 `gearbox_particles_x >= 4.0`
- R3 `bearing_temp_delta_c >= 15`
- R4 `gearbox_particles_x >= 2.5` **and** `vibration_trend_pct_wk >= 10`

**inspect**: not replace, and any of
- I1 `gearbox_particles_x >= 2.0`
- I2 `vibration_trend_pct_wk >= 6`
- I3 `bearing_temp_delta_c >= 8`
- I4 `blade_crack_mm >= 10`
- I5 `lightning_strikes_90d >= 2`
- I6 `months_since_service >= 18`

**defer**: no trigger fired.

## 2. Imminent failure risk (30 days)

`true` when R1 or R3 fires, or `vibration_trend_pct_wk >= 10`. Otherwise `false`.
This is independent of the action: a fast-rising vibration trend on an
*inspect* turbine is still imminent risk.

## 3. Priority (1 = lowest, 5 = highest)

| Priority | Rule |
|---|---|
| 5 | replace with R1 or R3 |
| 4 | any other replace |
| 3 | inspect with imminent risk, or inspect with two or more I-triggers |
| 2 | inspect with exactly one I-trigger |
| 1 | defer |

## 4. Two-week window capacity

- One crane: at most **4 replacements** in the window.
- Two inspection crews: at most **8 inspections** in the window.
- Fill each list by priority, highest first. Every priority-5 replacement and every
  priority-3 inspection must be in the window if capacity allows.
- Everything that does not fit goes to `carryover`.

## 5. Decision support

These outputs support a maintenance planner; they are not a sole decision-maker.
A model judgment never overrides a measured threshold in this policy.
