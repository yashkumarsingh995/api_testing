import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse
from rctools.aws.cognito import get_user_with_access_token, merge_user_data
from rctools.customers import (get_customer_data_from_s3, put_customer_data_into_s3,
                               update_customer_data_in_cognito)
from rctools.models import Customer

USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')
CUSTOMER_USER_POOL_ID = os.getenv('CUSTOMER_USER_POOL_ID')

cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')


@router.put('/customer', status_code=status.HTTP_200_OK)
def edit_customer(user: dict,  X_Amz_Access_Token: Optional[str] = Header(default=None)) -> dict:
    """Updates customers attributes from customer user pool"""
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    customer_id = user['Username']
    logger.info(f'Updating customer {customer_id}')
    try:
        put_customer_data_into_s3(s3_client, USER_DATA_BUCKET, customer_id, user)
        return update_customer_data_in_cognito(cognito_client, CUSTOMER_USER_POOL_ID, customer_id, user)
    except ClientError as e:
        logger.exception('Error updating customer: {e}')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/customer', response_model=Customer, status_code=status.HTTP_200_OK)
def get_customer(X_Amz_Access_Token: Optional[str] = Header(default=None)) -> Customer:
    """
    Fetches a customer user and returns data from the customer user pool 
    in cognito and its corresponding data in s3
    """
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    user.pop('ResponseMetadata')
    user_data = get_customer_data_from_s3(s3_client, USER_DATA_BUCKET, user['Username'])
    return Customer(**merge_user_data(user, user_data))
