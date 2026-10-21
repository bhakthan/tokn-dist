---
name: chart-metrics
description: Summarise a metrics dataset into an analysis report with simple statistics.
category: data-fetching
triggers: chart metrics, summarise metrics, metrics report
consumes: data/dataset
produces: analysis/report
---

# chart-metrics

Read `metrics.csv`, compute the number of builds, the pass rate, and the mean
and maximum duration. Write `report.md` with those numbers and one sentence
about the slowest build.
