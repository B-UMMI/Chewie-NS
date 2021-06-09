const text = `
# About Chewie-NS

## Welcome

Chewie-NS is a web-based Nomenclature Server, based on the 
[TypOn ontology](https://jbiomedsem.biomedcentral.com/articles/10.1186/2041-1480-5-43),
that integrates with the [chewBBACA suite](https://github.com/B-UMMI/chewBBACA) to provide a centralized service to download or update schemas, allowing the easy sharing of results, while ensuring the reproducibility and consistency of these steps.

Chewie-NS is developed by the [Molecular Microbiology and Infection Unit (UMMI)](http://im.fm.ul.pt) at the [Instituto de Medicina Molecular João Lobo Antunes](https://imm.medicina.ulisboa.pt/) and [Faculdade de Medicina of Universidade de Lisboa](https://www.medicina.ulisboa.pt/).

## Goals

With this service we have following main goals:

1. Providing a public and centralised web service to manage typing schemas.
2. Establish a common nomenclature for allele calling.
3. Ensure the reproducibility and consistency of wg/cgMLST analysis.

## Citation

If you use **Chewie-NS**, please cite: 

[Mamede, R., Vila-Cerqueira, P., Silva, M., Carriço, J. A., & Ramirez, M. (2020). Chewie Nomenclature Server (chewie-NS): 
    a deployable nomenclature server for easy sharing of core and whole genome MLST schemas. Nucleic Acids Research.](https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkaa889/5929238)    

## Licensing

This project is licensed under the [GPLv3 license](https://github.com/B-UMMI/Chewie-NS/blob/master/LICENSE).
The source code of Chewie-NS is available at https://github.com/B-UMMI/Chewie-NS and the webservice is available at https://chewbbaca.online/.

## Contacts

For any issues contact the development team at [imm-bioinfo@medicina.ulisboa.pt](mailto:imm-bioinfo@medicina.ulisboa.pt) or open an issue at the Chewie-NS Github [repository](https://github.com/B-UMMI/Chewie-NS).`;

const chewbbacaIntegration = `
## Integration with chewBBACA

The chewBBACA suite has integration with Chewie-NS that enables users to directly upload new schemas to Chewie-NS, 
download existing schemas and synchronize local and remote schemas from chewBBACA command line version,
allowing an easier integration into high-throughput analysis pipelines.

If you use **chewBBACA**, please cite:

[Silva M, Machado M, Silva D, Rossi M, Moran-Gilad J, Santos S, Ramirez M, Carriço J. 15/03/2018. M Gen 4(3): doi:10.1099/mgen.0.000166
](https://www.microbiologyresearch.org/content/journal/mgen/10.1099/mgen.0.000166)`;

export { text, chewbbacaIntegration };
