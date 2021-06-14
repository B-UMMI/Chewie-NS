from pydantic import BaseModel, AnyHttpUrl
import typing as t


class SequenceList(BaseModel):
    message: str


class SequenceBase(BaseModel):
    result: t.List[t.Dict[str, t.Dict[str, str]]]


class SequenceDNA(SequenceBase):
    sequence_uri: AnyHttpUrl
    number_alleles_loci: int


class SequenceHash(SequenceBase):
    number_alleles_loci: int
