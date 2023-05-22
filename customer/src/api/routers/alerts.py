import logging
import os
import stat
from typing import Optional
from xmlrpc.client import Boolean

import boto3
from fastapi import APIRouter, Header, status
from rctools.aws.cognito import get_user_with_access_token
from rctools.alerts import check_for_user_alerts
from rctools.customers import update_customer_data_in_s3
from rctools.models import AlertsResponse
from rctools.utils import mk_timestamp

ALERTS_TABLE = os.environ.get('ALERTS_TABLE')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')

dynamodb = boto3.resource('dynamodb')
alerts_table = dynamodb.Table(ALERTS_TABLE)


@router.get('/alerts', response_model=AlertsResponse, status_code=status.HTTP_200_OK)
def check_for_new_customer_alerts(X_Amz_Access_Token: Optional[str] = Header(default=None)) -> AlertsResponse:
    """
    Checks for any alerts after the given timestamp for an authenticated customer
    user.
    """
    logger.info('Checking for customer alerts')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    response = AlertsResponse()
    response.alerts = check_for_user_alerts(alerts_table, uid)
    logger.info(f'Found {len(response.alerts)} alert(s) for user {uid}')
    logger.info(ALERTS_TABLE)
    return response
