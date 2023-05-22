import json
import logging
import os
from typing import Optional

import boto3
import botocore
from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse
from rctools.alerts import add_user_alert, create_certification_in_progress_alert
from rctools.aws.cognito import get_user_with_access_token, merge_user_data
from rctools.aws.s3 import get_object_from_s3, put_object_into_s3
from rctools.installers import (add_photo_to_installer_data, get_installer_data_from_s3, get_installer,
                                update_installer_service_area,
                                update_installer_data_in_s3, put_installer_data_into_s3)
from rctools.models import Installer
from rctools.models.users import InstallerImage
from rctools.utils import mk_timestamp
from rctools.rates import lookup_rate_by_state


ALERTS_TABLE = os.environ.get('ALERTS_TABLE')
CERTIFICATION_LAMBDA_NAME = os.environ.get('CERTIFICATION_LAMBDA_NAME')
INSTALLER_SERVICE_AREA_TABLE_NAME = os.environ.get('INSTALLER_SERVICE_AREA_TABLE_NAME')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')
ZIP_CODE_DISTANCE_BUCKET = os.environ.get('ZIP_CODE_DISTANCE_BUCKET')


cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
lambda_config = botocore.config.Config(retries={'max_attempts': 0})
lambda_client = boto3.client('lambda', config=lambda_config)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')

alerts_table = dynamodb.Table(ALERTS_TABLE)
service_area_table = dynamodb.Table(INSTALLER_SERVICE_AREA_TABLE_NAME)


@router.get('/installer', response_model=Installer, status_code=status.HTTP_200_OK)
def get_installer_from_access_token(X_Amz_Access_Token: Optional[str] = Header(default=None)) -> Installer:
    """
    This endpoint fetches an installer user and returns data from the installer user pool 
    in cognito and its corresponding data in s3
    """
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    # pop metadata from individual user
    user.pop('ResponseMetadata')
    user_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, user['Username'])
    return Installer(**merge_user_data(user, user_data))


@router.put('/installer', response_model=Installer, status_code=status.HTTP_200_OK)
def edit_installer(update: Installer, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> Installer:
    """Updates installers attributes from admin user pool"""
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    installer_id = user['Username']
    update_dict = update.dict(exclude_none=True)['update']
    try:
        user_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, installer_id)
        logger.info(f'User data {user_data}')
        logger.info(f'Update {update_dict}')
        user_data.update(update_dict)
        logger.info(f'Updated {user_data}')
        put_installer_data_into_s3(s3_client, USER_DATA_BUCKET, installer_id, user_data)
        if update_dict.get('license'):
            pass # TODO move over code from /installer/certificaiton
        if update_dict.get('serviceArea'):
            zip_code = user_data.get('zip')
            radius = update_dict['serviceArea'].get('radius')
            logger.info(f'Updating service area to {zip_code} and {radius}')
            update_installer_service_area(s3_client, service_area_table, ZIP_CODE_DISTANCE_BUCKET, installer_id, zip_code, radius)
        # update_installer_data_in_cognito(cognito_client, INSTALLER_USER_POOL_ID, installer_id, update)
        return Installer(**user, **update_dict)
    except ClientError as e:
        logger.exception('Error updating installer: {e}')
        return JSONResponse({'error': str(e)}, 400)


@router.put('/installer/certification', response_model=Installer, status_code=status.HTTP_200_OK)
def update_installer_certification(update: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> Installer:
    """Updates installer with certification data and triggers the lambda to check it by state"""
    logger.info(f'Updating with certification info {update}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    installer_id = user['Username']

    try:
        installer_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, installer_id)
        installer = Installer(**{**installer_data, **update['update']}).dict()
        installer['license']['lastAttemptedAt'] = mk_timestamp()
        update_installer_data_in_s3(s3_client, USER_DATA_BUCKET, installer_id, installer)
        # Collect data for certification check
        state = installer['state']
        license_number = installer['license']['licenseNumber']
        # Add certification in-progress alert
        alert = create_certification_in_progress_alert(installer_id)
        add_user_alert(alerts_table, installer_id, alert)
        # Invoke lambda
        logger.info(f'Invoking certification lambda {CERTIFICATION_LAMBDA_NAME}')
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


@router.get('/installer/rates', status_code=status.HTTP_200_OK)
def get_installer_rates_by_state(X_Amz_Access_Token: Optional[str] = Header(default=None)) -> dict:
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']
    installer = get_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, uid)
    return lookup_rate_by_state(installer['state'])


# @router.post('/installer/image', response_model=InstallerImage, status_code=status.HTTP_201_CREATED)
# def post_installer_image(image: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> InstallerImage:
#     """Uploads a an installer image"""
#     user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
#     installer_id = user['Username']
#     image['uid'] = installer_id
#     new_installer_image = InstallerImage(**image).dict()
#     s3_path = f"installers/{installer_id}/images/{new_installer_image['image_id']}.json"
#     try:
#         add_photo_to_installer_data(s3_client, USER_DATA_BUCKET, installer_id, new_installer_image)
#         put_object_into_s3(s3_client, USER_DATA_BUCKET, s3_path, json.dumps(new_installer_image))
#         return new_installer_image
#     except ClientError as e:
#         logger.exception('Error uploading photo: {e}')
#         return JSONResponse({'error': str(e)}, 400)


# @router.post('/installer/image/profile', response_model=InstallerImage, status_code=status.HTTP_201_CREATED)
# def post_profile_image(image: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> InstallerImage:
#     """Uploads a file to use as the installer's profile image"""
#     user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
#     installer_id = user['Username']
#     image['uid'] = installer_id
#     new_installer_image = InstallerImage(**image).dict()
#     s3_path = f"installers/{installer_id}/images/profile/{new_installer_image['image_id']}.json"
#     try:
#         # add_photo_to_installer_data(s3_client, USER_DATA_BUCKET, installer_id, new_installer_image)
#         put_object_into_s3(s3_client, USER_DATA_BUCKET, s3_path, json.dumps(new_installer_image))
#         return new_installer_image
#     except ClientError as e:
#         logger.exception('Error uploading photo: {e}')
#         return JSONResponse({'error': str(e)}, 400)


@router.post('/image/{type}', response_model=InstallerImage, status_code=status.HTTP_201_CREATED)
def post_type_image(image: dict, type: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> InstallerImage:
    """Uploads an image of a specific type in s3"""
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    installer_id = user['Username']
    image['uid'] = installer_id
    new_installer_image = InstallerImage(**image).dict()
    s3_path = f"installers/{installer_id}/images/{type}/{new_installer_image['image_id']}.json"
    try:
        add_photo_to_installer_data(s3_client, USER_DATA_BUCKET, installer_id, new_installer_image)
        put_object_into_s3(s3_client, USER_DATA_BUCKET, s3_path, json.dumps(new_installer_image))
        return new_installer_image
    except ClientError as e:
        logger.exception('Error uploading photo: {e}')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/image/{type}', response_model=InstallerImage, status_code=status.HTTP_200_OK)
def get_profile_image(type: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> InstallerImage:
    """Gets an image to use as the installer's profile image"""
    try:
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        installer_id = user['Username']
        return get_object_from_s3(s3_client, USER_DATA_BUCKET, f'installers/{installer_id}/images/{type}/', {})
    except ClientError as e:
        logger.exception('Error uploading photo: {e}')
        return JSONResponse({'error': str(e)}, 400)