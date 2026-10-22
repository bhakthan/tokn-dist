You are helping a small product team turn meeting minutes into a plan and a proof of concept.

Read `minutes.md` in the repository root. It holds the minutes of a planning meeting.

Do two things.

1. Write `design-plan.md` in the repository root. Use these exact level-2 headings, in this order:
   - `## Scope`
   - `## Approach`
   - `## Risks`
   - `## Open Questions`
   Keep the plan between 200 and 400 words. Base it only on what the minutes say.
   Where the minutes are silent, write the gap under Open Questions instead of guessing.

2. Create a proof-of-concept scaffold in the `poc/` folder:
   - `poc/go.mod`: a valid module file. The module name is `feedbackhub`.
   - `poc/main.go`: a single Go program that uses only the standard library. Keep it under 200 lines.
     It should read a CSV file path from the command line, count rows per keyword tag from a small
     built-in taxonomy, and print the top five tags with their counts.
   - `poc/README.md`: how to run the program, the expected input columns, and the known limits.

Do not add any third-party dependencies. Do not write any file outside the repository root.
When you finish, list the files you created.
