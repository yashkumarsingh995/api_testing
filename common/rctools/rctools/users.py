import json
import jwt
import logging

from rctools.aws.cognito import (
    flatten_user_attributes, get_user_groups, get_user_from_user_pool, merge_user_data
)
from rctools.aws.s3 import get_object_from_s3, put_object_into_s3
from rctools.models.users import AdminUser


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def decode_access_token(access_token: str):
    """Decodes the JWT access token from cognito"""
    return jwt.decode(access_token, algorithms=['RS256'], options={'verify_signature': False})


def get_admin_user(cognito_client, s3_client, pool_id, bucket, user_id) -> dict:
    """Returns an admin user by ID"""
    logger.info(f'Getting admin user {user_id}')
    cognito_user = get_user_from_user_pool(cognito_client, pool_id, user_id)
    flatten_user_attributes(cognito_user)
    user_data = get_admin_user_data_from_s3(s3_client, bucket, user_id)
    return merge_user_data(cognito_user, user_data)


def get_admin_user_data_from_s3(s3_client, bucket, user_id):
    """Returns extra installer user data stored in S3"""
    return get_object_from_s3(s3_client, bucket, f'admins/{user_id}.json', {})


def get_user_pool_from_access_token(access_token: str):
    """Pulls the user pool from the logged in user's access token"""
    decoded = decode_access_token(access_token)
    iss = decoded['iss']
    return '/'.split(iss)[-1]


def is_rc_admin(client, pool_id, username, admin_group_id):
    """Returns true if user is in the RC admin user group otherwise false"""
    user_groups = get_user_groups(client, pool_id, username)
    group_names = [group['GroupName'] for group in user_groups]
    if any(user_group in group_names for user_group in [admin_group_id]):
        return True
    return False


def put_admin_user_data_into_s3(s3_client, bucket, user_id, data):
    """Updates admin user data in S3"""
    AdminUser.strip_cognito_fields(data)
    logger.info(f'Updating admin user {user_id} with {data}')
    return put_object_into_s3(s3_client, bucket, f'admins/{user_id}.json', json.dumps(data))


def update_admin_data_in_s3(s3_client, bucket, user_id, data):
    """Updates an existing admin user data object in S3 with new data"""
    user_data = get_admin_user_data_from_s3(s3_client, bucket, user_id)
    user_data.update(data)
    put_admin_user_data_into_s3(s3_client, bucket, user_id, user_data)
