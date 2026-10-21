Review the synthetic experiment plans in experiments.json against the device specs in devices.json.

For each experiment:
1. Compute the circuit fidelity from the two-qubit error rate and gate count, and the accumulated error (1 minus fidelity).
2. Compute the execution time (depth times two-qubit gate time) as a fraction of T2, and flag it if the fraction is too high.
3. Check the shot count against the expectation-value and publication thresholds.
4. Check the tier label. Each result must be labelled [EXACT-SIM], [NOISY-SIM], [HARDWARE:{backend}:{date}] or [ANALOG-SIM].
5. For any ZNE mitigation, check the number of scale factors, the scale range, and whether the fit type is valid for the accumulated error.
6. For any fault-tolerant claim, check the two-qubit fidelity and the physical-qubits-per-logical-qubit count. If either fails, the claim is NISQ-era, not fault-tolerant.

Report each experiment as PASS or BLOCKED, with the numbers and the gate that fired. Do not call any quantum advantage over classical methods unless the plan gives a classical baseline. Label every number as computed from the files. Keep the answer short.
