# INNUENDO whole genome and core genome MLST schemas and datasets for Salmonella enterica

This schema was generated for the INNUENDO project and was adapted using [chewBBACA 2.5.0](https://github.com/B-UMMI/chewBBACA) (accessed and downloaded on 2020-06-12).

For more information please access the [schema page](https://zenodo.org/record/1323684).

## Dataset

As reference dataset, 4,307 public available draft or complete genome assemblies and available metadata of *Salmonella enterica* have been downloaded from public repositories (i.e. [EnteroBase](https://enterobase.warwick.ac.uk/), [National Center for Biotechnology Information NCBI](https://www.ncbi.nlm.nih.gov/) and [The European Bioinformatics Institute EMBL-EBI](https://www.ebi.ac.uk/); accessed April 2017). The collection includes 1,465 S. Enteritidis, 2,442 S.Typhimurium, and 400 of other frequently isolated serovars in Europe. The dataset includes also 153 S.Typhimurium variant 4,[5],12:i:- collected from different Italian regions between 2012 and 2014 during a surveillance study and 129 S. Enteritidis belonging to the INNUENDO sequence dataset [(PRJEB27020)](https://www.ebi.ac.uk/ena/data/view/PRJEB27020). The 282 additional genomes were assembled using [INNUca v3.1](https://github.com/B-UMMI/INNUca).

## Schema creation and validation

The wgMLST schema from [EnteroBase](https://enterobase.warwick.ac.uk/species/senterica/download_data) have been downloaded and curated using [*chewBBACA AutoAlleleCDSCuration*](https://github.com/B-UMMI/chewBBACA/wiki/1.-Schema-Creation) for removing all alleles that are not coding sequences (CDS). The quality of the remain loci have been assessed using [*chewBBACA Schema Evaluation*](https://github.com/B-UMMI/chewBBACA/wiki/1.-Schema-Creation) and loci with single alleles, those with high length variability (i.e. if more than 1 allele is outside the mode +/- 0.05 size) and those present in less than 0.5% of the *Salmonella* genomes in EnteroBase at the date of the analysis (April 2017) have been removed. The wgMLST schema have been further curated, excluding all those loci detected as “Repeated Loci” and loci annotated as “non-informative paralogous hit (NIPH/ NIPHEM)” or “Allele Larger/ Smaller than length mode (ALM/ ASM)” by the chewBBACA Allele Calling engine in more than 1% of a dataset composed by 4,589 *Salmonella* genomes.

## Aditional citations

The schema are prepared to be used with [chewBBACA](https://github.com/B-UMMI/chewBBACA/wiki). When using the schema in this repository please cite also:

- Silva M, Machado M, Silva D, Rossi M, Moran-Gilad J, Santos S, Ramirez M, Carriço J. chewBBACA: A complete suite for gene-by-gene schema creation and strain identification. 15/03/2018. M Gen 4(3): doi:10.1099/mgen.0.000166
[Publication](http://mgen.microbiologyresearch.org/content/journal/mgen/10.1099/mgen.0.000166)

*Salmonella enterica* schema is a derivation of EnteroBase *Salmonella* [EnteroBase](https://enterobase.warwick.ac.uk/) wgMLST schema. When using the schema in this repository please cite also:

- Alikhan N-F, Zhou Z, Sergeant MJ, Achtman M (2018) A genomic overview of the population structure of Salmonella. PLoS Genet 14 (4):e1007261.
[Publication](https://doi.org/10.1371/journal.pgen.1007261)
