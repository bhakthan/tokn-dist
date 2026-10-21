---
name: harvest-metrics
description: Collect build metrics into a CSV dataset that later steps can chart.
category: product-verification
triggers: build metrics, collect metrics, metrics csv
produces: data/dataset
---

# harvest-metrics

Create `metrics.csv` in the working directory with one row per build and the
columns `build_id,duration_s,status`. Use five made-up builds if no input is
given. Keep the file small and plain.
