"""Helper methods for customer api"""
import json
import logging
import os
from typing import List

from rctools.aws.cognito import (create_user_in_user_pool,
                                 flatten_user_attributes,
                                 get_user_from_user_pool,
                                 list_users_from_user_pool, merge_user_data,
                                 update_user_attributes)
from rctools.aws.dynamodb import (KEY_COND_EQ, DynamoPrimaryKey,
                                  fetch_items_by_gsi, fetch_items_by_pk)
from rctools.aws.s3 import get_object_from_s3, put_object_into_s3
from rctools.models import Customer, CustomerUser

logger = logging.getLogger()

OWNER_ADMIN_GROUP_ID = os.getenv('OWNER_ADMIN_GROUP_ID')
MANAGER_GROUP_ID = os.getenv('MANAGER_GROUP_ID')


def create_customer(cognito_client, s3_client, pool_id, bucket, data) -> str:
    """Creates a full customer, returning the newly created user ID"""
    cognito_resp = create_customer_user(cognito_client, pool_id, data)
    user_id = cognito_resp['User']['Username']
    put_customer_data_into_s3(s3_client, bucket, user_id, data)
    return user_id


def create_customer_user(cognito_client, pool_id, data):
    """Creates a new customer in Cognito"""
    logger.info('Creating customer user in user pool')
    user = CustomerUser(**data).dict()
    return create_user_in_user_pool(cognito_client, pool_id, user, password=data.get('password'))


# TODO utilize pagination tokens in React Admin instead of start/end, which doesn't really work for cognito/dynamo
def get_all_customers(cognito_client, s3_client, pool_id, bucket, pagination_token=None, limit=20) -> List[Customer]:
    customers = list_users_from_user_pool(cognito_client, pool_id)
    for customer in customers:
        user_data = get_customer_data_from_s3(s3_client, bucket, customer['Username'])
        customer = merge_user_data(customer, user_data)
    return customers


def update_customer_data_in_cognito(cognito_client, CUSTOMER_USER_POOL_ID, customer_id, data):
    flatten_user_attributes(data)
    user = CustomerUser(**data).dict()
    attributes = [
        # {
        #     'Name': 'given_name',
        #     'Value': user['given_name']
        # },
        # {
        #     'Name': 'family_name',
        #     'Value': user['family_name']
        # },
        {
            'Name': 'phone_number',
            'Value': user['phone_number']
        },
        {
            'Name': 'email',
            'Value': user['email']
        },
    ]
    update_user_attributes(cognito_client, customer_id, attributes, CUSTOMER_USER_POOL_ID)


def get_customer(cognito_client, s3_client, pool_id, bucket, user_id) -> Customer:
    """Returns an customer user by ID"""
    cognito_user = get_user_from_user_pool(cognito_client, pool_id, user_id)
    flatten_user_attributes(cognito_user)
    user_data = get_customer_data_from_s3(s3_client, bucket, user_id)
    return merge_user_data(cognito_user, user_data)


def get_customer_data_from_s3(s3_client, bucket, user_id):
    """Returns extra customer user data stored in S3"""
    return get_object_from_s3(s3_client, bucket, f'customers/{user_id}.json', {})


def get_customer_jobs_from_dynamo(jobs_table, customer_id, limit=20):
    """
    Queries a dyanmo table for any jobs assigned to the customer
    """
    logger.info(f'Checking for jobs for user {customer_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {'customer_id': customer_id}
    # pk.sort = {'ts': mk_timestamp()}
    
    jobs, pagination_token = [], None
    while True:
        # Query the customer's tickets using the jobs table
        items, cursor_token = fetch_items_by_gsi(jobs_table, pk, 'customer_id', cursor_token=pagination_token)
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


def get_pool_attributes(pool_res, user):
    user['Attributes'] = pool_res['User']['Attributes']
    user['id'] = pool_res['User']['Username']
    # user['Enabled'] = pool_res['User']['Enabled']
    # user['UserStatus'] = pool_res['User']['UserStatus']
    # user['UserLastModifiedDate'] = pool_res['User']['UserLastModifiedDate']
    # user['UserCreateDate'] = pool_res['User']['UserCreateDate']
    return user


def put_customer_data_into_s3(s3_client, bucket, user_id, data):
    CustomerUser.strip_cognito_fields(data)
    logger.info(f'Updating customer user {user_id} with {data}')
    return put_object_into_s3(s3_client, bucket, f'customers/{user_id}.json', json.dumps(data))


def update_customer_data_in_s3(s3_client, bucket, user_id, data):
    """Updates an existing customer user data object in S3 with new data"""
    user_data = get_customer_data_from_s3(s3_client, bucket, user_id)
    user_data.update(data)
    put_customer_data_into_s3(s3_client, bucket, user_id, user_data)


def update_customer_job_data_in_s3(s3_client, bucket, user_id, job_data):
    """appends the new customer job data to user data object in S3"""
    user_data = get_customer_data_from_s3(s3_client, bucket, user_id)
    if user_data.get('jobs') is not None:
        user_data['jobs'].append(job_data) # XXX list or dict or?
        return put_customer_data_into_s3(s3_client, bucket, user_id, user_data)
    user_data['jobs'] = []
    user_data['jobs'].append(job_data) 
    put_customer_data_into_s3(s3_client, bucket, user_id, user_data)



# def determine_price_estimate(job_estimate, state):
#     """Returns price estimate based off of tier, hours estimate, and state"""
#     rate = get_rate(state)
#     # XXX need tier multiplier + readicharge price?
#     return rate * job_estimate.hours


# def update_customer_job(table, data, id):
#     """Update exiting job_ticket in jobs table"""
#     # pk = DynamoPrimaryKey()
#     # pk.partition = {'ticket_id': id}
#     # pk.sort = {'ts': mk_timestamp()}
#     # pk.sort.comparator = 'EQ'
#     response = table.query(
#         KeyConditionExpression=Key('ticket_id').eq(id)
#     )
#     items = items = response.get("Items", None)
#     if items:
#         job_ticket = JobTicket(**items[0]).dict()
#         update_dynamo_record(table, {'ticket_id': id, 'ts': job_ticket.pop('ts')}, data)
#         return job_ticket
#     logger.warn('No job ticket found.')
