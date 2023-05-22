import json
import logging
import os
from operator import itemgetter
from typing import List
from urllib.parse import parse_qs

import boto3
from fastapi import APIRouter, Request, Response
from rctools.customers import get_all_customers
from rctools.models.users import Customer
from utils import build_content_range_header, filter_results, parse_params

router = APIRouter()

COMPANY_DATA_BUCKET = os.getenv('COMPANY_DATA_BUCKET')
CUSTOMER_USER_POOL_ID = os.environ.get('CUSTOMER_USER_POOL_ID')
INSTALLER_CODES_TABLE = os.getenv('INSTALLER_CODES_TABLE')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
OWNER_ADMIN_GROUP_ID = os.environ.get('OWNER_ADMIN_GROUP_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')

cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')


@router.get('/customers', response_model=List[Customer])
def get_customers(request: Request, response: Response) -> dict:
    """/customers endpoint with pagination and sorting from query params"""
    # get query params
    req_url = request.url
    start, end, field, order, search = parse_params(req_url)

    data = get_all_customers(cognito_client, s3_client, CUSTOMER_USER_POOL_ID, USER_DATA_BUCKET, None)  # TODO, use RA pagination that uses tokens instead of start, end
    if field:
        # Handle fields not in data
        data = sorted(data, key=lambda k: (field not in k, k.get(field, None)), reverse=bool(order == 'DESC'))
    if search:
        search_fields = ['name', 'id', 'type', 'state', 'region']
        search_result = filter_results(data, search, search_fields)
        response.headers['Content-Range'] = f'customers {start}-{end}/{len(search_result)}'
        return [Customer(**u) for u in search_result[start:end]]
    response.headers['Content-Range'] = build_content_range_header('customers', data, start, end)
    return [Customer(**d) for d in data[start:end]]
