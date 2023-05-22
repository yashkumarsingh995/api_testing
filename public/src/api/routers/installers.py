import logging
import os
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, RedirectResponse
from models import (InstallerCodeResponse, QualificationResponse,
                    QualificationUserData, InstallersInYourAreaResponse)
from rate import get_rate
from rctools.aws.dynamodb import create_dynamo_record, update_dynamo_record
from rctools.aws.secrets import get_json_secret
from rctools.company import get_company_data, get_company_installer_by_code
from rctools.installers import create_installer, get_installer, update_installer_data_in_s3
from rctools.models import Installer, InstallerUser, NewInstallerResponse
from rctools.payments import create_connected_installer_account_link
from rctools.utils import create_random_code, mk_timestamp
from rctools.zip_codes import get_installers_by_zip


AWS_REGION_NAME = os.getenv('AWS_REGION_NAME')
COMPANY_DATA_BUCKET = os.getenv('COMPANY_DATA_BUCKET')
INSTALLER_CODES_TABLE = os.getenv('INSTALLER_CODES_TABLE')
INSTALLER_QUALIFICATION_TABLE = os.getenv('INSTALLER_QUALIFICATION_TABLE')
INSTALLER_SERVICE_AREA_TABLE = os.getenv('INSTALLER_SERVICE_AREA_TABLE')
INSTALLER_USER_POOL_ID = os.getenv('INSTALLER_USER_POOL_ID')
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

installer_codes_table = dynamodb.Table(INSTALLER_CODES_TABLE)
installer_qualification_table = dynamodb.Table(INSTALLER_QUALIFICATION_TABLE)
service_area_table = dynamodb.Table(INSTALLER_SERVICE_AREA_TABLE)


g_context = {}


def get_stripe_api_key():
    if 'stripe_api_key' not in g_context:
        secret = get_json_secret(secrets_client, STRIPE_PRIVATE_KEY, AWS_REGION_NAME)
        g_context['stripe_api_key'] = secret['api_key']
    return g_context['stripe_api_key']


@router.post('/installer', response_model=NewInstallerResponse)
def create_new_installer(data: Installer):
    """
    Creates a new installer user in Cognito. It will return a user id for the
    newly created user.

    Email and phone number are the only required fields, but the endpoint will accept
    any other additional fields that you want to store with the user object.
    """
    logger.info(f'Creating new installer user')  # Careful not to log data object and expose passwords
    try:
        user_id = create_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, data.dict())
        logger.info(f'Installer {user_id} created!')
        response = NewInstallerResponse(**{'user_id': user_id})
        return response
    except ClientError as e:
        logger.exception('Error creating new installer')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/installer/code/{code}', response_model=InstallerCodeResponse)
def get_installer_by_code(code: str):
    """
    Looks up an installer by sign-up code provided by a company admin. If valid, it will return
    the company data including contact information (like email address and phone number).
    """
    response = InstallerCodeResponse()
    logger.info(f'Fetching installer with user_id: {code}')
    installer = get_company_installer_by_code(installer_codes_table, code)
    if not installer:
        return JSONResponse({'error': 'Installer code not found'}, 404)
    if installer:
        response.installer = installer
        response.valid = True
        # Get company info
        company_id = installer['company_id']
        company = get_company_data(s3_client, COMPANY_DATA_BUCKET, company_id)
        if not company:
            return JSONResponse({'error': 'No valid company found for installer code'}, 400) 
        # response.contact_info = {
        #     'email': company['email'],
        #     'phone': company['phone_number']
        # }
    return response


@router.post('/installer/code/{code}', response_model=NewInstallerResponse)
def create_installer_by_code(code: str, data: Installer):
    """
    Creates an installer user from the company code created for them. The
    installer will automatically be assigned to the company the code was created in.

    An installer code can only be used once to create an installer user.
    """
    logger.info(f'Creating installer user from code {code}')
    logger.info(data)
    installer = get_company_installer_by_code(installer_codes_table, code)
    if installer and not installer.get('user_created'):
        # Create the installer user
        new_user = data.dict()
        new_user['company_id'] = installer['company_id']
        temp_password = 'X1' + create_random_code(16)
        new_user['password'] = temp_password
        user_id = create_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, new_user)
        logger.info(f'Installer {user_id} created!')
        response = NewInstallerResponse(**{'user_id': user_id, 'temp_password': temp_password})
        update_dynamo_record(installer_codes_table, {'code': code, 'ts': installer.pop('ts')}, {'user_created': True, 'user_id': user_id, 'valid': False })
        return response


@router.get('/installer/onboarding/complete', response_class=RedirectResponse, status_code=status.HTTP_301_MOVED_PERMANENTLY)
def redirects_user_back_to_installer_app():
    """Uses deep linking to direct the user back to the account setup onboarding screen"""
    return RedirectResponse('readicharge://onboarding/account/payment')


@router.get('/installer/onboarding/refresh')
def generates_new_account_link(uid: str, refresh_token: str):
    """
    Generates a new link for Stripe account onboarding for new installer users. This public endpoint
    is called by an authenticated installer and requires a refresh token added to the installer user
    when onboarding was started.
    """
    user = get_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, uid)
    api_key = get_stripe_api_key()
    account_id = user['payments']['connected_account_id']
    new_refresh_token = str(uuid4())
    if refresh_token == user['payments']['refresh_token']:
        update_installer_data_in_s3(
            s3_client, USER_DATA_BUCKET, uid, {'payments': {'connected_account_id': account_id, 'refresh_token': new_refresh_token}}
        )
        return create_connected_installer_account_link(
            api_key,
            account_id,
            f'https://{PUBLIC_API_ROOT}/installer/onboarding/refresh?uid={uid}&refresh_token={new_refresh_token}',
            f'https://{PUBLIC_API_ROOT}/installer/onboarding/complete'
        )


@router.get('/installers/{zip_code}', response_model=InstallersInYourAreaResponse)
def get_installers_in_your_area(zip_code: str) -> InstallersInYourAreaResponse:
    """
    Checks whether or not there are installers in a given zipcode. This is used by the
    customer app before the onboarding screens
    """
    logger.info(f'Searching for installers with zip {zip_code}')
    response = InstallersInYourAreaResponse()
    installer_ids = get_installers_by_zip(service_area_table, zip_code)
    logger.info(f'{len(installer_ids)} installer(s) found!')
    if installer_ids:
        response.installers_found = True
    return response


@router.post('/qualify', response_model=QualificationResponse)
def check_installer_qualification(user_data: QualificationUserData):
    """
    Records a request for qualification through the installer app and - provided all required fields
    are present - currently usually returns 'yes'.

    A dedicated qualification endpoint could be useful in the future though if ReadiCharge ever needs
    to be more selective or wants to update its selection critieria without updating the app
    """
    logger.info(f'Starting installer qualification request')
    logger.info(user_data)

    response = QualificationResponse()
    # Current requirements accepts all valid applicants
    if user_data.licensed and user_data.insured and user_data.agree_to_background_check:
        response.qualify = True
    # Record qualification request
    create_dynamo_record(installer_qualification_table, {
        **user_data.dict(),
        'qualifed': response.qualify,
        'ts': mk_timestamp()
    })
    # If true, grab current rate
    if response.qualify:
        response.current_rate = get_rate(user_data.state)
    # If false, attach error messages
    if not user_data.licensed:
        response.reasons.append('Not state licensed')
    if not user_data.insured:
        response.reasons.append('Not insured')
    if not user_data.agree_to_background_check:
        response.reasons.append('Must agree to background check')
    
    logger.info('Returning response')
    logger.info(response.json())
    return response
