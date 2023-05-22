import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from pydantic import ValidationError

from rctools.aws.dynamodb import (KEY_COND_GTE, DynamoPrimaryKey, Key,
                                  create_dynamo_record, fetch_items_by_gsi, fetch_items_by_pk,
                                  scan_by_attributes)
from rctools.models.users import Installer
from rctools.models.jobs import JobSchedule, Reservation
from rctools.models.scheduling import Day, Job, Strategy, StrategyFirstAvailable

logger = logging.getLogger()
logger.setLevel(logging.INFO)


MINIMUM_DELAY_BEFORE_SCHEDULING = 48  # delay from first request to the time a job can be scheduled (in hrs)
MINIMUM_RATING_DECAY = .25  # the amount the minumum installer rating required for a job decays per day

DATE_FORMAT = '%Y%m%d'
MINIMUM_DELAY_BEFORE_SCHEDULING = 2  # number of days before first timeslot should appear
MINIMUM_NUMBER_OF_TIMES = 20
MINIMUM_WEEKS_FOR_SCHEDULING = 2
SCHEDULING_INTERVAL = 15  # interval starting on the hour for when we will schedule a job
TIME_SLOT_RESERVATION = 60  # number of minutes a timeslot is reserved when selected by a customer
TOTAL_NUMBER_OF_DAYS_TO_OFFER = 28  # number of days to calculate available timeslots for
WEEKLY_MINIMUM_RATING_DECAY = .75  # the amount
MINIMUM_START_TIME = '0000' # minimum start time a job can be scheduled
MAXIMUM_END_TIME = '2300'# maximum end time a job can be scheduled


# have to approximate drive time between jobs
# will have to consider whether we schedule closer jobs sooner than far away jobs,
# or jobs all in the same area vs a single job by itself


def get_available_times(scheduled_jobs: List[Job], installers: List[Installer], job_tier: Dict, job_zip: str, reservations_table: any, strategy: Strategy = StrategyFirstAvailable()):
    """
    Returns a list of available times for a user to choose from in the app.

    Currently returns at least MIN_WEEKS_FOR_SCHEDULING and at least 
    MIN_NUM_OF_TIMES. 
    
    Once a time is selected, the slot is reserved for TIME_SLOT_RESERVATION
    and then re-opened if the customer has not pre-paid in that time period.

    The algorithm attempts to fill the minimum # of time slots with installers
    in preferential order, moving to installers with lower ratings as necessary
    to fill the times.
    """
    available_times = defaultdict(lambda : defaultdict(list))
    if scheduled_jobs:
        organized_schedule = get_organized_schedule(scheduled_jobs)

    today = datetime.today()
    start = today + timedelta(hours=MINIMUM_DELAY_BEFORE_SCHEDULING)
    end = datetime.strptime(MAXIMUM_END_TIME, '%H%M')
    delta = timedelta(minutes=15)
    job_tier_hours = job_tier['hours'][1]*100

    for i in range(TOTAL_NUMBER_OF_DAYS_TO_OFFER):
        current_day = Day(dt=start + timedelta(days=i), idx=i)
        available_installers = strategy.get_available_installers(current_day, installers, job_tier, job_zip, reservations_table)
        for installer in available_installers:
            t = datetime.strptime(MINIMUM_START_TIME, '%H%M')
            # XXX need reservations, scheduled jobs
            schedule = installer['scheduling']
            if schedule.get('exceptions') and schedule['exceptions'].get(current_day.ts):
                availability = schedule['exceptions'][current_day.ts]
            else:
                availability = schedule[current_day.weekday]
            if not availability['available']:
                break

            while t <= end:
                current_time = int(datetime.strftime(t, '%H%M'))
                # if duration is past endtime move on to next installer
                if availability['end'] < current_time + job_tier_hours:
                    break

                if  availability['end'] - availability['start'] >= job_tier_hours and current_time >= availability['start']:
                    if scheduled_jobs:
                        jobs = organized_schedule[current_day.ts]
                        for j in jobs:
                            if current_time >= j.start_ts and current_time <= j.start_ts + j.duration:
                                continue

                    # Include installer as available
                    available_times[current_day.ts][installer['Username']].append(datetime.strftime(t, '%H:%M'))
                t += delta
    return available_times


