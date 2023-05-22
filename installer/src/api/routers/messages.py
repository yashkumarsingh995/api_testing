import logging
import os
from typing import Optional

import boto3
from fastapi import APIRouter, Header, status
from rctools.aws.cognito import get_user_with_access_token
from rctools.messages import check_for_conversations, get_latest_message, get_messages_for_conversation, post_message_to_conversation
from rctools.models import ConversationsResponse, Message, MessagePostRequest, MessageResponse


MESSAGES_TABLE = os.environ.get('MESSAGES_TABLE')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

message_table = dynamodb.Table(MESSAGES_TABLE)


@router.get('/conversations', response_model=ConversationsResponse, status_code=status.HTTP_200_OK)
def get_all_conversations(X_Amz_Access_Token: Optional[str] = Header(default=None), cursor_token: Optional[str] = None) -> ConversationsResponse:
    """
    Checks for any conversations for the installer by returning the markers for the conversation_start
    """
    logger.info('Checking for conversations')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    response = ConversationsResponse()
    convos, cursor_token = check_for_conversations(message_table, 'installer', uid, cursor_token=cursor_token, limit=20)  # limiting by max presumed to display on a screen at once
    if convos:
        response.conversations = [get_latest_message(message_table, c['conversation_id']) for c in convos]
        response.cursor_token = cursor_token

    logger.info(f'Found {len(response.conversations)} conversation(s) for user {uid}')
    return response


@router.get('/messages/{conversation_id}', response_model=MessageResponse, status_code=status.HTTP_200_OK)
def get_messages_for_conversation_id(conversation_id: str, X_Amz_Access_Token: Optional[str] = Header(default=None), cursor_token: Optional[str] = None) -> MessageResponse:
    """
    Returns all messages for a given conversation up to the given limit, or any messages occuring after the
    provided cursor token
    """
    logger.info(f'Polling messages for conversation {conversation_id}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    response = MessageResponse()
    messages, cursor_token = get_messages_for_conversation(message_table, conversation_id, cursor_token=cursor_token, limit=20)  # arbitray "reasonable" number of messages to show at once
    if messages:
        response.conversation_id = conversation_id
        response.messages = messages
        response.cursor_token = cursor_token

    logger.info(f'Found {len(response.messages)} conversation(s) for user {uid}')
    return response


@router.post('/messages/{conversation_id}', status_code=status.HTTP_201_CREATED)
def add_message_to_conversation(new_msg: MessagePostRequest, conversation_id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    logger.info(f'Posting message {new_msg.text} to conversation {conversation_id}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    message = Message(conversation_id=conversation_id)
    message.installer_id = uid
    message.text = new_msg.text
    message.type = new_msg.type
    
    return post_message_to_conversation(message_table, message.dict())
