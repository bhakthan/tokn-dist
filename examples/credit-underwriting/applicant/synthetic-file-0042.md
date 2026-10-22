# Synthetic applicant file

Fictional borrower for a training walkthrough. Every name, identifier, and figure is invented.
Amounts are in thousands of US dollars unless a line says otherwise.

borrower_name: Tallow Creek Print Co. (fictional)
application_id: APP-SYN-0042
reference_date: 2025-12-31
loan_request_usd_k: 1800
loan_term_months: 60
industry: specialty printing (fictional sample)
jurisdiction_note: US-style covenant language, synthetic

## Financial statements (fiscal year ending 2025-12-31)

revenue_k: 6400
ebitda_k: 1020
interest_expense_k: 150
principal_due_k: 300
total_debt_k: 3100
current_assets_k: 1450
current_liabilities_k: 1120
inventory_k: 380

## Interim statement

interim_period_end: 2025-09-30
interim_revenue_k: 4650
interim_ebitda_k: 690
interim_total_debt_k: 3250

## Covenant terms (proposed, fictional)

min_dscr: 1.25
max_leverage_x: 3.5
min_current_ratio: 1.2

## Data-quality notes

- The interim statement period end is 2025-09-30, which is before the annual reference date. That is
  correct for an interim period, and the temporal check should confirm the ordering rather than flag it.
- Inventory is included in current assets. A quick-ratio check would exclude it.
