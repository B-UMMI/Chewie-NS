import os
import time
import pickle
import shutil
import hashlib
import zipfile
import datetime as dt

# import typing as t
from fastapi import HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from aiosparql.client import SPARQLClient, SPARQLRequestFailed

from app.core.celery_app import celery_app
from app.api.dependencies import auxiliary_functions as aux
from app.api.dependencies import sparql_queries as sq

from app.api.dependencies import rm_functions

from SPARQLWrapper import SPARQLWrapper


async def get_species():
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))
    # check if user provided a species name
    # species_name = []

    # get single species or full species list
    # returns empty results if species does not exist in the NS
    query_end = "typon:name ?name. "

    result = await client.query(
        sq.SELECT_SPECIES.format(os.environ.get("DEFAULT_GRAPH"), query_end)
    )

    # Close SPARQLClient to avoid aiohttp warning about unclosed session
    await client.close()

    species_list = result["results"]["bindings"]
    if species_list == []:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species does not exists in the NS",
        )
    else:
        return {"result": result["results"]["bindings"]}


async def get_species_id(species_id):
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))
    species_url = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), species_id
    )

    # get species name and its schemas
    # returns empty list if there is no species with provided identifier
    result = await client.query(
        sq.SELECT_SPECIES_AND_SCHEMAS.format(
            os.environ.get("DEFAULT_GRAPH"), species_url
        )
    )

    await client.close()

    species_info = result["results"]["bindings"]
    if species_info == []:
        # return {'NOT FOUND': 'No species found with the provided ID.'}, 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No species found with the provided ID.",
        )
    else:
        return {"result": species_info}


async def create_species(species_name):
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))
    # client_uniprot = SPARQLClient(os.environ.get("UNIPROT_SPARQL"))

    # get taxon name from the post data
    taxon_name = str(species_name)

    # get total number of taxa already on the graph
    result = await client.query(
        sq.COUNT_TAXON.format(os.environ.get("DEFAULT_GRAPH"))
    )

    number_taxa = int(result["results"]["bindings"][0]["count"]["value"])

    # get the taxon id from uniprot, if not found return 404
    uniprot_query = sq.SELECT_UNIPROT_TAXON.format(taxon_name)

    # check if species exists on uniprot
    result2 = aux.get_data(
        SPARQLWrapper(os.environ.get("UNIPROT_SPARQL")), uniprot_query
    )

    # result2 = await client_uniprot.query(uniprot_query)

    # await client_uniprot.close()

    # print(result2, flush=True)

    try:
        uniprot_url = result2["results"]["bindings"][0]["taxon"]["value"]
    except:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Species name not found on uniprot. Please provide a valid species name or search at http://www.uniprot.org/taxonomy/",
        )

    # check if species already exists locally (typon)
    result = await client.query(sq.ASK_SPECIES_UNIPROT.format(uniprot_url))

    if result["boolean"]:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Species already added to the NS."
        )

    # species exists on uniprot, everything ok to create new species
    new_spec_url = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), str(number_taxa + 1)
    )

    data2send = sq.INSERT_SPECIES.format(
        os.environ.get("DEFAULT_GRAPH"), new_spec_url, uniprot_url, taxon_name
    )

    result = await client.update(data2send)

    # print(result, flush=True)

    # {'head': {'link': [],
    #  'vars': ['callret-0']},
    #  'results': {'distinct': False, 'ordered': True,
    #  'bindings': [{'callret-0': {'type': 'literal',
    #  'value': 'Insert into <http://localhost:8890/chewiens>,
    #  3 (or less) triples -- done'}}]}}

    # Close SPARQLClient to avoid aiohttp warning about unclosed session
    await client.close()

    return {"message": "{0} added to the NS.".format(taxon_name)}

    # if result.status_code in [200, 201]:
    #     return {'message': '{0} added to the NS.'.format(taxon_name)}, 201
    # else:
    #     return {'message': 'Could not add new taxon to the NS.',
    #             'error': result.text}, result.status_code


async def get_species_loci(species_id, prefix, sequence, locus_ori_name):
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # check if species exists
    species_url = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), species_id
    )

    result = await client.query(sq.ASK_SPECIES_NS.format(species_url))

    if not result["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="There is no species with provided ID.",
        )

    # sequence was provided, return the locus uri found that has the sequence
    if sequence is not None:

        sequence = sequence.upper()

        # Generate hash
        sequence_hash = hashlib.sha256(sequence.encode("utf-8")).hexdigest()

        # Query virtuoso
        sequence_uri = "{0}sequences/{1}".format(
            os.environ.get("BASE_URL"), sequence_hash
        )

        result = await client.query(
            sq.SELECT_LOCI_WITH_DNA.format(
                os.environ.get("DEFAULT_GRAPH"), sequence_uri, species_url
            )
        )

        res_loci = result["results"]["bindings"]
    else:

        result = await client.query(
            sq.SELECT_SPECIES_LOCI.format(
                os.environ.get("DEFAULT_GRAPH"), species_url
            )
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

    # if there are loci with the sequence, filter based on other arguments
    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="None of the loci in the NS meet the filtering criteria.",
        )


async def create_species_loci(species_id, locus_id):
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    spec_url = "{0}species/{1}".format(os.environ.get("BASE_URL"), species_id)

    # result_spec = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             (sq.ASK_SPECIES_NS.format(spec_url)))

    result_spec = await client.query(sq.ASK_SPECIES_NS.format(spec_url))

    if not result_spec["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Species not found.",
        )

    locus_id = str(locus_id)

    new_locus_url = "{0}loci/{1}".format(os.environ.get("BASE_URL"), locus_id)

    # result_locus = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             (sq.ASK_LOCUS.format(new_locus_url)))

    result_locus = await client.query(sq.ASK_LOCUS.format(new_locus_url))

    if not result_locus["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Species not found.",
        )

    # Associate locus to species
    query2send = (
        "INSERT DATA IN GRAPH <{0}> "
        "{{ <{1}> a typon:Locus; typon:isOfTaxon <{2}> .}}".format(
            os.environ.get("DEFAULT_GRAPH"), new_locus_url, spec_url
        )
    )

    # result = aux.send_data(query2send,
    #                         current_app.config['LOCAL_SPARQL'],
    #                         current_app.config['VIRTUOSO_USER'],
    #                         current_app.config['VIRTUOSO_PASS'])

    result = await client.update(query2send)

    # Close SPARQLClient to avoid aiohttp warning about unclosed session
    await client.close()

    return {"message": "New locus added to species." + str(species_id)}

    # if result.status_code in [200, 201]:
    #     return {"message": "New locus added to species." + str(species_id)}, 201
    # else:
    #     return {"message": "Could not add locus to species."}, result.status_code


async def delete_species_loci(species_id, loci_id, request_type):

    results = await rm_functions.rm_loci_links(
        "splinks",
        loci_id,
        os.environ.get("DEFAULT_GRAPH"),
        os.environ.get("LOCAL_SPARQL"),
        os.environ.get("BASE_URL"),
        os.environ.get("VIRTUOSO_USER"),
        os.environ.get("VIRTUOSO_PASS"),
    )

    return results


async def get_species_schemas(species_id):
    """
    Get the schemas for a particular species ID
    """
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    species_url = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), species_id
    )

    # check if there is a species with provided identifier
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         sq.ASK_SPECIES_NS.format(species_url))

    result = await client.query(sq.ASK_SPECIES_NS.format(species_url))

    species_exists = result["boolean"]
    if species_exists is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="There is no species in the NS with the provided ID.",
        )

    # if there is a species with the ID, get all schemas for that species

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_SPECIES_SCHEMAS.format(current_app.config['DEFAULTHGRAPH'], species_url)))

    result = await client.query(
        sq.SELECT_SPECIES_SCHEMAS.format(
            os.environ.get("DEFAULT_GRAPH"), species_url
        )
    )

    species_schemas = result["results"]["bindings"]
    if species_schemas == []:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="There are no schemas for that species.",
        )
    else:
        return {"result": species_schemas}


