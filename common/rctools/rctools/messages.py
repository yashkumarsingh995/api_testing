import logging
from typing import List, Literal, Optional
from uuid import uuid4
from rctools.alerts import create_new_message_alert

from rctools.aws.dynamodb import (KEY_COND_GTE, DynamoPrimaryKey,
                                  create_dynamo_record, fetch_items_by_pk)
from rctools.models import Message
from rctools.models.users import Installer
from rctools.utils import mk_timestamp


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_for_conversations(table: str, user_type: Literal['customer', 'installer'], user_id: str, cursor_token: Optional[str] = None, limit: Optional[int] = None) -> List[Message]:
    """
    Queries a dyanmo table for any messages
    """
    logger.info(f'Checking for conversations for user {user_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {f'{user_type}_id': user_id}
    pk.sort = {'conversation_start': 1}
    messages, pagination_token = [], cursor_token
    index_name = f'gsi{user_type.capitalize()}Index'
    while True:
        items, new_cursor_token = fetch_items_by_pk(table, pk, cursor_token=pagination_token, limit=limit, IndexName=index_name, ScanIndexForward=False)
        messages += items
        pagination_token = new_cursor_token
        if not pagination_token or len(messages) >= limit:
            break
    return messages, pagination_token


def get_latest_message(table: str, conversation_id: str) -> Message:
    """
    Returns the latest message posted to a conversation, usually used to
    provide a conversation preview
    """
    logger.info(f'Fetching messages for conversation {conversation_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {'conversation_id': conversation_id}
    items, _ = fetch_items_by_pk(table, pk, limit=1, ScanIndexForward=False)
    return items[0]


def get_messages_for_conversation(table: str, conversation_id: str, ts: Optional[int] = 0, cursor_token: Optional[str] = None, limit: Optional[int] = None) -> List[Message]:
    """
    Returns messages for a given conversation. Either returns all messages or messages
    after a given timestamp (ts)
    """
    logger.info(f'Fetching messages for conversation {conversation_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {'conversation_id': conversation_id}
    if ts:
        pk.sort = {'ts': ts}
        pk.sort.comparator = KEY_COND_GTE
    messages, pagination_token = [], cursor_token
    while True:
        items, new_cursor_token = fetch_items_by_pk(table, pk, cursor_token=pagination_token, limit=limit, ScanIndexForward=False)
        messages += items
        pagination_token = new_cursor_token
        if not pagination_token or len(messages) >= limit:
            break
    # Filter out blank conversation start, when applicable, and return
    return [m for m in messages if 'conversation_start' not in m], pagination_token


def find_conversation(table: str, installer_id: str, customer_id: str) -> str:
    """Returns the conversation ID for a conversation"""
    conversations, _ = check_for_conversations(table, 'installer', installer_id)
    for c in conversations:
        if c['customer_id'] == customer_id:
            return c['conversation_id']


def post_message_to_conversation(table: str, message: Message) -> Message:
    """
    Adds a message to a given conversation
    """
    logger.info(f'Posting message to conversation {message}')
    create_dynamo_record(table, message.dict())
    return message


def start_conversation(table: str, installer_data: dict, installer_id: str, customer_id: str) -> str:
    """
    Creates conversation-start indexes for both installer and customer users. Returns
    the newly created conversation_id
    """
    logger.info(f'Starting conversation between installer {installer_id} and customer {customer_id}')
    conversation_id = str(uuid4())
    # Start conversation
    create_dynamo_record(table,  Message(**{
        'conversation_id': conversation_id,
        'conversation_start': 1, 
        'installer_id': installer_id, 
        'customer_id': customer_id,
    }).dict())

    # Add automated message
    installer = Installer(**installer_data)
    txt = f'Hi, I\'m {installer.get_first_name()}. I am your certified installer. I am receiving all of the job information now and will follow up with you soon if I have any questions.'
    post_message_to_conversation(table, Message(**{
        'conversation_id': conversation_id,
        'installer_id': installer_id,
        'text': txt
    }))
    # With customer message alert
    create_new_message_alert(customer_id, txt)
    return conversation_id
    