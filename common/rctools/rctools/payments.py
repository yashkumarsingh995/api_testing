import logging
import stripe

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Literal, Union


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def cancel_hold(api_key: str, payment_intent_id: str):
    """Cancels a hold via payment intent ID"""
    stripe.api_key = api_key
    logger.info(f'Canceling hold on payment intent {payment_intent_id}')
    stripe.PaymentIntent.cancel(payment_intent_id)


def create_connected_installer_account(api_key: str, email: str):
    """
    Creates a connected installer account for payouts to occur after collecting fees from a
    customer
    """
    stripe.api_key = api_key
    logger.info(f'Creating Stripe account for email {email}')
    resp = stripe.Account.create(
        type="express",
        country="US",
        email=email,
        capabilities={
            "transfers": {"requested": True},
        }
    )
    return resp


def create_connected_installer_account_link(api_key: str, account_id: str, refresh_url: str, return_url: str):
    """Returns a time sensitive link to Stripe account onboarding"""
    stripe.api_key = api_key
    return stripe.AccountLink.create(
        account=account_id,
        refresh_url=refresh_url,  # URL to generate another account link
        return_url=return_url,
        type='account_onboarding'
    )


def create_connected_installer_payment_method(api_key: str, customer_id: str, pub_key: str):
    """"""
    stripe.api_key = api_key
    ephemeralKey = stripe.EphemeralKey.create(
        customer=customer_id,
        stripe_version='2020-08-27',
    )
    paymentIntent = stripe.PaymentIntent.create(
        amount=1099,
        currency='us',
        customer=customer_id,
        automatic_payment_methods={
            'enabled': True,
        },
        application_fee_amount=123,
        transfer_data={
        'destination': '{{CONNECTED_ACCOUNT_ID}}',
        },
    )
    return {
        'paymentIntent': paymentIntent.client_secret,
        'ephemeralKey': ephemeralKey.secret,
        'customer_id': customer_id,
        'publishableKey': pub_key
    }


def create_customer(api_key: str, email: str, payment_method_id: str):
    """Creates a Stripe customer"""
    stripe.api_key = api_key
    return stripe.Customer.create(
        email=email,
        payment_method=payment_method_id,
        invoice_settings={
            'default_payment_method': payment_method_id
        }
    )


def create_payment_intent(api_key: str, customer_id: str, payment_method: str, amount_in_cents: int, metadata: dict):
    stripe.api_key = api_key
    # Since we are providing the payment method from client, create and confirm in same call
    stripe_response = stripe.PaymentIntent.create(
        amount=amount_in_cents,
        confirm=True,  # Creates and confirms in same call
        currency='usd',
        customer=customer_id,
        description=f"Initial processing payment for premium subscription(s)",
        payment_method=payment_method,
        payment_method_types=['card'],
        metadata=metadata
    )
    logger.info(f'Response from stripe "{stripe_response["status"]}"')
    return stripe_response


def create_subscription(api_key: str, description: str, customer_id: str, amount_in_cents: int, interval: Union[Literal['year'], Literal['month']], metadata: dict):
    """Creates a recurring subscription in Stripe"""
    logger.info('Starting subscription for recurring payments')
    stripe.api_key = api_key
    
    today = datetime.now()
    trial_end = today + relativedelta(years=1)
    if interval == 'month':
        trial_end = today + relativedelta(months=1)

    # Create price object
    price_resp = stripe.Price.create(
        nickname=description,
        unit_amount=amount_in_cents,
        product_data={
            'name': description,
            'metadata': metadata
        },
        currency='usd',
        recurring={
            'interval': interval,
            'usage_type': 'licensed',
        },
    )
    logger.info(price_resp)

    # Set subscription
    sub_resp = stripe.Subscription.create(
        customer=customer_id,
        items=[{
            'price': price_resp['id'],
            'quantity': 1
        }],
        metadata=metadata,
        trial_end=trial_end
    )
    logger.info(sub_resp)
    return sub_resp



def charge_for_a_hold(api_key: str, payment_intent_id: str, amount: float):
    """
    Charges a user for the held charge. Note, Stripe allows us to charge for an amount different than
    what the hold was made for
    """
    stripe.api_key = api_key
    return stripe.PaymentIntent.capture(
        payment_intent_id,
        amount_to_capture=amount
    )


def has_user_completed_onboarding(api_key: str, account_id: str):
    """
    Determines whether or not a user has completed onboarding by checking charges_enabled per the
    Stripe documentation here: 
    https://stripe.com/docs/connect/collect-then-transfer-guide?platform=react-native&ui=payment-sheet#handle-users
    """
    stripe.api_key = api_key
    account = stripe.Account.retrieve(account_id)
    return account['charges_enabled']


def place_a_hold_on_customer_account(api_key:str, amount: float):
    """
    Places a hold on a customer account for an installation. Holds are valid until a job is complete
    """
    stripe.api_key = api_key
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency='usd',
        payment_method_types=['card'],
        capture_method='manual',
    )

def start_a_subscription(api_key: str, installer_id: str, price_id: str):
    """Starts a subscription payment for a given installer user"""
    stripe.api_key = api_key
    stripe.Subscription.create(
        customer=installer_id,
        items=[{'price': price_id}],
    )