async def create_species_schemas(species_id, create_schema, current_user):
    """
    Adds a new schema for a particular species ID
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # get the current user id
    c_user = current_user.id
    user_url = "{0}users/{1}".format(os.environ.get("BASE_URL"), c_user)

    # print(create_schema, flush=True)

    # schema name
    name = str(create_schema.name)
    # blast score ratio
    bsr = str(create_schema.bsr)
    # prodigal training file
    ptf = str(create_schema.prodigal_training_file)
    # translation table
    translation_table = str(create_schema.translation_table)
    # minimum locus length
    min_locus_len = str(create_schema.minimum_locus_length)
    # size threshold
    size_threshold = str(create_schema.size_threshold)
    # chewBBACA_version
    chewie_version = str(create_schema.chewBBACA_version)
    # clustering word_size
    word_size = str(create_schema.dict().get("word_size", "None"))
    # clustering cluster similarity threshold
    cluster_sim = str(create_schema.dict().get("cluster_sim", "None"))
    # clustering representative similarity exclusion threshold
    rep_filter = str(create_schema.dict().get("representative_filter", "None"))
    # clustering intra cluster similarity exclusion threshold
    intra_filter = str(create_schema.dict().get("intraCluster_filter", "None"))
    # schema description
    description = create_schema.dict().get("SchemaDescription", "None")
    # schema locking property
    schema_lock = user_url
    # schema files hashes
    schema_hashes = create_schema.dict().get("schema_hashes", None)

    # print(schema_hashes, flush=True)

    if "" in (
        name,
        bsr,
        ptf,
        translation_table,
        min_locus_len,
        chewie_version,
        word_size,
        cluster_sim,
        rep_filter,
        intra_filter,
        schema_hashes,
    ):
        raise HTTPException(
            status.HTTP_406_NOT_ACCEPTABLE,
            detail="No schema parameters specified.",
        )

    if schema_hashes is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Schema files hashes not provided.",
        )

    # check if species exists
    species_url = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), species_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         sq.ASK_SPECIES_NS.format(species_url))

    result = await client.query(sq.ASK_SPECIES_NS.format(species_url))

    if not result["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Species does not exist",
        )

    # check if a schema already exists with this name for this species
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.ASK_SCHEMA_DESCRIPTION.format(species_url, name)))

    result = await client.query(
        sq.ASK_SCHEMA_DESCRIPTION.format(species_url, name)
    )

    if result["boolean"]:

        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], species_url, name)))

        result = await client.query(
            sq.SELECT_SCHEMA.format(
                os.environ.get("DEFAULT_GRAPH"), species_url, name
            )
        )

        await client.close()

        schema_url = result["results"]["bindings"][0]["schema"]["value"]

        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="schema with that name already exists {0}".format(
                schema_url
            ),
        )

    # get schema with highest integer identifier
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_HIGHEST_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], species_url)))

    result = await client.query(
        sq.SELECT_HIGHEST_SCHEMA.format(
            os.environ.get("DEFAULT_GRAPH"), species_url
        )
    )

    highest_schema = result["results"]["bindings"]
    # if species has no schemas
    if highest_schema == []:
        schema_id = 1
    else:
        highest_schema = highest_schema[0]["schema"]["value"]
        highest_id = int(highest_schema.split("/")[-1])
        schema_id = highest_id + 1

    # Create the uri for the new schema
    new_schema_url = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # create new schema
    insertion_date = "singularity"
    query2send = sq.INSERT_SCHEMA.format(
        os.environ.get("DEFAULT_GRAPH"),
        new_schema_url,
        species_url,
        user_url,
        name,
        bsr,
        chewie_version,
        ptf,
        translation_table,
        min_locus_len,
        size_threshold,
        word_size,
        cluster_sim,
        rep_filter,
        intra_filter,
        insertion_date,
        insertion_date,
        schema_lock,
        description,
    )

    # result = aux.send_data(query2send,
    #                         current_app.config['LOCAL_SPARQL'],
    #                         current_app.config['VIRTUOSO_USER'],
    #                         current_app.config['VIRTUOSO_PASS'])

    try:

        result = await client.update(query2send)

        # save file with schema files hashes
        root_dir = os.path.abspath(os.environ.get("SCHEMA_UP"))

        # folder to hold temp files for schema insertion
        temp_dir = os.path.join(
            root_dir, "{0}_{1}".format(species_id, schema_id)
        )

        # create folder when uploading first file
        if os.path.isdir(temp_dir) is False:
            os.mkdir(temp_dir)

        # save file with schema hashes after schema is created
        hashes_file = os.path.join(
            temp_dir, "{0}_{1}_hashes".format(species_id, schema_id)
        )
        with open(hashes_file, "wb") as hf:
            schema_hashes = {
                k: [False, [False, False, False]] for k in schema_hashes
            }
            pickle.dump(schema_hashes, hf)

        return {
            "message": "A new schema for {0} was created sucessfully".format(
                species_url
            ),
            "url": new_schema_url,
        }

    except SPARQLRequestFailed as error:
        raise HTTPException(
            error.status, detail="Could not add new schema to the NS.",
        )
        # return {'message': 'Could not add new schema to the NS.'}

    # return {
    #     "message": "A new schema for {0} was created sucessfully".format(
    #         species_url
    #     ),
    #     "url": new_schema_url,
    # }

    # if result.status_code in [200, 201]:
    #     # save file with schema files hashes
    #     root_dir = os.path.abspath(os.environ.get('SCHEMA_UP'))

    #     # folder to hold temp files for schema insertion
    #     temp_dir = os.path.join(root_dir, '{0}_{1}'.format(species_id, schema_id))

    #     # create folder when uploading first file
    #     if os.path.isdir(temp_dir) is False:
    #         os.mkdir(temp_dir)

    #     # save file with schema hashes after schema is created
    #     hashes_file = os.path.join(temp_dir, '{0}_{1}_hashes'.format(species_id, schema_id))
    #     with open(hashes_file, 'wb') as hf:
    #         schema_hashes = {k:[False, [False, False, False]] for k in schema_hashes}
    #         pickle.dump(schema_hashes, hf)

    #     return {'message': 'A new schema for {0} was created sucessfully'.format(species_url),
    #             "url": new_schema_url}, 201
    # else:
    #     return {'message': 'Could not add new schema to the NS.'}, result.status_code


async def get_species_schemas_id(species_id, schema_id, current_user):
    """
    Return a particular schema for a particular species
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    user_id = current_user.id

    user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

    # check if there is a species with provided identifier
    species_url = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), species_id
    )

    result = await client.query(sq.ASK_SPECIES_NS.format(species_url))

    species_exists = result["boolean"]
    if species_exists is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="There is no species in the NS with the provided ID.",
        )

    # construct schema URI
    schema_url = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # check if schema is deprecated
    result = await client.query(sq.ASK_SCHEMA_DEPRECATED.format(schema_url))
    if result["boolean"] is True:
        # check user permissions, Admin can access deprecated schemas
        user_info = await client.query(
            sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_uri)
        )
        user_role = user_info["results"]["bindings"][0]["role"]["value"]

        if user_role != "Admin":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Schema is deprecated.",
            )

    # get schema info
    schema_info = await client.query(
        sq.SELECT_SPECIES_SCHEMA.format(
            os.environ.get("DEFAULT_GRAPH"), schema_url
        )
    )

    await client.close()

    schema_properties = schema_info["results"]["bindings"]

    if schema_properties != []:
        locking_status = schema_properties[0]["Schema_lock"]["value"]
        schema_properties[0]["Schema_lock"]["value"] = (
            "Locked" if locking_status != "Unlocked" else locking_status
        )
        return schema_properties
    else:
        return schema_properties


async def delete_species_schema(species_id, schema_id, request_type):

    results = await rm_functions.rm_schema(
        str(schema_id),
        str(species_id),
        os.environ.get("DEFAULT_GRAPH"),
        os.environ.get("LOCAL_SPARQL"),
        os.environ.get("BASE_URL"),
        os.environ.get("VIRTUOSO_USER"),
        os.environ.get("VIRTUOSO_PASS"),
    )

    return results


