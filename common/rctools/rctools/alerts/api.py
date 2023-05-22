import logging
from typing import List

from rctools.aws.dynamodb import (KEY_COND_GTE, DynamoPrimaryKey,
                                  create_dynamo_record, fetch_items_by_pk)
from rctools.models.alerts import Alert

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def add_user_alert(table, user_id, alert: Alert) -> str:
    """
    Adds an alert for the specified user to the alerts table.

    Returns the newly created alert ID.
    """
    logger.info(f'Adding alert {alert.json()} for user {user_id}')
    if not alert.uid:
        alert.uid = user_id
    return create_dynamo_record(table, alert.dict())


def check_for_user_alerts(table, user_id, limit=20) -> List[Alert]:
    """
    Queries a dyanmo table for any alerts assigned to the user after the
    given timestamp
    """
    logger.info(f'Checking for alerts for user {user_id}')
    pk = DynamoPrimaryKey()
    pk.partition = {'uid': user_id}
    alerts, pagination_token = [], None
    while True:
        items, cursor_token = fetch_items_by_pk(table, pk, cursor_token=pagination_token, limit=limit)
        alerts += items
        pagination_token = cursor_token
        if not pagination_token:
            break
    return alerts
