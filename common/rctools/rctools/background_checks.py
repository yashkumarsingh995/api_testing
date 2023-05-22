"""Interface with ClearChecks API"""
import json
import logging
from typing import List

import requests
from rctools.aws.dynamodb import create_dynamo_record, delete_dynamo_record, DynamoPrimaryKey, fetch_items_by_pk
from rctools.aws.secrets import get_json_secret
from rctools.utils import create_random_code, mk_timestamp

logger = logging.getLogger()
logger.setLevel(logging.INFO)



def check_order_status(email: str, installer_id) -> str:
    pass


def create_background_check_hash(table, installer_id) -> str:
    """"Creates a new single-use background check hash in the table"""
    hash = create_random_code(16)
    create_dynamo_record(table, {
        'installer_id': installer_id,
        'hash': hash,
        'ts': mk_timestamp()
    })
    return hash


def create_request_body(emails: List[str]):
    return {
        'report_sku': 'HIRE1',
        'order_quantity': len(emails),
        'applicant_emails': emails,
        'drug_test': 'N',
        'drug_sku': 'drug',
        'mvr': 'Y',
        'employment': 'Y',
        'education': 'Y',
        'blj': 'Y',
        'federal_criminal': 'Y',
        'terms_agree': 'Y'
    }


def delete_background_check_hash(table, installer_id):
    pk = DynamoPrimaryKey()
    pk.partition = installer_id
    return delete_dynamo_record(table, pk)


def get_background_check_api_key(secrets_client, aws_region, secret_name):
    """Returns API key from global context or fetches it from Secrets Manager"""
    secrets = get_json_secret(secrets_client, secret_name, aws_region)
    return secrets['api_key']


def get_background_check_hash(table, installer_id):
    pk = DynamoPrimaryKey()
    pk.partition = installer_id
    items = fetch_items_by_pk(table, pk)
    return items[0]


def get_headers():
    """Returns required headers for ClearCheck API"""
    return {
        'Content-Type': 'application/json',
        'Accepts': 'application/json'
    }


def order_background_check(api_root, api_key, email) -> str:
    # Send create new order request
    resp = send_create_new_order_request(api_root, api_key, email)
    resp_json = resp.json()
    logger.info(f'Response from ClearChecks is {resp.status_code}: {resp.content}')
    # Endpoint returns an array of applicants for submitting multiple orders
    applicants = resp_json['applicants']
    report_key = applicants[0]['report_key']
    return report_key


def queue_background_check_status_check(sqs_client, queue_url, report_key, installer_id):
    # Queue background check status job
    return sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({
            'report_key': report_key,
            'installer_id': installer_id
        })
    )


def send_create_new_order_request(api_root, api_key, email):
    body = create_request_body([email])
    url = f'{api_root}/orders/new?api_token={api_key}'
    logger.info(f'Submitting order request to {url} with {body}')
    return requests.post(
        url,
        json=body,
        headers=get_headers()
    )
    