async def deprecate_species_schema(species_id, schema_id, current_user):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    user_id = current_user.id

    user_url = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

    # check if schema exists
    schema_url = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.ASK_SCHEMA_OWNERSHIP.format(schema_url, user_url)))

    result = await client.query(
        sq.ASK_SCHEMA_OWNERSHIP.format(schema_url, user_url)
    )

    if not result["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find schema with provided ID or schema is not administrated by current user.",
        )
        # return {'message': 'Could not find schema with provided ID or schema is not administrated by current user.'}, 404

    # add a triple to the link between the schema and the locus implying that the locus is deprecated for that schema
    query2send = sq.INSERT_SCHEMA_DEPRECATE.format(
        os.environ.get("DEFAULT_GRAPH"), schema_url
    )

    # result = aux.send_data(query2send,
    #                         current_app.config['LOCAL_SPARQL'],
    #                         current_app.config['VIRTUOSO_USER'],
    #                         current_app.config['VIRTUOSO_PASS'])

    result = await client.update(query2send)

    # Close SPARQLClient to avoid aiohttp warning about unclosed session
    await client.close()

    return {"message": "Schema sucessfully removed."}

    # if result.status_code in [200, 201]:
    #     return {'message': 'Schema sucessfully removed.'}, 201
    # else:
    #     return {'message': 'Sum Thing Wong.'}, result.status_code


async def schema_admin(species_id, schema_id, current_user):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    user_id = current_user.id

    user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.ASK_SCHEMA_OWNERSHIP.format(schema_uri, user_uri)))

    result = await client.query(
        sq.ASK_SCHEMA_OWNERSHIP.format(schema_uri, user_uri)
    )

    await client.close()

    administers = result["boolean"]

    res = {"administers": administers}

    return res


async def modification_date(species_id, schema_id):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_SCHEMA_DATE.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    result = await client.query(
        sq.SELECT_SCHEMA_DATE.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )

    await client.close()

    result_data = result["results"]["bindings"]
    if len(result_data) == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a schema with provided ID.",
        )

    schema_name = result_data[0]["name"]["value"]
    last_modified = result_data[0]["last_modified"]["value"]

    return {
        "modified": "Schema {0} ({1}) last modified on: {2}".format(
            schema_id, schema_name, last_modified
        )
    }


async def enforce_locking(user_role, user_uri, locking_value):
    """Enforce role permissions on users, in order to
    modify data.

    Parameters
    ----------
    user_role: str
        Role of a user.
    user_uri: str
        URI of a user.
    locking_value:

    Returns
    -------
    allow: list
        A list that contains:
            - bool, True if user has persmissions
              False otherwise.
            - dict, JSON format dict containing message
              detailing if the user is allowed or not
              to modify a schema.

    """

    allow = [True, user_role]
    if user_role not in ["Admin", "Contributor"]:
        allow = [False, "must have Admin or Contributor permissions."]

    # if user is a Contributor, check if it is the one that locked the schema
    if user_role == "Contributor" and user_uri != locking_value:
        allow = [
            False,
            "must have Admin permissions or be the Contributor that is altering the schema.",
        ]

    return allow


async def change_mod_date(species_id, schema_id, date, current_user):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    user_id = current_user.id

    user_url = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_url)))

    result = await client.query(
        sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_url)
    )

    # create schema URI
    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    user_role = result["results"]["bindings"][0]["role"]["value"]

    # get schema locking status
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    result = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )

    # get post data
    # post_data = request.get_json()

    result_data = result["results"]["bindings"]
    if len(result_data) == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a schema with provided ID.",
        )
        # return {'Not found': 'Could not find a schema with provided ID.'}, 404

    lock_state = result_data[0]["Schema_lock"]["value"]
    permission = await enforce_locking(user_role, user_url, lock_state)
    if permission[0] is not True:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail=permission[1],
        )
        # return permission[1], 403

    date = str(date.date)
    # check if date is in a valid date format
    try:
        dt.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Please provide a date in format Y-M-DTH:M:S",
        )
        # return {'Invalid Argument': 'Invalid date format. Please provide a date in format Y-M-DTH:M:S'}, 400

    # get schema info
    # schema_info = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             (sq.SELECT_SPECIES_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    schema_info = await client.query(
        sq.SELECT_SPECIES_SCHEMA.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )

    # print(schema_info, flush=True)

    schema_properties = schema_info["results"]["bindings"]

    dateEntered = schema_properties[0]["dateEntered"]["value"]

    # print(dateEntered, flush=True)

    # first delete current modification date value
    delprop_query = sq.DELETE_SCHEMA_DATE.format(
        os.environ.get("DEFAULT_GRAPH"), schema_uri, "last_modified"
    )

    # delprop_result = aux.send_data(delprop_query,
    #                                 current_app.config['LOCAL_SPARQL'],
    #                                 current_app.config['VIRTUOSO_USER'],
    #                                 current_app.config['VIRTUOSO_PASS'])

    delprop_result = await client.update(delprop_query)

    # print(delprop_result, flush=True)

    # insert new value
    query2send = sq.INSERT_SCHEMA_DATE.format(
        os.environ.get("DEFAULT_GRAPH"), schema_uri, "last_modified", date
    )

    # last_modified_result = aux.send_data(query2send,
    #                                         current_app.config['LOCAL_SPARQL'],
    #                                         current_app.config['VIRTUOSO_USER'],
    #                                         current_app.config['VIRTUOSO_PASS'])

    try:
        last_modified_result = await client.update(query2send)

        # print(last_modified_result, flush=True)

        # check insertion date
        if dateEntered == "singularity":
            delprop_query = sq.DELETE_SCHEMA_DATE.format(
                os.environ.get("DEFAULT_GRAPH"), schema_uri, "dateEntered"
            )

            # delprop_result = aux.send_data(delprop_query,
            #                                 current_app.config['LOCAL_SPARQL'],
            #                                 current_app.config['VIRTUOSO_USER'],
            #                                 current_app.config['VIRTUOSO_PASS'])

            delprop_result = await client.update(delprop_query)

            # insert new value
            query2send = sq.INSERT_SCHEMA_DATE.format(
                os.environ.get("DEFAULT_GRAPH"), schema_uri, "dateEntered", date
            )

            # date_entered_result = aux.send_data(query2send,
            #                                     current_app.config['LOCAL_SPARQL'],
            #                                     current_app.config['VIRTUOSO_USER'],
            #                                     current_app.config['VIRTUOSO_PASS'])

            date_entered_result = await client.update(query2send)

        await client.close()

        return {"result": "Changed schema modification date."}

    except SPARQLRequestFailed as error:
        await client.close()
        return {"message": "Could not change schema modification date."}

    # if last_modified_result.status_code in [200, 201]:
    #     return {'message': 'Changed schema modification date.'}, 201
    # else:
    #     return {'message': 'Could not change schema modification date.'}, last_modified_result.status_code


async def schema_lock_status(species_id, schema_id):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    result = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )

    result_data = result["results"]["bindings"]
    if len(result_data) == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a schema with provided ID.",
        )
        # return {'Not found': 'Could not find a schema with provided ID.'}, 404

    schema_name = result_data[0]["name"]["value"]
    locking_value = result_data[0]["Schema_lock"]["value"]

    await client.close()

    if locking_value == "Unlocked":
        return "Schema {0} ({1}) status: *unlocked*.".format(
            str(schema_id), schema_name
        )
    else:
        return "Schema {0} ({1}) status: [locked].".format(
            str(schema_id), schema_name
        )


