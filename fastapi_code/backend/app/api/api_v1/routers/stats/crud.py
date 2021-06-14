import os
import json

# import typing as t
from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from aiosparql.client import SPARQLClient, SPARQLRequestFailed

from app.api.dependencies import sparql_queries as sq

from SPARQLWrapper import SPARQLWrapper

from sqlalchemy.orm import Session

from app.db import models


async def get_summary():
    """Count the number of items in Typon"""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    # get simple counts for data in the NS
    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
    #                         (sq.NS_STATS.format(current_app.config['DEFAULTHGRAPH'])))

    result = await client.query(
        sq.NS_STATS.format(os.environ.get("DEFAULT_GRAPH"))
    )

    await client.close()

    stats = result["results"]["bindings"]
    if stats != []:
        return {"result": stats}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not retrieve summary info from NS.",
        )
        # return {'NOT FOUND': 'Could not retrieve summary info from NS.'}, 404


async def get_stats_species():
    """Get species properties values and total number of schemas per species."""

    client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    result = await client.query(
        sq.COUNT_SPECIES_SCHEMAS.format(os.environ.get("DEFAULT_GRAPH"))
    )

    await client.close()

    species_schemas_count = result["results"]["bindings"]
    if len(species_schemas_count) > 0:
        return {"result": species_schemas_count}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NS has no species or species have no schemas.",
        )
        # return {'NOT FOUND': 'NS has no species or species have no schemas.'}, 404


async def get_totals(db: Session, species_id, schema_id):
    """
    Get schema properties values, total number of loci and total
    number of alleles for all schemas of a species.
    """

    precomputed_data_file = os.path.join(
        os.getcwd(), "pre-computed-data/totals_{0}.json".format(str(species_id))
    )

    with open(precomputed_data_file, "r") as json_file:
        json_data = json.load(json_file)

    # get user id to obtain the username from the Postgres DB
    for i in json_data["message"]:

        json_user_id = int(i["user"].rsplit("/", 1)[-1])

        # user_db = User.query.get_or_404(json_user_id)
        user_db = (
            db.query(models.User).filter(models.User.id == json_user_id).first()
        )

        # replace the user id with the username
        i["user"] = user_db.username

    if schema_id is None:
        return json_data
    elif schema_id is not None:
        schema_data = [
            s
            for s in json_data["message"]
            if s["uri"].split("/")[-1] == schema_id
        ]
        return schema_data


async def get_nr_alleles(species_id, schema_id):
    """
    Get the loci and count the alleles for
    each schema of a particular species.
    """

    precomputed_data_file = os.path.join(
        os.getcwd(), "pre-computed-data/loci_{0}.json".format(str(species_id))
    )

    with open(precomputed_data_file, "r") as json_file:
        json_data = json.load(json_file)

    if schema_id is None:
        return json_data
    elif schema_id is not None:
        schema_data = [
            s
            for s in json_data["message"]
            if s["schema"].split("/")[-1] == schema_id
        ]
        return schema_data


async def get_modes(species_id, schema_id):
    """
    Get the loci and count the alleles for
    each schema of a particular species.
    """

    precomputed_data_file = os.path.join(
        os.getcwd(),
        "pre-computed-data/mode_{0}_{1}.json".format(species_id, schema_id),
    )

    with open(precomputed_data_file, "r") as json_file:
        json_data = json.load(json_file)

    return json_data


async def get_annotations(species_id, schema_id):
    """
    Get the loci and count the alleles for
    each schema of a particular species.
    """

    precomputed_data_file = os.path.join(
        os.getcwd(),
        "pre-computed-data/annotations_{0}_{1}.json".format(
            species_id, schema_id
        ),
    )

    with open(precomputed_data_file, "r") as json_file:
        json_data = json.load(json_file)

    return json_data


async def get_lengthStats(species_id, schema_id):
    """
    Get the loci and count the alleles for
    each schema of a particular species.
    """

    precomputed_data_file = os.path.join(
        os.getcwd(),
        "pre-computed-data/boxplot_{0}_{1}.json".format(species_id, schema_id),
    )

    with open(precomputed_data_file, "r") as json_file:
        json_data = json.load(json_file)

    return json_data


async def get_contributions(species_id, schema_id):
    """
    Get the loci and count the alleles for
    each schema of a particular species.
    """

    precomputed_data_file = os.path.join(
        os.getcwd(),
        "pre-computed-data/allele_contributions_{0}_{1}.json".format(
            species_id, schema_id
        ),
    )

    if os.path.exists(precomputed_data_file):

        with open(precomputed_data_file, "r") as json_file:
            json_data = json.load(json_file)

        return json_data
    else:

        json_data = "undefined"

        return json_data
