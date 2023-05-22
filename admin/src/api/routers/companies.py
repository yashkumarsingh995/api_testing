import logging
import os
from operator import itemgetter
from typing import Optional

import boto3
from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from rctools.aws.cognito import get_user_with_access_token
from rctools.aws.s3 import list_folders_in_s3
from rctools.company import (create_company_admin, create_company_id,
                             get_company_data, put_company_data,
                             put_company_installer_code)
from rctools.models import Company, CompanyAdmin, CompanyInstaller
from utils import build_content_range_header, filter_results, parse_params

ADMIN_USER_POOL_ID = os.getenv('ADMIN_USER_POOL_ID')
COMPANY_DATA_BUCKET = os.getenv('COMPANY_DATA_BUCKET')
INSTALLER_CODES_TABLE = os.getenv('INSTALLER_CODES_TABLE')
OWNER_ADMIN_GROUP_ID = os.getenv('OWNER_ADMIN_GROUP_ID')
RC_ADMIN_GROUP_ID = os.getenv('RC_ADMIN_GROUP_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')


@router.post('/companies/{company_id}/installer/code', status_code=status.HTTP_201_CREATED)
def create_new_installer_code(company_id: str, installer: CompanyInstaller) -> str:
    """
    Triggers the creation of a new installer code object within the given company
    and returns the six-digit code on success
    """
    installer['company_id'] = company_id
    return put_company_installer_code(INSTALLER_CODES_TABLE, installer)


@router.get('/companies')
def get_companies(request: Request, response: Response):
    """
    Returns all active companies, respecting React Admin query and filtering parameters
    """
    # get query params
    req_url = request.url
    start, end, field, order, search = parse_params(req_url)

    logger.info(f'Getting all companies with request url {req_url}')
    companies = list_folders_in_s3(s3_client, COMPANY_DATA_BUCKET)
    data = []
    for company_id in companies:
        logger.info(f'Getting data for id {company_id[:-1]}')
        company_data = get_company_data(s3_client, COMPANY_DATA_BUCKET, company_id[:-1])  # remove trailing slash from prefix
        if company_data:
            data.append(company_data)
    logger.info(f'{len(data)} found')

    if field:
        # Handle fields not in data
        data = sorted(data, key=lambda k: (field not in k, k.get(field, None)), reverse=bool(order == 'DESC'))
    if search:
        search_fields = ['name', 'id', 'address_1', 'city', 'state']
        search_result = filter_results(data, search, search_fields)
        response.headers['Content-Range'] = build_content_range_header('customers', search_result, start, end)
        return [Company(**u) for u in search_result[start:end]]

    response.headers['Content-Range'] = build_content_range_header('customers', data, start, end)
    return [Company(**d) for d in data[start:end]]


@router.get('/companies/{id}')
def get_company(id: str, request: Request, response: Response):
    """
    Returns the company with the given id
    """
    logger.info(f'Fetching company {id}')
    try:
        company = get_company_data(s3_client, COMPANY_DATA_BUCKET, id)
        logger.info(f'{company} found')
    except:
        raise HTTPException(status_code=404, detail='Company not found')

    return Company(**company)
    

# TODO decide if we want to deprecate this in favor of just the onboarding app or if we want to gate this by user group
@router.post('/companies', status_code=status.HTTP_201_CREATED)
def create_new_company(data: dict):
    """
    Creates a company in s3, a corresponding company admin in cognito, adds the admin and company
    to s3 buckets and returns the new company id
    """
    new_admin = CompanyAdmin(**data.pop('account'))
    new_company = Company(**data)
    # add company id to company and admin for future mapping
    company_id = create_company_id()
    new_admin.set_company_id(company_id)
    new_company.set_company_id(company_id)

    account_owner_id = create_company_admin(cognito_client, s3_client, ADMIN_USER_POOL_ID, OWNER_ADMIN_GROUP_ID, USER_DATA_BUCKET, new_admin.dict())
    new_company.set_account_owner(account_owner_id)

    put_company_data(s3_client, COMPANY_DATA_BUCKET, new_company.dict())
    logger.info(f'Created new company: {new_company} with company admin: {new_admin}')
    return company_id


@router.put('/onboarding/company/{id}', status_code=status.HTTP_200_OK)
def onboarding_update_company(id: str, data: Company, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """
    Updates a company from the onboarding app
    """
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']
    logger.info(f'Starting update company data request for user {uid}')

    company = get_company_data(s3_client, COMPANY_DATA_BUCKET, id)
    logger.info('Checking user permissions')
    if company['owner_id'] == uid:
        update = {**company, **data.dict()}
        logger.info(f'Updating company data {update}')
        return put_company_data(s3_client, COMPANY_DATA_BUCKET, update)

    logger.warning('User does not have permission to edit company')
    raise HTTPException(status_code=401)