async def change_schema_lock_status(
    species_id, schema_id, action, current_user
):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    user_id = current_user.id

    user_url = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_url)))

    result = await client.query(
        sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_url)
    )

    # create schema URI
    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    user_role = result["results"]["bindings"][0]["role"]["value"]

    # get schema locking status
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    result = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )

    # get post data
    # post_data = request.get_json()

    result_data = result["results"]["bindings"]
    if len(result_data) == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a schema with provided ID.",
        )
        # return {'Not found': 'Could not find a schema with provided ID.'}, 404

    lock_state = result_data[0]["Schema_lock"]["value"]

    # action = post_data['action']
    action = str(action.action)
    if action == "lock":
        lock_token = user_url
        if lock_state == "Unlocked":

            try:
                # first delete Schema_lock property value
                delprop_query = sq.DELETE_SCHEMA_LOCK.format(
                    os.environ.get("DEFAULT_GRAPH"), schema_uri
                )

                # delprop_result = aux.send_data(delprop_query,
                #                                 current_app.config['LOCAL_SPARQL'],
                #                                 current_app.config['VIRTUOSO_USER'],
                #                                 current_app.config['VIRTUOSO_PASS'])

                delprop_result = await client.update(delprop_query)

                # insert new value
                query2send = sq.INSERT_SCHEMA_LOCK.format(
                    os.environ.get("DEFAULT_GRAPH"), schema_uri, lock_token
                )

                # result = aux.send_data(query2send,
                #                         current_app.config['LOCAL_SPARQL'],
                #                         current_app.config['VIRTUOSO_USER'],
                #                         current_app.config['VIRTUOSO_PASS'])

                result = await client.update(query2send)

                await client.close()

                return {"message": "Schema sucessfully locked/unlocked."}

            except SPARQLRequestFailed as error:
                await client.close()
                return {"message": "Could not lock/unlock schema."}
        else:
            return {"message": "Schema already locked."}

    elif action == "unlock":
        unlock_token = "Unlocked"
        if lock_state == "Unlocked":
            return {"message": "Schema already unlocked."}
        else:
            # verify user identity and role
            if user_role != "Admin" and user_url != lock_state:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    detail="Only Admin or user that locked the schema may unlock it.",
                )
                # return {'Not authorized': 'Only Admin or user that locked the schema may unlock it.'}, 403

            try:

                # first delete Schema_lock property value
                delprop_query = sq.DELETE_SCHEMA_LOCK.format(
                    os.environ.get("DEFAULT_GRAPH"), schema_uri
                )
                # delprop_result = aux.send_data(delprop_query,
                #                                 current_app.config['LOCAL_SPARQL'],
                #                                 current_app.config['VIRTUOSO_USER'],
                #                                 current_app.config['VIRTUOSO_PASS'])

                delprop_result = await client.update(delprop_query)

                # insert new value
                query2send = sq.INSERT_SCHEMA_LOCK.format(
                    os.environ.get("DEFAULT_GRAPH"), schema_uri, unlock_token
                )

                # result = aux.send_data(query2send,
                #                         current_app.config['LOCAL_SPARQL'],
                #                         current_app.config['VIRTUOSO_USER'],
                #                         current_app.config['VIRTUOSO_PASS'])

                result = await client.update(query2send)

                await client.close()

                return {"message": "Schema sucessfully locked/unlocked."}

            except SPARQLRequestFailed as error:
                await client.close()
                return {"message": "Could not lock/unlock schema."}

    # if result.status_code in [200, 201]:
    #     return {"message": "Schema sucessfully locked/unlocked."}, 201
    # else:
    #     return {"message": "Could not lock/unlock schema."}, result.status_code


async def get_ptf_hash(species_id, schema_id):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # create schema URI
    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # get the prodigal training file hash
    # ptf_query = aux.get_data(SPARQLWrapper(os.environ.get("LOCAL_SPARQL")),
    #                             (sq.SELECT_SCHEMA_PTF.format(os.environ.get('DEFAULT_GRAPH'), schema_uri)))

    ptf_query = await client.query(
        sq.SELECT_SCHEMA_PTF.format(os.environ.get("DEFAULT_GRAPH"), schema_uri)
    )

    ptf_hash = ptf_query["results"]["bindings"][0]["ptf"]["value"]

    root_dir = os.path.abspath(os.environ.get("SCHEMAS_PTF"))

    await client.close()

    ptf_file = {"hash": ptf_hash, "root_dir": root_dir}

    return ptf_file


async def upload_ptf_file(species_id, schema_id, ptf_file):
    """Upload the Prodigal training file for the specified schema."""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    root_dir = os.path.abspath(os.environ.get("SCHEMAS_PTF"))

    filename = ptf_file.filename

    # check if training file hash is the one associated with the schema
    # create schema URI
    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # get the prodigal training file hash
    # ptf_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             (sq.SELECT_SCHEMA_PTF.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    ptf_query = await client.query(
        sq.SELECT_SCHEMA_PTF.format(os.environ.get("DEFAULT_GRAPH"), schema_uri)
    )

    await client.close()

    ptf_hash = ptf_query["results"]["bindings"][0]["ptf"]["value"]
    if filename != ptf_hash:
        raise HTTPException(
            status.HTTP_406_NOT_ACCEPTABLE,
            detail="Provided training file is not the one associated with the specified schema.",
        )
        # return {'Not acceptable': 'Provided training file is not the one associated with the specified schema.'}, 406

    # list training files in the NS
    ns_ptfs = os.listdir(root_dir)
    if filename in ns_ptfs:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Provided training file is already in the NS.",
        )
        # return {'Conflict': 'Provided training file is already in the NS.'}, 409
    else:
        with open(os.path.join(root_dir, filename), "wb") as buffer:
            shutil.copyfileobj(ptf_file.file, buffer)

        # file.save(os.path.join(root_dir, filename))

        return {"message": "Received new Prodigal training file."}


async def get_zip_file(species_id, schema_id, request_type):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # check if schema is locked
    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                                     (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    locking_status_query = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )

    locking_status = locking_status_query["results"]["bindings"]
    if len(locking_status) == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a schema with specified ID.",
        )
        # return {'Not found': 'Could not find a schema with specified ID.'}, 404

    locking_status = locking_status[0]["Schema_lock"]["value"]

    await client.close()

    if locking_status != "Unlocked":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Schema is locked.",
        )
        # return {'Unauthorized': 'Schema is locked.'}, 403

    zip_prefix = "{0}_{1}".format(species_id, schema_id)

    root_dir = os.path.abspath(os.environ.get("SCHEMAS_ZIP"))

    schema_zip = [
        z for z in os.listdir(root_dir) if z.startswith(zip_prefix) is True
    ]

    if len(schema_zip) == 1 and ".zip" in schema_zip[0]:

        if request_type == "check":
            return {"zip_file": schema_zip}

        elif request_type == "download":
            return FileResponse(
                os.path.join(root_dir, schema_zip[0]),
                media_type="application/zip",
                filename=schema_zip[0],
            )
            # return send_from_directory(
            #     root_dir, schema_zip[0], as_attachment=True
            # )

    elif (len(schema_zip) == 1 and ".zip" not in schema_zip[0]) or len(
        schema_zip
    ) > 1:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="A new compressed version of the schema is being created. Please try again later.",
        )
        # return {'Working': 'A new compressed version of the schema is being created. Please try again later.'}, 403

    elif len(schema_zip) == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a compressed version of specified schema.",
        )
        # return {'Not found': 'Could not find a compressed version of specified schema.'}, 404


async def compress_zip(species_id, schema_id, current_user):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    user_id = current_user.id

    user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri)))

    result = await client.query(
        sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_uri)
    )

    user_role = result["results"]["bindings"][0]["role"]["value"]

    await client.close()

    # check if schema is locked
    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                                     (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    locking_status_query = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )

    locking_status = locking_status_query["results"]["bindings"]
    if len(locking_status) == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a schema with specified ID.",
        )
        # return {'Not found': 'Could not find a schema with specified ID.'}, 404

    # if the schema is locked only the Admin or the Contributor
    # that locked the schema may give the order
    locking_status = locking_status[0]["Schema_lock"]["value"]
    if locking_status != "Unlocked":
        permission = aux.enforce_locking(user_role, user_uri, locking_status)
        if permission[0] is not True:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail=permission[1],
            )
            # return permission[1], 403

    # add '&' at the end so that it will not wait for process to finish
    # compress_cmd = ('python schema_compressor.py -m single '
    #                 '--sp {0} --sc {1} &'.format(species_id, schema_id))
    # os.system(compress_cmd)

    return {"message": "Schema will be compressed by the NS."}


