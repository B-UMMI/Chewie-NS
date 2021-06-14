from fastapi import APIRouter, Request, Depends, status, Form
from fastapi.responses import StreamingResponse
import typing as t

# import os

# from app.db.session import get_db
from app.core.auth import (
    get_current_active_user,
    get_current_active_superuser,
    get_current_active_superuser_or_contributor,
)

from . import schemas, crud
from app.api.dependencies import auxiliary_functions as aux


loci_router = r = APIRouter()


@r.get("/loci/list")
async def loci_list(
    current_user=Depends(get_current_active_superuser_or_contributor),
    prefix: t.Optional[str] = None,
    sequence: t.Optional[str] = None,
    locus_ori_name: t.Optional[str] = None,
):
    """
    Get a list of all loci on NS.
    """

    res = await crud.loci_list(prefix, sequence, locus_ori_name)

    return StreamingResponse(
        aux.generate("Loci", res), media_type="application/json"
    )


@r.post(
    "/loci/list",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SuccesfulLociCreation,
)
async def create_loci(
    prefix: str,
    loci_post: schemas.LociPost,
    current_user=Depends(get_current_active_superuser_or_contributor),
    locus_ori_name: t.Optional[str] = None,
):
    res = await crud.create_loci(prefix, locus_ori_name, loci_post)

    return res


@r.get("/loci/{loci_id}", response_model=schemas.Locus)
async def get_loci(loci_id: str):
    res = await crud.get_loci(loci_id)

    return res


@r.delete("/loci/{loci_id}", response_model=schemas.DeleteLoci)
async def delete_loci(loci_id: str):
    res = await crud.delete_loci(loci_id)

    return res


@r.get("/loci/{loci_id}/fasta")
async def loci_fasta(
    loci_id: str, date: t.Optional[str] = None,
):
    res = await crud.get_loci_fasta(loci_id, date)

    return StreamingResponse(
        aux.generate("Fasta", res), media_type="application/json"
    )


@r.get("/loci/{loci_id}/uniprot")
async def loci_uniprot(loci_id: str):
    res = await crud.get_loci_uniprot(loci_id)

    return StreamingResponse(
        aux.generate("UniprotInfo", res), media_type="application/json"
    )


@r.get(
    "/loci/{loci_id}/alleles",
    # response_model=schemas.AlleleList
)
async def loci_alleles(
    loci_id: str,
    current_user=Depends(get_current_active_user),
    species_name: t.Optional[str] = None,
):
    res = await crud.get_loci_alleles(loci_id, species_name)

    return res


@r.post(
    "/loci/{loci_id}/alleles",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SuccesfulLociAlleleCreation,
)
async def create_loci_alleles(
    loci_id: str,
    species_name: str,
    alleles_post: schemas.AllelePost,
    input_type: schemas.Request,
    current_user=Depends(get_current_active_superuser_or_contributor),
):

    res = await crud.create_loci_alleles(
        loci_id, species_name, alleles_post, input_type, current_user
    )

    return res


@r.get("/loci/{loci_id}/alleles/{allele_id}")
async def get_loci_allele_id(
    loci_id: int, allele_id: str, current_user=Depends(get_current_active_user)
):
    res = await crud.get_loci_allele_id(loci_id, allele_id)

    return res


@r.delete(
    "/loci/{loci_id}/alleles/{allele_id}",
    response_model=schemas.DeleteLociAllele,
)
async def delete_loci_allele_id(
    loci_id: int,
    allele_id: str,
    current_user=Depends(get_current_active_superuser),
):
    res = await crud.delete_loci_allele_id(loci_id, allele_id)

    return res
