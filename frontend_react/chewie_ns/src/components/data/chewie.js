const chewie_front = `
# Chewie-NS: Enabling the use of gene-by-gene typing methods through a public and centralized service

# IMPORTANT
## A reset was performed on our databases. We kindly ask users that had an account to register once more.
## We apologize for the incovenience.

## Overview

**Chewie-NS** is a Nomenclature Server that is based on the TypOn ontology and aims to provide a centralized 
service to download or update cg/wgMLST schemas, allowing the easy sharing of results, while ensuring the reproducibility 
and consistency of these steps. It has an integration with the previously proposed [chewBBACA](https://github.com/B-UMMI/chewBBACA), a suite that allows the creation 
of gene-by-gene schemas and determination of allelic profiles from assembled draft genomes.

**Chewie-NS** is an easy way for users worldwide to download the necessary data defining the cg/wgMLST schemas, 
perform analyses locally with chewBBACA, and, if they so wish, to submit their novel results to the web service 
through a REST API to ensure that a common nomenclature is maintained.

|[Click here to see the Available Schemas](https://chewbbaca.online/stats)|
|---|

## Tutorial

Please visit the Tutorial site at https://tutorial.chewbbaca.online/ or by clicking on the test tube icon on the sidebar! 
The Tutorial instructions will be available soon at [Chewie-NS' Read The Docs](https://chewie-ns.readthedocs.io/en/latest/index.html).


## Schema submission

If you wish to submit schemas to Chewie-NS you need to register first at the [Register](https://chewbbaca.online/register) page.

## Citation

If you use **Chewie-NS**, please cite: 

[Mamede, R., Vila-Cerqueira, P., Silva, M., Carriço, J. A., & Ramirez, M. (2020). Chewie Nomenclature Server (chewie-NS): 
    a deployable nomenclature server for easy sharing of core and whole genome MLST schemas. Nucleic Acids Research.](https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkaa889/5929238)    

## Contacts

Chewie-NS is developed by the [Molecular Microbiology and Infection Unit (UMMI)](http://im.fm.ul.pt/) at the 
[Instituto de Medicina Molecular João Lobo Antunes](https://imm.medicina.ulisboa.pt/) and [Faculdade de Medicina of Universidade de Lisboa](https://www.medicina.ulisboa.pt/).

For any issues contact the development team at [imm-bioinfo@medicina.ulisboa.pt](mailto:imm-bioinfo@medicina.ulisboa.pt) or open an issue at the Chewie-NS Github [repository](https://github.com/B-UMMI/Chewie-NS).`;

export default chewie_front;