async def get_description_file(species_id, schema_id, request_type):
    """Downloads file with the description for the specified schema."""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    root_dir = os.path.abspath(os.environ.get("PRE_COMPUTE"))

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_SCHEMA_DESCRIPTION.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    result = await client.query(
        sq.SELECT_SCHEMA_DESCRIPTION.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )

    schema_description = result["results"]["bindings"]

    await client.close()

    if len(schema_description) > 0:
        schema_description = schema_description[0]["description"]["value"]
    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Schema has no description or does not exist.",
        )
        # return {'Not found': 'Schema has no description or does not exist.'}, 404

    # determine if description file exists
    files = os.listdir(root_dir)

    if schema_description in files:
        if request_type == "download":
            return FileResponse(
                os.path.join(root_dir, schema_description),
                media_type="text/plain",
                filename=schema_description,
            )
            # return send_from_directory(
            #     root_dir, schema_description, as_attachment=True
            # )
        elif request_type == "check":
            description_file = "{0}/{1}".format(root_dir, schema_description)
            # print(description_file, flush=True)
            file_handle = open(description_file, "rb")
            file_contents = file_handle.read()
            file_contents_decoded = file_contents.decode()
            # print(file_contents_decoded, flush=True)
            response = {"description": file_contents_decoded}
            file_handle.close()
            return response
    elif len(schema_description) == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a description for specified schema.",
        )
        # return (
        #     {"Not found": "Could not find a description for specified schema."},
        #     404,
        # )


async def upload_description_file(
    species_id, schema_id, description_file, current_user
):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    user_id = current_user.id

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # check the role of the user that is trying to access
    user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), user_id)

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri)))

    result = await client.query(
        sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_uri)
    )

    user_role = result["results"]["bindings"][0]["role"]["value"]

    # only add description if user is Admin or Contributor that created the schema
    if "Admin" not in user_role:
        # only the Contributor that started schema upload might add a description
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.ASK_SCHEMA_OWNERSHIP.format(schema_uri, user_uri)))

        result = await client.query(
            sq.ASK_SCHEMA_OWNERSHIP.format(schema_uri, user_uri)
        )

        if not result["boolean"]:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Schema is not administrated by current user.",
            )
            # return {'message': 'Schema is not administrated by current user.'}, 403

        # only add description if schema has not been fully uploaded
        # date_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.ASK_SCHEMA_DATE.format(schema_uri, 'dateEntered', 'singularity')))

        date_result = await client.query(
            sq.ASK_SCHEMA_DATE.format(schema_uri, "dateEntered", "singularity")
        )

        if date_result["boolean"] is False:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Cannot change description of schema that has been fully uploaded.",
            )
            # return {'message': 'Cannot change description of schema that has been fully uploaded.'}, 403

    await client.close()

    # save file with description
    root_dir = os.path.abspath(os.environ.get("PRE_COMPUTE"))

    # get file with schema description from POST data
    # file = request.files["file"]
    filename = description_file.filename

    # save file
    file_path = os.path.join(root_dir, filename)
    # file.save(file_path)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(description_file.file, buffer)

    return {"message": "Schema description received."}


async def get_schema_loci_data(species_id, schema_id, local_date, ns_date):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # check if there is a species with provided identifier
    species_url = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), species_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         sq.ASK_SPECIES_NS.format(species_url))

    result = await client.query(sq.ASK_SPECIES_NS.format(species_url))

    species_exists = result["boolean"]
    if species_exists is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="There is no species in the NS with the provided ID.",
        )
        # return {'NOT FOUND': 'There is no species in the NS with the provided ID.'}, 404

    # check if schema exists or is deprecated
    schema_url = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.ASK_SCHEMA.format(schema_url)))

    result = await client.query(sq.ASK_SCHEMA.format(schema_url))

    if result["boolean"] is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Schema not found.",
        )
        # return {"message": "Schema not found."}, 404

    # if date is provided the request returns the alleles that were added after that specific date for all loci
    # else the request returns the list of loci
    # a correct request returns also the server date at which the request was done
    if local_date is not None:

        # query all alleles for the loci of the schema since a specific date, sorted from oldest to newest (limit of max 50k records)
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_SCHEMA_LATEST_FASTA.format(current_app.config['DEFAULTHGRAPH'], schema_url,
        #                                                             request_data['local_date'], request_data['ns_date'])))

        result = await client.query(
            sq.SELECT_SCHEMA_LATEST_FASTA.format(
                os.environ.get("DEFAULT_GRAPH"), schema_url, local_date, ns_date
            )
        )

        await client.close()

        new_alleles = result["results"]["bindings"]
        number_of_alleles = len(new_alleles)

        # if there are no new alleles
        if number_of_alleles == 0:

            response = StreamingResponse(
                aux.generate("newAlleles", new_alleles),
                media_type="application/json",
            )
            # if there are no alleles, return server date information
            response.headers.set("Server-Date", ns_date)
        else:
            # get the allele with the latest date from all retrieved alleles
            latest_allele = new_alleles[-1]

            # get allele date
            latest_datetime = latest_allele["date"]["value"]

            response = StreamingResponse(
                aux.generate("newAlleles", new_alleles),
                headers={"Last-Allele": latest_datetime},
                media_type="application/json",
            )
            # response.headers.set("Last-Allele", latest_datetime)

        return response

    # if no date provided, query for all loci for the schema
    else:

        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_SCHEMA_LOCI.format(current_app.config['DEFAULTHGRAPH'], schema_url)))

        result = await client.query(
            sq.SELECT_SCHEMA_LOCI.format(
                os.environ.get("DEFAULT_GRAPH"), schema_url
            )
        )

        # check if schema has loci
        loci_list = result["results"]["bindings"]
        if loci_list == []:
            return {"message": "Schema exists but does not have loci yet."}

        # return all loci in stream mode
        latestDatetime = str(dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"))
        headers = {"Server-Date": latestDatetime}
        r = StreamingResponse(
            aux.generate("Loci", loci_list),
            media_type="application/json",
            headers=headers,
        )
        # r.headers.set("Server-Date", latestDatetime)

        return r


async def post_schema_loci_data(species_id, schema_id, loci_id, current_user):
    """Add loci to a particular schema of a particular species."""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # get user id
    c_user = current_user.id

    # check if schema exists
    schema_url = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         sq.ASK_SCHEMA_DEPRECATED2.format(schema_url))

    result = await client.query(sq.ASK_SCHEMA_DEPRECATED2.format(schema_url))

    if result["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Schema not found.",
        )
        # return {'message': 'Schema not found.'}, 404

    # determine if schema is locked
    # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                                     (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_url)))
    locking_status_query = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_url
        )
    )
    locking_status = locking_status_query["results"]["bindings"][0][
        "Schema_lock"
    ]["value"]

    # if schema is locked, enforce condition that only the Admin
    # or the Contributor that locked the schema may get the FASTA sequences
    if locking_status != "Unlocked":
        # check the role of the user that is trying to access
        user_url = "{0}users/{1}".format(os.environ.get("BASE_URL"), c_user)

        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_url)))

        result = await client.query(
            sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_url)
        )

        await client.close()

        user_role = result["results"]["bindings"][0]["role"]["value"]
        allow = aux.enforce_locking(user_role, user_url, locking_status)
        if allow[0] is False:
            return allow[1], 403

    # # get post data
    # request_data = request.get_json()

    # check if locus exists
    # loci_id = str(request_data['loci_id'])
    new_locus_url = "{0}loci/{1}".format(
        os.environ.get("BASE_URL"), str(loci_id.loci_id)
    )

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         ('ASK where {{ <{0}> a typon:Locus}}'.format(new_locus_url)))

    result = await client.query(
        "ASK where {{ <{0}> a typon:Locus}}".format(new_locus_url)
    )

    if not result["boolean"]:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find locus with provided ID.",
        )
        # return {'message': 'Could not find locus with provided ID.'}, 404

    # check if locus already exists on schema
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.ASK_SCHEMA_LOCUS.format(schema_url, new_locus_url)))

    result = await client.query(
        sq.ASK_SCHEMA_LOCUS.format(schema_url, new_locus_url)
    )

    if result["boolean"]:
        # raise HTTPException(
        #     status.HTTP_404_NOT_FOUND,
        #     detail="Could not find locus with provided ID.",
        # )
        return {
            "message": "Locus already on schema",
            "locus_url": new_locus_url,
            "status": 409,
        }

    await client.close()

    # get the number of loci on schema and build the uri based on that number+1 , using a celery queue
    # task = add_locus_schema.apply(args=[schema_url, new_locus_url])
    task = celery_app.send_task(
        "app.tasks.add_locus_schema", args=[schema_url, new_locus_url]
    )

    time.sleep(1)
    process_result = task.result

    print(process_result, flush=True)

    process_ran = task.ready()
    process_sucess = task.status

    if process_ran and process_sucess == "SUCCESS":
        pass
    else:
        return {
            "status: "
            + process_sucess
            + " run: "
            + str(process_ran)
            + " status_code: "
            + "400"
        }

    # celery results
    new_allele_url = process_result[0]
    process_result_status_code = int(process_result[-1])

    if process_result_status_code > 201:
        # check if process was sucessfull
        return (
            {
                "message": "Could not add locus to schema.",
                "status": process_result_status_code,
            },
        )
    else:
        response_dict = {
            **new_allele_url,
            "status_code": process_result_status_code,
        }
        return response_dict
        # return new_allele_url, process_result_status_code


