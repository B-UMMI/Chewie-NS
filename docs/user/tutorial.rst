Step-by-step Tutorial
=====================

We prepared a `chewie-NS instance <https://tutorial.chewbbaca.online/>`_ that provides a
sandbox-style environment where anyone can test functionalities. This tutorial instance enables
testing with simple cases that were specially designed to demonstrate how users can use
`chewBBACA modules <https://github.com/B-UMMI/chewBBACA/tree/master/CHEWBBACA/CHEWBBACA_NS>`_
specifically designed to interact with chewie-NS to download, upload and synchronize schemas,
while also promoting the exploration of data uploaded to the chewie-NS tutorial in its 
`website <https://tutorial.chewbbaca.online/>`_ and a better understanding of how it is
possible to interact with the API.

Getting started - tutorial datasets
:::::::::::::::::::::::::::::::::::

You can start by downloading any of the archives with tutorial datasets that are available
at the chewie-NS tutorial `GitHub repository <https://github.com/B-UMMI/Chewie-NS_tutorial>`_.

Currently, there are datasets for the following species:

- *Streptococcus agalactiae*
  (`sagalactiae.zip <https://github.com/B-UMMI/Chewie-NS_tutorial/blob/master/tutorial_data/sagalactiae_tutorial.zip?raw=true>`_)

In this tutorial we will provide step-by-step instructions that use the
*Streptococcus agalactiae* tutorial dataset, but the procedure is valid for any schema that
we make available.

You will have to extract the contents in the archive. Tutorial datasets have the following
directory structure::

    sagalactiae_tutorial
    ├── sagalactiae_genomes
    │   ├── subset1
    │   └── subset2
    ├── sagalactiae_schema
    │   ├── short
    │   │   ├── sagalactiae_protein1_short.fasta
    │   │   ├── sagalactiae_protein2_short.fasta
    │   │   ├── sagalactiae_protein3_short.fasta
    │   │   ├── sagalactiae_protein4_short.fasta
    │   │   ├── sagalactiae_protein5_short.fasta
    │   │   ├── sagalactiae_protein6_short.fasta
    │   │   ├── sagalactiae_protein7_short.fasta
    │   │   ├── sagalactiae_protein8_short.fasta
    │   │   ├── sagalactiae_protein9_short.fasta
    │   │   └── sagalactiae_protein10_short.fasta
    │   ├── sagalactiae_protein1.fasta
    │   ├── sagalactiae_protein2.fasta
    │   ├── sagalactiae_protein3.fasta
    │   ├── sagalactiae_protein4.fasta
    │   ├── sagalactiae_protein5.fasta
    │   ├── sagalactiae_protein6.fasta
    │   ├── sagalactiae_protein7.fasta
    │   ├── sagalactiae_protein8.fasta
    │   ├── sagalactiae_protein9.fasta
    │   ├── sagalactiae_protein10.fasta
    │   └── Streptococcus_agalactiae.trn
    ├── sagalactiae_annotations.tsv
    └── sagalactiae_description.md

The ``subset1`` and ``subset2`` directories inside the ``sagalactiae_genomes`` directory contain two
sets of genomes that will be used at different steps of the tutorial.

The ``sagalactiae_schema`` directory contains a schema with 10 genes. The ``short`` directory contained
in the schema's directory has the set of FASTA files with representative sequences for each gene in the
schema. The ``Streptococcus_agalactiae.trn`` file is the Prodigal training file used to predict coding
sequences from input genomes.

The ``sagalactiae_annotations.tsv`` file contains User and Custom annotations for the loci in the schema
and the ``sagalactiae_description.md`` file is a sample description for the schema. The Custom annotation
field in the annotations file and the description file support markdown syntax. You may change the
contents of the files before uploading the schema if you wish.

chewBBACA installation
::::::::::::::::::::::

By taking advantage of chewie-NS’ API, chewBBACA is capable of handling not only the schema creation,
but also its upload, synchronization and download. The set of modules to interact with chewie-NS
included in the chewBBACA suite provide a simple and automatic solution for the main procedures
users will want to perform.

