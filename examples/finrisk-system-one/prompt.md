Run a synthetic financial-risk briefing exercise. No real company, investor or
financial records are involved. Use only the supplied inputs in case/synthetic-case.json.
Do not fetch market data, browse, run commands, write files or delegate. You have
explicit permission to send this synthetic case and your draft to System One.

Objective: prepare a qualified materiality briefing for a fictional company's
internal reviewer, using deterministic domain computation followed by external
typed judgment and then a revised generative answer.

1. Call assess_materiality with amount 6000000, total_assets 100000000 and
   jurisdiction SEC. Use the real returned level and ratio, not mental arithmetic.
2. Compose a short draft grounded in that result. The draft must say this is a
   synthetic exercise, not investment advice, and that quantitative thresholds
   alone do not establish a regulatory conclusion.
3. Call system_one_evaluate ONCE with shared state containing case_id
   "synthetic-materiality-6pct", domain_result (the domain tool's result), and
   draft (your draft text). Put ALL THREE independent questions in that one
   request, with these exact IDs:
   - grounded: type noul. Does the draft faithfully represent the domain result?
   - qualified: type noul. Does the draft explicitly acknowledge that quantitative
     thresholds alone do not establish a regulatory conclusion?
   - disposition: type choice. Classify the draft as "ready" (a qualified internal
     draft grounded in the supplied result) or "revise" (missing qualification or
     inconsistent with the result). This is editorial judgment, not permission
     to execute or approve a financial decision.
   Do not ask a question that depends on another question's answer.
4. Read the ACTUAL returned answers, then produce the final briefing. Do not
   claim System One approved compliance. If the tool fails, report the failure
   instead of fabricating scores or silently replacing System One with yourself.

Your final answer must be a single fenced JSON object with:
case_id, materiality_level, ratio, jev_model,
jev_answers (the three actual answer objects, copied without renaming fields),
draft (the text you sent to System One), briefing (your final qualified prose), and
revision_reason (explain whether you retained or revised the draft based on
the returned signals).
Do not emit a final JSON before both tools return.
