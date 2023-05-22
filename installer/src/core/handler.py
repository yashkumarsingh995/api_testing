import boto3
import json
import logging
import os

from typing import Dict
from aws_lambda_powertools.utilities.typing import LambdaContext


logger = logging.getLogger()
logger.setLevel(logging.INFO)
sqs_client = boto3.client('sqs')

BACKGROUND_CHECK_STATUS_QUEUE_URL = os.getenv('BACKGROUND_CHECK_STATUS_QUEUE_URL')
VERIFY_CERTIFICATION_QUEUE_URL = os.getenv('VERIFY_CERTIFICATION_QUEUE_URL')


def queue_background_status_check(event: Dict[str, any], context: LambdaContext):
    logger.info(f'Queuing background check status check {event}')
    report_key = event['report_key']
    installer_id = event['installer_id']
    resp = sqs_client.send_message(
        QueueUrl=BACKGROUND_CHECK_STATUS_QUEUE_URL,
        MessageBody=json.dumps({
            'report_key': report_key,
            'installer_id': installer_id
        })
    )
    logger.info(f'Response {resp}')
    return resp


def queue_verify_certification(event: Dict[str, any], context: LambdaContext):
    logger.info(f'Queuing certification check {event}')
    state = event['state']
    license_num = event['license_num']
    installer_id = event['installer_id']
    resp = sqs_client.send_message(
        QueueUrl=VERIFY_CERTIFICATION_QUEUE_URL,
        MessageBody=json.dumps({
            'state': state,
            'license_num': license_num,
            'installer_id': installer_id
        })
    )
    logger.info(f'Response {resp}')
    return resp
