import json
import logging
from uuid import uuid4

from pydantic import ValidationError
from rctools.aws.cognito import add_user_to_group, create_user_in_user_pool
from rctools.users import put_admin_user_data_into_s3
from rctools.zip_codes import get_zip_codes_in_radius
from .aws.dynamodb import create_dynamo_record, fetch_items_by_pk, DynamoPrimaryKey, delete_dynamo_record, fetch_items_by_gsi
from .aws.s3 import get_object_from_s3, put_object_into_s3
from .models import AdminUser, Company, CompanyAdminUser, CompanyInstaller
from .utils import create_random_code, mk_timestamp


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_company_data(s3_client, bucket, company_id):
    try:
        logger.info(f'Getting company data by id {company_id}')
        data = get_object_from_s3(s3_client, bucket, f'{company_id}/data.json')
        if data:
            # XXX When going through onboarding webapp the only company fields set are id, and account_owner_id
            # return Company(**data).dict() 
            return data
        logger.warn('No company data found.')
    except ValidationError:
        logger.exception(f'Company {company_id} failed validation')


def put_company_data(s3_client, bucket, data):
    logger.info(f'putting company in s3 before {data}')
    # company = Company(**data).dict()
    # logger.info(f'putting company in s3 after {company}')
    return put_object_into_s3(
        s3_client, bucket, f'{data["id"]}/data.json', json.dumps(data)
    )


def create_new_installer_code(table, length=6):
    while True:
        code = create_random_code(length)
        logger.info(f'code created {code}')
        pk = DynamoPrimaryKey()
        pk.partition = {'code': code}
        items, _ = fetch_items_by_pk(table, pk)
        if not items:
            break
    return code


def get_company_installer_by_code(table, code: str) -> dict:
    pk = DynamoPrimaryKey()
    pk.partition = {'code': code}
    items, _ = fetch_items_by_pk(table, pk)
    if items:
        return CompanyInstaller(**items[0]).dict()
    logger.warn('No installer found.')


def put_company_installer_code(table, data) -> dict:
    data['code'] = create_new_installer_code(table)
    data['ts'] = mk_timestamp()
    logger.info(f'creating installer with {data}')
    installer = CompanyInstaller(**data).dict()
    logger.info(f'creating dynamo record for {installer} in {table}')
    resp = create_dynamo_record(table, installer)
    logger.info(f'Results from dynamo {resp}')
    return data['code']


def create_company_id() -> str:
    """Creates company_id using with uuid4"""
    return str(uuid4())


def create_company_admin_user(cognito_client, pool_id, data):
    """Creates a new admin in Cognito"""
    user = CompanyAdminUser(**data).dict()
    return create_user_in_user_pool(cognito_client, pool_id, user, password=data.get('password'))


def create_company_admin(cognito_client, s3_client, pool_id, owner_admin_group, bucket, data):
    """Creates a full admin, returning the newly created user ID"""
    username = data['email']
    cognito_resp = create_company_admin_user(cognito_client, pool_id, data)
    user_id = cognito_resp['User']['Username']
    put_admin_user_data_into_s3(s3_client, bucket, user_id, data)
    add_user_to_group(cognito_client, pool_id, username, owner_admin_group)
    return user_id


def update_company_service_area(s3_client, service_area_table, zip_bucket, company_id, zip_code, radius):
    """
    Deletes all company entries from the service area table and repopulates using values from the
    zip code distance bucket, depending on the radius
    """ 
    # Delete old rows
    pk = DynamoPrimaryKey()
    pk.partition = {'company_id': company_id}
    pagination_token = None
    logger.info('Deleting old service area entries')
    while True:
        items, cursor_token = fetch_items_by_gsi(service_area_table, pk, 'gsiCompanyIndex', cursor_token=pagination_token)
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
        create_dynamo_record(service_area_table, {'zip_code': z, 'company_id': company_id, 'ts': ts})
