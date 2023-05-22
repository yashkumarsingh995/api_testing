import calendar
import logging

from datetime import datetime
from typing import Dict, List, Optional

from rctools.aws.dynamodb import DynamoPrimaryKey, fetch_items_by_gsi
from rctools.exceptions import ReservationConflict
from rctools.installers import (in_installer_scope, in_service_area)
from rctools.models.base import ReadiChargeBaseModel
from rctools.models.jobs import Reservation
from rctools.models.users import Installer
from rctools.utils import mk_timestamp


logger = logging.getLogger()
logger.setLevel(logging.INFO)

DATE_FORMAT = '%Y-%m-%d'

RESERVATION_EXPIRATION_TIME = 90 * 60 * 1000 # 1.5 hours to ms
STRATEGY__FIRST_AVAILABLE = 'strategy__first_available'
STRATEGY__PRIORITIZE_RATINGS = 'strategy__prioritize_ratings'


class Job(ReadiChargeBaseModel):
    installer_id: Optional[str]
    start_time: int   # unixtime

    @property
    def duration(self) -> int:
        """
        Returns the upper limit of the range of times given for
        the job to be used for scheduling - in minutes
        """
        # XXX
        return 240

    @property
    def duration_s(self) -> int:
        # XXX
        return 240 * 60

    @property
    def duration_ms(self) -> int:
        # XXX
        return 240 * 60 * 1000


class Day(ReadiChargeBaseModel):
    dt: datetime
    idx: int

    @property
    def ts(self):
        return datetime.strftime(self.dt, DATE_FORMAT)

    @property
    def weekday(self):
        # return calendar.day_name[self.dt.weekday()]
        return calendar.day_abbr[self.dt.weekday()].lower()


class Strategy(ReadiChargeBaseModel):
    name: str

    def get_available_installers(self, *args, **kwargs):
        pass


class StrategyPrioritizeRatings(Strategy):
    """
    This strategy prioritizes installers with high ratings and installers
    with priority scheduling for the first 7 days of availability when
    scheduling an appointment.

    After that, installers with lower ratings are allowed in the pool at a
    graduated basis, meaning a low rating installer with wide availability
    would not show up as available until the second or third week out from
    the current date. 
    """
    min_rating = 4.25
    name = STRATEGY__PRIORITIZE_RATINGS
    weekly_rating_decay = .5


    def get_available_installers(self, current_day: Day, installers: List[Installer], job_tier: Dict, job_zip: str, reservations_table) -> List[Installer]:
        """Returns the list of installers available for a given day"""
        available = []

        min_rating = self.min_rating - (current_day.idx % 7 * self.weekly_rating_decay)
        for i in installers:
            if i.rating < min_rating:
                continue
            # TODO check if they are willing to do this type of job
            # TODO calculate if they are close enough to qualify
            available.append(i)


class StrategyFirstAvailable(Strategy):
    """
    This strategy attempts to provide all available installers within the 
    given installer pool as soon as they are available. No installers are
    restricted from the first couple weeks of scheduling.

    In a given timeslot, installers are still sorted by rating/prioirty, but
    otherwise all available installers will be included in the selection pool.
    """
    min_rating = 3
    name = STRATEGY__FIRST_AVAILABLE


    def get_available_installers(self, current_day: Day, installers: List[Installer], job_tier: Dict, job_zip: str, reservations_table) -> List[Installer]:
        """Returns the list of installers available for a given day"""
        available = []
        for installer in installers:
            uid = installer['Username']
            # if i.rating < self.min_rating:
            #     continue
            try:
                current_time = mk_timestamp()
                if installer.get('scheduling') and installer.get('service_options') and installer.get('zip'):  # XXX for bad users, maybe check finished onboarding
                    # check if they are willing to do this type of job and close enough to qualify
                    if in_installer_scope(installer['service_options'], job_tier['name']) and in_service_area(installer['zip'], job_zip):
                        # assuming an installer cannot have two reservations in the same day
                        reservations = get_installer_reservations(reservations_table, uid)
                        for res in reservations: 
                           if res['reservation_date'] == current_day and current_time - res['ts'] <= RESERVATION_EXPIRATION_TIME:
                                print('found resevation for date', res)
                                raise ReservationConflict()

                        installer['Username'] = uid
                        available.append(installer)

            except ReservationConflict:
                logger.info(f'Found reservation {res} for day {current_day}')
                continue
           
        return available


def get_installer_reservations(jobs_table, installer_id) -> List[Reservation]:
    """
    Queries a dyanmo table for any reservations assigned to the installer after the
    given timestamp
    """
    logger.info(f'Checking for reservations for installer {installer_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {'installer_id': installer_id}
    # pk.sort = {'ts': ts}   # TODO use a reasonable GTE time so we don't pull _everything_
    # pk.sort.comparator = KEY_COND_GTE 
    reservations, pagination_token = [], None
    while True:
        items, cursor_token = fetch_items_by_gsi(jobs_table, pk, 'installer_id', cursor_token=pagination_token)
        pagination_token = cursor_token
        if not pagination_token:
            break
        reservations += items
    logger.info(f'Returning {len(reservations)} reservations(s)')
    return reservations
