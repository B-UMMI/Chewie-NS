from pydantic import BaseModel
import typing as t

# from enum import Enum


class SummaryResult(BaseModel):
    result: t.List[t.Dict[str, t.Dict[str, str]]]
