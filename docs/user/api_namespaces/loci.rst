Loci Namespace
==============

This namespace contains endpoints to get data about the loci of the database, such as its alleles, the FASTA sequence and the Uniprot annotation.

Get the list of all loci from Chewie-NS
:::::::::::::::::::::::::::::::::::::::

The ``/loci/list`` endpoint will return **all** loci form Chewie-NS.

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

.. warning::
    Using this endpoint with large databases will cause a considerable slow response from the server.
    Please don't abuse it.


Get details about a loci
::::::::::::::::::::::::

The ``/loci/{loci_id}`` will return detailed information about the locus, such as:

- The locus name.
- The name of the it was contained in.
- The Uniprot annotation.
- The Uniprot URI.

Example::

    [
      {
        "name": {
          "type": "literal",
          "value": "test_schema-000001"
        },
        "original_name": {
          "type": "literal",
          "value": "protein1.fasta"
        },
        "UniprotName": {
          "type": "typed-literal",
          "datatype": "http://www.w3.org/2001/XMLSchema#string",
          "value": "chromosomal replication initiator protein DnaA"
        },
        "UniprotLabel": {
          "type": "typed-literal",
          "datatype": "http://www.w3.org/2001/XMLSchema#string",
          "value": "chromosomal replication initiator protein DnaA"
        },
        "UniprotURI": {
          "type": "typed-literal",
          "datatype": "http://www.w3.org/2001/XMLSchema#string",
          "value": "http://purl.uniprot.org/uniparc/UPI001012CEFD"
        }
      }
    ]

Get the allele IDs of a locus
:::::::::::::::::::::::::::::

The ``/loci/{loci_id}/alleles`` endpoint returns the alleles IDs associated with a locus.

Example::

    {
        "alleles": {
        "type": "uri",
        "value": "https://127.0.0.1/NS/api/loci/1/alleles/1"
        }
    }

Get details about an allele associated with a locus
:::::::::::::::::::::::::::::::::::::::::::::::::::

The ``/loci/{loci_id}/alleles/{allele_id}`` returns detailed information about an allele.

The response contains:

- The sequence hash, which can be used in the :doc:`sequences`.
- The source organism.
- The insertion date.
- The allele ID.
- The isolate count.

Example::

    [
        {
            "sequence": {
            "type": "uri",
            "value": "https://127.0.0.1/NS/api/sequences/<hash>"
            },
            "source": {
            "type": "literal",
            "value": "Yersinia pestis"
            },
            "date": {
            "type": "typed-literal",
            "datatype": "http://www.w3.org/2001/XMLSchema#dateTime",
            "value": "2020-04-09T14:59:05.434355"
            },
            "id": {
            "type": "typed-literal",
            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
            "value": "1"
            },
            "isolate_count": {
            "type": "typed-literal",
            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
            "value": "0"
            }
        }
    ]


Getting the DNA sequence of all alleles associated with a locus
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

The ``/loci/{loci_id}/fasta`` endpoint returns the DNA sequence of all alleles belonging to a locus.

The response contains:

- The locus name.
- The allele ID.
- The nucleotide sequence.
- The length of the nucleotide sequence.

Example::

  "Fasta": [
    {
      "name": {
        "type": "typed-literal",
        "datatype": "http://www.w3.org/2001/XMLSchema#string",
        "value": "test_schema-000001"
      },
      "allele_id": {
        "type": "typed-literal",
        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
        "value": "1"
      },
      "nucSeq": {
        "type": "literal",
        "value": "ATGACTGAAAATGAACAAATTTTTTGGAACAGGGTCTTGGAATTAGCTCAGAGTCAAT
                  TAAAACAGGCAACTTATGAATTTTTTGTTCATGATGCCCGTCTATTAAAGGTCGATAA
                  GCATATTGCAACTATTTACTTAGATCAAATGAAAGAACTCTTTTGGGAAAAAAATCTT
                  AAAGATGTTATTCTTACTGCTGGTTTTGAAGTTTATAACGCTCAAATTTCTGTTGACT
                  ATGTTTTCGAAGAAGACCTAATGATTGAGCAAAATCAGACCAAAATCAATCAAAAACC
                  TAAGCAGCAAGCCTTAAATTCTTTGCCTACTGTTACTTCAGATTTAAACTCGAAATAT
                  AGTTTTGAAAACTTTATTCAAGGAGATGAAAATCGTTGGGCTGTTGCTGCTTCAATAG
                  CAGTAGCTAATACTCCTGGAACTACCTATAATCCTTTGTTTATTTGGGGTGGCCCTGG
                  GCTTGGGAAAACCCATTTATTAAATGCTATTGGTAATTCTGTACTATTAGAAAATCCA
                  AATGCTCGAATTAAATATATCACAGCTGAAAACTTTATTAATGAGTTTGTTATCCATA
                  TTCGCCTTGATACCATGGATGAATTGAAAGAAAAATTTCGTAATTTAGATTTACTCCT
                  TATTGATGATATCCAATCTTTAGCTAAAAAAACGCTCTCTGGAACACAAGAAGAGTTC
                  TTTAATACTTTTAATGCACTTCATAATAATAACAAACAAATTGTCCTAACAAGCGACC
                  GTACACCAGATCATCTCAATGATTTAGAAGATCGATTAGTTACTCGTTTTAAATGGGG
                  ATTAACAGTCAATATCACACCTCCTGATTTTGAAACACGAGTGGCTATTTTGACAAAT
                  AAAATTCAAGAATATAACTTTATTTTTCCTCAAGATACCATTGAGTATTTGGCTGGTC
                  AATTTGATTCTAATGTCAGAGATTTAGAAGGTGCCTTAAAAGATATTAGTCTGGTTGC
                  TAATTTCAAACAAATTGACACGATTACTGTTGACATTGCTGCCGAAGCTATTCGCGCC
                  AGAAAGCAAGATGGACCTAAAATGACAGTTATTCCCATCGAAGAAATTCAAGCGCAAG
                  TTGGAAAATTTTACGGTGTTACCGTCAAAGAAATTAAAGCTACTAAACGAACACAAAA
                  TATTGTTTTAGCAAGACAAGTAGCTATGTTTTTAGCACGTGAAATGACAGATAACAGT
                  CTTCCTAAAATTGGAAAAGAATTTGGTGGCAGAGACCATTCAACAGTACTCCATGCCT
                  ATAATAAAATCAAAAACATGATCAGCCAGGACGAAAGCCTTAGGATCGAAATTGAAAC
                  CATAAAAAACAAAATTAAATAA"
      },
      "nucSeqLen": {
        "type": "typed-literal",
        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
        "value": "1356"
      }
    } 
  ]


