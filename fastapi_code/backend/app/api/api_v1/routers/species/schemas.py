from pydantic import BaseModel
import typing as t
from enum import Enum


class SpeciesList(BaseModel):
    result: t.List[t.Dict[str, t.Dict[str, str]]]
    # species: str
    # name: str
    # type: str
    # value: str


class SuccesfulPost(BaseModel):
    message: str


class SuccesfulPostCelery(SuccesfulPost):
    status_code: int


class SuccesfulSchemaPost(SuccesfulPost):
    url: str


class RequestSpecies(str, Enum):
    delete = "delete"
    deprecate = "deprecate"


class DeleteSchemaLoci(str, Enum):
    delete = "delete"
    deprecate = "deprecate"


class RequestZip(str, Enum):
    check = "check"
    download = "download"


class RequestDescription(str, Enum):
    check = "check"
    download = "download"


class RequestDescriptionCheck(BaseModel):
    description: str


class RequestZipCheck(BaseModel):
    zip_file: t.List[str]


class SpeciesSchemasList(SpeciesList):
    pass


class SpeciesSchemaInfo(SpeciesList):
    pass


class CreateSpeciesSchema(BaseModel):
    name: str
    bsr: str
    prodigal_training_file: str
    translation_table: str
    minimum_locus_length: str
    size_threshold: str
    chewBBACA_version: str
    word_size: str
    cluster_sim: str
    representative_filter: str
    intraCluster_filter: str
    schema_hashes: str


class DeleteSchema(BaseModel):
    schema_id: int
    loci: int
    splinks: int
    sclinks: int
    alleles: int
    total_triples: int


class AdministratesSchema(BaseModel):
    administers: bool


class ModifiedSchema(BaseModel):
    modified: str


class ModifiedSchemaInput(BaseModel):
    date: str


class ChangeSchemaDate(BaseModel):
    result: str


class LockPost(BaseModel):
    action: str


class SchemaLociPost(BaseModel):
    loci_id: int


class SchemaStatus(BaseModel):
    status: str
    nr_alleles: str
    nr_loci: str
    last_modified: str
    compressed: str