def get_available_times_for_day(scheduled_jobs: List[Job], installers: List[Installer], job_tier: Dict, job_zip: str, current_day: datetime, reservations_table, strategy: Strategy = StrategyFirstAvailable()):
    """
    Returns a list of available times for a user to choose from in the app.

    Currently returns at least MIN_WEEKS_FOR_SCHEDULING and at least 
    MIN_NUM_OF_TIMES. 
    
    Once a time is selected, the slot is reserved for TIME_SLOT_RESERVATION
    and then re-opened if the customer has not pre-paid in that time period.

    The algorithm attempts to fill the minimum # of time slots with installers
    in preferential order, moving to installers with lower ratings as necessary
    to fill the times.
    """
    available_times = defaultdict(lambda : defaultdict(list))
    if scheduled_jobs:
        organized_schedule = get_organized_schedule(scheduled_jobs)

    end = datetime.strptime(MAXIMUM_END_TIME, '%H%M')
    delta = timedelta(minutes=15)
    job_tier_hours = job_tier['hours'][1]*100

    current_day = Day(dt=current_day, idx=0)
    available_installers = strategy.get_available_installers(current_day, installers, job_tier, job_zip, reservations_table)

    # XXX this could be more efficient if we place inside get_available_installers
    for installer in available_installers:
        logger.info(f'Checking available times on {current_day} for {installer}')

        t = datetime.strptime(MINIMUM_START_TIME, '%H%M')
        schedule = installer['scheduling']
        # check exceptions
        if schedule.get('exceptions') and schedule['exceptions'].get(current_day.ts):
            availability = schedule['exceptions'][current_day.ts]
        # else use recurring
        else:
            availability = schedule[current_day.weekday]
        if not availability['available']:
            break

        while t <= end:
            current_time = int(datetime.strftime(t, '%H%M'))
            if availability['end'] < current_time + job_tier_hours:
                break

            if  availability['end'] - availability['start'] >= job_tier_hours and current_time >= availability['start']:
                if scheduled_jobs:
                    jobs = organized_schedule[current_day.ts]
                    for j in jobs:
                        if current_time >= j.start_ts and current_time <= j.start_ts + j.duration:
                            continue

                # Include installer as available
                available_times[current_day.ts][installer['Username']].append(datetime.strftime(t, '%H:%M'))
            t += delta
    return available_times


def get_organized_schedule(scheduled_jobs: List[Job]):
    """Bins list of jobs into a dictionary with the start date as the key"""
    organized = defaultdict(defaultdict(list))
    for job in scheduled_jobs:
        start_dt = datetime.fromtimestamp(job.start_time)
        start_ts = datetime.strftime(start_dt, DATE_FORMAT)
        organized[start_ts][job.installer_id].append(job)
    return organized


def create_reservation(reservations_table, data):
    """Posts a new reservation in the reservations table"""
    logger.info(f'Creating reservation with {data}')
    reservation = Reservation(**data).dict()
    resp = create_dynamo_record(reservations_table, reservation)
    logger.info(f'Results from dynamo {resp}')
    reservation_id = reservation['id']
    logger.info(f'reservation {reservation_id} created!')
    return reservation_id


def add_job_to_schedule(job_schedule_table, data, ticket_id):
    """Posts a new job schedule in JobScheduleTable from reservation data"""
    logger.info(f'Creating job schedule with {data}')
    reservations_date = data.pop('reservation_date')
    job_schedule = JobSchedule(**data).dict()
    job_schedule['job_schedule_date'] = reservations_date
    job_schedule['ticket_id'] = ticket_id
    resp = create_dynamo_record(job_schedule_table, job_schedule)

    logger.info(f'Results from dynamo {resp}')
    job_schedule_id = job_schedule['job_schedule_id']
    logger.info(f'schedule {job_schedule_id} created!')
    return job_schedule_id


def get_reservation_by_id(table, id) -> dict:
    response = table.query(KeyConditionExpression=Key('id').eq(id))
    items = response.get('Items', None)
    if items:
        return items[0]
    logger.warn('No reservation found.')


def get_reservations(table) -> List[dict]: 
    items, _ = scan_by_attributes(table)
    reservations = []
    if items:
        for i in items:
            try:
                reservations.append(Reservation(**i))
            except ValidationError:
                logger.exception(f'Error validating ticket {id}. Skipping...')
    return reservations


def get_installer_reservations_by_id(table, installer_id) -> List[Reservation]:
    """
    Queries a dyanmo table for any reservations assigned to the installer after the
    given timestamp
    """
    logger.info(f'Checking for reservations for installer {installer_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {'installer_id': installer_id}
    # pk.sort = {'ts': ts}
    # pk.sort.comparator = KEY_COND_GTE
    reservations, pagination_token = [], None
    while True:
        items, cursor_token = fetch_items_by_pk(table, pk, cursor_token=pagination_token)
        reservations += items
        pagination_token = cursor_token
        if not pagination_token:
            break
    return reservations


def get_scheduled_job(table, id) -> dict:
    response = table.query(KeyConditionExpression=Key('ticket_id').eq(id))
    items = response.get('Items', None)
    if items:
        logger.info(f'Returning job ticket from dynamo {items[0]}')
        return items[0]
    logger.warn('No job ticket found.')


def get_customer_scheduled_jobs_from_dynamo(job_schedule_table, installer_id, limit=20):
    """
    Queries a dyanmo table for any jobs assigned to the customer
    """
    logger.info(f'Checking for jobs for user {installer_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {'installer_id': installer_id}
    # pk.sort = {'ts': mk_timestamp()}
    
    scheduled_jobs, pagination_token = [], None
    while True:
        # Query the customer's tickets using the jobs table
        items, cursor_token = fetch_items_by_gsi(job_schedule_table, pk, 'installer_id', cursor_token=pagination_token)
        # Then pull the whole ticket
        for i in items:
            schedule_pk = DynamoPrimaryKey()
            schedule_pk.partition = {'ticket_id': i['ticket_id']}
            logger.info(f'Fetching ticket_id {i["ticket_id"]}')
            job_items, _ = fetch_items_by_pk(job_schedule_table, schedule_pk)
            scheduled_jobs += job_items
        pagination_token = cursor_token
        if len(items) > limit:
            break
        if not pagination_token:
            break
    logger.info(f'Returning {len(scheduled_jobs)} job(s)')
    return scheduled_jobs