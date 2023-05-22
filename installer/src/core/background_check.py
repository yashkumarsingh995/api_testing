"""Interface with ClearChecks API"""
import json
import os
import logging
from typing import Dict

import boto3
import requests
from aws_lambda_powertools.utilities.typing import LambdaContext
from rctools.aws.secrets import get_json_secret
from rctools.alerts import add_user_alert, create_background_check_approved_alert, create_background_check_rejected_alert
from rctools.installers import update_installer_data_in_s3, get_installer_data_from_s3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

ALERTS_TABLE = os.environ.get('ALERTS_TABLE')
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME')
BACKGROUND_CHECK_API_ROOT = os.getenv('BACKGROUND_CHECK_API_ROOT')
BACKGROUND_CHECK_QUEUE_URL = os.getenv('BACKGROUND_CHECK_QUEUE_URL')
BACKGROUND_CHECK_SECRET_NAME = os.environ.get('BACKGROUND_CHECK_SECRET_NAME')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')

alerts_table = dynamodb.Table(ALERTS_TABLE)

g_context = {}


STATUSES = {
    "P": "pending",
    "C": "completed",
    "A": "adverse"
}



def get_api_key():
    """Returns API key from global context or fetches it from Secrets Manager"""
    if 'api_key' not in g_context:
        secrets = get_json_secret(BACKGROUND_CHECK_SECRET_NAME, AWS_REGION_NAME)
        g_context['api_key'] = secrets['api_key']
    return g_context['api_key']


def check_order_status(event: Dict[str, any], context: LambdaContext) -> str:
    """
    Checks the status of a pending background check. Responses will come in either
    "P" for pending, "C" for complete or "A" for adverse (or failed). An example response is:

    status	"P"
    flagged_for_end_user_review	false
    reports	
        background_report	"C"
        mvd_status	"C"
        education_status	"C"
        drug_status	"C"
        blj_status	"C"
        federal_criminal_status	"C"
    """
    for record in event['Records']:
        payload = json.loads(record['body'])
        report_key = payload['report_key']
        installer_id = payload['installer_id']
        retries = int(payload.get('retries', 0))

        resp = requests.get(
            f'{BACKGROUND_CHECK_API_ROOT}/reports/{report_key}/status?api_token={get_api_key()}'
        )
        resp_json = resp.json()
        reports = resp_json['reports']
        # Check for success
        if resp_json['status'] == STATUSES['C']:
            # Send approved alert
            add_user_alert(alerts_table, installer_id, create_background_check_approved_alert(installer_id))
        elif resp_json['status'] == STATUSES['A'] and len(reports) > 0 or retries > 96 * 2:  # 96 * 2 should give us about a 2 day period of checks
            # Send rejected alert if failed once reports have been filed
            add_user_alert(alerts_table, installer_id, create_background_check_rejected_alert(installer_id))
        elif resp_json['status'] == STATUSES['P'] or len(reports) == 0:
            # Requeue message if pending or if no reports have been filed
            retries += 1
            return sqs_client.send_message(
                QueueUrl=BACKGROUND_CHECK_QUEUE_URL,
                MessageBody=payload,
                DelaySeconds=900,
                MessageAttributes=record['messageAttributes']
            )
        else:
            logger.info(f'Background check came back {resp_json["status"]}, {STATUSES[resp_json["status"]]}')
        # Convert ClearChecks to readable statuses
        resp_json['status'] = STATUSES[resp_json['status']]
        for k in resp_json['reports'].keys():
            resp_json['reports'][k] = STATUSES[resp_json['reports'][k]]
        # And update user data
        data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, installer_id)
        update = {'background_check': {**data.get('background_check', {}), **resp.dict()}}
        logger.info(f'Updating user data with {update}')
        update_installer_data_in_s3(s3_client, USER_DATA_BUCKET, installer_id, update)
