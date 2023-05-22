import logging
import os
from typing import Optional
import boto3
from fastapi import APIRouter, Header, Request, Response, status
from rctools.aws.cognito import get_user_with_access_token
from rctools.customers import get_customer
from rctools.exceptions import UserNotAuthorizedToListTickets
from rctools.installers import (get_installer, get_installers_for_company,
                                get_user_company, is_company_admin)
from rctools.jobs import get_job_ticket, get_job_tickets
from rctools.scheduling import get_scheduled_job
from rctools.users import is_rc_admin
from utils import build_content_range_header, filter_results, parse_params

ADMIN_USER_POOL_ID = os.environ.get('ADMIN_USER_POOL_ID')
CUSTOMER_USER_POOL_ID = os.getenv('CUSTOMER_USER_POOL_ID')
INSTALLER_USER_POOL_ID = os.getenv('INSTALLER_USER_POOL_ID')
JOB_SCHEDULE_TABLE = os.environ.get('JOB_SCHEDULE_TABLE')
JOBS_TABLE = os.environ.get('JOBS_TABLE')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')
RC_ADMIN_GROUP_ID = os.getenv('RC_ADMIN_GROUP_ID')

router = APIRouter()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client('s3')
cognito_client = boto3.client('cognito-idp')

dynamodb = boto3.resource('dynamodb')
jobs_table = dynamodb.Table(JOBS_TABLE)
job_schedule_table = dynamodb.Table(JOB_SCHEDULE_TABLE)


@router.get('/job-tickets')
def get_all_job_tickets(request: Request, response: Response, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> dict:
    """Fetches all job tickets, per user scope"""
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    data = get_job_tickets(jobs_table)
    if not is_rc_admin(cognito_client, ADMIN_USER_POOL_ID, uid, RC_ADMIN_GROUP_ID):
        company_id = get_user_company(s3_client, USER_DATA_BUCKET, uid)
        installers = get_installers_for_company(cognito_client, s3_client, ADMIN_USER_POOL_ID, USER_DATA_BUCKET, company_id)
        installer_ids = [i['Username'] for i in installers]
        # TODO, we should switch to using dynamo indexes to fetch and filter
        data = [ticket for ticket in data if ticket.get('installer_id') in installer_ids]
        
    # get query params
    req_url = request.url
    logger.info(f'jobs request {request.headers}')
    start, end, field, order, search = parse_params(req_url)
    for d in data:
        d['id'] = d['ticket_id']

    # TODO we need custom pagination that works with cursor tokens
    start = 0
    end = len(data)

    if field:
        # Handle fields not in data
        data = sorted(data, key=lambda k: (field not in k, k.get(field, None)), reverse=bool(order == 'DESC'))
    if search:
        search_fields = ['installer', 'customer', 'address', 'region']
        search_result = filter_results(data, search, search_fields)
        response.headers['Content-Range'] = build_content_range_header('job-tickets', search_result, start, end)
        # return [JobTicketsResponse(**u) for u in search_result[start:end]]
        
    response.headers['Content-Range'] = build_content_range_header('job-tickets', data, start, end)
    return [d for d in data[start:end]]
    # return [JobTicketsResponse(**d) for d in data[start:end]]


@router.get('/job-tickets/{id}')
def get_job_ticket_by_id(id: str):
    """Fetches a job ticket by the id"""
    logger.info(f'Getting job {id}')
    ticket = get_job_ticket(jobs_table, id)
    ticket['id'] = ticket['ticket_id']
    ticket['customer_data'] = get_customer(cognito_client, s3_client, CUSTOMER_USER_POOL_ID, USER_DATA_BUCKET, ticket['customer_id'])
    if ticket.get('installer_id') is not None:
        ticket['installer_data'] = get_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, ticket['installer_id'])

    ticket['schedule_data'] = get_scheduled_job(job_schedule_table, ticket['id'])
    return ticket
    

@router.get('/installers/{installer_id}/job-tickets', status_code=status.HTTP_200_OK)
def get_installer_jobs(installer_id: str,request: Request, response: Response, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """Fetches and returns all the jobs corresponding to the installer id"""
    logger.info('Getting all jobs for installer with id {installer_id}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']
    data = get_job_tickets(jobs_table)

    if not is_rc_admin(cognito_client, ADMIN_USER_POOL_ID, uid, RC_ADMIN_GROUP_ID):
        if not is_company_admin(cognito_client, ADMIN_USER_POOL_ID, uid):
            # Not super admin or company admin is unauthorized
            raise UserNotAuthorizedToListTickets()

    data = [ticket for ticket in data if ticket.get('installer_id') == installer_id]
    
    # get query params
    req_url = request.url
    logger.info(f'jobs request {request.headers}')
    start, end, field, order, search = parse_params(req_url)
    for d in data:
        d['id'] = d['ticket_id']

    # TODO we need custom pagination that works with cursor tokens
    start = 0
    end = len(data)

    if field:
        # Handle fields not in data
        data = sorted(data, key=lambda k: (field not in k, k.get(field, None)), reverse=bool(order == 'DESC'))
    if search:
        search_fields = ['installer', 'customer', 'address', 'region']
        search_result = filter_results(data, search, search_fields)
        response.headers['Content-Range'] = build_content_range_header('job-tickets', search_result, start, end)
        # return [JobTicketsResponse(**u) for u in search_result[start:end]]
        
    response.headers['Content-Range'] = build_content_range_header('job-tickets', data, start, end)
    return [d for d in data[start:end]]
    # return [JobTicketsResponse(**d) for d in data[start:end]]

