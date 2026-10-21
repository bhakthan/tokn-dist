Use the geospatial domain to prepare a short change-detection summary for the
synthetic Maple Hollow Reserve study area.

Inputs are in the inputs/ folder:
- inputs/aoi.geojson: study-area boundary, stated CRS EPSG:4326
- inputs/roads_3857.geojson: access road, stated CRS EPSG:3857
- inputs/scenes.csv: scene metadata (sensor, date, CRS, resolution, cloud cover, mask flags)

Do the following, in order:
1. Load the study-area boundary and the access road, and check their CRS.
2. Compute the area of the study area and the length of the access road.
   Report each figure with its units and its CRS.
3. Pick the current scene for change detection. Use only scenes whose cloud
   mask is applied. Apply the cloud mask before computing any index.
4. Compare the current scene (10 m) against the coarse context layer (250 m)
   for the same date window, and say whether the two are compatible.
5. Compare the current scene against the baseline scene from 2014. State the
   time gap in years and whether it is within the study's temporal window.
6. Write a one-page summary with a "Findings" section. For each blocked or
   flagged step, quote the gate message and say what data you would need to
   fix it. Do not invent results for steps that were blocked.

This is a synthetic exercise. Do not treat any output as a real land-use or
regulatory finding.
