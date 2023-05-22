import json
import logging
import random

from rctools.aws.s3 import get_object_from_s3, put_object_into_s3

from mergedeep import merge, Strategy
from pydantic import ValidationError
from typing import List
from rctools.aws.dynamodb import create_dynamo_record, Key, scan_by_attributes, update_dynamo_record
from rctools.customers import get_customer
from rctools.exceptions import CustomerNotAuthorizedToEditTicket
from rctools.messages import find_conversation

from rctools.models import JobTicket, JobTier


logger = logging.getLogger()
logger.setLevel(logging.INFO)


BI_1 = JobTier(
    name='BI-1',
    description='$1,500 (Basic - BI-1) [4-6 Hrs] @ 5 Hrs',
    hours=[4,6],
    num_chargers=1,
    price=1500
)

BI_2 = JobTier(
    name='BI-2',
    description='Customer Price for 2 (BI-2) Installs [5-6 Hrs] @ 6 Hrs',
    hours=[5,6],
    num_chargers=2,
    price=2000
)

BI_3 = JobTier(
    name='BI-3',
    description='Customer Price for 3 (BI-3) Installs [6-7 Hrs] @ 7 Hrs',
    hours=[6,7],
    num_chargers=3,
    price=2500
)

II_1 = JobTier(
    name='II-1',
    description='$2,000 (Intermediate - II-1) [6-8 Hrs] @ 7 Hrs',
    hours=[6,8],
    num_chargers=1,
    price=2000
)

II_2 = JobTier(
    name='II-2',
    description='Customer Price for 2 (II-2) Installs [7-8 Hrs] @ 8 Hrs',
    hours=[7,8],
    num_chargers=2,
    price=2500
)

II_3 = JobTier(
    name='II-3',
    description='Customer Price for 3 (II-3) Installs [8-9 Hrs] @ 9 Hrs',
    hours=[8,9],
    num_chargers=3,
    price=3000
)

AI_1 = JobTier(
    name='AI-1',
    description='☆$2,500 (Advanced - AI-1) [8-10 Hrs] @ 9 Hrs',
    hours=[8,10],
    num_chargers=1,
    price=2500
)

AI_2 = JobTier(
    name='AI-2',
    description='Customer Price for 2 (AI-2) Installs [9-11 Hrs] @ 10 Hrs',
    hours=[9,11],
    num_chargers=2,
    price=3125
)

AI_3 = JobTier(
    name='AI-3',
    description='Customer Price for 3 (AI-3) Installs [10-12 Hrs] @ 11 Hrs',
    hours=[10,12],
    num_chargers=3,
    price=3750
)

AI80_1 = JobTier(
    name='AI80-1',
    description='$3,000 (Advanced - AI80-1) [8-10 Hrs] @ 9 Hrs',
    hours=[8,10],
    num_chargers=1,
    price=3000
)

AI80_2 = JobTier(
    name='AI80-2',
    description='Customer Price for 2 (AI80-2) Installs [9-11 Hrs] @ 10 Hrs',
    hours=[9,11],
    num_chargers=2,
    price=4500
)

AI80_3 = JobTier(
    name='AI80-3',
    description='Customer Price for 3 (AI80-3) Installs [10-12 Hrs] @ 11 Hrs',
    hours=[10,12],
    num_chargers=3,
    price=6000
)


def add_photo_to_s3(s3_client, bucket, id, data):
    s3_path = f"photos/{id}/{data.photo_id}.json"
    put_object_into_s3(s3_client, bucket, s3_path, json.dumps(data))


def add_note_to_s3(s3_client, bucket, id, data):
    s3_path = f"notes/{id}/{data.note_id}.json"
    put_object_into_s3(s3_client, bucket, s3_path, json.dumps(data.dict()))


def get_job_notes(s3_client, bucket, ticket_id, note_ids):
    notes = []
    for id in note_ids:
        s3_path = f"notes/{ticket_id}/{id}.json"
        notes.append(get_object_from_s3(s3_client, bucket, s3_path))
    return notes


