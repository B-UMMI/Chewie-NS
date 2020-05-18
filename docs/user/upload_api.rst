Upload a schema to Chewie-NS
============================

To upload schemas generated with the chewBBACA suite to Chewie-NS we make use of
chewBBACA's `load_schema.py <https://github.com/B-UMMI/chewBBACA/blob/dev2_chewie_NS/CHEWBBACA/CHEWBBACA_NS/load_schema.py>`_ script.

Example
:::::::

.. important:: **You need to be registered in Chewie-NS and have the correct credentials to be to upload a schema!**

To upload a schema generated with chewBBACA to Chewie-NS we need to provide some important information:

- the **ID** of the species that the schema will be associated to.
- a **description** of the schema to help understand its content.
- a **prefix** for the loci to facilitate the identification of the schema they belong to.

So if we want to add a schema for *Yersinia pestis*, we need to run the following command::

    python chewBBACA.py LoadSchema -i path/to/schema/to/be/sent -sp 1 -sd cgMLST_95 -lp cgMLST_95

Usage
:::::

The usage of this script is as follows::

    python chewBBACA.py LoadSchema -h

    chewBBACA version: 2.1.0
    Authors: Mickael Silva, Pedro Cerqueira, Rafael Mamede
    Github: https://github.com/B-UMMI/chewBBACA
    Wiki: https://github.com/B-UMMI/chewBBACA/wiki
    Tutorial: https://github.com/B-UMMI/chewBBACA_tutorial
    Contacts: imm-bioinfo@medicina.ulisboa.pt, rmamede@medicina.ulisboa.pt, pedro.cerqueira@medicina.ulisboa.pt

    usage: 
    Load schema:
    chewBBACA.py LoadSchema -i <schema_directory> -sp <species_id> -sd <schema_description>
                            -lp <loci_prefix> 

    Load schema with non-default parameters:
    chewBBACA.py LoadSchema -i <schema_directory> -sp <species_id> -sd <schema_description>
                            -lp <loci_prefix> --thr <threads> --ns_url <nomenclature_server_url>

    Continue schema upload that was interrupted or aborted:
    chewBBACA.py LoadSchema -i <schema_directory> -sp <species_id> -sd <schema_description>
                            --continue_up

    This program uploads a schema to the NS.

    positional arguments:
    LoadSchema                        This program loads a schema to the NS.
                                        

    optional arguments:
    -h, --help                        show this help message and exit
                                        
    -i SCHEMA_DIRECTORY               Path to the directory with the local
                                        schema files. (default: None)
                                        
    -sp SPECIES_ID                    The integer identifier or name of the
                                        species that the schema will be associated
                                        to in the NS. (default: None)
                                        
    -sd SCHEMA_DESCRIPTION            A brief and meaningful description that
                                        should help understand the type and
                                        content of the schema. (default: None)
                                        
    -lp LOCI_PREFIX                   Prefix included in the name of each locus
                                        of the schema. (default: None)
                                        
    --cpu CPU_CORES                   Number of CPU cores that will be used in
                                        multiprocessing steps. (default: 1)
                                        
    --thr THREADS                     Number of threads to use to upload the
                                        alleles of the schema. (default: 20)
                                        
    --ns_url NOMENCLATURE_SERVER_URL  The base URL for the Nomenclature Server.
                                        (default: http://127.0.0.1:5000/NS/api/)
                                        
    --continue_up                     If the process should check if the schema
                                        upload was interrupted and try to finish
                                        it. (default: False)

