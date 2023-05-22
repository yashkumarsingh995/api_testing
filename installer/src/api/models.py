"""Response and request models for FastAPI"""

from datetime import datetime
from typing import List, Optional
from fastapi import Query

from pydantic import BaseModel, Extra
from rctools.models import ReadiChargeBaseModel


class HealthResponse(ReadiChargeBaseModel):
    GIT_HASH: str

