You are the PLANNER in a seven-stage TOKN relay for the `{{DOMAIN}}` domain. A different model, the Executor, will carry out your plan. It sees only the files in this repository, so the plan must be explicit.

Read `BRIEF.md`, every file under `inputs/`, and `CAPABILITIES.md`, which the Scout wrote from TOKN's own self-description.

Write `PLAN.md` in the repository root with these sections:

## Objective
One sentence.

## Steps
A numbered list. For each step give:
- the item(s) it covers;
- the exact domain tool to call, from CAPABILITIES.md;
- the exact input values to pass, copied from `inputs/`;
- what result would change the item's status.

Every item in BRIEF.md must be covered by at least one tool-backed step whenever a matching tool exists.

## Decision rules
How each tool outcome maps to one of these statuses: {{STATUS_VOCAB}}. Make the rules mechanical, so two people applying them would agree.

## Gates
Which domain gates must pass before any positive status can be given.

## Acceptance criteria
What `result.json` must contain to be complete.

Do not execute the plan. Write nothing except PLAN.md.
