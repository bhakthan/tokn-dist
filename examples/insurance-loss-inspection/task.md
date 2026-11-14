# Task: prepare the adjuster worklist for claim CLM-DEMO-0001

Every path below is relative to the repository root (this example folder).

1. The Loss Inspection report is `out/report.json`, written by
   `tokn loss-inspect run`. Do not edit it, and you do not need to read it.
2. Call the `ins_loss_inspect` tool once with exactly one argument:
   `report_path` set to `out/report.json`. Do not copy the report's contents
   into the call, and do not pass a calibration or a guidelines argument.
3. From the tool result, take the open adjuster referrals in the order the tool
   returns them. Keep that order in the worklist.
4. Create `out/worklist.md`. It must contain:
   - a heading with the claim reference from the tool result's run provenance;
   - one markdown table with exactly these columns, in this order: `priority`,
     `point`, `check`, `label`, `probability`, `reasons`;
   - one row per open adjuster referral, copied from the tool result, with
     probabilities written to two decimal places;
   - one short paragraph of at most three sentences that says a licensed
     adjuster must review every referral before any decision.
5. Do not resolve, close or change any referral. Do not call
   `ins_inspection_referral` or `ins_workflow_advance`. Those actions belong to
   a human adjuster only.
6. Do not decide coverage, liability or payment, and do not write any amount.
7. Use the `ins_loss_inspect` tool and file writing only. Do not write or run
   scripts, and do not change any other file.

When the file is written, reply with one line: DONE.
