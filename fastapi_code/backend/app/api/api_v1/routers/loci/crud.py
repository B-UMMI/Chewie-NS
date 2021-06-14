import os
import time
import hashlib

# import typing as t
from fastapi import HTTPException, status
from aiosparql.client import SPARQLClient

from app.core.celery_app import celery_app
from app.api.dependencies import auxiliary_functions as aux
from app.api.dependencies import sparql_queries as sq

from app.api.dependencies import rm_functions

from SPARQLWrapper import SPARQLWrapper


async def loci_list(prefix, sequence, locus_ori_name):
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # Get list of loci that contain the provided DNA sequence
    if sequence is not None:

        # Get sequence from request
        sequence = sequence.upper()

        # Generate hash
        sequence_hash = hashlib.sha256(sequence.encode("utf-8")).hexdigest()

        # Query virtuoso
        sequence_uri = "{0}sequences/{1}".format(
            os.environ.get("BASE_URL"), str(sequence_hash)
        )

        # get all loci that have the provided sequence
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_SEQUENCE_LOCI.format(current_app.config['DEFAULTHGRAPH'], sequence_uri)))

        result = await client.query(
            sq.SELECT_SEQUENCE_LOCI.format(
                os.environ.get("DEFAULT_GRAPH"), sequence_uri
            )
        )

        res_loci = result["results"]["bindings"]

    else:
        # get list of loci, ascending order of locus identifier
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         sq.SELECT_ALL_LOCI.format(current_app.config['DEFAULTHGRAPH']))

        result = await client.query(
            sq.SELECT_ALL_LOCI.format(os.environ.get("DEFAULT_GRAPH"))
        )

        res_loci = result["results"]["bindings"]

    if prefix is not None:
        res_loci = [res for res in res_loci if prefix in res["name"]["value"]]

    if locus_ori_name is not None:
        res_loci = [
            res
            for res in res_loci
            if locus_ori_name in res["original_name"]["value"]
        ]

    # if result is not empty, stream with context
    if len(res_loci) > 0:
        return res_loci
        # return Response(stream_with_context(generate('Loci', res_loci)), content_type='application/json', mimetype='application/json')

    # if there are loci with the sequence, filter based on other arguments
    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="None of the loci in the NS meet the filtering criteria.",
        )


async def create_loci(prefix, locus_ori_name, loci_post):
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # check if prefix is not invalid
    if aux.check_prefix(prefix) is False:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid prefix.",
        )

    # count total number of loci in the NS
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                       (sq.COUNT_TOTAL_LOCI.format(current_app.config['DEFAULTHGRAPH'])))

    result = await client.query(
        sq.COUNT_TOTAL_LOCI.format(os.environ.get("DEFAULT_GRAPH"))
    )

    number_loci_spec = int(result["results"]["bindings"][0]["count"]["value"])

    newLocusId = number_loci_spec + 1

    # name will be something like prefix-000001
    aliases = "{0}-{1}".format(prefix, "%06d" % (newLocusId,))

    # check if already exists locus with that aliases
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.ASK_LOCUS_PREFIX.format(aliases)))

    result = await client.query(sq.ASK_LOCUS_PREFIX.format(aliases))

    if result["boolean"]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Locus with that prefix already exists.",
        )

    new_locus_url = "{0}loci/{1}".format(os.environ.get("BASE_URL"), newLocusId)

    # try to get locus original FASTA file name
    if not locus_ori_name:
        locus_ori_name = False
    # locus_ori_name = post_data.get('locus_ori_name', False)

    uniprot_name = loci_post.uniprot_name
    uniprot_label = loci_post.uniprot_label
    uniprot_uri = loci_post.uniprot_url
    ns_locus_ori_name = (
        '; typon:originalName "{0}"^^xsd:string.'.format(locus_ori_name)
        if locus_ori_name not in ["", "string", False]
        else " ."
    )

    # if locus_ori_name then also save the original fasta name
    query2send = sq.INSERT_LOCUS.format(
        os.environ.get("DEFAULT_GRAPH"),
        new_locus_url,
        aliases,
        uniprot_name,
        uniprot_label,
        uniprot_uri,
        "-",
        "-",
        ns_locus_ori_name,
    )

    # result = aux.send_data(query2send,
    #                         current_app.config['LOCAL_SPARQL'],
    #                         current_app.config['VIRTUOSO_USER'],
    #                         current_app.config['VIRTUOSO_PASS'])

    result = await client.update(query2send)

    await client.close()

    return {
        "message": "New locus added at {0} with the alias {1}".format(
            new_locus_url, aliases
        ),
        "uri": new_locus_url,
        "id": str(newLocusId),
    }

    # if result.status_code in [200, 201]:
    #     return {'message': 'New locus added at {0} with the alias {1}'.format(new_locus_url, aliases),
    #             'uri': new_locus_url,
    #             'id': str(newLocusId)}, 201
    # else:
    #     return {'message': 'Could not create locus.'}, result.status_code


