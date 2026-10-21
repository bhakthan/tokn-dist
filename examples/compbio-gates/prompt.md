The current working directory contains:

- `demo-input/cohort_chr1.vcf`: chromosome-1 variant calls from cohort A
- `demo-input/cohort_chr2.vcf`: chromosome-2 variant calls from cohort B
- `demo-input/counts.csv`: RNA-seq raw count matrix (24 samples)
- `demo-input/Snakefile.unpinned`: a draft Snakemake workflow stub

Start by listing the directory and inspecting each file. Then perform an
integrative eQTL analysis that ties variant genotypes from the merged VCF to
gene-expression changes from `counts.csv`.

Specifically:

1. **Inspect** both VCFs and the count matrix. Report what you see, especially
   any genome-build, normalization, or batch-effect signals.
2. **Merge** the two VCFs into a single cohort-wide VCF that I can feed into a
   downstream eQTL pipeline. Use the `merge_vcfs` tool.
3. **Run a differential-expression analysis** on `counts.csv` between the case
   group (samples `S1`-`S12`) and the control group (`S13`-`S24`). Use the
   `differential_expression` tool. Report which genes are significantly
   differentially expressed.
4. **Wrap the whole thing in a reproducible Snakemake workflow**. Start from
   `demo-input/Snakefile.unpinned` and harden it for publication. Use
   `pin_environment` and `validate_workflow`.
5. **Emit a final summary** that someone reviewing the work can use to
   reproduce the results.

The work needs to be **publication-ready**. The journal runs an automated
reproducibility check on whatever I send.
