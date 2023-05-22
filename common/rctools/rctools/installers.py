"""Helper methods for installer api"""
import json
import logging
import os
from typing import List

from boto3.dynamodb.conditions import Key

from rctools.aws.cognito import (create_user_in_user_pool,
                                 flatten_user_attributes,
                                 get_user_from_user_pool, get_user_groups,
                                 list_users_from_user_pool, merge_user_data,
                                 update_user_attributes)
from rctools.aws.dynamodb import (KEY_COND_EQ, DynamoPrimaryKey, delete_dynamo_record,
                                  create_dynamo_record, fetch_items_by_gsi,
                                  fetch_items_by_pk, update_dynamo_record)
from rctools.aws.s3 import get_object_from_s3, put_object_into_s3
from rctools.models.users import Installer, InstallerUser
from rctools.models.jobs import JobTicket
from rctools.users import get_admin_user_data_from_s3
from rctools.utils import mk_timestamp
from rctools.zip_codes import get_zip_codes_in_radius

OWNER_ADMIN_GROUP_ID = os.getenv('OWNER_ADMIN_GROUP_ID')
MANAGER_GROUP_ID = os.getenv('MANAGER_GROUP_ID')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_installer(cognito_client, s3_client, pool_id, bucket, data) -> str:
    """Creates a full installer, returning the newly created user ID"""
    cognito_resp = create_installer_user(cognito_client, pool_id, data)
    user_id = cognito_resp['User']['Username']
    put_installer_data_into_s3(s3_client, bucket, user_id, data)
    return user_id


def create_installer_user(cognito_client, pool_id, data):
    """Creates a new installer in Cognito"""
    logger.info('Creating installer user in user pool')
    user = InstallerUser(**data).dict()
    return create_user_in_user_pool(cognito_client, pool_id, user, password=data.get('password'))


def get_installer(cognito_client, s3_client, pool_id, bucket, user_id) -> dict:
    """Returns an installer user by ID"""
    logger.info(f'Getting installer user {user_id}')
    cognito_user = get_user_from_user_pool(cognito_client, pool_id, user_id)
    flatten_user_attributes(cognito_user)
    user_data = get_installer_data_from_s3(s3_client, bucket, user_id)
    return merge_user_data(cognito_user, user_data)


def get_installers_for_company(cognito_client, s3_client, pool_id, bucket, company_id):
    installer_users = list_users_from_user_pool(cognito_client, pool_id)
    data = []
    for user in installer_users:
        uid = user['Username']
        user_data = get_installer_data_from_s3(s3_client, bucket, uid)
        if company_id:
            if user_data.get('company_id') == company_id:
                data.append(merge_user_data(user, user_data))
    return data


def get_installer_data_from_s3(s3_client, bucket, user_id):
    """Returns extra installer user data stored in S3"""
    return get_object_from_s3(s3_client, bucket, f'installers/{user_id}.json', {})


def get_pool_attributes(pool_res, user):
    user['Attributes'] = pool_res['User']['Attributes']
    user['id'] = pool_res['User']['Username']
    # user['Enabled'] = pool_res['User']['Enabled']
    # user['UserStatus'] = pool_res['User']['UserStatus']
    # user['UserLastModifiedDate'] = pool_res['User']['UserLastModifiedDate']
    # user['UserCreateDate'] = pool_res['User']['UserCreateDate']
    return user


def update_installer_data_in_cognito(cognito_client, pool_id, installer_id, data):
    user = InstallerUser(**data).dict()
    attributes = [
        # {
        #     'Name': 'given_name',
        #     'Value': user['given_name']
        # },
        {
            'Name': 'name',
            'Value': user['name']
        },
        {
            'Name': 'phone_number',
            'Value': user['phone_number']
        },
        {
            'Name': 'email',
            'Value': user['email']
        },
    ]
    update_user_attributes(cognito_client, installer_id, attributes, pool_id)


def put_installer_data_into_s3(s3_client, bucket, user_id, data):
    """Updates installer user data in S3"""
    InstallerUser.strip_cognito_fields(data)
    logger.info(f'Updating installer user {user_id} with {data}')
    return put_object_into_s3(s3_client, bucket, f'installers/{user_id}.json', json.dumps(data))


def update_installer_data_in_s3(s3_client, bucket, user_id, data):
    """Updates an existing installer user data object in S3 with new data"""
    user_data = get_installer_data_from_s3(s3_client, bucket, user_id)
    user_data.update(data)
    put_installer_data_into_s3(s3_client, bucket, user_id, user_data)


def update_installer_job_data_in_s3(s3_client, bucket, user_id, job_data):
    """Appends the new installer job data to user data object in S3"""
    user_data = get_installer_data_from_s3(s3_client, bucket, user_id)
    if user_data.get('jobs') is not None:
        user_data['jobs'].append(job_data) # XXX list or dict or?
        return put_installer_data_into_s3(s3_client, bucket, user_id, user_data)
    user_data['jobs'] = []
    user_data['jobs'].append(job_data) 
    put_installer_data_into_s3(s3_client, bucket, user_id, user_data)


