from fastapi import APIRouter, Request, Depends
import typing as t

# import os

# from app.db.session import get_db
from app.core.auth import get_current_active_user

from . import schemas, crud

sequences_router = r = APIRouter()


@r.get("/list", response_model=schemas.SequenceList)
async def seq_list(current_user=Depends(get_current_active_user)):
    """
    Gets the total number of sequences on NS.
    """

    res = await crud.get_seq_list()

    return res


@r.get(
    "/seq_info",
    response_model=t.Union[schemas.SequenceDNA, schemas.SequenceHash],
)
async def seq_info(
    request: Request,
    sequence: t.Optional[str] = None,
    species_id: t.Optional[str] = None,
    seq_id: t.Optional[str] = None,
):
    """
    Get information on sequence, DNA string, uniprot URI and uniprot label.
    """

    res = await crud.get_sequence(request, sequence, species_id, seq_id)

    return res
