# Task: one role first, the emergency-stop path

Build only the **reactive safety layer** of a warehouse fleet of autonomous
mobile robots (AMRs). This is software for a simulation. Do not write any code
that talks to real hardware, a network or a serial port.

1. Create `safety/estop.py` with a class `EStopBus` that any agent can call to
   request an emergency stop (`request_stop(reason)`), and that every
   registered robot handle receives within one control cycle
   (`tick()` delivers pending stops; `stopped(robot_id)` reports the state).
2. Create `safety/README.md` describing the contract above in a few lines.
3. Create `safety/test_estop.py`, using only `unittest` from the standard
   library, with a fleet of six simulated robot handles: one stop request must
   reach all six on the next `tick()`, and a stop must not be cleared by a later
   `tick()` without an explicit `reset()`.
4. Create a short `STATUS.md` saying what was built, that everything is
   simulated, and what is still open.

Use only the Python standard library. Do not write anything outside the output
folder.