async def get_schema_loci_data_2(species_id, schema_id):
    """"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    species_uri = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), species_id
    )

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # check if schema has been fully uploaded
    # date_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             (sq.ASK_SCHEMA_DATE.format(schema_uri, 'dateEntered', 'singularity')))

    date_result = await client.query(
        sq.ASK_SCHEMA_DATE.format(schema_uri, "dateEntered", "singularity")
    )

    if not date_result["boolean"]:
        return {"message": "Schema has been fully uploaded."}, 200

    root_dir = os.path.abspath(os.environ.get("SCHEMA_UP"))

    # folder to hold files with alleles to insert
    temp_dir = os.path.join(root_dir, "{0}_{1}".format(species_id, schema_id))

    # check if temp folder exists
    if os.path.isdir(temp_dir) is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="There is no temp folder for specified schema.",
        )
        # return {'message': 'There is no temp folder for specified schema.'}, 404

    # count number of loci in Chewie-NS
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #             (sq.COUNT_TOTAL_LOCI.format(current_app.config['DEFAULTHGRAPH'])))
    result = await client.query(
        sq.COUNT_TOTAL_LOCI.format(os.environ.get("DEFAULT_GRAPH"))
    )
    nr_loci = result["results"]["bindings"][0]["count"]["value"]
    # links to species
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #             (sq.COUNT_SPECIES_LOCI.format(os.environ.get('DEFAULT_GRAPH'), species_uri)))
    result = await client.query(
        sq.COUNT_SPECIES_LOCI.format(
            os.environ.get("DEFAULT_GRAPH"), species_uri
        )
    )
    sp_loci = result["results"]["bindings"][0]["count"]["value"]
    # links to schema
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #             (sq.COUNT_SCHEMA_LOCI.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))
    result = await client.query(
        sq.COUNT_SCHEMA_LOCI.format(os.environ.get("DEFAULT_GRAPH"), schema_uri)
    )
    sc_loci = result["results"]["bindings"][0]["count"]["value"]

    filename = os.path.join(
        temp_dir, "{0}_{1}_hashes".format(species_id, schema_id)
    )
    file_path = os.path.join(temp_dir, filename)
    # check if file with schema files hashes exists
    if os.path.isfile(file_path) is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find file with schema hashes.",
        )
        # return {'Not found': 'Could not find file with schema hashes.'}, 404
    else:
        with open(file_path, "rb") as hf:
            schema_hashes = pickle.load(hf)

        inserted = []
        for k, v in schema_hashes.items():
            inserted.extend(v[1])

        inserted = set(inserted)
        if False not in inserted:
            return (
                {
                    "status": "complete",
                    "hashes": schema_hashes,
                    "nr_loci": nr_loci,
                    "sp_loci": sp_loci,
                    "sc_loci": sc_loci,
                },
                201,
            )
        else:
            return (
                {
                    "status": "incomplete",
                    "hashes": schema_hashes,
                    "nr_loci": nr_loci,
                    "sp_loci": sp_loci,
                    "sc_loci": sc_loci,
                },
                201,
            )


async def post_schema_loci_data_r(
    species_id, schema_id, temp_file, current_user
):
    """"""
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    c_user = current_user.id

    species_uri = "{0}species/{1}".format(
        os.environ.get("BASE_URL"), species_id
    )

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # check if schema has been fully uploaded
    # date_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             (sq.ASK_SCHEMA_DATE.format(schema_uri, 'dateEntered', 'singularity')))

    date_result = await client.query(
        sq.ASK_SCHEMA_DATE.format(schema_uri, "dateEntered", "singularity")
    )

    if not date_result["boolean"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Cannot add loci after schema has been fully uploaded.",
        )
        # return {'message': 'Cannot add loci after schema has been fully uploaded.'}, 403

    # determine if schema is locked
    # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                                     (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    locking_status_query = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )
    locking_status = locking_status_query["results"]["bindings"][0][
        "Schema_lock"
    ]["value"]

    if locking_status != "Unlocked":
        # check the role of the user that is trying to access
        user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), c_user)

        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri)))

        result = await client.query(
            sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_uri)
        )

        user_role = result["results"]["bindings"][0]["role"]["value"]

        allow = aux.enforce_locking(user_role, user_uri, locking_status)

        if allow[0] is False:
            return allow[1], 403

    root_dir = os.path.abspath(os.environ.get("SCHEMA_UP"))
    # folder to hold files with alleles to insert
    temp_dir = os.path.join(root_dir, "{0}_{1}".format(species_id, schema_id))

    # get the list of schema loci
    hashes_file = os.path.join(
        temp_dir, "{0}_{1}_hashes".format(species_id, schema_id)
    )
    with open(hashes_file, "rb") as hf:
        loci_hashes = pickle.load(hf)
        # determine incomplete cases
        loci_hashes = {k: v for k, v in loci_hashes.items() if False in v[1]}

    # check if all loci data has been inserted
    # if len(loci_hashes) == 0:
    #    return {'message': 'All loci were previously inserted and linked to species and schema.'}, 201

    # get file from POST data
    # file = request.files['file']
    filename = temp_file.filename

    # save file in schema temporary directory
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(temp_dir.file, buffer)
    # file.save(file_path)

    # uncompress ZIP
    with zipfile.ZipFile(file_path) as zf:
        zf.extractall(temp_dir)

    # get loci insert data
    loci_file = file_path.split(".zip")[0]
    with open(loci_file, "rb") as lf:
        loci_data = pickle.load(lf)

    # check if all loci belong to schema
    local_loci = set([l[1] for l in loci_data[1]])
    ns_loci = set(list(loci_hashes.keys()))

    valid = ns_loci - local_loci
    if len(valid) > 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Loci list sent does not match schema loci list.",
        )
        # return {'message': 'Loci list sent does not match schema loci list.'}, 400
    elif len(valid) == 0:

        # count number of loci in Chewie-NS
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #             (sq.COUNT_TOTAL_LOCI.format(current_app.config['DEFAULTHGRAPH'])))

        result = await client.query(
            sq.COUNT_TOTAL_LOCI.format(os.environ.get("DEFAULT_GRAPH"))
        )
        nr_loci = result["results"]["bindings"][0]["count"]["value"]
        # links to species
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #             (sq.COUNT_SPECIES_LOCI.format(current_app.config['DEFAULTHGRAPH'], species_uri)))

        result = await client.query(
            sq.COUNT_SPECIES_LOCI.format(
                os.environ.get("DEFAULT_GRAPH"), species_uri
            )
        )
        sp_loci = result["results"]["bindings"][0]["count"]["value"]
        # links to schema
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #             (sq.COUNT_SCHEMA_LOCI.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        result = await client.query(
            sq.COUNT_SCHEMA_LOCI.format(
                os.environ.get("DEFAULT_GRAPH"), schema_uri
            )
        )
        sc_loci = result["results"]["bindings"][0]["count"]["value"]

        await client.close()

        # delete ZIP
        os.remove(file_path)

        # insert loci
        # loci_insertion = insert_loci.apply_async(queue='loci_queue',
        #                                             args=(temp_dir,
        #                                                 current_app.config['DEFAULTHGRAPH'],
        #                                                 current_app.config['LOCAL_SPARQL'],
        #                                                 current_app.config['BASE_URL'],
        #                                                 current_app.config['VIRTUOSO_USER'],
        #                                                 current_app.config['VIRTUOSO_PASS']))

    return (
        {
            "message": "Received file.",
            "nr_loci": nr_loci,
            "sp_loci": sp_loci,
            "sc_loci": sc_loci,
        },
        201,
    )


async def delete_schema_loci(
    species_id, schema_id, loci_id, request_type, current_user
):
    """Delete or deprecate loci link to a particular schema of a particular species."""
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    if request_type == "delete":
        results = await rm_functions.rm_loci_links(
            "sclinks",
            loci_id,
            os.environ.get("DEFAULT_GRAPH"),
            os.environ.get("LOCAL_SPARQL"),
            os.environ.get("BASE_URL"),
            os.environ.get("VIRTUOSO_USER"),
            os.environ.get("VIRTUOSO_PASS"),
        )

        return results

    elif request_type == "deprecate":
        # it adds an attribute typon:deprecated "true"^^xsd:boolean to that part of the schema,
        c_user = current_user.id

        # get post data
        # request_data = request.args

        # try:
        #     request_data["loci_id"]
        # except:
        #     return {"message": "No valid id for loci provided"}, 404

        if type(loci_id) != str:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="No valid id for loci provided",
            )

        user_url = "{0}users/{1}".format(os.environ.get("BASE_URL"), c_user)

        print(user_url, flush=True)

        # check if schema exists
        schema_url = "{0}species/{1}/schemas/{2}".format(
            os.environ.get("BASE_URL"), species_id, schema_id
        )

        # this will return FALSE for Admin if the schema was uploaded by a Contributor?
        # result = aux.get_data(
        #     SPARQLWrapper(current_app.config["LOCAL_SPARQL"]),
        #     (
        #         "ASK where {{ <{0}> a typon:Schema; typon:administratedBy <{1}>;"
        #         ' typon:deprecated  "true"^^xsd:boolean }}'.format(
        #             schema_url, user_url
        #         )
        #     ),
        # )

        result = await client.query(
            "ASK where {{ <{0}> a typon:Schema; typon:administratedBy <{1}>;"
            ' typon:deprecated  "true"^^xsd:boolean }}'.format(
                schema_url, user_url
            )
        )

        print(result, flush=True)

        if not result["boolean"]:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Schema not found or schema is not yours",
            )
            # return {"message": "Schema not found or schema is not yours"}, 404

        # check if locus exists
        locus_url = "{0}species/{1}/loci/{2}".format(
            os.environ.get("BASE_URL"), species_id, loci_id
        )

        # result = aux.get_data(
        #     SPARQLWrapper(current_app.config["LOCAL_SPARQL"]),
        #     (sq.ASK_LOCUS.format(locus_url)),
        # )

        result = await client.query(sq.ASK_LOCUS.format(locus_url))

        if not result["boolean"]:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Locus not found",
            )
            # return {"message": "Locus not found"}, 404

        # check if locus exists on schema
        # result = aux.get_data(
        #     SPARQLWrapper(current_app.config["LOCAL_SPARQL"]),
        #     (sq.ASK_SCHEMA_LOCUS2.format(schema_url, locus_url)),
        # )

        result = await client.query(
            sq.ASK_SCHEMA_LOCUS2.format(schema_url, locus_url)
        )

        if not result["boolean"]:
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="Locus already on schema",
            )
            # return {"message": "Locus already on schema"}, 409

        # result = aux.get_data(
        #     SPARQLWrapper(current_app.config["LOCAL_SPARQL"]),
        #     (
        #         "select ?parts "
        #         "from <{0}> "
        #         "where "
        #         "{{ <{1}> typon:hasSchemaPart ?parts. "
        #         "?parts typon:hasLocus <{2}>.}}".format(
        #             current_app.config["DEFAULTHGRAPH"], schema_url, locus_url
        #         )
        #     ),
        # )

        result = await client.query(
            "select ?parts "
            "from <{0}> "
            "where "
            "{{ <{1}> typon:hasSchemaPart ?parts. "
            "?parts typon:hasLocus <{2}>.}}".format(
                os.environ.get("DEFAULT_GRAPH"), schema_url, locus_url
            )
        )

        schema_link = result["results"]["bindings"][0]["parts"]["value"]

        # add a triple to the link between the schema and the locus implying that the locus is deprecated for that schema
        query2send = (
            "INSERT DATA IN GRAPH <{0}> "
            '{{ <{1}> typon:deprecated "true"^^xsd:boolean.}}'.format(
                os.environ.get("DEFAULT_GRAPH"), schema_link
            )
        )

        # result = aux.send_data(
        #     query2send,
        #     current_app.config["LOCAL_SPARQL"],
        #     current_app.config["VIRTUOSO_USER"],
        #     current_app.config["VIRTUOSO_PASS"],
        # )

        result = await client.update(query2send)

        await client.close()

        print(result, flush=True)

        return {"message": "Locus sucessfully removed from schema"}

        # if result.status_code in [200, 201]:
        #     return {"message": "Locus sucessfully removed from schema"}, 201
        # else:
        #     return (
        #         {"message": "Could not remove locus from schema."},
        #         result.status_code,
        #     )


async def post_schema_loci_id_data(
    species_id, schema_id, loci_id, data_file, current_user
):
    """
    """
    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    c_user = current_user.id

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # check if schema has been fully uploaded
    # date_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             (sq.ASK_SCHEMA_DATE.format(schema_uri, 'dateEntered', 'singularity')))

    date_result = await client.query(
        sq.ASK_SCHEMA_DATE.format(schema_uri, "dateEntered", "singularity")
    )

    if not date_result["boolean"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Cannot add initial set of alleles after schema has been fully uploaded.",
        )
        # return {'message': 'Cannot add initial set of alleles after schema has been fully uploaded.'}, 403

    # determine if schema is locked
    # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                                     (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    locking_status_query = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )
    locking_status = locking_status_query["results"]["bindings"][0][
        "Schema_lock"
    ]["value"]

    if locking_status != "Unlocked":
        # check the role of the user that is trying to access
        user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), c_user)

        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri)))

        result = await client.query(
            sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_uri)
        )

        user_role = result["results"]["bindings"][0]["role"]["value"]

        allow = aux.enforce_locking(user_role, user_uri, locking_status)

        if allow[0] is False:
            return allow[1], 403

    await client.close()

    root_dir = os.path.abspath(os.environ.get("SCHEMA_UP"))

    # folder to hold files with alleles to insert
    temp_dir = os.path.join(root_dir, "{0}_{1}".format(species_id, schema_id))

    # create folder when uploading first file
    if os.path.isdir(temp_dir) is False:
        os.mkdir(temp_dir)

    # file = request.files['file']
    locus_hash = data_file.filename

    hashes_file = os.path.join(
        temp_dir, "{0}_{1}_hashes".format(species_id, schema_id)
    )
    with open(hashes_file, "rb") as hf:
        loci_hashes = pickle.load(hf)

    if locus_hash not in loci_hashes:
        raise HTTPException(
            status.HTTP_406_NOT_ACCEPTABLE,
            detail="Provided locus data does not match any locus from the schema.",
        )
        # return {'Not acceptable': 'Provided locus data does not match any locus from the schema'}, 406
    elif locus_hash in loci_hashes:
        with open(os.path.join(temp_dir, locus_hash), "wb") as buffer:
            shutil.copyfileobj(data_file.file, buffer)
        # file.save(os.path.join(temp_dir, locus_hash))

        loci_hashes[locus_hash][0] = True
        with open(hashes_file, "wb") as hf:
            pickle.dump(loci_hashes, hf)

    alleles_values = [v[0] for v in list(loci_hashes.values())]
    # if all(alleles_values) is True:
    #     # insert alleles
    #     alleles_insertion = insert_alleles.apply_async(
    #         queue="alleles_queue",
    #         args=(
    #             temp_dir,
    #             os.environ.get("DEFAULT_GRAPH"),
    #             os.environ.get("LOCAL_SPARQL"),
    #             os.environ.get("BASE_URL"),
    #             os.environ.get("VIRTUOSO_USER"),
    #             os.environ.get("VIRTUOSO_PASS"),
    #         ),
    #     )

    return (
        {"OK": "Received file with data to insert alleles of new locus."},
        201,
    )


async def get_schema_status(species_id, schema_id, current_user):
    """Verify the status of a particular schema.
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # get user role
    c_user = current_user.id

    user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), c_user)

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri)))

    result = await client.query(
        sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_uri)
    )

    user_role = result["results"]["bindings"][0]["role"]["value"]

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # check if schema exists
    # schema_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.ASK_SCHEMA.format(schema_uri)))

    schema_query = await client.query(sq.ASK_SCHEMA.format(schema_uri))
    if schema_query["boolean"] is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a schema with specified ID.",
        )
        # return {'Not found': 'Could not find a schema with specified ID.'}, 404

    # determine if schema is locked
    # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    locking_status_query = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )
    locking_status = locking_status_query["results"]["bindings"][0][
        "Schema_lock"
    ]["value"]

    if locking_status != "Unlocked":
        locking_status = "LOCKED"

    # determine last modification date
    # date_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.SELECT_SCHEMA_DATE.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    date_query = await client.query(
        sq.SELECT_SCHEMA_DATE.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )
    modification_date = date_query["results"]["bindings"][0]["last_modified"][
        "value"
    ]

    # count number of alleles
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    result = await client.query(
        sq.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )
    nr_alleles = result["results"]["bindings"][0]["nr_alleles"]["value"]

    # count number of loci
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.COUNT_SCHEMA_LOCI.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    result = await client.query(
        sq.COUNT_SCHEMA_LOCI.format(os.environ.get("DEFAULT_GRAPH"), schema_uri)
    )
    nr_loci = result["results"]["bindings"][0]["count"]["value"]

    # determine compressed version date
    compressed_dir = os.path.abspath(os.environ.get("SCHEMAS_ZIP"))
    compressed_schema = [
        f
        for f in os.listdir(compressed_dir)
        if f.startswith("{0}_{1}".format(species_id, schema_id))
    ]
    if len(compressed_schema) > 0 and "temp" not in compressed_schema[0]:
        compressed_schema = compressed_schema[0].split("_")[-1].rstrip(".zip")
    else:
        compressed_schema = "N/A"

    return {
        "status": locking_status,
        "nr_alleles": nr_alleles,
        "nr_loci": nr_loci,
        "last_modified": modification_date,
        "compressed": compressed_schema,
    }