def get_job_photos(s3_client, bucket, ticket_id, photo_ids):
    photos = []
    for id in photo_ids:
        s3_path = f"notes/{ticket_id}/{id}.json"
        photos.append(get_object_from_s3(s3_client, bucket, s3_path))
    return photos


def add_note_to_job_ticket(table, note_id, ticket_id, customer_id):
    """Adds note_id to job ticket"""
    job = get_job_ticket(table, ticket_id)
    if job.customer_id != customer_id:
        raise CustomerNotAuthorizedToEditTicket()
    job_ticket = job.dict()
    if not job_ticket.get('notes'):
        job.notes = []
    job.notes.append(note_id)
    update_job_ticket(table, job.dict(), ticket_id, customer_id)


def add_photo_to_job_ticket(table, photo_id, ticket_id, customer_id):
    """Adds photo_id to job ticket"""
    job = get_job_ticket(table, ticket_id)
    if job.customer_id != customer_id:
        raise CustomerNotAuthorizedToEditTicket()
    job_ticket = job.dict()
    if not job_ticket.get('photos'):
        job.photos = []
    job.photos.append(photo_id)
    update_job_ticket(table, job.dict(), ticket_id, customer_id)


# def get_job_ticket(table, id) -> JobTicket:  # XXX returning a di
def get_job_ticket(table, id) -> dict:
    response = table.query(KeyConditionExpression=Key('ticket_id').eq(id))
    items = response.get('Items', None)
    if items:
        logger.info(f'Returning job ticket from dynamo {items[0]}')
        return items[0]
    logger.warn('No job ticket found.')


# def get_job_tickets(table) -> List[JobTicket]:
def get_job_tickets(table) -> List[dict]: 
    items, _ = scan_by_attributes(table)
    tickets = []
    if items:
        for i in items:
            try:
                tickets.append(i)
            except ValidationError:
                logger.exception(f'Error validating ticket {id}. Skipping...')
    return tickets


def get_job_tier(job_ticket: JobTicket) -> JobTier:
    # XXX entirely placeholder
    num_chargers = job_ticket['job_scope']['chargers']['num_chargers']
    if num_chargers == 1:
        return random.choice([BI_1, II_1, AI_1, AI80_1])
    if num_chargers == 2:
        return random.choice([BI_2, II_2, AI_2, AI80_2])
    return random.choice([BI_3, II_3, AI_3, AI80_3])
    

def fill_out_job_ticket(cognito_client, s3_client, messages_table, pool_id, bucket, job_ticket: dict) -> JobTicket:
    """Looks up any missing information on a given job ticket and fills it in"""
    if not job_ticket.get('customer') and 'customer_id' in job_ticket:
        job_ticket['customer'] = get_customer(cognito_client, s3_client, pool_id, bucket, job_ticket['customer_id'])  # gets filtered to just name fields by the model
    if not job_ticket.get('conversation_id'):
        job_ticket['conversation_id'] = find_conversation(messages_table, job_ticket['installer_id'], job_ticket['customer_id'])
    return job_ticket


def put_new_job(table, data) -> dict:
    """Creates a new job ticket object"""
    logger.info(f'Creating job with {data}')
    job = JobTicket(**data).dict()
    resp = create_dynamo_record(table, job)
    logger.info(f'Results from dynamo {resp}')
    return job['ticket_id']


def update_job_ticket(table, data, id, customer_id) -> str:
    """Update existing job ticket in jobs table"""
    logger.info(f'Attaching data {data} to {id}')
    job_ticket = get_job_ticket(table, id)
    if job_ticket['customer_id'] != customer_id:
        raise CustomerNotAuthorizedToEditTicket()
 
    logger.info(f'Before job ticket {job_ticket["job_scope"]}')
    updated_ticket = JobTicket(**merge({}, job_ticket, data))  # validate new object
    update_data = updated_ticket.dict()
    logger.info(f'New job ticket {update_data["job_scope"]}')
    update_dynamo_record(table, {'ticket_id': update_data.pop('ticket_id'), 'ts': update_data.pop('ts')}, update_data)
    
    return updated_ticket.ticket_id
