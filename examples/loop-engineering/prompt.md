Task: write a shortlist of five candidates.

Read properties.csv and scoring.json in this folder. Select exactly five candidates from properties.csv that meet every criterion in scoring.json: activity_index at or above activity_index_min, stability_index at or above stability_index_min, and liability_flag at or below liability_flag_max.

Rank the qualifying candidates by composite_score, where composite_score = sum over weights of (weight x property value), using the weights in scoring.json. Keep the top five.

Write shortlist.csv in this folder with the header:
candidate_id,composite_score

Then list the five rows, highest composite_score first, with each score rounded to two decimal places.

Rules:
- Do not edit properties.csv, scoring.json, or check_shortlist.py. They are the fixed inputs and the checker.
- Do not add candidates that are not in properties.csv.
- Run `python check_shortlist.py` (use `python3` on macOS or Linux) to confirm the result. Fix shortlist.csv until it prints PASS.
