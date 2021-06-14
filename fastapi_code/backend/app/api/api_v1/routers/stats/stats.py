from fastapi import APIRouter, Request, File, UploadFile, Depends, status
from fastapi.responses import StreamingResponse, FileResponse
import typing as t
import os
import json

from app.core.auth import (
    get_current_active_user,
    get_current_active_superuser,
    get_current_active_superuser_or_contributor,
)

from . import schemas, crud

from app.db.session import get_db

stats_router = r = APIRouter()


@r.get(
    "/summary", response_model=schemas.SummaryResult,
)
async def stats_summary():
    """
    Count the number of items in Typon.
    """

    res = await crud.get_summary()

    return res


@r.get(
    "/species_summary", response_model=schemas.SummaryResult,
)
async def stats_species():
    """
    Get species properties values and total number of schemas per species.
    """

    res = await crud.get_stats_species()

    return res


@r.get("/species/{species_id}/totals",)
async def stats_totals(
    species_id: int, schema_id: str = None, db=Depends(get_db),
):
    """
    Get schema properties values, total number of loci and total
    number of alleles for all schemas of a species.
    """

    res = await crud.get_totals(db, species_id, schema_id)

    return res


@r.get("/species/{species_id}/schema/loci/nr_alleles",)
async def stats_nr_alleles(
    species_id: int, schema_id: str = None,
):
    """
    Get the loci and count the alleles for
    each schema of a particular species.
    """

    res = await crud.get_nr_alleles(species_id, schema_id)

    return res


@r.get("/species/{species_id}/schema/{schema_id}/modes",)
async def stats_modes(
    species_id: int, schema_id: int,
):
    """
    Get the all the loci and calculate the allele mode
    for a particular schema of a particular species.
    """

    res = await crud.get_modes(species_id, schema_id)

    return res


@r.get("/species/{species_id}/schema/{schema_id}/annotations",)
async def stats_annotations(
    species_id: int, schema_id: int,
):
    """
    Get all the annotations in NS.
    """

    res = await crud.get_annotations(species_id, schema_id)

    return res


@r.get("/species/{species_id}/schema/{schema_id}/lengthStats",)
async def stats_lengthStats(
    species_id: int, schema_id: int,
):
    """
    Get the five-number summary and mean for
    the set of loci of any schema.
    """

    res = await crud.get_lengthStats(species_id, schema_id)

    return res


@r.get("/species/{species_id}/schema/{schema_id}/contributions")
async def stats_contributions(
    species_id: int,
    schema_id: int,
    current_user=Depends(get_current_active_user),
):
    """
    Get the five-number summary and mean for
    the set of loci of any schema.
    """

    res = await crud.get_contributions(species_id, schema_id)

    return res
