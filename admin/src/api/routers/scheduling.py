import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse
from rctools.aws.cognito import (get_user_with_access_token)
from rctools.exceptions import (InstallerNotAuthorizedToEditSchedule)
from rctools.exceptions import UserNotAuthorizedToEditInstaller

from rctools.installers import is_company_admin
from rctools.scheduling import (get_customer_scheduled_jobs_from_dynamo, get_scheduled_job)
from rctools.users import is_rc_admin

JOBS_TABLE = os.environ.get('JOBS_TABLE')
JOB_SCHEDULE_TABLE = os.environ.get('JOB_SCHEDULE_TABLE')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
ADMIN_USER_POOL_ID = os.environ.get('ADMIN_USER_POOL_ID')
RC_ADMIN_GROUP_ID = os.getenv('RC_ADMIN_GROUP_ID')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()

dynamodb = boto3.resource('dynamodb')
jobs_table = dynamodb.Table(JOBS_TABLE)
job_schedule_table = dynamodb.Table(JOB_SCHEDULE_TABLE)


@router.get('/schedule/job/{ticket_id}', status_code=status.HTTP_201_CREATED)
def get_installer_job_schedule(ticket_id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    logger.info(f'Getting schedule for job ticket {ticket_id}')
    try:
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        installer_id = user['Username']

        job_schedule = get_scheduled_job(job_schedule_table, ticket_id)
        if job_schedule['installer_id'] != installer_id: 
            raise InstallerNotAuthorizedToEditSchedule()

        return job_schedule

    except InstallerNotAuthorizedToEditSchedule:
        err = f'Installer {installer_id} is not authorized to get schedule for ticket {ticket_id}'
        logger.exception(err)
        return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error posting reservation')
        return JSONResponse({'error': str(e)}, 400)


@router.get('/schedule/{id}', status_code=status.HTTP_201_CREATED)
def get_installer_scheduled_jobs(id: str, X_Amz_Access_Token: Optional[str] = Header(default=None)):
    logger.info(f'Getting scheduled for jobs for installer')
    try:
        user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
        uid = user['Username']

        installer_id = user['Username']
        if not is_rc_admin(cognito_client, ADMIN_USER_POOL_ID, uid, RC_ADMIN_GROUP_ID):
            if not is_company_admin(cognito_client, ADMIN_USER_POOL_ID, uid):
                # Not super admin or company admin is unauthorized
                raise UserNotAuthorizedToEditInstaller()

        scheduled_jobs = get_customer_scheduled_jobs_from_dynamo(job_schedule_table, installer_id)
        # if job_schedule['installer_id'] != installer_id: 
        #     raise InstallerNotAuthorizedToEditSchedule()

        return scheduled_jobs

    # except InstallerNotAuthorizedToEditSchedule:
    #     err = f'Installer {installer_id} is not authorized to get schedule for ticket {ticket_id}'
    #     logger.exception(err)
    #     return JSONResponse({'error': err}, 403)
    except ClientError as e:
        logger.exception(f'Error posting reservation')
        return JSONResponse({'error': str(e)}, 400)

