---
name: publish-findings
description: Publish a findings report using a deployment manifest.
category: deployment
triggers: publish findings, publish report
consumes: deploy/manifest
---

# publish-findings

Read the deployment manifest and publish `report.md` to the destination it
names. This fixture has no step that produces a deployment manifest, so the
dataflow check should flag it.
