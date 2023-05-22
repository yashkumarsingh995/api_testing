import logging
import os
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse
from rctools.aws.cognito import get_user_with_access_token
from rctools.aws.s3 import get_object_from_s3
from rctools.customers import get_customer_jobs_from_dynamo
from rctools.exceptions import CustomerNotAuthorizedToEditTicket
from rctools.installers import get_installer
from rctools.jobs import (add_note_to_job_ticket, add_note_to_s3,
                          add_photo_to_job_ticket, add_photo_to_s3,
                          get_job_notes, get_job_ticket, get_job_tier,
                          put_new_job, update_job_ticket)
from rctools.models import JobNote, JobsResponse
from rctools.models.jobs import JobPhoto, JobTier
from rctools.models.users import Installer

JOBS_TABLE = os.environ.get('JOBS_TABLE')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
CUSTOMERS_USER_POOL_ID = os.environ.get('CUSTOMERS_USER_POOL_ID')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')
MESSAGES_TABLE = os.environ.get('MESSAGES_TABLE')
JOB_NOTE_BUCKET = os.environ.get('JOB_NOTE_BUCKET')
JOB_PHOTO_BUCKET = os.environ.get('JOB_PHOTO_BUCKET')

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
def get_customer_jobs(X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """Fetches and returns all the jobs corresponding to the customer id"""
    logger.info('Getting all jobs for customer')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    customer_id = user['Username']
    response = JobsResponse()
    response.jobs = get_customer_jobs_from_dynamo(jobs_table, customer_id)
    return response


@router.post('/job', response_model=str, status_code=status.HTTP_201_CREATED)
def create_customer_job_ticket(job_data: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> str:
    """
    Creates a new job ticket and places it in the jobs table, 
    adds ticket_id to customer's s3 bucket
    """
    logger.info(f'Creating a new job ticket {job_data}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    customer_id = user['Username']
    logger.info(f'Creating job for customer {customer_id}')
    job_data['customer_id'] = customer_id

    try:
        ticket_id = put_new_job(jobs_table, job_data)
        logger.info(f'Job {ticket_id} created!')
        return ticket_id
    except ClientError as e:
        logger.exception('Error creating new job')
        return JSONResponse({'error': str(e)}, 400)


@router.put('/job/{id}', status_code=status.HTTP_200_OK)
def edit_customer_job(id: str, data: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """Fetches existing job from the jobs table, updates the item and determines if in scope"""
    logger.info(f'Editing customer job {id} with {data}')
    try:
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        customer_id = user['Username']
        job_ticket = get_job_ticket(jobs_table, id)
        if job_ticket['customer_id'] != customer_id:
            raise CustomerNotAuthorizedToEditTicket()
        update_job_ticket(jobs_table, data, id, customer_id)
        return id
    except CustomerNotAuthorizedToEditTicket:
        err = f'Customer {customer_id} is not authorized to edit ticket {id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error editing job')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/job/{id}/notes', status_code=status.HTTP_200_OK)
def get_notes_for_job(id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    try:
        job_ticket = get_job_ticket(jobs_table, id)
        if job_ticket.get('notes'):
            return get_job_notes(s3_client, JOB_NOTE_BUCKET, id, job_ticket['notes'])
    except ClientError as e:
        logger.exception(f'Error getting job notes')
        return JSONResponse({'error': str(e)}, 400)

    
@router.get('/job/{id}', status_code=status.HTTP_200_OK)
def get_job(id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """Fetches existing job from the jobs table"""
    logger.info(f'Editing customer job {id}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    customer_id = user['Username']
    try:
        job_ticket = get_job_ticket(jobs_table, id)
        if job_ticket['customer_id'] != customer_id:
            raise CustomerNotAuthorizedToEditTicket()
        return job_ticket
    except CustomerNotAuthorizedToEditTicket:
        err = f'Customer {customer_id} is not authorized to view ticket {id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error creating new installer')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/job/{id}/installer', response_model=Installer, status_code=status.HTTP_200_OK)
def get_installer_for_job(id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> Optional[Installer]:
    """Fetches existing job from the jobs table"""
    logger.info(f'Editing customer job {id}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    customer_id = user['Username']
    try:
        job_ticket = get_job_ticket(jobs_table, id)
        if job_ticket['customer_id'] != customer_id:
            raise CustomerNotAuthorizedToEditTicket()
        if 'installer_id' in job_ticket:
            return get_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, job_ticket['installer_id'])
    except CustomerNotAuthorizedToEditTicket:
        err = f'Customer {customer_id} is not authorized to get installer {id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error creating new installer')
        return JSONResponse({'error': str(e)}, 400)


@router.post('/job/{id}/note', response_model=JobNote, status_code=status.HTTP_201_CREATED)
def add_customer_job_note(note: dict, id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobNote:
    """Adds a note_id to the jobs table and the note to a bucket in s3"""
    logger.info(f'Creating a new job note {note}')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    customer_id = user['Username']
    logger.info(f'Creating note for customer {customer_id}')
    note['uid'] = customer_id
    note['ticket_id'] = id
    new_job_note = JobNote(**note)
    try:
        job_ticket = get_job_ticket(jobs_table, id)
        if job_ticket['customer_id'] != customer_id:
            raise CustomerNotAuthorizedToEditTicket()
        add_note_to_job_ticket(jobs_table, new_job_note.note_id, id, customer_id)
        add_note_to_s3(s3_client, JOB_NOTE_BUCKET, id, new_job_note)
        return new_job_note
    except CustomerNotAuthorizedToEditTicket:
        err = f'Customer {customer_id} is not authorized to post note {id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error adding note to job')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/job/{id}/tier', response_model=JobTier, status_code=status.HTTP_200_OK)
def determine_job_scope(id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobTier:
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    customer_id = user['Username']
    try:
        job_ticket = get_job_ticket(jobs_table, id)
        if job_ticket['customer_id'] != customer_id:
            raise CustomerNotAuthorizedToEditTicket()
        logger.info(job_ticket)
        job_ticket['job_scope']['tier'] = get_job_tier(job_ticket)
        update_job_ticket(jobs_table, job_ticket, id, customer_id)
        return job_ticket['job_scope']['tier']
    except CustomerNotAuthorizedToEditTicket:
        err = f'Customer {customer_id} is not authorized to get job tier {id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error determining job tier')
        return JSONResponse({'error': str(e)}, 400)


@router.post('/job/{id}/photo', response_model=JobPhoto, status_code=status.HTTP_201_CREATED)
def post_job_photo(id: str, file: dict = None, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> JobPhoto:
    """Uploads a file to use as the installer's profile image"""
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    customer_id = user['Username']
    new_job_photo['uid'] = customer_id
    new_job_photo['ticket_id'] = id
    new_job_photo = JobPhoto(**file)
    try:
        add_photo_to_job_ticket(jobs_table, new_job_photo.photo_id, id, customer_id)
        add_photo_to_s3(s3_client, JOB_PHOTO_BUCKET, id, new_job_photo)
        return new_job_photo
    except ClientError as e:
        logger.exception('Error posting job photo: {e}')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/job/{id}/photo', response_model=List[JobPhoto],  status_code=status.HTTP_200_OK)
def get_job_photo(id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> List[JobPhoto]:
    """Fetches job images from s3"""
    s3_path = f"photos/{id}"
    photos = get_object_from_s3(s3_client, JOB_PHOTO_BUCKET, s3_path)
    print(f'photos received {photos}')
    return get_object_from_s3(s3_client, JOB_PHOTO_BUCKET, s3_path)
