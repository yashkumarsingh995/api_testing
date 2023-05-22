import logging
import os
from typing import Optional
from uuid import uuid4

import boto3
from fastapi import APIRouter, Header, status
from rctools.aws.cognito import get_user_with_access_token, merge_user_data
from rctools.aws.secrets import get_json_secret
from rctools.installers import get_installer_data_from_s3, update_installer_data_in_s3
from rctools.payments import (
    create_customer, create_payment_intent, create_subscription,
    create_connected_installer_account, create_connected_installer_account_link
)
from rctools.utils import mk_timestamp

AWS_REGION_NAME = os.environ.get('AWS_REGION')
INSTALLER_USER_POOL_ID = os.environ.get('INSTALLER_USER_POOL_ID')
PUBLIC_API_ROOT = os.environ.get('PUBLIC_API_ROOT')
STRIPE_PRIVATE_KEY = os.environ.get('STRIPE_PRIVATE_KEY')
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

g_context = {}


def get_stripe_api_key():
    if 'stripe_api_key' not in g_context:
        secret = get_json_secret(secrets_client, STRIPE_PRIVATE_KEY, AWS_REGION_NAME)
        g_context['stripe_api_key'] = secret['api_key']
    return g_context['stripe_api_key']


@router.get('/payment/account/onboarding', status_code=status.HTTP_200_OK)
def get_account_onboarding_link(X_Amz_Access_Token: Optional[str] = Header(default=None)):
    """
    Returns an account onboarding link for a Stripe connected account. If no account exists on the
    installer object, a new one is created and saved
    """
    logger.info('Retrieving new account onboarding link')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    user_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, uid)
    merge_user_data(user, user_data)

    api_key = get_stripe_api_key()

    payments = user.get('payments')
    if not payments:
        payments = {}
    account_id = payments.get('connected_account_id')
    refresh_token = payments.get('refresh_token')
    if not account_id:
        logger.info('Creating Stripe connected account')
        account = create_connected_installer_account(api_key, user['email'])
        logger.info(account)
        account_id = account['id']
        refresh_token = str(uuid4())
        update_installer_data_in_s3(s3_client, USER_DATA_BUCKET, uid, {'payments': {'connected_account_id': account_id, 'refresh_token': refresh_token}})
    link = create_connected_installer_account_link(
        api_key,
        account_id,
        f'https://{PUBLIC_API_ROOT}/installer/onboarding/refresh?uid={uid}&refresh_token={refresh_token}',
        f'https://{PUBLIC_API_ROOT}/installer/onboarding/complete'
    )
    logger.info(f'Returning link {link}')
    return link

@router.post('/payment/premium/pay', status_code=status.HTTP_201_CREATED)
def pay_for_premium_subscriptions(data: dict, X_Amz_Access_Token: Optional[str] = Header(default=None)) -> str:
    """
    Submits payment for premium services to Stripe
    """
    logger.info('Processing payments for premium options')
    user = get_user_with_access_token(cognito_client, X_Amz_Access_Token)
    uid = user['Username']

    user_data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, uid)
    
    api_key = get_stripe_api_key()

    # Get customer ID
    payments = user_data.get('payments', {})
    customer_id = payments.get('customer_id')
    if not customer_id:
        customer = create_customer(api_key, user_data['email'], data['payment_method_id'])
        customer_id = customer['id']
    # Create intent
    amount_in_cents = data['amount'] * 100
    payment_intent = create_payment_intent(api_key, customer_id, data['payment_method_id'], amount_in_cents, metadata={'uid': uid})
    # Create subscription
    subscription_ids = []
    for product in data['premium_options']:
        # name, price, repeat
        interval = 'month' if product['repeat'] == 'monthly' else 'year'
        subscription = create_subscription(
            api_key, product['name'], customer_id, product['price'] * 100, interval, metadata={'uid': uid}
        )
        subscription_ids.append(subscription['id'])
    # Record payment data
    update = {
        'ts': mk_timestamp(),
        'customer_id': customer_id,
        'payment_id': payment_intent['id'],
        'plans': data['premium_options'],
        'subscription_ids': subscription_ids,
        'amount_in_cents': amount_in_cents
    }
    update_installer_data_in_s3(s3_client, USER_DATA_BUCKET, uid, {'payments': {**payments, **update}})
    # Return confirmed intent
    return payment_intent['id']