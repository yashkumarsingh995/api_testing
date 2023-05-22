import json
import logging
import os
from operator import itemgetter
from typing import List, Optional

import boto3
import botocore
from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, Request, Response, status
from fastapi.responses import JSONResponse
from rctools.alerts import (add_user_alert,
                            create_certification_in_progress_alert)
from rctools.aws.cognito import (disable_user, get_user_from_user_pool,
                                 get_user_with_access_token,
                                 list_users_from_user_pool, merge_user_data)
from rctools.company import (get_company_installer_by_code,
                             put_company_installer_code)
from rctools.exceptions import UserNotAuthorizedToEditInstaller
from rctools.installers import (get_installer_data_from_s3, get_user_company,
                                is_company_admin, put_installer_data_into_s3,
                                update_installer_data_in_cognito,
                                update_installer_data_in_s3, update_installer_service_area)
from rctools.jobs import get_job_tickets
from rctools.models import Installer, NewInstallerResponse
from rctools.users import is_rc_admin
from rctools.utils import mk_timestamp
from rctools.installers import get_installer as get_full_installer
from utils import build_content_range_header, filter_results, parse_params

ADMIN_USER_POOL_ID = os.environ.get('ADMIN_USER_POOL_ID')
COMPANY_DATA_BUCKET = os.getenv('COMPANY_DATA_BUCKET')
INSTALLER_CODES_TABLE = os.getenv('INSTALLER_CODES_TABLE')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
OWNER_ADMIN_GROUP_ID = os.environ.get('OWNER_ADMIN_GROUP_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')
JOBS_TABLE = os.environ.get('JOBS_TABLE')
RC_ADMIN_GROUP_ID = os.getenv('RC_ADMIN_GROUP_ID')
CERTIFICATION_LAMBDA_NAME = os.environ.get('CERTIFICATION_LAMBDA_NAME')
ALERTS_TABLE = os.environ.get('ALERTS_TABLE')
INSTALLER_SERVICE_AREA_TABLE_NAME = os.environ.get('INSTALLER_SERVICE_AREA_TABLE_NAME')
ZIP_CODE_DISTANCE_BUCKET = os.environ.get('ZIP_CODE_DISTANCE_BUCKET')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')


dynamodb = boto3.resource('dynamodb')
lambda_config = botocore.config.Config(retries={'max_attempts': 0})
lambda_client = boto3.client('lambda', config=lambda_config)
alerts_table = dynamodb.Table(ALERTS_TABLE)
jobs_table = dynamodb.Table(JOBS_TABLE)
installer_codes_table = dynamodb.Table(INSTALLER_CODES_TABLE)
service_area_table = dynamodb.Table(INSTALLER_SERVICE_AREA_TABLE_NAME)


@router.get('/installers', response_model=List[Installer], status_code=status.HTTP_200_OK)
def get_installers(request: Request, response: Response, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> List[Installer]:
    """
    Fetches either all installers for admin users or a subset by company for company
    admin or support users
    """
    logger.info('Fetching installers')
    company_id = None
    if X_Amz_Access_Token:
        # Access token will exist on all almost all requests; this condition allows requests from /docs endpoint on dev
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        uid = user['Username']
        if is_company_admin(cognito_client, ADMIN_USER_POOL_ID, uid):
            company_id = get_user_company(s3_client, USER_DATA_BUCKET, uid)
            logger.info(f'Fetching company installers for {company_id}')
    installer_users = list_users_from_user_pool(cognito_client, INSTALLER_USER_POOL_ID)

    data = []
    job_data = get_job_tickets(jobs_table)

    for user in installer_users:
        uid = user['Username']
        user_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, uid)
        user_data['jobs'] = [ticket for ticket in job_data if ticket.get('installer_id') == uid]

        if company_id:
            if user_data.get('company_id') == company_id:
                data.append(merge_user_data(user, user_data))
        else:
            data.append(merge_user_data(user, user_data))

    # get query params
    req_url = request.url
    start, end, field, order, search = parse_params(req_url)
    
    if field:
        # Handle fields not in data
        data = sorted(data, key=lambda k: (field not in k, k.get(field, None)), reverse=bool(order == 'DESC'))
    if search:
        search_fields = ['name', 'id', 'type', 'state', 'region']
        data = filter_results(data, search, search_fields)
    # response.headers['Content-Range'] = f'installers {start}-{end}/{len(data)}'
    response.headers['Content-Range'] = build_content_range_header('installers', data, start, end)
    return [Installer(**u) for u in data[start:end]]


@router.get('/installers/{id}', response_model=Installer, status_code=status.HTTP_200_OK)
def get_installer(id: str) -> Installer:
    """
    Fetches an installer user and returns data from the installer user pool 
    in cognito and its corresponding data in s3
    """
    logger.info(f'Getting user {id}')
    # XXX temp solution for seeing uncreated company installer with company user_id
    if len(id) < 7:
        installer = get_company_installer_by_code(installer_codes_table, id)
        installer['id'] = installer['code']
        logger.info(f'found database installer {installer}')
        return installer
        
    user = get_user_from_user_pool(cognito_client, INSTALLER_USER_POOL_ID, id)
    # pop metadata from individual user
    user.pop('ResponseMetadata')
    user_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, id)
    return Installer(**merge_user_data(user, user_data))