You can install `chewBBACA <https://github.com/B-UMMI/chewBBACA>`_ through 
`conda <https://anaconda.org/bioconda/chewbbaca>`_ or `pip <https://pypi.org/project/chewBBACA/>`_.
chewBBACA has dependencies that will not be included if you install it through pip. If you install
through pip you need to ensure that you have Prodigal 2.6.0 and BLAST 2.9.0 or greater.

.. important:: Do not use a BLAST version older that 2.9.0 as it does not include functionalities
               used in the latest version of chewBBACA.


Uploading the tutorial schema
:::::::::::::::::::::::::::::

::

    $ chewBBACA.py LoadSchema -i sagalactiae_schema/ -sp 1 -sn tut -lp tut --df sagalactiae_description.md --a sagalactiae_annotations.tsv --ns tutorial

    ==========================
      chewBBACA - LoadSchema
    ==========================

    -- User Permissions --
    User id: 
    User role: 
    Authorized: True

    -- Parameters Validation --
    Local schema: sagalactiae_schema
    Schema's species: Streptococcus agalactiae (id=1)
    Number of loci: 10
    Number of alleles: 10

    Verifying schema configs...
      bsr: 0.6
      translation_table: 11
      minimum_locus_length: 201
      chewBBACA_version: 2.5.0
      size_threshold: 0.2
      word_size: None
      cluster_sim: None
      representative_filter: None
      intraCluster_filter: None
    All configurations successfully validated.

    New schema name: "tut" 
    Schema description: sagalactiae_description.md

    -- Schema Pre-processing --
    Determining data to upload...
      Loci to create and associate with species and schema: 10
      Loci without the full set of alleles: 10

    Translating sequences based on schema configs...
      Found a total of 0 invalid alleles.

    Loci missing UniProt annotation: 10
    Creating SPARQL queries to search UniProt for annotations...
    Searching for annotations on UniProt...
    Searched annotations for 10/10 loci
    User provided valid annotations for 10 loci.

    -- Schema Upload --
    Created schema with name tut (id=1).

    Loci data:
      Collecting loci data...
      Sending data to the NS...
        Inserted 10 loci; Linked 10 to species; Linked 10 to schema.
      The NS completed the insertion of 10 loci.

    Alleles data:
      Collecting alleles data...
      Compressing files with alleles data...
      Sending alleles data to the NS...
        Sent data for alleles of 10 loci.

    Uploading Prodigal training file...
    Provided training file is already in the NS.

    The NS has received the data and will insert the alleles into the database.
    Schema will be available for download as soon as the process has completed.
    Schema information will also be available on the NS website.

    Removing intermediate files...

Downloading the schema
::::::::::::::::::::::

::

    $ chewBBACA.py DownloadSchema -sp 1 -sc 1 -o sagalactiae_ns --ns tutorial

    ==============================
      chewBBACA - DownloadSchema
    ==============================

    Schema id: 1
    Schema name: tut
    Schema's species: Streptococcus agalactiae (id=1)

    Downloading compressed version...
    Decompressing schema...
    Schema is now available at: /home/rfm/Desktop/NS_tutorial_data/tutorial_data/tests/sagalactiae_ns/sagalactiae_tut


Local analysis with subset1
:::::::::::::::::::::::::::

