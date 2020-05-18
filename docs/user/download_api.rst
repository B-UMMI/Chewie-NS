Download a schema from Chewie-NS
================================

The API contains a ``download`` namespace, as mentioned in :doc:`api_docs`, however, these endpoints are to be used exclusively by the user-interface.

Instead, we take advantage of the integration with the chewBBACA suite and use the 
`download_schema.py <https://github.com/B-UMMI/chewBBACA/blob/dev2_chewie_NS/CHEWBBACA/CHEWBBACA_NS/down_schema.py>`_ script.

Example
:::::::

For example, if we want to download a schema of *Yersinia pestis* we need to go provide 
the internal ID of the species (in this case it's 1), and the schema ID that we want to download. ::

    python chewBBACA.py DownloadSchema -sc 1 -sp 1 -o path/to/download/folder

Usage
:::::

This script downloads a schema from Chewie-NS and its usage is as follows::

    python chewBBACA.py DownloadSchema -h

    chewBBACA version: 2.1.0
    Authors: Mickael Silva, Pedro Cerqueira, Rafael Mamede
    Github: https://github.com/B-UMMI/chewBBACA
    Wiki: https://github.com/B-UMMI/chewBBACA/wiki
    Tutorial: https://github.com/B-UMMI/chewBBACA_tutorial
    Contacts: imm-bioinfo@medicina.ulisboa.pt, rmamede@medicina.ulisboa.pt, pedro.cerqueira@medicina.ulisboa.pt

    usage: 
    Download schema:
    chewBBACA.py DownloadSchema -sc <schema_id> -sp <species_id> -o <download_folder> 

    Download schema with non-default parameters:
    chewBBACA.py DownloadSchema -sc <schema_id> -sp <species_id> -o <download_folder>
                                --cpu <cpu_cores> --ns_url <nomenclature_server_url> 

    This program downloads a schema from Chewie-NS.

    positional arguments:
    DownloadSchema                    This program downloads a schema from the
                                        NS.
                                        

    optional arguments:
    -h, --help                        show this help message and exit
                                        
    -sc SCHEMA_ID                     The URI, integer identifier or description
                                        of the schema to download from the NS.
                                        (default: None)
                                        
    -sp SPECIES_ID                    The integer identifier or name of the
                                        species that the schema is associated to
                                        in the NS. (default: None)
                                        
    -o DOWNLOAD_FOLDER                Output folder to which the schema will be
                                        saved. (default: None)
                                        
    --cpu CPU_CORES                   Number of CPU cores that will be passed to
                                        the PrepExternalSchema process to
                                        determine representatives and create the
                                        final schema. (default: 1)
                                        
    --ns_url NOMENCLATURE_SERVER_URL  The base URL for the Nomenclature Server.
                                        (default: http://127.0.0.1:5000/NS/api/)
                                        
    --d DATE                          Download schema with state from specified
                                        date. Must be in the format "Y-m-dTH:M:S".
                                        (default: None)
                                        
    --latest                          If the compressed version that is
                                        available is not the latest, downloads all
                                        loci and constructs schema locally.
                                        (default: False)




