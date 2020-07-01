Synchronize a local chewBBACA schema with data from the Chewie-NS
=================================================================

The `SyncSchema <https://github.com/B-UMMI/chewBBACA/blob/master/CHEWBBACA/CHEWBBACA_NS/sync_schema.py>`_ 
process included in the chewBBACA suite allows users to synchronize local schemas, previously 
downloaded from the Chewie-NS, with their remote versions. All chewBBACA users can synchronize 
schemas to **get the latest alleles added to the Chewie-NS and to ensure that a common allele**
**identifier nomenclature is maintained for the alleles that are common to local and remote**
**schemas**. We also provide the option to **submit novel alleles**, that were identified during
local analyses and are not present in the Chewie-NS.

.. important:: **Only registered users can submit novel alleles to update remote schemas.**

To synchronize a local schema with its remote version it is only necessary to provide the path
to the schema directory. The simplicity of the process is ensured by a configuration file,
present in all schemas downloaded from the Chewie-NS, that contains the identifier of the
schema in the Chewie-NS and the last modification date of the schema.

Configuration file content::

    $ ...
    
    ['2020-06-30T19:10:37.466104', 'http://chewbbaca.online/NS/api/species/9/schemas/1']

Novel alleles identified during local analyses are added to the schema with a '*' preceding 
their integer identifier.

Local FASTA file example::

    $ cat prefix-018549.fasta

    >prefix-018550_1
    ATGAGCAAGCCTAATGTTGTTCAGTTAAATAATCAATATATTAACGATGAGAATCTAAAAAAACGTTACGAAGCTGAGGAGTTACGCTAA
    >prefix-018550_2
    ATGAGCAAGCCTAATGTTGTTCAGTTAAATAATCAATATATTAACGATGAGAATCTAAAAAAACGTTACGAAGCTGAGGAGTTACGCTAA
    >prefix-018550_3
    ATGAGCAAGCCTAATGTTGTTCAGTTAAATAATCAATATATTAACGATGAGAATCTAAAAAAACGTTACGAAGCTGAGGAGTTACGCTAA
    >prefix-018550_*4
    ATGAGCAAGCCTAATGTTGTTCAGTTAAATAATCAATATATTAACGATGAGAATCTAAAAAAACGTTACGAAGCTGAGGAGTTACGCTAA
    >prefix-018550_*5
    ATGAGCAAGCCTAATGTTGTTCAGTTAAATAATCAATATATTAACGATGAGAATCTAAAAAAACGTTACGAAGCTGAGGAGTTACGCTAA
    >prefix-018550_*6
    ATGAGCAAGCCTAATGTTGTTCAGTTAAATAATCAATATATTAACGATGAGAATCTAAAAAAACGTTACGAAGCTGAGGAGTTACGCTAA
    >prefix-018550_*7
    ATGAGCAAGCCTAATGTTGTTCAGTTAAATAATCAATATATTAACGATGAGAATCTAAAAAAACGTTACGAAGCTGAGGAGTTACGCTAA

Alleles retrieved from the Chewie-NS are compared to local alleles and the process 
reassigns allele identifiers to ensure that the alleles that are common to local and remote 
schemas have the same identifiers. Local alleles that are not in the Chewie-NS are shifted 
to the last positions in the FASTA files and keep a '*' in the identifier. If the user wants 
to submit those alleles, the necessary data will be collected and uploaded to the Chewie-NS. 
The Chewie-NS will return the identifiers assigned to the submitted alleles and the local 
process will remove the '*' from the submitted alleles and assign the correct identifier. 
If the process retrieves new alleles from the Chewie-NS, it will redetermine representative 
sequences **ONLY** for the loci in the local schema that were altered by the synchronization 
process.

.. note:: If the local schema has a SQLite database to store allelic profiles, the SyncSchema 
          process will also update the allele identifiers in the stored profles.

.. important:: It is strongly advised that users adjust the value of the ``--cpu`` argument
               in order to speed up the determination of representative sequences.

Example
:::::::

If we want to synchronize a local schema we only need to provide the path to the directory that contains it::

    $ chewBBACA.py SyncSchema -i path/to/schema

The ``--submit`` argument allows users to submit novel alleles in their local schemas::

    $ chewBBACA.py SyncSchema -i path/to/schema --submit

Script Usage
::::::::::::

::

    $ chewBBACA.py SyncSchema -h

    chewBBACA version: 2.5.0
    Authors: Mickael Silva, Pedro Cerqueira, Rafael Mamede
    Github: https://github.com/B-UMMI/chewBBACA
    Wiki: https://github.com/B-UMMI/chewBBACA/wiki
    Tutorial: https://github.com/B-UMMI/chewBBACA_tutorial
    Contacts: imm-bioinfo@medicina.ulisboa.pt

    usage: 
    Sync schema:
      chewBBACA.py SyncSchema -sc <schema_directory> 

    Sync schema with non-default parameters:
      chewBBACA.py SyncSchema -sc <schema_directory> --cpu <cpu_cores> --ns <nomenclature_server_url>

    Sync schema and send novel local alleles to the NS:
      chewBBACA.py SyncSchema -sc <schema_directory> --submit

    This program syncs a local schema with NS

    positional arguments:
    SyncSchema                Synchronize a local schema, previously downloaded
                                from the NS, with its latest version in the NS.
                                

    optional arguments:
    -h, --help                show this help message and exit
                                
    -sc SCHEMA_DIRECTORY      Path to the directory with the schema to besynced.
                                (default: None)
                                
    --cpu CPU_CORES           Number of CPU cores that will be used to determine
                                new representatives if the process downloads new
                                alleles from the Chewie-NS. (default: 1)
                                
    --ns NOMENCLATURE_SERVER  The base URL for the Nomenclature Server.
                                (default: main)
                                
    --submit                  If the process should identify new alleles in the
                                local schema and send them to the NS. (only users
                                with permissons level of Contributor can submit
                                new alleles). (default: False)


