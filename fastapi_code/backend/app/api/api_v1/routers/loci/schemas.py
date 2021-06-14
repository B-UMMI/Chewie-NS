from pydantic import BaseModel, AnyHttpUrl
import typing as t
from enum import Enum


class Request(str, Enum):
    manual = "manual"
    auto = "auto"


class LociPost(BaseModel):
    uniprot_name: str
    uniprot_label: str
    uniprot_url: str


class AllelePost(LociPost):
    sequence: str
    sequence_uri: str
    enforceCDS: bool


class SuccesfulLociAlleleCreation(BaseModel):
    operation: str
    message: str


class SuccesfulLociCreation(BaseModel):
    message: str
    uri: AnyHttpUrl
    id: str


class Locus(BaseModel):
    result: t.List[t.Dict[str, t.Dict[str, str]]]


class LocusAllele(BaseModel):
    result: t.List[t.Dict[str, t.Dict[str, str]]]


# class AlleleList(BaseModel):
#     alleles: t.List[t.Dict[t.Dict[str, str]]]


class DeleteLoci(BaseModel):
    loci: int
    splinks: int
    sclinks: int
    alleles: int
    total_triples: int


class DeleteLociAllele(BaseModel):
    alleles: int
    total_triples: int
