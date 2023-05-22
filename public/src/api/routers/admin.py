import logging
import os
from uuid import uuid4

import boto3
from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from rctools.aws.secrets import get_json_secret
from rctools.payments import create_connected_installer_account_link
from rctools.users import get_admin_user, update_admin_data_in_s3


ADMIN_USER_POOL_ID = os.getenv('ADMIN_USER_POOL_ID')
AWS_REGION_NAME = os.getenv('AWS_REGION_NAME')
COMPANY_DATA_BUCKET = os.getenv('COMPANY_DATA_BUCKET')
PUBLIC_API_ROOT = os.getenv('PUBLIC_API_ROOT')
STAGE = os.getenv('STAGE')
STRIPE_PRIVATE_KEY = os.getenv('STRIPE_PRIVATE_KEY')
USER_DATA_BUCKET = os.getenv('USER_DATA_BUCKET')

cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()

s3_client = boto3.client('s3')
secrets_client = boto3.session.Session()


g_context = {}


def get_stripe_api_key():
    if 'stripe_api_key' not in g_context:
        secret = get_json_secret(secrets_client, STRIPE_PRIVATE_KEY, AWS_REGION_NAME)
        g_context['stripe_api_key'] = secret['api_key']
    return g_context['stripe_api_key']


@router.get('/admin/onboarding/complete', response_class=RedirectResponse, status_code=status.HTTP_301_MOVED_PERMANENTLY)
def redirects_user_back_to_admin_app():
    """Uses deep linking to direct the user back to the account setup onboarding screen"""
    return RedirectResponse(f'https://admin--${STAGE}.rcdevel.com/onboarding')


@router.get('/admin/onboarding/refresh')
def generates_new_account_link(uid: str, refresh_token: str):
    """
    Generates a new link for Stripe account onboarding for new admin users. This public endpoint
    is called by an authenticated admin and requires a refresh token added to the admin user
    when onboarding was started.
    """
    user = get_admin_user(cognito_client, s3_client, ADMIN_USER_POOL_ID, USER_DATA_BUCKET, uid)
    api_key = get_stripe_api_key()
    account_id = user['payments']['connected_account_id']
    new_refresh_token = str(uuid4())
    if refresh_token == user['payments']['refresh_token']:
        update_admin_data_in_s3(
            s3_client, USER_DATA_BUCKET, uid, {'payments': {'connected_account_id': account_id, 'refresh_token': new_refresh_token}}
        )
        return create_connected_installer_account_link(
            api_key,
            account_id,
            f'https://{PUBLIC_API_ROOT}/admin/onboarding/refresh?uid={uid}&refresh_token={new_refresh_token}',
            f'https://{PUBLIC_API_ROOT}/admin/onboarding/complete'
        )