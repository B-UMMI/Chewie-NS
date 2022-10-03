Species Namespace
=================

This namespace contains endpoints to get data about all species on the database and also about a specific species.

Get the list of species
:::::::::::::::::::::::

To get the list of species available in Chewie-NS you need to use the ``/species/list`` endpoint.

Click on the ``Try it out`` on the top-right corner of the endpoint and afterwards the ``Execute`` button.

An example of a possible response from Chewie-NS is the following

::

    [
  {
    "species": {
      "type": "uri",
      "value": "https://127.0.0.1/NS/api/species/1"
    },
    "name": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "Yersinia pestis"
    }
  },
  {
    "species": {
      "type": "uri",
      "value": "https://127.0.0.1/NS/api/species/2"
    },
    "name": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "Streptococcus agalactiae"
    }
  }
    ]

In the response we obtain the internal ID of the species, which is important if we want to
`Download a schema from Chewie-NS <https://chewbbaca.readthedocs.io/en/latest/user/modules/DownloadSchema.html>_` or
`Upload a schema to Chewie-NS <https://chewbbaca.readthedocs.io/en/latest/user/modules/LoadSchema.html>_`.
We also obtain the name of the species associated with each ID.

Alternatively, we can check if a species is already on Chewie-NS by filling the ``species_name`` field. If the species exists, the response
will contain the associated ID.

For example if we search for *Yersinia pestis* and it already exists the response will be the following::

  {
    "species": {
      "type": "uri",
      "value": "https://127.0.0.1/NS/api/species/1"
    }
  }

If it does not exist, the response will be the following::

    {
        "NOT FOUND": "Species does not exists in the NS."
    }


Getting all the loci for a species
::::::::::::::::::::::::::::::::::

To get all the loci of a species, we need to access the ``/species/{species_id}/loci`` and provide the ID 
of the species obtained in endpoint described above.

The obtained response contains:

- The name of the locus.
- The locus ID, which can be used to obtain more information in the :doc:`loci`.
- The name of the file it was contained.

Example::

  "Loci": [
    {
      "name": {
        "type": "literal",
        "value": "test_schema-000006"
      },
      "locus": {
        "type": "uri",
        "value": "https://127.0.0.1/NS/api/loci/6"
      },
      "original_name": {
        "type": "literal",
        "value": "original_file.fasta"
      }
    }
  ]


Getting schemas information
:::::::::::::::::::::::::::

The ``/species/{species_id}/schemas`` endpoint allows users to get all the schemas associated with a species. 
The response will contain:

- The schema ID.
- The schema name.

Example::

    [
        {
            "schemas": {
                "type": "uri",
                "value": "https://127.0.0.1/NS/api/species/1/schemas/1"
            },
            "name": {
                "type": "typed-literal",
                "datatype": "http://www.w3.org/2001/XMLSchema#string",
                "value": "test_schema"
            }
        }
    ]


Getting chewBBACA parameters of a schema
::::::::::::::::::::::::::::::::::::::::

The ``/species/{species_id}/schemas/{schema_id}`` will return the chewBBACA parameters used to create a schema.

Example::

    [
  {
    "name": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "test_schema"
    },
    "bsr": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "0.6"
    },
    "chewBBACA_version": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "2.1.0"
    },
    "prodigal_training_file": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "<hash>"
    },
    "translation_table": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "11"
    },
    "minimum_locus_length": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "201"
    },
    "size_threshold": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "None"
    },
    "word_size": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "None"
    },
    "cluster_sim": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "None"
    },
    "representative_filter": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "None"
    },
    "intraCluster_filter": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "None"
    },
    "dateEntered": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "2020-04-09T19:35:38.287942"
    },
    "last_modified": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "2020-04-09T19:35:38.287942"
    },
    "Schema_lock": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "Unlocked"
    },
    "SchemaDescription": {
      "type": "typed-literal",
      "datatype": "http://www.w3.org/2001/XMLSchema#string",
      "value": "Schema description."
    }
  }
    ]


Getting the loci of a schema
::::::::::::::::::::::::::::

The ``/species/{species_id}/schemas/{schema_id}/loci`` will return the loci corresponding to a schema, instead of the loci of the species.

The response has the same format as described in `Getting all the loci for a species`_.

