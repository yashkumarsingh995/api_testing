import logging
import os
from typing import Optional

import boto3
from fastapi import APIRouter, Header, status
from rctools.aws.cognito import get_user_with_access_token
from rctools.messages import check_for_conversations, get_messages_for_conversation, post_message_to_conversation
from rctools.models import Message, MessagePostRequest, MessageResponse


MESSAGES_TABLE = os.environ.get('MESSAGES_TABLE')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

message_table = dynamodb.Table(MESSAGES_TABLE)


@router.get('/messages', response_model=MessageResponse, status_code=status.HTTP_200_OK)
def get_all_messages(X_Amz_Access_Token: Optional[str] = Header(default=None), cursor_token: Optional[str] = None) -> MessageResponse:
    """
    Pulls the latest messages for the customer
    """
    logger.info('Checking for messages')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    response = MessageResponse()
    convos, _ = check_for_conversations(message_table, 'customer', uid, cursor_token=cursor_token, limit=1)  # just grab the latest
    if convos:
        latest_conversation_id = convos[0]['conversation_id']
        response.conversation_id = latest_conversation_id
        messages, cursor_token = get_messages_for_conversation(message_table, latest_conversation_id, limit=15)  # limit by max assumed to show up on screen at one time
        if messages:    
            response.cursor_token = cursor_token
            response.messages = messages

    logger.info(f'Found {len(response.messages)} message(s) for user {uid}')
    return response


@router.post('/messages/{conversation_id}', status_code=status.HTTP_201_CREATED)
def add_message_to_conversation(new_msg: MessagePostRequest, conversation_id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    logger.info(f'Posting message {new_msg.text} to conversation {conversation_id}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    message = Message(conversation_id=conversation_id)
    message.customer_id = uid
    message.text = new_msg.text
    message.type = new_msg.type
    
    return post_message_to_conversation(message_table, message)
