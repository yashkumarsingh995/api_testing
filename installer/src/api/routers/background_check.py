import json
import logging
import os
from typing import Optional

import boto3
import botocore
from fastapi import APIRouter, Header, status
from rctools.background_checks import (
    create_background_check_hash, order_background_check,
    get_background_check_api_key
)
from rctools.aws.cognito import get_user_with_access_token, flatten_user_attributes
from rctools.alerts import create_background_check_in_progress_alert, add_user_alert
from rctools.installers import get_installer_data_from_s3, update_installer_data_in_s3


ALERTS_TABLE = os.getenv('ALERTS_TABLE')
AWS_REGION_NAME = os.getenv('AWS_REGION')
BACKGROUND_CHECK_API_ROOT = os.getenv('BACKGROUND_CHECK_API_ROOT')
BACKGROUND_CHECK_QUEUE_URL = os.getenv('BACKGROUND_CHECK_QUEUE_URL')
BACKGROUND_CHECK_SECRET_NAME = os.environ.get('BACKGROUND_CHECK_SECRET_NAME')
BACKGROUND_CHECK_STATUS_CHECK_LAMBDA_NAME = os.environ.get('BACKGROUND_CHECK_STATUS_CHECK_LAMBDA_NAME')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')


cognito_client = boto3.client('cognito-idp')
lambda_config = botocore.config.Config(retries={'max_attempts': 0})
lambda_client = boto3.client('lambda', config=lambda_config)
secrets_client = boto3.client('secretsmanager')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')

dynamodb = boto3.resource('dynamodb')
alerts_table = dynamodb.Table(ALERTS_TABLE)

g_context = {}


def get_api_key():
    """Returns API key from global context or fetches it from Secrets Manager"""
    if 'api_key' not in g_context:
        g_context['api_key'] = get_background_check_api_key(secrets_client, AWS_REGION_NAME, BACKGROUND_CHECK_SECRET_NAME)
    return g_context['api_key']


@router.put('/installer/background-check', status_code=status.HTTP_201_CREATED)
def submit_background_check(update: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """
    Submits a request for a ClearChecks background check.

    ClearChecks background checks require sensitive information that we do NOT
    want to store or log on our servers. As such, the data used for a background check
    comes in hashed from the client with a one-time use encryption key. This request
    data is only decrypted when the ClearChecks API request is submitted.
    """
    logger.info(f'Starting background check for user')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']
    flatten_user_attributes(user)

    email = user['email']
    user = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, uid)
    if user.get('background_check'):
        if user['background_check'].get('report_key'):
            logger.info('Found existing background check; returning report key')
            # Queue status check
            lambda_client.invoke(
                FunctionName=BACKGROUND_CHECK_STATUS_CHECK_LAMBDA_NAME,
                InvocationType='Event',  # async, response will be saved to user data
                Payload=json.dumps({
                    'report_key': user['background_check']['report_key'],
                    'installer_id': uid
                })
            )
            return user['background_check']['report_key']

    logger.info(f'Submitting background check for {email}')
    # s3_client, api_root, api_key, email, installer_id
    api_key = get_api_key()
    report_key = order_background_check(BACKGROUND_CHECK_API_ROOT, api_key, email)
    logger.info(f'Success! Returned report key {report_key}')
    update_installer_data_in_s3(s3_client, USER_DATA_BUCKET, uid, {'background_check': {'report_key': report_key}})
    # Create in-progress alert
    add_user_alert(alerts_table, uid, create_background_check_in_progress_alert(uid))
    # Queue status check
    lambda_client.invoke(
        FunctionName=BACKGROUND_CHECK_STATUS_CHECK_LAMBDA_NAME,
        InvocationType='Event',  # async, response will be saved to user data
        Payload=json.dumps({
            'report_key': report_key,
            'installer_id': uid
        })
    )
    logger.info(f'Queued background check status checks')
    return report_key
    