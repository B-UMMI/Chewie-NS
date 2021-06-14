import os
import hashlib

# import typing as t
from fastapi import HTTPException, status
from aiosparql.client import SPARQLClient

from app.api.dependencies import sparql_queries as sq


async def get_seq_list():

    # Define SPARQLClient
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # query number of sequences on database
    # should return 0 if there are no sequences
    result = await client.query(
        sq.COUNT_SEQUENCES.format(os.environ.get("DEFAULT_GRAPH"))
    )

    # Close SPARQLClient to avoid aiohttp warning about unclosed session
    await client.close()

    number_sequences = result["results"]["bindings"][0]["count"]["value"]

    return {
        "message": "Total number of sequences in the Chewie-NS: {0}".format(
            number_sequences
        )
    }


async def get_sequence(request, sequence, species_id, seq_id):

    # Define SPARQLClient
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # get request data
    # request_data = await request.json()
    # if len(request_data) == 0:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Please provide a string for a valid DNA sequence or a valid DNA sequence hash.",
    #     )

    # determine if species identifier was provided
    query_part = ""
    if species_id:
        # species_id = request_data['species_id']
        species_uri = "{0}{1}/{2}".format(
            os.environ.get("BASE_URL"), "species", species_id
        )
        # create additional query part to filter by species
        query_part = "?locus a typon:Locus; typon:isOfTaxon <{0}> .".format(
            species_uri
        )

    # if DNA sequence is provided, hash it and send request to virtuoso
    if sequence:

        # sequence = request_data['sequence']

        seq_hash = hashlib.sha256(sequence.encode("utf-8")).hexdigest()

        seq_url = "{0}sequences/{1}".format(
            os.environ.get("BASE_URL"), seq_hash
        )

        # check if the sequence exists
        result_existence = await client.query(
            sq.ASK_SEQUENCE_HASH.format(seq_url)
        )

        if not result_existence["boolean"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provided DNA sequence is not in the NS.",
            )

        result = await client.query(
            sq.SELECT_SEQUENCE_INFO_BY_DNA.format(
                os.environ.get("DEFAULT_GRAPH"), seq_url, query_part
            )
        )

        sequence_info = result["results"]["bindings"]
        if len(sequence_info) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sequence is in the NS but is not linked to any locus.",
            )

        locus_url = sequence_info[0]["locus"]["value"]

        locus_result = await client.query(
            sq.COUNT_LOCUS_ALLELES.format(
                os.environ.get("DEFAULT_GRAPH"), locus_url
            )
        )

        await client.close()

        number_alleles_loci = int(
            locus_result["results"]["bindings"][0]["count"]["value"]
        )

        return {
            "result": sequence_info,
            "sequence_uri": seq_url,
            "number_alleles_loci": number_alleles_loci,
        }

    # if sequence hash is provided
    elif seq_id:
        seq_url = "{0}sequences/{1}".format(os.environ.get("BASE_URL"), seq_id)

        # get information on sequence, DNA string, uniprot URI and uniprot label
        result = await client.query(
            sq.SELECT_SEQUENCE_INFO_BY_HASH.format(
                os.environ.get("DEFAULT_GRAPH"), seq_url, query_part
            )
        )

        sequence_info = result["results"]["bindings"]

        if len(sequence_info) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not find information for a sequence with provided hash.",
            )

        locus_url = sequence_info[0]["locus"]["value"]

        locus_result = await client.query(
            sq.COUNT_LOCUS_ALLELES.format(
                os.environ.get("DEFAULT_GRAPH"), locus_url
            )
        )

        await client.close()

        number_alleles_loci = int(
            locus_result["results"]["bindings"][0]["count"]["value"]
        )

        return {
            "result": sequence_info,
            "number_alleles_loci": number_alleles_loci,
        }
