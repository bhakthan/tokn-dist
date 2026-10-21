# Processing summary (synthetic)

Project: demo-sample-01 (synthetic example, not a real dataset)

- Reported resolution: 2.9 Å
- Particles after 3D refinement: 180,000 (synthetic)
- Half-maps: half1.mrc and half2.mrc (gold-standard, unmasked FSC computed)
- FSC curve: data/fsc_curve.csv
- Phase randomization: applied to the masked FSC
- Model: 412 residues built into the map
- Model quality: clashscore 14.0, Ramachandran favored 96.1%, rotamer outliers 1.2%
- Water molecules modelled: 58 (at the reported resolution)
- Missing loop: residues 210–226, to be filled
- Raw data: raw/gain_ref.mrc (gain reference used for motion correction)
- Planned fix: overwrite raw/gain_ref.mrc with a corrected copy
- Planned loop fill: AlphaFold3 full-chain prediction, replacing the modelled chain
- AlphaFold3 mean pLDDT on the loop: 62
