import logging
import os
from datetime import datetime
from typing import Optional, List

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse
from rctools.alerts import add_user_alert
from rctools.alerts.customer import create_customer_new_job_alert
from rctools.alerts.installer import create_installer_new_job_alert
from rctools.aws.cognito import get_user_with_access_token 
from rctools.exceptions import (CustomerNotAuthorizedToEditSchedule,
                                CustomerNotAuthorizedToEditTicket)
from rctools.installers import get_installer
from rctools.messages import start_conversation
from rctools.jobs import get_job_ticket, update_job_ticket
from rctools.scheduling import (add_job_to_schedule, get_scheduled_job,
                                create_reservation, get_available_times,
                                get_available_times_for_day,
                                get_reservation_by_id)
from rctools.zip_codes import get_installers_by_zip


ALERTS_TABLE = os.environ.get('ALERTS_TABLE')
INSTALLER_SERVICE_AREA_TABLE = os.environ.get('INSTALLER_SERVICE_AREA_TABLE')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
JOBS_TABLE = os.environ.get('JOBS_TABLE')
JOB_SCHEDULE_TABLE = os.environ.get('JOB_SCHEDULE_TABLE')
MESSAGES_TABLE = os.environ.get('MESSAGES_TABLE')
RESERVATIONS_TABLE = os.environ.get('RESERVATIONS_TABLE')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')

cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')

dynamodb = boto3.resource('dynamodb')
alerts_table = dynamodb.Table(ALERTS_TABLE)
job_schedule_table = dynamodb.Table(JOB_SCHEDULE_TABLE)
jobs_table = dynamodb.Table(JOBS_TABLE)
messages_table = dynamodb.Table(MESSAGES_TABLE)
reservations_table = dynamodb.Table(RESERVATIONS_TABLE)
service_area_table = dynamodb.Table(INSTALLER_SERVICE_AREA_TABLE)


def fetch_installers(installer_ids: List[str]):
    """Helper method to return list of all installers"""
    return [get_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, i) for i in installer_ids]


@router.get('/schedule/{ticket_id}/installers', status_code=status.HTTP_200_OK)
def get_installer_schedules(ticket_id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """
    Iterates and filters all available installers by service area (zip), 
    job scope/service option, and availability 

    return an array of date and times 
    """
    try:
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        customer_id = user['Username']
        job = get_job_ticket(jobs_table, ticket_id)
        if job['customer_id'] != customer_id:
            raise CustomerNotAuthorizedToEditTicket()

        zip_code = job['address']['zip']
        installer_ids = get_installers_by_zip(service_area_table, zip_code)
        installers = [get_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, i) for i in installer_ids]
        return get_available_times(None, installers, job['job_scope']['tier'], job['address']['zip'], reservations_table)
    except CustomerNotAuthorizedToEditTicket:
        err = f'Customer {customer_id} is not authorized to get installer dates for ticket {ticket_id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error editing job')
        return JSONResponse({'error': str(e)}, 400) 


@router.post('/schedule/reservation/{ticket_id}/{day}', status_code=status.HTTP_201_CREATED)
def post_customer_reservation(ticket_id: str, day: datetime, reservation_data: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    logger.info(f'Posting reservation for ticket {ticket_id}')
    try:
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        customer_id = user['Username']
        job = get_job_ticket(jobs_table, ticket_id)
        if job['customer_id'] != customer_id: 
            raise CustomerNotAuthorizedToEditTicket()
        logger.info(f'Getting available times for job {job}')
        installers = fetch_installers(reservation_data['installer_ids'])
        available_times = get_available_times_for_day(None, installers, job['job_scope']['tier'], job['address']['zip'], day, reservations_table)
        logger.info(f'Returning available times {available_times} from {reservation_data}')
        for date, availabilities in available_times.items():
            for installer, times in availabilities.items():
                if reservation_data['start_time'] in times:
                    reservation = {
                        'installer_id': installer,
                        'start_time': reservation_data['start_time'],
                        'customer_id': customer_id,
                        'ticket_id': ticket_id,
                        'reservation_date': date
                    }
                    reservation_id = create_reservation(reservations_table, reservation)
                    return reservation_id
        return False
    except CustomerNotAuthorizedToEditTicket:
        err = f'Customer {customer_id} is not authorized to post reservations for ticket {ticket_id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error posting reservation')
        return JSONResponse({'error': str(e)}, 400) 


@router.post('/schedule/job/{ticket_id}/{reservation_id}', status_code=status.HTTP_201_CREATED)
# def post_customer_job_schedule(reserved_installer_id: str, ticket_id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
def post_customer_job_schedule(reservation_id: str, ticket_id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    logger.info(f'Posting scheduled job for from reservation {reservation_id}')
    try:
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        customer_id = user['Username']

        job = get_job_ticket(jobs_table, ticket_id)
        if job['customer_id'] != customer_id: 
            raise CustomerNotAuthorizedToEditTicket()

        # reservations = get_installer_reservations_by_id(reservations_table, reserved_installer_id)
        res = get_reservation_by_id(reservations_table, reservation_id)
        # logger.info(f'found reservation {reservations}')
        # for res in reservations:
        if res['customer_id'] == customer_id:
            installer_id = res['installer_id']
            installer = get_installer(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET, installer_id)
            conversation_id = start_conversation(messages_table, installer, installer_id, customer_id)
            logger.info(f'Updating job ticket with installer {installer_id} and conversation {conversation_id}')
            update_job_ticket(jobs_table, {'installer_id': installer_id, 'conversation_id': conversation_id}, ticket_id, customer_id)
            # Create the job
            add_job_to_schedule(job_schedule_table, res, ticket_id)
            # Then send alerts
            add_user_alert(alerts_table, customer_id, create_customer_new_job_alert(customer_id))
            add_user_alert(alerts_table, installer_id, create_installer_new_job_alert(installer_id))
            return installer_id
        raise CustomerNotAuthorizedToEditSchedule()
        
    except CustomerNotAuthorizedToEditTicket:
        err = f'Customer {customer_id} is not authorized to edit ticket {ticket_id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except CustomerNotAuthorizedToEditSchedule:
        err = f'Customer {customer_id} is not authorized to post schedule for ticket {ticket_id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error posting reservation')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/schedule/job/{ticket_id}', status_code=status.HTTP_201_CREATED)
def get_customer_job_schedule(ticket_id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    logger.info(f'Getting scheduled job for job ticket {ticket_id}')
    try:
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        customer_id = user['Username']

        job_schedule = get_scheduled_job(job_schedule_table, ticket_id)
        if job_schedule['customer_id'] != customer_id: 
            raise CustomerNotAuthorizedToEditSchedule()
        return job_schedule     
    except CustomerNotAuthorizedToEditSchedule:
        err = f'Customer {customer_id} is not authorized to get schedule for ticket {ticket_id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error posting reservation')
        return JSONResponse({'error': str(e)}, 400)