def update_installer_service_area(s3_client, service_area_table, zip_bucket, installer_id, zip_code, radius):
    """
    Deletes all installer entries from the service area table and repopulates using values from the
    zip code distance bucket, depending on the radius
    """ 
    # Delete old rows
    pk = DynamoPrimaryKey()
    pk.partition = {'installer_id': installer_id}
    pagination_token = None
    logger.info('Deleting old service area entries')
    while True:
        items, cursor_token = fetch_items_by_gsi(service_area_table, pk, 'gsiInstallerIndex', cursor_token=pagination_token)
        logger.info(f'Deleting {len(items)}')
        for i in items:
            row_pk = {'zip_code': i['zip_code'], 'ts': i['ts']}
            delete_dynamo_record(service_area_table, row_pk)
        pagination_token = cursor_token
        if not pagination_token:
            break
    # Fetch pre-calculated zip codes from bucket
    zips = get_zip_codes_in_radius(s3_client, zip_bucket, zip_code, radius)
    logger.info(f'Found {len(zips)} zips')
    for idx, z in enumerate(zips):
        ts = mk_timestamp() + idx  # ensure unique ts for dynamo key
        create_dynamo_record(service_area_table, {'zip_code': z, 'installer_id': installer_id, 'ts': ts})


def get_user_company(s3_client, bucket, username):
    """Returns the company the username belongs to"""
    logger.info(f'Getting company for user {username}')
    s3_data = get_admin_user_data_from_s3(s3_client, bucket, username)
    return s3_data.get('company_id')


def is_company_admin(client, pool_id, username):
    """Returns true if user is in a company admin user group otherwise false"""
    user_groups = get_user_groups(client, pool_id, username)
    group_names = [group['GroupName'] for group in user_groups]
    if any(company_admins in group_names for company_admins in [OWNER_ADMIN_GROUP_ID, MANAGER_GROUP_ID]):
        return True
    return False


def in_service_area(installer_zip, job_zip):
    """Fetches installer s3 data and returns whether job zip matches installer zip"""
    # XXX Should take into account service area and distance between addresses
    if installer_zip == job_zip:
        return True
    return False


def in_installer_scope(installer_service, tier):
    """Returns whether installer can handle job tier"""
    basic = tier in ['BI-1','BI-2','BI-3'] and installer_service['basic']
    intermediate = tier in ['II-1', 'II-2', 'II-3'] and installer_service['intermediate']
    advanced = tier in ['AI-1', 'AI-2', 'AI-3'] and installer_service['advanced']
    advanced80 = tier in ['AI80-1', 'AI80-2', 'AI80-3'] and installer_service['advanced80']

    if basic or intermediate or advanced or advanced80:
        return True
    return False

# TODO utilize pagination tokens in React Admin instead of start/end, which doesn't really work for cognito/dynamo
def get_all_installers(cognito_client, s3_client, pool_id, bucket, pagination_token=None, limit=20) -> List[Installer]:
    installers = list_users_from_user_pool(cognito_client, pool_id)
    for installer in installers:
        user_data = get_installer_data_from_s3(s3_client, bucket, installer['Username'])
        installer = merge_user_data(installer, user_data)
    return installers


def get_installer_zip(s3_client, bucket, user_id):
    """Fetches installer s3 data and returns installer zip code"""
    data = get_object_from_s3(s3_client, bucket, f'installers/{user_id}.json', {})
    logger.info(f'installer data for zip is {data}')
    return data.get('zip')


def get_installer_jobs_from_dynamo(jobs_table, installer_id, limit=20):
    """
    Queries a dyanmo table for any jobs assigned to the installer
    """
    logger.info(f'Checking for jobs for user {installer_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {'installer_id': installer_id}
    
    jobs, pagination_token = [], None
    while True:
        # Query the customer's tickets using the jobs table
        items, cursor_token = fetch_items_by_gsi(jobs_table, pk, 'installer_id', cursor_token=pagination_token)
        # Then pull the whole ticket
        for i in items:
            job_pk = DynamoPrimaryKey()
            job_pk.partition = {'ticket_id': i['ticket_id']}
            logger.info(f'Fetching ticket_id {i["ticket_id"]}')
            job_items, _ = fetch_items_by_pk(jobs_table, job_pk)
            jobs += job_items
        pagination_token = cursor_token
        if len(items) > limit:
            break
        if not pagination_token:
            break
    logger.info(f'Returning {len(jobs)} job(s)')
    return jobs


def update_installer_job(table, data, id):
    """Update exiting job ticket in jobs table"""
    logger.info(f'Attaching data {data} to {id}')
    job_ticket = get_installer_job(table, id)
    update_data = {**job_ticket, **data}
    update_dynamo_record(table, {'ticket_id': update_data.pop('ticket_id'), 'ts': update_data.pop('ts')}, update_data)
    return job_ticket


def get_installer_job(table, id):
    response = table.query(
        KeyConditionExpression=Key('ticket_id').eq(id)
    )
    items = response.get("Items", None)
    if items:
        return JobTicket(**items[0]).dict()
    logger.warn('No job ticket found.')


def add_photo_to_installer_data(s3_client, bucket, user_id, data):
    """Adds image_id to installer"""
    user_data = get_installer_data_from_s3(s3_client, bucket, user_id)
    if user_data.get('images') == None:
        user_data['images'] = []

    user_data['images'].append({data.type, data.image_id}) # Only saving the image_id and type to the installer

    update_installer_data_in_s3(s3_client, bucket, user_id, user_data)
