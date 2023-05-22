from typing import List, Optional
from uuid import uuid4

from rctools.models.base import IdMixin, ReadiChargeBaseModel, TimestampMixin
from rctools.utils import mk_timestamp


class Message(IdMixin, TimestampMixin, ReadiChargeBaseModel):
    conversation_id: str
    conversation_start: Optional[int]
    text: Optional[str]
    customer_id: Optional[str]
    installer_id: Optional[str]
    type: str = 'text'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = str(uuid4())
        self.ts = mk_timestamp()

class MessagePostRequest(ReadiChargeBaseModel):
    text: str
    type: str = 'text'


class MessageResponse(ReadiChargeBaseModel):
    conversation_id: Optional[str]
    messages: Optional[List[Message]] = []
    cursor_token: Optional[str]  # dynamo cursor token for pagination


class ConversationsResponse(ReadiChargeBaseModel):
    conversations: Optional[List[Message]] = []
    cursor_token: Optional[str]  # dynamo cursor token for pagination