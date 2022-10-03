Populate the Database
=====================

When Chewie-NS is deployed the Virtuoso database only contains the admin user, so we 
need to populate the database. Here we will describe the manual process to add a 
schema, loci and alleles to Chewie-NS. To add a schema with multiple loci and alleles 
please read `Upload a schema to Chewie-NS <https://chewbbaca.readthedocs.io/en/latest/user/modules/LoadSchema.html>`_.

To add data to the database we have to follow these steps:

Authenticate
::::::::::::

First we need to authenticate the admin user and obtain a token that will allow a 
user to access the POST endpoints (GET endpoints don't require authentication).

Add a new species
:::::::::::::::::

Afterwards, we need to access the ``species`` namespace on the Swagger page. 
There go to the ``/species/list`` POST endpoint and press the ``Try it out`` button.

Next fill the ``name`` field of the JSON payload with the name of the species to be 
added to the database and press the execute button.

::

    {
        "name": "Yersinia pestis"
    }

Output

::

    {
        "message": "Yersinia pestis added to the NS."
    }

Add a new for schema for a species
::::::::::::::::::::::::::::::::::

To add a new schema to a species we need to use the ``{species_id}/schemas`` 
POST endpoint and provide the species ID to add the new schema and also the
following parameters, which are the parameters used to obtain the chewBBACA schema::

    {
        "name": "string",
        "bsr": "string",
        "prodigal_training_file": "string",
        "translation_table": "string",
        "minimum_locus_length": "string",
        "size_threshold": "string",
        "chewBBACA_version": "string",
        "word_size": "string",
        "cluster_sim": "string",
        "representative_filter": "string",
        "intraCluster_filter": "string"
    }

- **name** - schema name;
- **bsr** - blast score ratio;
- **ptf** - prodigal training file;
- **translation_table** - translation table;
- **minimum_locus_length** - minimum locus length;
- **size_threshold** - size threshold;
- **chewBBACA_version** - chewBBACA's version;
- **word_size** - word size;
- **cluster_sim** - cluster_sim;
- **representative_filter** - representative_filter;
- **intraCluster_filter** - intraCluster_filter;

Add a new locus
:::::::::::::::

We have a species and a schema now we need some loci. For that we need to go the 
``loci`` namespace and add a new locus there.

There use the ``/list`` POST endpoint and fill the JSON payload with the 
*locus prefix* and the original name of the locus. ::

    {
        "prefix": "string",
        "locus_ori_name": "string"
    }

The output is the following::

    {
        "message": "New locus added at http://127.0.0.1:5000/NS/api/loci/1 with the alias test-000001",
        "uri": "http://127.0.0.1:5000/NS/api/loci/1",
        "id": "1"
    }


Add an allele to the locus
::::::::::::::::::::::::::

Now we need to add some alleles to the locus we added before. For that we need to 
go to the ``/loci/{loci_id}/alleles`` POST endpoint.

Just fill the following parameters and provide the locus ID obtained previously 
to give that locus a new allele. ::

    {
        "sequence": "string",
        "species_name": "string",
        "uniprot_url": "string",
        "uniprot_label": "string",
        "uniprot_sname": "string",
        "sequence_uri": "string",
        "enforceCDS": false,
        "input": "manual, auto"
    }

- **sequence** - DNA sequence of the allele;
- **species_name** - the name of the species we are tring to add the allele;
- **uniprot_url** - the url to the uniprot annotation;
- **uniprot_label** - the uniprot label;
- **uniprot_sname** - the uniprot submitted name;
- **sequence_uri** - 
- **enforceCDS** - forces the endpoint to only accept CDS;
- **input** - the input type should be **manual**. The other options are for scripts that automate this process.

This is the output::

    {
        "message": "A new allele has been added to http://127.0.0.1:5000/NS/api/loci/1/alleles/1"
    }

Add locus to schema
:::::::::::::::::::

Finally, we return to the ``species`` namespace, namely to the 
``/{species_id}/schemas/{schema_id}/loci`` POST endpoint and we simply provide the locus ID to the JSON payload and we are done.

With these steps you sucessfully added a schema with one locus (with one allele) to the Nomenclature Server! 