::

    $ chewBBACA.py AlleleCall -i subset1/ -g sagalactiae_ns/sagalactiae_tut/ -o subset1_results 

    ==========================
      chewBBACA - AlleleCall
    ==========================

    Prodigal training file: Streptococcus_agalactiae.trn
    Number of CPU cores: 1

    Checking dependencies...
    Blast installation...True
    Prodigal installation...True
    Blast version meets minimum requirements (>=2.5.0).

    Checking if genome files exist...
    Checking if gene files exist...

    Starting Prodigal at: 21:00:02-07/08/2020
    done prodigal run on:GCA_000012705.1_ASM1270v1_genomic.fna
    done prodigal run on:GCA_000007265.1_ASM726v1_genomic.fna
    done prodigal run on:GCA_000302475.2_ASM30247v2_genomic.fna
    done prodigal run on:GCA_000196055.1_ASM19605v1_genomic.fna
    done prodigal run on:GCA_000299135.1_ASM29913v1_genomic.fna
    done prodigal run on:GCA_000427035.1_09mas018883_genomic.fna
    done prodigal run on:GCA_000427055.1_ILRI112_genomic.fna
    done prodigal run on:GCA_000427075.1_ILRI005_genomic.fna
    done prodigal run on:GCA_000599965.1_ASM59996v1_genomic.fna
    done prodigal run on:GCA_000689235.1_GBCO_p1_genomic.fna
    done prodigal run on:GCA_000730255.1_ASM73025v1_genomic.fna
    done prodigal run on:GCA_000730215.2_ASM73021v2_genomic.fna
    Finishing Prodigal at: 21:00:05-07/08/2020

    Checking if Prodigal created all the necessary files...
    All files were created.

    Translating genomes...
    Creating Blast databases for all genomes...

    Starting Allele Calling at: 21:00:07-07/08/2020
    Processing tut-00000002.fasta. Start 21:00:08-07/08/2020 Locus 9 of 10. Done 90%.
    Finished Allele Calling at: 21:00:09-07/08/2020

    Wrapping up the results...
    ##################################################
    12 genomes used for 10 loci

    Used a BSR of: 0.6

    17 exact matches found out of 120

    14.17 percent of exact matches
    ##################################################

    Writing output files...

    ------------------------------------------------------------------------------------------
    Genome                                      EXC    INF    LNF   PLOT   NIPH    ALM    ASM 
    ------------------------------------------------------------------------------------------
    GCA_000007265.1_ASM726v1_genomic.fna         1      5      4      0      0      0      0  
    GCA_000012705.1_ASM1270v1_genomic.fna        1      4      5      0      0      0      0  
    GCA_000196055.1_ASM19605v1_genomic.fna       1      5      4      0      0      0      0  
    GCA_000299135.1_ASM29913v1_genomic.fna       4      1      4      0      0      0      1  
    GCA_000302475.2_ASM30247v2_genomic.fna       0      5      5      0      0      0      0  
    GCA_000427035.1_09mas018883_genomic.fna      2      3      5      0      0      0      0  
    GCA_000427055.1_ILRI112_genomic.fna          1      4      4      0      0      0      1  
    GCA_000427075.1_ILRI005_genomic.fna          1      5      4      0      0      0      0  
    GCA_000599965.1_ASM59996v1_genomic.fna       0      5      5      0      0      0      0  
    GCA_000689235.1_GBCO_p1_genomic.fna          0      5      5      0      0      0      0  
    GCA_000730215.2_ASM73021v2_genomic.fna       3      3      4      0      0      0      0  
    GCA_000730255.1_ASM73025v1_genomic.fna       3      2      4      0      0      0      1  
    ------------------------------------------------------------------------------------------

    Checking the existence of paralog genes...
    Detected number of paralog loci: 0

    Creating SQLite database to store profiles...done.
    Inserted 10 loci into database.

    Sending allelic profiles to SQLite database...done.
    Inserted 12 profiles (12 total, 12 total unique).



Syncing schema
::::::::::::::

::

    $ chewBBACA.py SyncSchema -sc sagalactiae_ns/sagalactiae_tut/ --submit


Getting schema snapshot
:::::::::::::::::::::::

::

    $ chewBBACA.py DownloadSchema -sp 1 -sc 1 -o sagalactiae_snapshot --ns tutorial --d "2020-06-07T20:20:20"


Local analysis with subset2
:::::::::::::::::::::::::::

::

    $ chewBBACA.py AlleleCall -i subset2/ -g sagalactiae_snapshot/sagalactiae_tut/ -o subset2_results 

Syncing schema
::::::::::::::

::

    $ chewBBACA.py SyncSchema -sc sagalactiae_ns/sagalactiae_tut/ --submit


