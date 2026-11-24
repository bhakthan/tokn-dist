# Prompts for the live finrisk step (step 4)

Run these from a scratch folder that has a `.nospace/environment.json` copied
from either `team-ifrs/` or nothing at all. Use the finrisk mode with a model
that has a valid provider key. The finrisk tool needs a trial or paid licence.

## Prompt A: nothing named (team-unstated)

```text
Is a misstatement of 70000 material? Total assets are 1000000.
Call assess_materiality with amount 70000 and total_assets 1000000.
Do not assume a jurisdiction. Report the status, level, open reasons and whether a ratio was produced.
```

## Prompt B: regime named (team-ifrs)

```text
Is a misstatement of 70000 material? Total assets are 1000000.
The regime is IFRS, as stated in this folder's environment contract.
Call assess_materiality with amount 70000, total_assets 1000000 and jurisdiction IFRS.
Report the status, level, ratio and the basis you used.
```

## Which facts were open?

After both runs, answer in your own notes before reading the walkthrough
answer: which facts did the question need that nobody had stated?