@router.put('/installers/{id}', response_model=Installer, status_code=status.HTTP_200_OK)
def edit_installer(id: str, update: Installer, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> Installer:
    """Updates installers attributes from admin user pool"""
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']
    try:
        if not is_rc_admin(cognito_client, ADMIN_USER_POOL_ID, uid, RC_ADMIN_GROUP_ID):
            if not is_company_admin(cognito_client, ADMIN_USER_POOL_ID, uid):
                # Not super admin or company admin is unauthorized
                raise UserNotAuthorizedToEditInstaller()
            # Check that company id matches
            else:
                # get_installer_data_from_s3()
                company_id = get_user_company(s3_client, USER_DATA_BUCKET, uid)
                # if company_id != update.company_id

        update_dict = update.dict(exclude_none=True)
        # user_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, id)
        user_data = get_full_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, id)
        logger.info(f'Updating installer {user_data}')
        user_data.update(update_dict)

        update_installer_data_in_cognito(cognito_client, INSTALLER_USER_POOL_ID, id, user_data)
        put_installer_data_into_s3(s3_client, USER_DATA_BUCKET, id, user_data)

        if update_dict.get('license'): # XXX will need to take into account manual cert
            pass # TODO move over code from /installer/certificaiton
        if update_dict.get('serviceArea'):
            logger.info(user_data)
            zip_code = user_data.get('zip')
            radius = update_dict['serviceArea'].get('radius')
            update_installer_service_area(s3_client, service_area_table, ZIP_CODE_DISTANCE_BUCKET, id, zip_code, radius)

        return Installer(**user_data)
    except ClientError as e:
        logger.exception('Error updating installer: {e}')
        return JSONResponse({'error': str(e)}, 400)


    # Old put request
    #     logger.info(f'Updating installer with data {update.dict()}')
    #     update_installer_data_in_s3(s3_client, USER_DATA_BUCKET, id, update.dict())
    #     update_installer_data_in_cognito(cognito_client, INSTALLER_USER_POOL_ID, id, update.dict())
    #     # user_data = get_user_from_user_pool(cognito_client, INSTALLER_USER_POOL_ID, id)

    #     # update_installer_data_in_cognito(cognito_client, INSTALLER_USER_POOL_ID, installer_id, update)
    #     return Installer(**update.dict())

    # except ClientError as e:
    #     logger.exception('Error updating installer: {e}')
    #     return JSONResponse({'error': str(e)}, 400)


@router.post('/installers', response_model=NewInstallerResponse, status_code=status.HTTP_201_CREATED)
def create_new_installer(installer: dict, request: Request, response: Response):
    """
    Creates a new installer in the installer user pool,
    adds the non-cognito data to s3 and returns a new installer with s3 data and cognito data
    """
    logger.info(f'POST request received with {installer}')
    code = put_company_installer_code(installer_codes_table, installer)
    logger.info(f'Generate code {code} for company installer')
    response = NewInstallerResponse(**{'user_id': code, 'id': code})
    return response
    # may need enabled for superadmins like Brian
    # uid = create_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, installer.dict())
    # logger.info(f'Creating installer with data {installer}')
    # return Installer(**{ **installer.dict(), 'uid': uid })


@router.delete('/installers/{id}')
def delete_installer(id: str):
    """End point that disables installer from installer user pool"""
    return disable_user(cognito_client, id, INSTALLER_USER_POOL_ID)


@router.post('/download/object', status_code=status.HTTP_201_CREATED)
def create_presigned_url(data: dict, request: Request, response: Response, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param data: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    logger.info(f'Generating presigned url for object {data}')
    try:
        response = s3_client.generate_presigned_url('get_object', Params={'Bucket': USER_DATA_BUCKET, 'Key': data['object_name']}, ExpiresIn=expiration)
        logger.info(f'generated url {response}')
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


@router.put('/installer/{installer_id}/certification', response_model=Installer, status_code=status.HTTP_200_OK)
def update_installer_certification(installer_id: str, update: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> Installer:
    """Updates installer with certification data and triggers the lambda to check it by state"""
    logger.info(f'Updating with certification info {update}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']
    try:
        if not is_rc_admin(cognito_client, ADMIN_USER_POOL_ID, uid, RC_ADMIN_GROUP_ID):
            if not is_company_admin(cognito_client, ADMIN_USER_POOL_ID, uid):
                # Not super admin or company admin is unauthorized
                raise UserNotAuthorizedToEditInstaller()

        installer_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, installer_id)
        installer = Installer(**{**installer_data, **update['update']}).dict()
        logger.info(f'Updated installer data {installer}')
        installer['license']['lastAttemptedAt'] = mk_timestamp()
        update_installer_data_in_s3(s3_client, USER_DATA_BUCKET, installer_id, installer)
        # Collect data for certification check
        state = installer['state']
        license_number = installer['license']['licenseNumber']
        # Add certification in-progress alert
        alert = create_certification_in_progress_alert(installer_id)
        add_user_alert(alerts_table, installer_id, alert)
        # Invoke lambda
        logger.info(f'Invoking certification lambda {CERTIFICATION_LAMBDA_NAME} with {state, license_number, installer_id}')
        # logger.info (f'with {state, license_number, installer_id}')
        resp = lambda_client.invoke(
            FunctionName=CERTIFICATION_LAMBDA_NAME,
            InvocationType='Event',  # async, repsonse will be saved to user data
            Payload=json.dumps({
                'state': state,
                'license_num': license_number,
                'installer_id': installer_id
            })
        )
        logger.info(resp)
        return installer
        
    except ClientError as e:
        logger.exception('Error updating installer: {e}')
        return JSONResponse({'error': str(e)}, 400)