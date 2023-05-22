
import boto3
import json
import logging
import os

from rctools.aws.ses import send_email
from typing import Dict
from aws_lambda_powertools.utilities.typing import LambdaContext
from mail import get_content


logger = logging.getLogger()
logger.setLevel(logging.INFO)
ses_client = boto3.client('ses')
sqs_client = boto3.client('sqs')

SEND_EMAIL_QUEUE_URL = os.getenv('SEND_EMAIL_QUEUE_URL')


def queue_send_email(event: Dict[str, any], context: LambdaContext):
    logger.info(f'Queuing email {event}')
    email_type = event['type']
    to_addrs = event['to']
    if type(to_addrs) == str:
        to_addrs = [to_addrs]
    cc_addrs = event.get('cc', [])
    bcc_addrs = event.get('bcc', [])
    params = event.get('params', {})

    body = {
        'type': email_type,
        'to': to_addrs,
        'cc': cc_addrs,
        'bcc': bcc_addrs,
        **params
    }
    logger.info(f'Sending {body}')
    resp = sqs_client.send_message(
        QueueUrl=SEND_EMAIL_QUEUE_URL,
        MessageBody=json.dumps(body)
    )
    logger.info(f'Response {resp}')
    return resp


def send_queued_email(event: Dict[str, any], context: LambdaContext):
    for record in event['Records']:
        logger.info(f'Sending queued email {record}')
        body = json.loads(record['body'])
        logger.info(f'Reading {body}')
        email_type = body.pop('type')
        to_addrs = body.pop('to', [])
        cc_addrs = body.pop('cc', [])
        bcc_addrs = body.pop('bcc', [])
        email = get_content(email_type, record)
        res = send_email(
            ses_client,
            email['subject'],
            email['text'],
            email['html'],
            'info@rcdevel.com',
            to_addrs,
            cc_addrs,
            bcc_addrs
        )
        logger.info(f'SES response: {res}')
        # Then delete upon success
        sqs_client.delete_message(
            QueueUrl=SEND_EMAIL_QUEUE_URL,
            ReceiptHandle=record['receiptHandle']
        )
    return True