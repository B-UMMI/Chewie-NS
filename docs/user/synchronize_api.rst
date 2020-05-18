Synchronize a local chewBBACA schema with data from Chewie-NS
=============================================================

The chewBBACA suite also allows users to synchronize their local schemas with Chewie-NS.

This means that any locally identified alleles, which have been identified also in the remote server will now be recognized
by their public identification.

We also provide the **option to submit novel alleles**, which are alleles identified locally and not present in Chewie-NS.

The `sync_schema.py <https://github.com/B-UMMI/chewBBACA/blob/dev2_chewie_NS/CHEWBBACA/CHEWBBACA_NS/sync_schema.py>`_ 
script handles the synchronization process.

Example
:::::::

If we want to synchronize a local schema we only need to provide the path to the directory that contains it::

    python chewBBACA.py SyncSchema -i path/to/schema

We also allow users to synchronize their schemas with their local instance of Chewie-NS.
For that we need to provide the local instance's URL::

    python chewBBACA.py SyncSchema -i path/to/schema -ns_url <local_chewie_ns_url>


Finally, if the user wishes to submit their novel alleles to Chewie-NS, the ``submit`` flag must be used. ::

    python chewBBACA.py SyncSchema -i path/to/schema --submit


Usage
:::::

::

    python chewBBACA.py SyncSchema -h

    chewBBACA version: 2.1.0
    Authors: Mickael Silva, Pedro Cerqueira, Rafael Mamede
    Github: https://github.com/B-UMMI/chewBBACA
    Wiki: https://github.com/B-UMMI/chewBBACA/wiki
    Tutorial: https://github.com/B-UMMI/chewBBACA_tutorial
    Contacts: imm-bioinfo@medicina.ulisboa.pt, rmamede@medicina.ulisboa.pt, pedro.cerqueira@medicina.ulisboa.pt

    usage: 
    Sync schema:
    chewBBACA.py SyncSchema -i <schema_directory> 

    Sync schema with non-default parameters:
    chewBBACA.py SyncSchema -i <schema_directory> --cpu <cpu_cores> -ns_url <nomenclature_server_url>

    Sync schema and send novel local alleles to the NS:
    chewBBACA.py SyncSchema -i <schema_directory> --submit

    This program syncs a local schema with NS

    positional arguments:
    SyncSchema                        Synchronize a local schema, previously
                                        downloaded from the NS, with its latest
                                        version in the NS.
                                        

    optional arguments:
    -h, --help                        show this help message and exit
                                        
    -i SCHEMA_DIRECTORY               Path to the directory with the local
                                        schema files. (default: None)
                                        
    --cpu CPU_CORES                   Number of CPU cores/threads that will be
                                        passed to the PrepExternalSchema to
                                        determine representatives for the updated
                                        version of the schema. (default: 1)
                                        
    --ns_url NOMENCLATURE_SERVER_URL  The base URL for the Nomenclature Server.
                                        (default: http://127.0.0.1:5000/NS/api/)
                                        
    --submit                          If the local alleles that are not in the
                                        NS should be uploaded to update the NS
                                        schema. (default: False)


