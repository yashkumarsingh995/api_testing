import json
import logging
import os
from typing import Optional

import boto3
from fastapi import APIRouter, Header, status
from rctools import get_user_with_access_token
from rctools.aws.cognito import merge_user_data
from rctools.company import update_company_service_area
from rctools.models import Admin
from rctools.users import get_admin_user_data_from_s3, update_admin_data_in_s3


ADMIN_USER_POOL_ID = os.environ.get('ADMIN_USER_POOL_ID')
CERTIFICATION_LAMBDA_NAME = os.environ.get('CERTIFICATION_LAMBDA_NAME')
INSTALLER_SERVICE_AREA_TABLE_NAME = os.environ.get('INSTALLER_SERVICE_AREA_TABLE_NAME')
OWNER_ADMIN_GROUP_ID = os.environ.get('OWNER_ADMIN_GROUP_ID')
RC_ADMIN_GROUP_ID = os.environ.get('RC_ADMIN_GROUP_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')
ZIP_CODE_DISTANCE_BUCKET = os.environ.get('ZIP_CODE_DISTANCE_BUCKET')


cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()

service_area_table = dynamodb.Table(INSTALLER_SERVICE_AREA_TABLE_NAME)



@router.get('/profile', status_code=status.HTTP_200_OK)
def get_current_user(X_Amz_Access_Token: Optional[str] = Header(default=None)) -> Admin:
    """Returns the currently logged in user"""
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    user_data = get_admin_user_data_from_s3(s3_client, USER_DATA_BUCKET, uid)
    return merge_user_data(user, user_data)


@router.put('/profile', status_code=status.HTTP_200_OK)
def update_current_user(update: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """"Updates the logged in user's profile"""
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    if update.get('license'):
        # Collect data for certification check
        logger.info('Received license data')
        user_data = get_admin_user_data_from_s3(s3_client, USER_DATA_BUCKET, uid)
        state = user_data['state']
        license_number = update['license'].get('licenseNumber')
        if license_number:
            # Invoke lambda
            logger.info(f'Invoking certification lambda {CERTIFICATION_LAMBDA_NAME}')
            resp = lambda_client.invoke(
                FunctionName=CERTIFICATION_LAMBDA_NAME,
                InvocationType='Event',  # async, repsonse will be saved to user data
                Payload=json.dumps({
                    'state': state,
                    'license_num': license_number,
                    'installer_id': uid
                })
            )
        logger.info(resp)
    elif update.get('serviceArea'):
        logger.info('Received service area data')
        user_data = get_admin_user_data_from_s3(s3_client, USER_DATA_BUCKET, uid)
        zip_code = user_data.get('zip')
        radius = update['serviceArea'].get('radius')
        if radius:
            logger.info('Updating company service area')
            update_company_service_area(s3_client, service_area_table, ZIP_CODE_DISTANCE_BUCKET, user_data['company_id'], zip_code, radius)
    
    update_admin_data_in_s3(s3_client, USER_DATA_BUCKET, uid, update)
    return {'uid': uid}