async def get_loci(loci_id):
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    locus_url = "{0}loci/{1}".format(os.environ.get("BASE_URL"), loci_id)

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_LOCUS.format(current_app.config['DEFAULTHGRAPH'], locus_url)))

    result = await client.query(
        sq.SELECT_LOCUS.format(os.environ.get("DEFAULT_GRAPH"), locus_url)
    )

    await client.close()

    locus = result["results"]["bindings"]

    if locus == []:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="There is no locus with the provided ID.",
        )
    else:
        return {"result": locus}


async def delete_loci(loci_id):
    results = await rm_functions.rm_loci(
        loci_id,
        os.environ.get("DEFAULT_GRAPH"),
        os.environ.get("LOCAL_SPARQL"),
        os.environ.get("BASE_URL"),
        os.environ.get("VIRTUOSO_USER"),
        os.environ.get("VIRTUOSO_PASS"),
    )

    return results


async def get_loci_fasta(loci_id, date):
    """
    Gets the FASTA sequence of the alleles
    from a particular loci of a particular species.
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    locus_uri = "{0}loci/{1}".format(os.environ.get("BASE_URL"), loci_id)

    # check if locus exists
    locus_exists = await client.query(sq.ASK_LOCUS.format(locus_uri))

    locus_exists = locus_exists["boolean"]
    if locus_exists is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="There is no locus with the provided ID.",
        )

    # get schema that the locus is associated with
    locus_schema_query = await client.query(
        sq.SELECT_LOCUS_SCHEMA.format(
            os.environ.get("DEFAULT_GRAPH"), locus_uri
        )
    )

    # get schema URI from response
    has_schema = (
        False if locus_schema_query["results"]["bindings"] == [] else True
    )

    if has_schema is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Locus is not associated with any schema.",
        )

    # locus_schema = locus_schema_query["results"]["bindings"][0]["schema"][
    #     "value"
    # ]

    # get request data
    if date:
        result = await client.query(
            sq.SELECT_LOCUS_FASTA_BY_DATE.format(
                os.environ.get("DEFAULT_GRAPH"), locus_uri, date,
            )
        )
    else:
        # find all alleles from the locus and
        # return the sequence and id sorted by id
        result = await client.query(
            sq.SELECT_LOCUS_FASTA.format(
                os.environ.get("DEFAULT_GRAPH"), locus_uri
            )
        )

    # virtuoso returned an error because request length exceeded maximum value
    # get each allele separately
    try:
        fasta_seqs = result["results"]["bindings"]
    except:
        # get locus sequences hashes
        if date:
            result = await client.query(
                sq.SELECT_LOCUS_SEQS_BY_DATE.format(
                    os.environ.get("DEFAULT_GRAPH"), locus_uri, date,
                )
            )
        else:
            result = await client.query(
                sq.SELECT_LOCUS_SEQS.format(
                    os.environ.get("DEFAULT_GRAPH"), locus_uri
                )
            )

        fasta_seqs = result["results"]["bindings"]
        for s in range(len(fasta_seqs)):
            # get the sequence corresponding to the hash
            result2 = await client.query(
                sq.SELECT_SEQ_FASTA.format(
                    os.environ.get("DEFAULT_GRAPH"),
                    fasta_seqs[s]["sequence"]["value"],
                )
            )

            fasta_seqs[s]["nucSeq"] = result2["results"]["bindings"][0][
                "nucSeq"
            ]

    await client.close()

    return fasta_seqs


async def get_loci_uniprot(loci_id):
    """
    Gets Uniprot annotations for a particular loci from a particular species.
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    locus_url = "{0}loci/{1}".format(os.environ.get("BASE_URL"), loci_id)

    # get all uniprot labels and URI from all alleles of the selected locus
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_LOCUS_UNIPROT.format(current_app.config['DEFAULTHGRAPH'],
    #                                                         locus_url)))

    result = await client.query(
        sq.SELECT_LOCUS_UNIPROT.format(
            os.environ.get("DEFAULT_GRAPH"), locus_url
        )
    )

    await client.close()

    annotations = result["results"]["bindings"]

    if annotations == []:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No Uniprot annotations found for the provided loci ID.",
        )

    return annotations