async def get_schema_update_f(species_id, schema_id, loci_id, current_user):
    """
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # Get user ID
    c_user = current_user.id

    # get list of authorized users
    with open("authorized_users", "rb") as au:
        auth_list = pickle.load(au)

    if c_user not in auth_list:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Unauthorized",
        )
        # return {'message': 'Unauthorized'}, 403

    user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), c_user)

    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri)))

    result = await client.query(
        sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_uri)
    )

    user_role = result["results"]["bindings"][0]["role"]["value"]

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    # check if schema exists
    # schema_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.ASK_SCHEMA.format(schema_uri)))
    schema_query = await client.query(sq.ASK_SCHEMA.format(schema_uri))
    if schema_query["boolean"] is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Could not find a schema with specified ID.",
        )
        # return {'Not found': 'Could not find a schema with specified ID.'}, 404

    # determine if schema is locked
    # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))
    locking_status_query = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )
    locking_status = locking_status_query["results"]["bindings"][0][
        "Schema_lock"
    ]["value"]

    # count number of alleles
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #     (sq.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))
    result = await client.query(
        sq.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )
    nr_alleles = result["results"]["bindings"][0]["nr_alleles"]["value"]

    await client.close()

    if user_uri == locking_status:
        root_dir = os.path.abspath(os.environ.get("SCHEMA_UP"))

        # folder to hold files with alleles to insert
        temp_dir = os.path.join(
            root_dir, "{0}_{1}".format(species_id, schema_id)
        )

        # read file with results
        identifiers_file = os.path.join(temp_dir, "identifiers")
        if os.path.isfile(identifiers_file) is True:
            # determine if file has been fully written
            start_size = os.stat(identifiers_file).st_size
            written = False
            while written is False:
                time.sleep(2)
                current_size = os.stat(identifiers_file).st_size
                if current_size == start_size:
                    written = True
                else:
                    start_size = current_size

            # get alleles insertion response
            with open(identifiers_file, "rb") as rf:
                results = pickle.load(rf)

            # remove temp directory
            shutil.rmtree(temp_dir)

            return (
                {
                    "message": "Complete",
                    "nr_alleles": nr_alleles,
                    "identifiers": results,
                },
                201,
            )
        else:
            return {"nr_alleles": nr_alleles}, 201
    else:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only Admin or user that is updating the schema may retrieve this data.",
        )
        # return {'Not authorized': 'Only Admin or user that is updating '
        #         'the schema may retrieve this data.'}, 403


async def post_schema_update_f(
    species_id, schema_id, loci_id, update_file, current_user
):
    """
    """

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    c_user = current_user.id

    schema_uri = "{0}species/{1}/schemas/{2}".format(
        os.environ.get("BASE_URL"), species_id, schema_id
    )

    locus_uri = "{0}loci/{1}".format(os.environ.get("BASE_URL"), loci_id)

    # check if locus is linked to schema
    # schema_locus = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                             sq.ASK_SCHEMA_LOCUS.format(schema_uri, locus_uri))

    schema_locus = await client.query(
        sq.ASK_SCHEMA_LOCUS.format(schema_uri, locus_uri)
    )

    if schema_locus["boolean"] is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Schema has no locus with provided ID.",
        )
        # return {'Not Found': 'Schema has no locus with provided ID.'}

    # determine if schema is locked
    # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                                     (sq.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

    locking_status_query = await client.query(
        sq.SELECT_SCHEMA_LOCK.format(
            os.environ.get("DEFAULT_GRAPH"), schema_uri
        )
    )
    locking_status = locking_status_query["results"]["bindings"][0][
        "Schema_lock"
    ]["value"]

    if locking_status == "Unlocked":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Schema cannot be updated if it is not locked.",
        )
        # return {'Unauthorized': 'Schema cannot be updated if it is not locked.'}, 403
    elif locking_status != "Unlocked":
        # check the role of the user that is trying to access
        user_uri = "{0}users/{1}".format(os.environ.get("BASE_URL"), c_user)

        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri)))

        result = await client.query(
            sq.SELECT_USER.format(os.environ.get("DEFAULT_GRAPH"), user_uri)
        )

        user_role = result["results"]["bindings"][0]["role"]["value"]

        if user_role != "Admin" and user_uri != locking_status:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Only Admin or user that locked the schema may send data.",
            )
            # return {'Not authorized': 'Only Admin or user that locked the schema may send data.'}, 403

    root_dir = os.path.abspath(os.environ.get("SCHEMA_UP"))

    # folder to hold files with alleles to insert
    temp_dir = os.path.join(root_dir, "{0}_{1}".format(species_id, schema_id))

    # create folder when uploading first file
    if os.path.isdir(temp_dir) is False:
        os.mkdir(temp_dir)

    # file = request.files['file']
    locus_hash = update_file.filename

    with open(os.path.join(temp_dir, locus_hash), "wb") as buffer:
        shutil.copyfileobj(update_file.file, buffer)

    # file.save(os.path.join(temp_dir, locus_hash))

    if "complete" in update_request.headers:
        # count number of alleles in schema
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                         (sq.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        result = await client.query(
            sq.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(
                os.environ.get("DEFAULT_GRAPH"), schema_uri
            )
        )
        nr_alleles = result["results"]["bindings"][0]["nr_alleles"]["value"]

        # start script that inserts submitted alleles
        # result = update_alleles.apply_async(
        #     queue="sync_queue",
        #     args=(
        #         temp_dir,
        #         current_app.config["DEFAULTHGRAPH"],
        #         current_app.config["LOCAL_SPARQL"],
        #         current_app.config["BASE_URL"],
        #         current_app.config["VIRTUOSO_USER"],
        #         current_app.config["VIRTUOSO_PASS"],
        #         str(c_user),
        #     ),
        # )

        return {"nr_alleles": nr_alleles}, 201

    return {"OK": "Received data."}, 201


# async def post_schema_schema_len():
#     """
#     """
#     pass
