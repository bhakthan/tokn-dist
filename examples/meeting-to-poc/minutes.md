# Team minutes: Feedback Hub planning (synthetic example)

> This file is fictional. Every person and product detail is made up for the walkthrough.

**Date:** 2031-03-04
**Attendees:** Ava (product), Ben (engineering lead), Chloe (design), Dana (support lead)

## Context

Customers send product feedback through three channels: a web form, a shared
support mailbox, and an in-app chat. Each channel has its own export and nobody
can see the whole picture. The team wants one place that collects feedback,
groups it into themes, and produces a weekly digest for the product group.

## Discussion

- Ava: the first version only needs to ingest a CSV export from each channel.
  Live connectors can wait.
- Ben: clustering should start with simple keyword tags and a fixed taxonomy.
  Machine clustering can come later once we have labelled examples.
- Chloe: the digest should show the top five themes, a count per theme, and two
  short quotes per theme. Quotes must be trimmed to remove names and order numbers.
- Dana: support wants each theme to link back to the original tickets so agents
  can follow up. Store ticket identifiers, not customer names.
- Ben: store a salted hash of the customer email for de-duplication. Do not keep
  the raw address after ingest.
- Ava: keep raw exports for 30 days, then delete them. Confirm the number with
  the privacy lead before release.

## Decisions

1. MVP ingests CSV exports from the three channels.
2. Themes come from a fixed keyword taxonomy with about ten entries.
3. The weekly digest lists the top five themes with counts and linked ticket IDs.
4. Raw customer email addresses are never stored after ingest.

## Action items

- Ava: draft the taxonomy with the product group by Friday.
- Ben: propose a project layout for the aggregator and a plan for the first milestone.
- Chloe: sketch the digest layout.
- Dana: list the export fields each channel provides.

## Open questions

- Which channel should be added first in version two?
- Who owns the taxonomy after launch?
- Do we need an audit log for digest views?
