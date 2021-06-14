from fastapi import APIRouter, Request, File, UploadFile, Depends, status
from fastapi.responses import StreamingResponse, FileResponse
import typing as t
import os
import json

# from enum import Enum

# from app.db.session import get_db
from app.core.auth import (
    get_current_active_user,
    get_current_active_superuser,
    get_current_active_superuser_or_contributor,
)

from . import schemas, crud
from app.api.dependencies import auxiliary_functions as aux


species_router = r = APIRouter()


@r.get(
    "/species", response_model=schemas.SpeciesList,
)
async def species_list():
    """
    Get all species
    """

    res = await crud.get_species()

    return res


@r.post(
    "/species",
    response_model=schemas.SuccesfulPost,
    status_code=status.HTTP_201_CREATED,
)
async def create_species(
    species_name: str, current_user=Depends(get_current_active_superuser)
):
    """
    """

    res = await crud.create_species(species_name)

    return res


@r.get(
    "/species/{species_id}", response_model=schemas.SpeciesList,
)
async def species(species_id: int):
    """
    Gets the species corresponding to the given id.
    """

    res = await crud.get_species_id(species_id)

    return res


@r.get("/species/{species_id}/loci",)
async def species_loci(
    species_id: int,
    prefix: t.Optional[str] = None,
    sequence: t.Optional[str] = None,
    locus_ori_name: t.Optional[str] = None,
):
    """
    Lists the loci of a particular species
    """

    res = await crud.get_species_loci(
        species_id, prefix, sequence, locus_ori_name
    )

    return StreamingResponse(
        aux.generate("Loci", res), media_type="application/json"
    )


