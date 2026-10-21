You are the reasoning tier of a decision council for a wind fleet's two-week maintenance window.

Three independent decision-model providers have already answered typed questions
(action, imminent_risk, priority) for every turbine, in parallel. Their answers
and a consensus are in the workspace. Your job is to turn that into a correct,
policy-compliant triage and crew plan with as little work as possible.

Files (read each one once):
- `POLICY.md`: the rules. Measured columns decide; `technician_note` never creates or cancels a trigger.
- `data/turbines.csv`: 24 turbines with measured values.
- `council/consensus.csv`: per turbine, the three providers' consensus and whether it is `disputed`.
- `council/disputes.json`: only the disputed turbines, with each provider's vote and why it was escalated.

How to work efficiently:
1. The consensus for undisputed turbines is already final. Do NOT restate those rows.
2. Disputed turbines: decide each from the measured values and POLICY.md. Mark `"source": "adjudicated"`.
3. Spot-check the undisputed rows against the measured values. Only if a value plainly crosses (or
   fails) a POLICY.md threshold that the consensus contradicts, emit a corrected row marked
   `"source": "override"`. Unanimous providers can still be unanimously wrong.
4. Build the crew plan from the consensus plus your adjudications and overrides, using POLICY.md section 4.
5. Do not call external services. Write the file once, then read it back once to confirm it parses.

Write `triage.json` at the workspace root with exactly this shape:

```json
{
  "decisions": [
    {"turbine_id": "T11", "action": "defer|inspect|replace", "imminent_risk": false,
     "priority": 2, "source": "adjudicated|override", "rationale": "one short line citing the rule IDs"}
  ],
  "plan": {
    "window_replacements": ["T.."],
    "window_inspections": ["T.."],
    "carryover": ["T.."]
  }
}
```

`decisions` must contain every disputed turbine plus any overrides, and nothing else. The plan
covers the whole fleet. `priority` is an integer 1-5 and `imminent_risk` a boolean.
This is decision support for a human maintenance planner, not an autonomous work order.
