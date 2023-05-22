import logging
import os
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, Request, Response, status
from fastapi.responses import JSONResponse
from rctools.aws.cognito import (add_pool_attributes, add_user_to_group,
                                 create_user_in_user_pool, disable_user,
                                 get_user_from_user_pool, get_user_groups,
                                 get_user_with_access_token,
                                 list_users_from_user_pool, merge_user_data,
                                 update_user_attributes)
from rctools.installers import get_user_company, is_company_admin
from rctools.models import Admin
from rctools.users import get_admin_user_data_from_s3, is_rc_admin
from utils import filter_results, parse_params

ADMIN_USER_POOL_ID = os.environ.get('ADMIN_USER_POOL_ID')
RC_ADMIN_GROUP_ID = os.environ.get('RC_ADMIN_GROUP_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')


@router.get('/admins', response_model=List[dict], status_code=status.HTTP_200_OK)
def get_admin_users(request: Request, response: Response, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> List[dict]:  # TODO return dict not Admin until models while models are in flux
    """
    Returns all users in the admin user pool, applies user group data,
    search, and pagination
    """
    try:
        company_id = None

        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        uid = user['Username']

        if is_company_admin(cognito_client, ADMIN_USER_POOL_ID, uid):
            company_id = get_user_company(s3_client, USER_DATA_BUCKET, uid)
            logger.info(f'Fetching company installers for {company_id}')

        users = list_users_from_user_pool(cognito_client, ADMIN_USER_POOL_ID)
        data = []

        for u in users:
            user_id = u['Username']
            user_data = get_admin_user_data_from_s3(s3_client, USER_DATA_BUCKET, user_id)
            u['id'] = user_id
            u['groups'] = get_user_groups(cognito_client, ADMIN_USER_POOL_ID, user_id)
            if company_id:
                if user_data.get('company_id') == company_id:
                    data.append(merge_user_data(u, user_data))
            elif is_rc_admin(cognito_client, ADMIN_USER_POOL_ID, uid, RC_ADMIN_GROUP_ID):
                data.append(merge_user_data(u, user_data))
            

        # get query params
        req_url = request.url
        start, end, field, order, search = parse_params(req_url)

        if field:
            # Handle fields not in data
            data = sorted(data, key=lambda k: (field not in k, k.get(field, None)), reverse=bool(order == 'DESC'))

        # TODO implement pagination with tokens
        start = 0
        end = len(data)

        if search:
            search_fields = ['name', 'id', 'email']
            data = filter_results(data, search, search_fields)

        response.headers['Content-Range'] = f'users {start}-{end}/{len(data)}'
        return [u for u in data[start:end]]
    except ClientError as e:
        logger.exception('Error updating installer: {e}')
        return JSONResponse({'error': str(e)}, 400)
    


@router.get('/admins/{id}', response_model=Admin, status_code=status.HTTP_200_OK)
def get_admin(id: str):
    """
    End point that fetches and returns user data on a cognito user from
    the admin user pool
    """
    logger.info(f'Fetching user {id}')
    user = get_user_from_user_pool(cognito_client, ADMIN_USER_POOL_ID, id)
    user_data = get_admin_user_data_from_s3(s3_client, USER_DATA_BUCKET, id)
    merge_user_data(user, user_data)
    user['id'] = id
    if 'groups' not in user:
        user['groups'] = get_user_groups(cognito_client, ADMIN_USER_POOL_ID, id)
    return Admin(**user)


@router.post('/admins', response_model=Admin, status_code=status.HTTP_201_CREATED)
def create_admin(user: dict) -> dict:
    """
    End point that creates a new user in the admin user pool, 
    and adds user to the admin user group
    """
    if user['group'] == 'admin':
        group_name = 'admin'
        user.pop('group')
        user = create_user_in_user_pool(
            cognito_client, ADMIN_USER_POOL_ID, user)
    # new_user = user.pop('User')
    new_user = user['User']
    required_attributes = [
        'Username', 'UserLastModifiedDate', 'UserCreateDate', 'Enabled', 'UserStatus']

    new_user = add_pool_attributes(new_user, required_attributes)
    new_user = merge_user_data(new_user, None, new_user['Attributes'])
    uid = new_user['Username']
    if group_name == 'admin':
        add_user_to_group(cognito_client, ADMIN_USER_POOL_ID,
                          uid, RC_ADMIN_GROUP_ID)
        groups = get_user_groups(cognito_client, ADMIN_USER_POOL_ID, uid)
    new_user['groups'] = groups['Groups']
    new_user['phone_number_verified'] = 'false'
    return Admin(**new_user)


@router.put('/admins/{id}', response_model=Admin, status_code=status.HTTP_200_OK)
def edit_admin(user: dict) -> dict:
    """End point that updates user attributes from admin user pool"""
    username = user['Username']
    # current attributes allowed to be updated
    attributes = [
        {
            'Name': 'phone_number',
            'Value': user['phone_number']
        },
        {
            'Name': 'email',
            'Value': user['email']
        },
        # {
        #     'Name': 'GroupName',
        #     'Value': user['groups'][0]['GroupName']
        # }
    ]
    update_user_attributes(cognito_client, username,
                           attributes, ADMIN_USER_POOL_ID)
    return Admin(**user)


@router.delete('/admins/{id}', status_code=status.HTTP_200_OK)
def delete_admin(id: str):
    """End point that deletes user from admin user pool"""
    return disable_user(cognito_client, id, ADMIN_USER_POOL_ID)
