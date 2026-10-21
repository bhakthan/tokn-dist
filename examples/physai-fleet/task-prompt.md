# Task: warehouse AMR fleet

Build a multi-agent software system for a warehouse fleet of autonomous mobile
robots (AMRs). Organise it as 14 cooperating agents across five layers.

- **Reactive:** low-latency loops for emergency stop and collision avoidance.
- **Perception:** object detection and pose estimation from onboard sensors. Use a
  detector and a pose estimator as named model components, not hard-coded values.
- **Tactical:** local path planning for each robot, using the perception output.
- **Strategic:** fleet coordination, including task assignment by auction and
  deadlock detection and resolution.
- **Hardware:** the interface to motor controllers and sensors, behind a
  replaceable adapter.

Requirements:

1. Safety first. Any agent may request an emergency stop, and the stop must reach
   every robot within one control cycle.
2. Each layer has its own module directory with a short README.
3. Include a simulation test that runs a fleet of at least six robots through a
   small warehouse map and reports deliveries, throughput, and E-stop latency.
4. Keep dependencies to the Python standard library unless a component truly
   needs more, and say which ones and why.
5. Put a short STATUS.md at the top level listing what was built, what was
   simulated rather than run on hardware, and what is still open.

Do not write anything outside the output folder.
