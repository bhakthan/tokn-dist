---
name: deploy-alert
description: Package a flood alert and publish it through the release pipeline to the on-call channel.
triggers: deploy, release, pipeline, publish alert, rollout
category: ci-cd
---

# Deploy an alert

## When to use
A flood alert must be published to the on-call channel through the release pipeline.

## Steps
1. Build the alert message from the confirmed breaches.
2. Run the release pipeline with the alert as its payload.
3. Confirm the pipeline reports success.

## Gotchas
- Never publish an alert that has not passed verification.
