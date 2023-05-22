import logging
import os
from typing import Optional

import boto3
from fastapi import APIRouter, Header, status
from rctools.aws.cognito import get_user_with_access_token
from rctools.alerts import check_for_user_alerts
from rctools.installers import get_installer_data_from_s3, update_installer_data_in_s3
from rctools.models import AlertsResponse
from rctools.utils import mk_timestamp

ALERTS_TABLE = os.environ.get('ALERTS_TABLE')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

alerts_table = dynamodb.Table(ALERTS_TABLE)


@router.get('/alerts', response_model=AlertsResponse, status_code=status.HTTP_200_OK)
def check_for_new_installer_alerts(X_Amz_Access_Token: Optional[str] = Header(default=None)) -> AlertsResponse:
    """
    Checks for any alerts after the given timestamp for an authenticated installer
    user.
    
    If no timestamp is given in the parameters, it checks for alerts up to 3 days old, adding older alerts
    to the list until it exceeds twenty or finds no more alerts.
    """
    logger.info('Checking for installer alerts')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    response = AlertsResponse()
    response.alerts = check_for_user_alerts(alerts_table, uid)
    logger.info(f'Found {len(response.alerts)} alert(s) for user {uid}')
    logger.info(ALERTS_TABLE)
    return response