@r.post(
    "/species/{species_id}/loci",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SuccesfulPost
    # include_in_schema=False
)
async def create_species_loci(
    species_id: int,
    locus_id: int,
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """
    Add a new locus for a particular species
    """

    res = await crud.create_species_loci(species_id, locus_id)

    return res


@r.delete("/species/{species_id}/loci/{loci_id}")
async def delete_species_loci(
    species_id: int,
    loci_id: str,
    request_type: schemas.RequestSpecies,
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete or deprecate loci link to a particular species.
    """

    if request_type == schemas.RequestSpecies.delete:

        results = await crud.delete_species_loci(
            species_id, loci_id, request_type
        )

        return results


@r.get(
    "/species/{species_id}/schemas", response_model=schemas.SpeciesSchemasList
)
async def get_species_schemas(species_id: str):
    res = await crud.get_species_schemas(species_id)

    return res


@r.post(
    "/species/{species_id}/schemas",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SuccesfulSchemaPost,
)
async def create_species_schemas(
    species_id: str,
    create_schema: schemas.CreateSpeciesSchema,
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    res = await crud.create_species_schemas(
        species_id, create_schema, current_user
    )

    return res


@r.get(
    "/species/{species_id}/schemas/{schema_id}",
    # response_model=schemas.SpeciesSchemasList,
)
async def get_species_schemas_id(
    species_id: str,
    schema_id: int,
    current_user=Depends(get_current_active_user),
):
    res = await crud.get_species_schemas_id(species_id, schema_id, current_user)

    return res


@r.delete("/species/{species_id}/schemas/{schema_id}")
async def delete_schema_species(
    species_id: int,
    schema_id: str,
    request_type: schemas.RequestSpecies,
    current_user=Depends(get_current_active_superuser),
):
    """
    Deletes or deprecates a particular schema for a particular species.
    """

    if request_type == schemas.RequestSpecies.delete:

        results = await crud.delete_species_schema(
            species_id, schema_id, request_type
        )

        return results

    elif request_type == schemas.RequestSpecies.deprecate:

        results = await crud.deprecate_species_schema(
            species_id, schema_id, current_user
        )

        return results


@r.get(
    "/species/{species_id}/schemas/{schema_id}/administrated",
    response_model=schemas.AdministratesSchema,
)
async def get_schema_admin(
    species_id: int,
    schema_id: int,
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """ Determine if current user administrates schema with provided ID.
    """

    admin = await crud.schema_admin(species_id, schema_id, current_user)

    return admin


@r.get(
    "/species/{species_id}/schemas/{schema_id}/modified",
    response_model=schemas.ModifiedSchema,
)
async def get_modification_date(
    species_id: int, schema_id: int,
):
    """
    Get last modification date of the schema with the given identifier.
    """

    modified = await crud.modification_date(species_id, schema_id)

    return modified


@r.post(
    "/species/{species_id}/schemas/{schema_id}/modified",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.ChangeSchemaDate,
)
async def change_modification_date(
    species_id: int,
    schema_id: int,
    date: schemas.ModifiedSchemaInput,
    current_user=Depends(get_current_active_superuser),
):
    """ Change the last modification date of the schema with the given identifier.
    """

    change_date = await crud.change_mod_date(
        species_id, schema_id, date, current_user
    )

    return change_date


@r.get(
    "/species/{species_id}/schemas/{schema_id}/lock",
    response_model=schemas.SuccesfulPost,
)
async def get_schema_lock_status(
    species_id: int, schema_id: int,
):
    """Get the locking state of the schema with the given identifier."""

    lock_status = await crud.schema_lock_status(species_id, schema_id)

    return {"message": lock_status}


@r.post(
    "/species/{species_id}/schemas/{schema_id}/lock",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SuccesfulPost,
)
async def change_schema_lock(
    species_id: int,
    schema_id: int,
    action: schemas.LockPost,
    current_user=Depends(get_current_active_user),
):
    """Change the locking state of the schema with the given identifier.
    """

    new_lock_status = await crud.change_schema_lock_status(
        species_id, schema_id, action, current_user
    )

    return new_lock_status


@r.get("/species/{species_id}/schemas/{schema_id}/ptf")
async def get_ptf(
    species_id: int,
    schema_id: int,
    current_user=Depends(get_current_active_user),
):
    """Download the Prodigal training file for the specified schema.
    """

    ptf_file = await crud.get_ptf_hash(species_id, schema_id)

    return FileResponse(
        os.path.join(ptf_file["root_dir"], ptf_file["hash"]),
        media_type="application/octet-stream",
        filename=ptf_file["hash"],
    )


@r.post("/species/{species_id}/schemas/{schema_id}/ptf")
async def upload_ptf(
    species_id: int,
    schema_id: int,
    ptf_file: UploadFile = File(...),
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """Download the Prodigal training file for the specified schema.
    """

    upload_ptf_result = await crud.upload_ptf_file(
        species_id, schema_id, ptf_file
    )

    return upload_ptf_result


@r.get(
    "/species/{species_id}/schemas/{schema_id}/zip",
    response_model=t.Union[schemas.RequestZipCheck, None],
)
async def get_zip(
    species_id: int,
    schema_id: int,
    request_type: schemas.RequestZip,
    current_user=Depends(get_current_active_user),
):
    """Checks existence of or downloads zip archive of the specified schema.
    """

    zip_file = await crud.get_zip_file(species_id, schema_id, request_type)

    return zip_file


@r.post(
    "/species/{species_id}/schemas/{schema_id}/zip",
    response_model=schemas.SuccesfulPost,
)
async def compress_zip(
    species_id: int,
    schema_id: int,
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """Give the order to compress a single schema that exists in the NS.
    """

    # UNFINISHED!!
    compressed_zip_status = await crud.compress_zip(
        species_id, schema_id, current_user
    )

    return compressed_zip_status


@r.get(
    "/species/{species_id}/schemas/{schema_id}/description",
    response_model=schemas.RequestDescriptionCheck,
)
async def get_description(
    species_id: int,
    schema_id: int,
    request_type: schemas.RequestDescription,
    current_user=Depends(get_current_active_user),
):
    """Downloads file with the description for the specified schema.
    """

    description_status = await crud.get_description_file(
        species_id, schema_id, request_type
    )

    return description_status


@r.post(
    "/species/{species_id}/schemas/{schema_id}/description",
    response_model=schemas.SuccesfulPost,
)
async def upload_description(
    species_id: int,
    schema_id: int,
    description_file: UploadFile = File(...),
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """Post file with the description for the specified schema.
    """

    upload_description_status = await crud.upload_description_file(
        species_id, schema_id, description_file, current_user
    )

    return upload_description_status


@r.get("/species/{species_id}/schemas/{schema_id}/loci")
async def get_schema_loci(
    species_id: int,
    schema_id: int,
    local_date: str = None,
    ns_date: str = None,
):
    """Returns the loci of a particular schema from a particular species
    """

    schema_loci = await crud.get_schema_loci_data(
        species_id, schema_id, local_date, ns_date
    )

    return schema_loci


@r.post(
    "/species/{species_id}/schemas/{schema_id}/loci",
    # response_model=schemas.SuccesfulPostCelery
)
async def post_schema_loci(
    species_id: int,
    schema_id: int,
    loci_id: schemas.SchemaLociPost,
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """Add loci to a particular schema of a particular species.
    """

    schema_loci_post = await crud.post_schema_loci_data(
        species_id, schema_id, loci_id, current_user
    )

    return schema_loci_post


@r.get("/species/{species_id}/schemas/{schema_id}/loci/data")
async def get_schema_loci_data(
    species_id: int,
    schema_id: int,
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """
    """

    schema_loci_data = await crud.get_schema_loci_data_2(species_id, schema_id)

    return schema_loci_data


@r.post("/species/{species_id}/schemas/{schema_id}/loci/data")
async def post_schema_loci_data2(
    species_id: int,
    schema_id: int,
    temp_file: UploadFile = File(...),
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """
    """

    post_schema_loci_data_resp = await crud.post_schema_loci_data_r(
        species_id, schema_id, temp_file, current_user
    )

    return post_schema_loci_data_resp


@r.delete("/species/{species_id}/schemas/{schema_id}/loci/{loci_id}")
async def delete_schema_loci(
    species_id: int,
    schema_id: int,
    loci_id: str,
    request_type: schemas.DeleteSchemaLoci,
    current_user=Depends(get_current_active_superuser),
):
    """Delete or deprecate loci link to a particular schema of a particular species.
    """

    delete_schema_loci_status = await crud.delete_schema_loci(
        species_id, schema_id, loci_id, request_type, current_user
    )

    return delete_schema_loci_status


@r.post("/species/{species_id}/schemas/{schema_id}/loci/{loci_id}/data")
async def post_schema_loci_id_data(
    species_id: int,
    schema_id: int,
    loci_id: str,
    data_file: UploadFile = File(...),
    current_user=Depends(get_current_active_superuser_or_contributor),
):
    """
    """

    post_schema_loci_id_data_status = crud.post_schema_loci_id_data(
        species_id, schema_id, loci_id, data_file, current_user
    )

    return post_schema_loci_id_data_status


@r.get(
    "/species/{species_id}/schemas/{schema_id}/status",
    response_model=schemas.SchemaStatus,
)
async def get_schema_status(
    species_id: int,
    schema_id: int,
    current_user=Depends(get_current_active_user),
):
    """Verify the status of a particular schema.
    """

    schema_status = await crud.get_schema_status(
        species_id, schema_id, current_user
    )

    return schema_status


@r.get("/species/{species_id}/schemas/{schema_id}/loci/{loci_id}/update")
async def get_schema_update(
    species_id: int,
    schema_id: int,
    loci_id: str,
    current_user=Depends(get_current_active_user),
):
    """
    """

    schema_update = await crud.get_schema_update_f(
        species_id, schema_id, loci_id, current_user
    )

    return schema_update


@r.post("/species/{species_id}/schemas/{schema_id}/loci/{loci_id}/update")
async def post_schema_update(
    species_id: int,
    schema_id: int,
    loci_id: str,
    update_request: Request,
    update_file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
):
    """
    """

    post_schema_update_res = await crud.post_schema_update_f(
        species_id,
        schema_id,
        loci_id,
        update_request,
        update_file,
        current_user,
    )

    return post_schema_update_res


# @r.post("/species/{species_id}/schemas/{schema_id}/loci/{loci_id}/lengths")
# async def post_schema_lengths(
#     species_id: int,
#     schema_id: int,
#     loci_id: int,
#     content: dict,
#     update_file: UploadFile = File(...),
#     current_user=Depends(get_current_active_user),
# ):
#     """
#     """
#     pass
