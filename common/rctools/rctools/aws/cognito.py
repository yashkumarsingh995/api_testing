"""Helper methods for pulling user profiles from Cognito"""
import logging

from typing import Optional, Union

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_user_in_user_pool(client: str, pool_id: str, user: dict, password=Optional[str]):
    """
    Creates a new user in the given user pool. If a password if provided, it skips the default
    Cognito process with temporary passwords, confirms the user and manually sets the password
    itself
    """
    logger.info(f'Creating user in pool {pool_id} with password' if password else f'Creating user in {pool_id}')
    attributes = get_user_attributes(user)
    params = {
        'UserPoolId': pool_id,
        'Username': user['email'],
        'UserAttributes': attributes,
        'DesiredDeliveryMediums': [
            'EMAIL',
        ]
    }
    if password:
        params['MessageAction'] = 'SUPPRESS'

    resp = client.admin_create_user(**params)
    if password:
        client.admin_set_user_password(
            UserPoolId=pool_id,
            Username=user['email'],
            Password=password,
            Permanent=True
        )
    logger.info('Setting email verified')
    client.admin_update_user_attributes(
        UserPoolId=pool_id,
        Username=user['email'],
        UserAttributes=[
            {
                'Name': 'email_verified',
                'Value': 'true'
            },
            {
                'Name': 'email',
                'Value': user['email']
            },
        ]
    )
    return resp


def add_pool_attributes(user, required_attributes):
    for attribute in required_attributes:
        user['Attributes'].append(
            ({'Name': attribute, 'Value': user[attribute]}))
    return user


def format_phone_number(phone: str):
    """
    Modifies a phone number to be in the expected Cognito format. 
    Cognito is extra picky about phone number validation as it can provide SMS.

    This method assumes phone numbers already have 7-8 characters as validated
    by a UI and is only valid for US numbers
    """
    phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')  # Remove all dashes and spaces
    if len(phone) == 11:
        phone = f'+{phone}'
    if len(phone) == 10:
        phone = f'+1{phone}'
    return phone


def disable_user(client, username, pool_id):
    logger.info(f'Deleting user {username}')
    return client.admin_disable_user(
        UserPoolId=pool_id,
        Username=username
    )


def get_user_attributes(user: dict) -> list:
    attributes = []
    if user.get('name') is None:
        user['name'] = f'{user.pop("given_name")} {user.pop("family_name")}'
    required_attributes = ['email', 'phone_number', 'name']
    for attribute in required_attributes:
        if attribute == 'phone_number':
            user[attribute] = format_phone_number(user[attribute])
        attributes.append({'Name': attribute, 'Value': user[attribute]})
    return attributes


def get_user_with_access_token(client, access_token):
    user = client.get_user(
        AccessToken=access_token
    )
    return user


def get_user_from_user_pool(client, pool_id, username):
    user = client.admin_get_user(
        Username=username,
        UserPoolId=pool_id
    )
    return user


def add_user_to_group(client, pool_id, username, group_name):
    return client.admin_add_user_to_group(
        UserPoolId=pool_id,
        Username=username,
        GroupName=group_name
    )


def get_user_groups(client, pool_id, username):
    resp = client.admin_list_groups_for_user(
        Username=username,
        UserPoolId=pool_id
    )
    return resp.get('Groups', [])


def update_user_attributes(client, username, attributes, pool_id):
    return client.admin_update_user_attributes(
        UserPoolId=pool_id,
        Username=username,
        UserAttributes=attributes
    )


def delete_user(client, username, pool_id):
    return client.admin_delete_user(
        UserPoolId=pool_id,
        Username=username
    )


def get_access_token_from_header(headers: Union[str, dict]):
    if isinstance(headers, str):
        return headers.replace('Bearer ', '')
    # else, it's a dict
    authorization = headers['Authorization']
    if 'Bearer' in authorization:
        return authorization.replace('Bearer ', '')
    return authorization


def list_users_from_user_pool(client, pool_id, pagination_token=None, limit=None):
    users = []
    params = {
        'UserPoolId': pool_id,
    }
    if limit:
        params['Limit'] = limit
    while True:
        if pagination_token:
            params['PaginationToken'] = pagination_token
        resp = client.list_users(**params)
        users += [u for u in resp['Users'] if u['Enabled'] is True]
        if not resp.get('PaginationToken'):
            break
        pagination_token = resp['PaginationToken']
    return users


def merge_user_data(user, data):
    user.update(data)
    flatten_user_attributes(user)
    # Assign id explicitly
    if 'sub' in user:
        user['id'] = user['sub']
    return user


def flatten_user_attributes(user):
    """
    Helper method for applying the Cognito attributes array to the top-level
    user object. 
    """
    # Cognito uses the key Attributes for fetch responses and UserAttributes for create or update responses
    for label in ['Attributes', 'UserAttributes']:
        if label in user:
            for attr in user.pop(label):
                name = attr['Name']
                value = attr['Value']
                user[name] = value
    # Remove metadata
    user.pop('ResponseMetadata', None)
    return user