async def get_loci_alleles(loci_id, species_name):
    """
    Gets all alleles from a particular locus ID.
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    locus_url = "{0}loci/{1}".format(os.environ.get("BASE_URL"), loci_id)

    # check if provided loci id exists
    # result_loci = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             (sq.ASK_LOCUS.format(locus_url)))

    result_loci = await client.query(sq.ASK_LOCUS.format(locus_url))

    if not result_loci["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a locus with provided ID.",
        )

    # if user provided a species name, filter the query to contain only that species
    if species_name:

        species = species_name

        # get the taxon id from uniprot, if not found return 404
        uniprot_query = sq.SELECT_UNIPROT_TAXON.format(species)

        # Check if species exists on uniprot
        # result2 = aux.get_data(SPARQLWrapper(
        #     current_app.config['UNIPROT_SPARQL']), uniprot_query)

        result2 = await client.query(uniprot_query)

        uniprot_taxid = result2["results"]["bindings"]
        if uniprot_taxid != []:
            taxon_uri = uniprot_taxid[0]["taxon"]["value"]
        else:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Species name not found on uniprot, search on http://www.uniprot.org/taxonomy/.",
            )

        # check if species already exists locally (typon)
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.ASK_SPECIES_UNIPROT.format(taxon_uri)))

        result = await client.query(sq.ASK_SPECIES_UNIPROT.format(taxon_uri))

        if not result["boolean"]:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Species does not exists in NS.",
            )

        # determine if locus with provided identifier is associated to provided species
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_LOCUS_SPECIES_ALLELES.format(current_app.config['DEFAULTHGRAPH'],
        #                                                                 locus_url,
        #                                                                 species)))

        result = await client.query(
            sq.SELECT_LOCUS_SPECIES_ALLELES.format(
                os.environ.get("DEFAULT_GRAPH"), locus_url, species
            )
        )

    # simply get all alleles for provided locus
    else:
        # get list of alleles from that locus
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_LOCUS_ALLELES.format(current_app.config['DEFAULTHGRAPH'],
        #                                                         locus_url)))

        result = await client.query(
            sq.SELECT_LOCUS_ALLELES.format(
                os.environ.get("DEFAULT_GRAPH"), locus_url
            )
        )

    locus_info = result["results"]["bindings"]
    if locus_info == []:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Locus with provided ID is not associated to the provided species name.",
        )
    else:
        return locus_info


async def create_loci_alleles(
    loci_id, species_name, alleles_post, input, current_user
):
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    user_id = current_user.id

    # get the DNA sequence
    sequence = (str(alleles_post.sequence)).upper()

    locus_url = "{0}loci/{1}".format(os.environ.get("BASE_URL"), loci_id)

    # if the input mode is 'manual' we need to check that the species exists
    if input == "manual":

        # this is the user URI
        user_url = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

        # check sequence length
        if not aux.check_len(sequence):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Sequence has invalid length value.",
            )

        query = sq.SELECT_UNIPROT_TAXON.format(species_name)

        # Check if species exists on uniprot
        result_species = aux.get_data(
            SPARQLWrapper(os.environ.get("UNIPROT_SPARQL")), query
        )

        # result_species = await client.query(query)
        try:
            url = result_species["results"]["bindings"][0]["taxon"]["value"]
        except:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Species name not found on UniProt. Please provide a valid species name or search for one on http://www.uniprot.org/taxonomy/",
            )

        # after determining that the species exists,
        # check if the sequence is a valid CDS
        translation_result = aux.translate_dna(sequence, 11, 0)
        if isinstance(translation_result, list):
            protein_sequence = str(translation_result[0][0])
        else:
            raise HTTPException(
                status.HTTP_417_EXPECTATION_FAILED,
                detail="Sequence is not a valid CDS.",
            )
            # return {'INVALID CDS': 'Sequence is not a valid CDS.'}, 418

        # check if sequence already belongs to the locus
        query = sq.SELECT_LOCUS_ALLELE.format(
            os.environ.get("DEFAULT_GRAPH"), locus_url, sequence
        )

        # queries with big sequences need different approach
        if len(sequence) > 9000:
            result = aux.send_big_query(
                SPARQLWrapper(os.environ.get("LOCAL_SPARQL")), query
            )
        else:
            # result = aux.get_data(SPARQLWrapper(
            #     os.environ.get('LOCAL_SPARQL')), query)
            result = await client.query(query)

        # if sequence already exists on locus return the allele uri, if not create new sequence
        try:
            new_allele_url = result["results"]["bindings"][0]["alleles"][
                "value"
            ]
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Allele already exists at {0}".format(new_allele_url),
            )
            # return {'REPEATED ALLELE': 'Allele already exists at {0}'.format(new_allele_url)}, 409
        except Exception:
            pass

        # check if sequence exists in uniprot only if the sequence was translatable
        # query the uniprot sparql endpoint and build the RDF with the info on uniprot
        # should not be necessary if properly translated

        # in manual, the allele URI is not provided
        # construct allele URI by counting the total number of alleles in locus

        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.COUNT_LOCUS_ALLELES.format(current_app.config['DEFAULTHGRAPH'], locus_url)))

        result = await client.query(
            sq.COUNT_LOCUS_ALLELES.format(
                os.environ.get("DEFAULT_GRAPH"), locus_url
            )
        )

        number_alleles_loci = int(
            result["results"]["bindings"][0]["count"]["value"]
        )

        allele_uri = "{0}/alleles/{1}".format(
            locus_url, number_alleles_loci + 1
        )

    # Get the uniprot info if it's provided
    elif input == "auto":

        # in auto mode the permissions were previously
        # validated in the load_schema process
        # get token and construct user URI
        # user_id = request.headers.get("user_id")
        user_url = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

        # in 'auto' mode, alleles URIs are provided by the load schema process
        allele_uri = alleles_post.sequence_uri

    # build the id of the sequence by hashing it
    seq_hash = hashlib.sha256(sequence.encode("utf-8")).hexdigest()

    # build the endpoint URI for the sequence
    new_seq_url = "{0}sequences/{1}".format(
        os.environ.get("BASE_URL"), str(seq_hash)
    )

    # check if there is a sequence with the same hash

    hash_presence_query = sq.ASK_SEQUENCE_HASH.format(new_seq_url)

    hash_presence = await client.query(hash_presence_query)

    # hash_presence = aux.get_data(
    #     SPARQLWrapper(current_app.config["LOCAL_SPARQL"]),
    #     (sq.ASK_SEQUENCE_HASH.format(new_seq_url)),
    # )

    # check if the sequence that has the same hash is the same or a different DNA sequence
    # only enter here if hash is attributed to a sequence that is in the NS
    # if hash_presence['boolean'] is True:

    #    hashed_sequence = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                                   (sq.ASK_SEQUENCE_HASH_SEQ.format(new_seq_url, sequence)))

    # WARNING: there was a hash collision, two different sequences have the same hash
    #    if hashed_sequence['boolean'] is False:
    #        return {'HASH COLLISION': ('Found hash collision. New sequence has same hash as sequence at URI {0}.\n{1}'.format(new_seq_url, sequence))}, 409

    # if the sequence already exists in the NS
    if hash_presence["boolean"]:
        # celery task
        # task = add_allele.apply(
        #     args=[
        #         locus_url,
        #         species_name,
        #         loci_id,
        #         user_url,
        #         new_seq_url,
        #         False,
        #         sequence,
        #         allele_uri,
        #     ]
        # )

        print("before celery", flush=True)

        task = celery_app.send_task(
            "app.tasks.add_allele",
            args=[
                locus_url,
                species_name,
                loci_id,
                user_url,
                new_seq_url,
                False,
                sequence,
                allele_uri,
            ],
        )

    # if there is no sequence with that hash
    else:
        # celery task
        # task = add_allele.apply(
        #     args=[
        #         locus_url,
        #         species_name,
        #         loci_id,
        #         user_url,
        #         new_seq_url,
        #         True,
        #         sequence,
        #         allele_uri,
        #     ]
        # )

        # print("before celery", flush=True)

        task = celery_app.send_task(
            "app.tasks.add_allele",
            args=[
                locus_url,
                species_name,
                loci_id,
                user_url,
                new_seq_url,
                True,
                sequence,
                allele_uri,
            ],
        )

    # get POST message
    time.sleep(2)
    process_result = task.result
    # print(task, flush=True)

    # ola = celery_app.AsyncResult(task.id)
    # print(ola.result, flush=True)
    # process_result = "Done"

    return process_result


async def get_loci_allele_id(loci_id, allele_id):
    """
    Gets a particular allele from a particular loci
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    allele_url = "{0}loci/{1}/alleles/{2}".format(
        os.environ.get("BASE_URL"), loci_id, allele_id
    )

    # check if provided loci id exists
    locus_url = allele_url.split("/alleles")[0]

    # result_loci = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             sq.ASK_LOCUS.format(locus_url))

    result_loci = await client.query(sq.ASK_LOCUS.format(locus_url))

    if not result_loci["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Specified locus does not exist.",
        )

    # get information on allele, sequence, submission date, id and number of isolates with this allele

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_ALLELE_INFO.format(current_app.config['DEFAULTHGRAPH'], allele_url)))

    result = await client.query(
        sq.SELECT_ALLELE_INFO.format(
            os.environ.get("DEFAULT_GRAPH"), allele_url
        )
    )

    await client.close()

    allele_info = result["results"]["bindings"]
    if allele_info == []:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No allele found with the provided id.",
        )
    else:
        return {"result": allele_info}


async def delete_loci_allele_id(loci_id, allele_id):

    results = await rm_functions.rm_alleles(
        allele_id,
        loci_id,
        os.environ.get("DEFAULT_GRAPH"),
        os.environ.get("LOCAL_SPARQL"),
        os.environ.get("BASE_URL"),
        os.environ.get("VIRTUOSO_USER"),
        os.environ.get("VIRTUOSO_PASS"),
    )

    return results
