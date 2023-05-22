from uuid import uuid4
from typing import Optional

from pydantic import BaseModel, Extra, validator
from rctools.utils import mk_timestamp


class DateTimeModelMixin(BaseModel):
    created_at: Optional[int]
    updated_at: Optional[int]

    @validator("created_at", "updated_at", pre=True, always=True)
    def default_datetime(cls, value: int) -> int:
        return value or mk_timestamp()


class IdMixin(BaseModel):
    id: Optional[str]

    @validator("id", pre=True, always=True)
    def random_id(cls, value: str) -> str:
        return value or str(uuid4())


class TimestampMixin(BaseModel):
    ts: Optional[int]

    @validator("ts", pre=True, always=True)
    def random_id(cls, value: int) -> int:
        return value or mk_timestamp()


class ReadiChargeBaseModel(DateTimeModelMixin, BaseModel):
    """BaseModel superclass that will always fail if extra attributes are included"""
    class Config:
        extra = Extra.forbid
