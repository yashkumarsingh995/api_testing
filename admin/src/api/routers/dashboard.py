import logging
import os

from enum import Enum

import boto3
from fastapi import APIRouter
from models import DashboardCard
from rctools.customers import get_all_customers
from rctools.installers import get_all_installers
from rctools.jobs import get_job_tickets


cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')

CUSTOMER_USER_POOL_ID = os.getenv('CUSTOMER_USER_POOL_ID')
INSTALLER_USER_POOL_ID = os.getenv('INSTALLER_USER_POOL_ID')
JOBS_TABLE = os.getenv('JOBS_TABLE')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')

# alerts_table = dynamodb.Table(ALERTS_TABLE)
jobs_table = dynamodb.Table(JOBS_TABLE)
# message_table = dynamodb.Table(MESSAGES_TABLE)

class DashboardDataTypes(str, Enum):
    customers = 'customers'
    chargers = 'chargers'
    installers = 'installers'
    jobs = 'jobs'
    support = 'support'


@router.get('/dashboard/{data}', response_model=DashboardCard)
def get_dashboard_data(data: DashboardDataTypes):
    if data == DashboardDataTypes.installers:
        # get all installers
        installer_card = DashboardCard(title='Installers')
        installers = get_all_installers(cognito_client, s3_client, INSTALLER_USER_POOL_ID, USER_DATA_BUCKET)  # TODO can we call this without going into S3
        scheduled = 0  # TODO waiting on scheduling work
        total_installers = len(installers)
        installer_card.add_entries({
            'total': total_installers,
            'available': total_installers - scheduled,
            'scheduled': scheduled
        })
        return installer_card

    elif data == DashboardDataTypes.customers:
        # get all customers, get all scheduled
        customer_card = DashboardCard(title='Customers')
        customers = get_all_customers(cognito_client, s3_client, CUSTOMER_USER_POOL_ID, USER_DATA_BUCKET)
        scheduled = 0  # TODO waiting on scheduling work
        total_customers = len(customers)
        customer_card.add_entries({
            'total': total_customers,
            'scheduled': scheduled
        })
        return customer_card
    
    elif data == DashboardDataTypes.jobs:
        # get all jobs, get the day's total, get open, canceled and potential
        jobs_card = DashboardCard(title='Jobs')
        jobs = get_job_tickets(jobs_table)
        days_total = 0  # TODO waiting on scheduling work
        open = 0  # TODO waiting on scheduling work
        cancelled = 0  # TODO waiting on scheduling work
        potential = 0  # TODO waiting on scheduling work (total_completed - scheduled)
        total_jobs = len(jobs)
        jobs_card.add_entries({
            'total': total_jobs,
            'day_total': days_total,
            'open': open,
            'cancelled': cancelled,
            'potential': potential
        })
        return jobs_card
    
    elif data == DashboardDataTypes.support:
        # get all support tickets TBD
        support_card = DashboardCard(title='Support Tickets')
        support_card.add_entries({
            'total': 0,
            'day_total': 0,
            'open': 0,
            'resolved': 0,
            'high_severity': 0
        })
        return support_card

    elif data == DashboardDataTypes.chargers:
        # get all chargers TBD
        chargers_card = DashboardCard(title='Chargers')
        chargers_card.add_entries({
            'total': 0,
            'day_total': 0,
            'models': 0
        })
        return chargers_card
