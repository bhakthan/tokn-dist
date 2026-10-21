# Design proposal: HelpDesk Triage Bot (synthetic example)

All names, teams, and numbers here are invented for a TOKN example.

## Summary

A bot reads each new internal helpdesk ticket, classifies it into one of six
queues, and resolves simple requests (password resets, license requests)
automatically. Agents handle the rest.

## Design

1. Ticket text, including the requester's name, email, and device serial, is
   sent to one hosted language model for classification and reply drafting.
2. The classifier runs as a single service. If it is unavailable, new tickets
   wait in the queue until it recovers.
3. Automatic resolution runs for requests the model rates above 0.8 confidence.
4. Agents may escalate tricky tickets to a human when they want to.

## Success criteria

- We will auto-resolve 95% of tickets within one quarter.
- Customer satisfaction should improve.

## Rollout

Pilot with one office for four weeks, then expand to all offices. Two engineers
build it. No budget has been set for the model API.
