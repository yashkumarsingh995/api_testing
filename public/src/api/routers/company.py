import logging
import os

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from rctools.company import create_company_admin, create_company_id, put_company_data
from rctools.models import CompanyAdmin
from models import NewCompanyAdminResponse

ADMIN_USER_POOL_ID = os.getenv('ADMIN_USER_POOL_ID')
COMPANY_DATA_BUCKET = os.getenv('COMPANY_DATA_BUCKET')
OWNER_ADMIN_GROUP_ID = os.getenv('OWNER_ADMIN_GROUP_ID')
USER_DATA_BUCKET = os.getenv('USER_DATA_BUCKET')


cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')


@router.post('/company/admin', response_model=NewCompanyAdminResponse)
def create_new_company_admin(data: CompanyAdmin):
    """
    Creates a new company admin user in Cognito. It will return a user id for the
    newly created user.

    Email and phone number are the only required fields, but the endpoint will accept
    any other additional fields that you want to store with the user object.
    """
    logger.info(f'Creating new company admin user')  # Careful not to log data object and expose passwords
    try:
        # Creating company
        company_id = create_company_id()
        data.company_id = company_id
        # Adding user
        user_id = create_company_admin(cognito_client, s3_client, ADMIN_USER_POOL_ID, OWNER_ADMIN_GROUP_ID, USER_DATA_BUCKET, data.dict())
        logger.info(f'Company admin {user_id} created!')
        # Saving company
        put_company_data(s3_client, COMPANY_DATA_BUCKET, {
            'id': company_id, 'account_owner_id': user_id
        })
        return NewCompanyAdminResponse(user_id=user_id, company_id=company_id)
    except ClientError as e:
        logger.exception('Error creating new company admin')
        return JSONResponse({'error': str(e)}, 400)
