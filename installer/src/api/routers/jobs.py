import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse
from rctools.aws.cognito import get_user_with_access_token
from rctools.exceptions import InstallerNotAuthorizedToEditTicket
from rctools.installers import get_installer_jobs_from_dynamo
from rctools.jobs import fill_out_job_ticket, get_job_ticket
from rctools.models import JobsResponse

JOBS_TABLE = os.environ.get('JOBS_TABLE')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
CUSTOMER_USER_POOL_ID = os.environ.get('CUSTOMER_USER_POOL_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')
MESSAGES_TABLE = os.environ.get('MESSAGES_TABLE')

ALERTS_TABLE = os.environ.get('ALERTS_TABLE')

cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')

dynamodb = boto3.resource('dynamodb')
alerts_table = dynamodb.Table(ALERTS_TABLE)
jobs_table = dynamodb.Table(JOBS_TABLE)
message_table = dynamodb.Table(MESSAGES_TABLE)


@router.get('/job', response_model=JobsResponse, status_code=status.HTTP_200_OK)
def get_installer_jobs(X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """Fetches and returns all the jobs corresponding to the installer id"""
    logger.info('Getting all jobs for installer')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    installer_id = user['Username']
    response = JobsResponse()
    response.jobs = get_installer_jobs_from_dynamo(jobs_table, installer_id)
    for job in response.jobs:
        fill_out_job_ticket(cognito_client, s3_client, message_table,
                            CUSTOMER_USER_POOL_ID, USER_DATA_BUCKET, job)
    return response


@router.get('/job/{id}', status_code=status.HTTP_200_OK)
def get_job(id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """Fetches existing job from the jobs table"""
    logger.info(f'Fetching installer job {id}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    installer_id = user['Username']
    try:
        job_ticket = get_job_ticket(jobs_table, id)
        if job_ticket['installer_id'] != installer_id:
            raise InstallerNotAuthorizedToEditTicket()
        return fill_out_job_ticket(cognito_client, s3_client, message_table, CUSTOMER_USER_POOL_ID, USER_DATA_BUCKET, job_ticket)
    except InstallerNotAuthorizedToEditTicket:
        err = f'Installer {installer_id} is not authorized to view ticket {id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error fetching job ticket {id}')
        return JSONResponse({'error': str(e)}, 400)


# @router.post('/customer/job/{id}/note', response_model=JobNote, status_code=status.HTTP_201_CREATED)
# def add_customer_job_note(note: dict, id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobNote:
#     """Adds a note_id to the jobs table and the note to a bucket in s3"""
#     logger.info(f'Creating a new job note {note}')
#     user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
#     installer_id = user['Username']
#     logger.info(f'Creating note for customer {installer_id}')
#     note['note_id'] = create_random_code(16)
#     note['uid'] = installer_id
#     new_job_note = JobNote(**note)
#     try:
#         add_note_to_job_ticket(jobs_table, new_job_note, id)
#         return new_job_note
#     except ClientError as e:
#         logger.exception(f'Error adding note to job')
#         return JSONResponse({'error': str(e)}, 400)


# @router.get('/customer/job/{id}/tier', response_model=JobTier, status_code=status.HTTP_200_OK)
# def determine_job_scope(id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobTier:
#     try:
#         job_ticket = get_job_ticket(jobs_table, id)
#         logger.info(job_ticket)
#         return get_job_tier(job_ticket)
#     except ClientError as e:
#         logger.exception(f'Error determining job tier')
#         return JSONResponse({'error': str(e)}, 400)


# @router.get('/customer/job/{ticket_id}/installer', status_code=status.HTTP_200_OK)
# def get_customer_job_installer(ticket_id: str):
#     """Fetches the installer that has the matching job uid"""
#     logger.info(f'Getting installer assigned to customer job {ticket_id}')
#     job = get_job_ticket(jobs_table, ticket_id)
#     installer_id = job['installer_id']
#     logger.info(f'Looking for installer {installer_id}')
#     installer_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, installer_id)
#     installer_user = get_user_from_user_pool(cognito_client, INSTALLER_USER_POOL_ID, installer_id)
#     logger.info(f'Found installer {installer_data}')
#     return merge_user_data(installer_user, installer_data)


# @router.get('/job/{ticket_id}/referrals', status_code=status.HTTP_200_OK)
# def get_job_referrals(ticket_id: str):
#     return fakeInstallers


# @router.post('/customer/job/message', response_model=Message, status_code=status.HTTP_201_CREATED)
# def send_customer_job_message(installer: Installer, customer: Installer, job: JobTicket, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobTicket:
#     """Adds message to message table and updates job table"""


# @router.post('/customer/job/image',  status_code=status.HTTP_201_CREATED)
# def upload_customer_job_image(job: JobTicket, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobTicket:
#     """Adds an upload image to the jobs table"""


# @router.get('/customer/job/note/{id}', response_model=JobNote, status_code=status.HTTP_201_CREATED)
# def add_customer_job_note(note: JobNote, id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobNote:
#     """Adds a note to the jobs table"""


# @router.get('/customer/job/message/{id}', response_model=Message, status_code=status.HTTP_201_CREATED)
# def send_customer_job_message(installer: Installer, customer: Installer, job: JobTicket, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobTicket:
#     """Adds message to message table and updates job table"""


# @router.get('/customer/job/image/{id}',  status_code=status.HTTP_201_CREATED)
# def upload_customer_job_image(job: JobTicket, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobTicket:
#     """Adds an upload image to the jobs table"""
