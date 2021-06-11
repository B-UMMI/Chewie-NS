Sequences Namespace
===================

The ``/sequences/seq_info`` endpoint allows users to check if a particular allele (or DNA sequence) is 
present in Chewie-NS already. 

The response will contain:

- The schema ID where the sequence is associated.
- The locus ID where the sequence is associated.
- The allele ID of the sequence.
- The URI of the sequence.

Example::

    {
  "result": [
    {
      "schemas": {
        "type": "uri",
        "value": "https://127.0.0.1/NS/api/species/2/schemas/1"
      },
      "locus": {
        "type": "uri",
        "value": "https://127.0.0.1/NS/api/loci/6"
      },
      "alleles": {
        "type": "uri",
        "value": "https://127.0.0.1/NS/api/loci/15441/alleles/1"
      },
      "name": {
        "type": "typed-literal",
        "datatype": "http://www.w3.org/2001/XMLSchema#string",
        "value": "Species name"
      }
    }
    ],
    "sequence_uri": "https://127.0.0.1/NS/api/sequences/<uri>",
    "number_alleles_loci": 1000
    }


