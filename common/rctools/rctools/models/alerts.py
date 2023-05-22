from enum import Enum
from typing import List, Optional

from rctools.models.base import IdMixin, ReadiChargeBaseModel, TimestampMixin


class Alert(IdMixin, TimestampMixin, ReadiChargeBaseModel):
    class AlertTypes(str, Enum):
        message = 'message'   # icon: chat bubble
        notification = 'notification'  # icon: bell
        payment_incoming = 'payment_incoming'  # icon: dollar sign with arrow entering from left
        payment_outgoing = 'payment_outgoing'  # icon: dollar sign with arrow exiting on right
        rating = 'rating'   # icon: star
        warning = 'warning'  # icon: red exclamation mark in a circle
    
    uid: Optional[str]
    title: str
    type: AlertTypes
    content: Optional[str]
    expired: Optional[int]
    path: Optional[str]
    path_id: Optional[str]
    rating: Optional[float]


class AlertsResponse(ReadiChargeBaseModel):
    alerts: Optional[List[Alert]] = []

